#!/usr/bin/env python3

import os
import glob
import hcl2
import re
import argparse

def parse_terraform(tf_dir):
    resources = {}
    edges = []
    tf_files = glob.glob(os.path.join(tf_dir, '*.tf'))

    for tf_file in tf_files:
        with open(tf_file, 'r') as f:
            obj = hcl2.load(f)

        # Extract resources
        for block in obj.get('resource', []):
            for res_type, instances in block.items():
                for res_name, attrs in instances.items():
                    key = f"{res_type}.{res_name}"
                    resources[key] = {
                        'type': res_type,
                        'name': res_name,
                        'attrs': attrs
                    }

        # Extract modules (optional grouping)
        for block in obj.get('module', []):
            for mod_name, attrs in block.items():
                key = f"module.{mod_name}"
                resources[key] = {
                    'type': 'module',
                    'name': mod_name,
                    'attrs': attrs
                }

    # Detect simple interpolation-based edges
    pattern = re.compile(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)\.')
    for src, data in resources.items():
        for val in data['attrs'].values():
            # string values
            if isinstance(val, str):
                for match in pattern.findall(val):
                    if match in resources:
                        edges.append((src, match))
            # lists of strings
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        for match in pattern.findall(item):
                            if match in resources:
                                edges.append((src, match))

    return resources, edges

def generate_plantuml(resources, edges, output_file):
    with open(output_file, 'w') as f:
        f.write("@startuml\n")
        f.write("skinparam componentStyle rectangle\n\n")

        # Define nodes
        for key, data in resources.items():
            alias = key.replace('.', '_').replace('-', '_')
            label = key
            f.write(f'component "{label}" as {alias}\n')

        f.write("\n")

        # Define edges
        for src, tgt in edges:
            src_alias = src.replace('.', '_').replace('-', '_')
            tgt_alias = tgt.replace('.', '_').replace('-', '_')
            f.write(f"{src_alias} --> {tgt_alias}\n")

        f.write("\n@enduml\n")

def main():
    parser = argparse.ArgumentParser(
        description="Generate a PlantUML diagram from Terraform HCL files.")
    parser.add_argument(
        "--tf-dir", default="terraform",
        help="Path to directory containing .tf files")
    parser.add_argument(
        "--output", default="architecture.puml",
        help="Output PlantUML filename")
    args = parser.parse_args()

    resources, edges = parse_terraform(args.tf_dir)
    generate_plantuml(resources, edges, args.output)
    print(f"✅ Generated {args.output} ({len(resources)} nodes, {len(edges)} edges)")

if __name__ == "__main__":
    main()
