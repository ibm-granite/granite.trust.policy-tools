#!/usr/bin/env python3
#
# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0
#

"""Generate a markdown tree of risks from the safety policy YAML files."""

import glob
import yaml
from pathlib import Path


def load_yaml_files(policy_dir: Path) -> list[dict]:
    """Load all YAML policy files from the directory."""
    policies = []

    for yaml_file in policy_dir.glob("*.yaml"):
        # Skip the schema file
        if yaml_file.parent.name == "specs":
            continue

        with open(yaml_file, "r") as f:
            try:
                data = yaml.safe_load(f)
                if data and "risk_group" in data:
                    policies.append(data)
            except yaml.YAMLError as e:
                print(f"Error parsing {yaml_file}: {e}")

    return policies


def format_risk_group_name(name: str) -> str:
    """Convert snake_case to Title Case."""
    return name.replace("_", " ").title()


def generate_markdown(policies: list[dict]) -> str:
    """Generate markdown content from policy data."""
    lines = ["# Safety Policy v1.0 - Risk Tree", ""]

    # Sort policies by risk_group_id
    sorted_policies = sorted(policies, key=lambda p: p.get("risk_group_id", 999))

    for policy in sorted_policies:
        risk_group_id = policy.get("risk_group_id", "?")
        risk_group_name = format_risk_group_name(policy.get("risk_group", "Unknown"))

        lines.append(f"## {risk_group_id}. {risk_group_name}")

        if policy.get("description"):
            lines.append(f"*{policy['description']}*")

        lines.append("")

        risks = policy.get("risks", [])
        for risk in risks:
            risk_id = risk.get("risk_id", "?")
            risk_name = format_risk_group_name(risk.get("risk", "Unknown"))
            lines.append(f"- **{risk_id}** {risk_name}")

            if risk.get("description"):
                lines.append(f"  - {risk['description']}")

        lines.append("")

    return "\n".join(lines)


def generate_mermaid_split(policies: list[dict]) -> str:
    """Generate multiple mermaid graphs in one file, one per risk group."""
    lines = ["# Safety Policy v1.0 - Risk Graphs", ""]

    # Sort policies by risk_group_id
    sorted_policies = sorted(policies, key=lambda p: p.get("risk_group_id", 999))

    for policy in sorted_policies:
        risk_group_id = policy.get("risk_group_id", "?")
        risk_group_name = format_risk_group_name(policy.get("risk_group", "Unknown"))

        lines.append(f"## {risk_group_id}. {risk_group_name}")
        lines.append("")
        lines.append("```mermaid")
        lines.append("graph LR")

        group_node_id = f"G{risk_group_id}"
        lines.append(f"    {group_node_id}[{risk_group_name}]")

        risks = policy.get("risks", [])
        for risk in risks:
            risk_id = risk.get("risk_id", "?")
            risk_name = format_risk_group_name(risk.get("risk", "Unknown"))
            risk_node_id = f"R{str(risk_id).replace('.', '_')}"
            lines.append(f"    {group_node_id} --> {risk_node_id}[{risk_name}]")

        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def generate_exceptions(policies: list[dict]) -> str:
    """Generate markdown content listing exceptions from policy data."""
    lines = ["# Safety Policy v1.0 - Exceptions", ""]
    lines.append("This document lists all exceptions defined in the policy files.")
    lines.append("")

    # Sort policies by risk_group_id
    sorted_policies = sorted(policies, key=lambda p: p.get("risk_group_id", 999))

    # Collect all unique exceptions
    exceptions_map = {}  # exception -> list of (risk_group, risk_id, risk_name)

    for policy in sorted_policies:
        risk_group_name = format_risk_group_name(policy.get("risk_group", "Unknown"))

        risks = policy.get("risks", [])
        for risk in risks:
            exception = risk.get("exception")
            if exception:
                risk_id = risk.get("risk_id", "?")
                risk_name = format_risk_group_name(risk.get("risk", "Unknown"))

                if exception not in exceptions_map:
                    exceptions_map[exception] = []
                exceptions_map[exception].append((risk_group_name, risk_id, risk_name))

    if not exceptions_map:
        lines.append("*No exceptions defined in the policy files.*")
        return "\n".join(lines)

    # Generate summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Exception | Count |")
    lines.append("|-----------|-------|")
    for exception in sorted(exceptions_map.keys()):
        count = len(exceptions_map[exception])
        lines.append(f"| `{exception}` | {count} |")
    lines.append("")

    # Generate detailed listing by exception
    lines.append("## Exceptions Detail")
    lines.append("")

    for exception in sorted(exceptions_map.keys()):
        lines.append(f"### `{exception}`")
        lines.append("")
        for risk_group_name, risk_id, risk_name in exceptions_map[exception]:
            lines.append(f"- **{risk_id}** {risk_name} *(from {risk_group_name})*")
        lines.append("")

    return "\n".join(lines)


def generate_mermaid(policies: list[dict]) -> str:
    """Generate mermaid graph content from policy data."""
    lines = ["```mermaid", "flowchart TD", "    Root([Safety Policy v1.0])"]

    # Sort policies by risk_group_id
    sorted_policies = sorted(policies, key=lambda p: p.get("risk_group_id", 999))

    for policy in sorted_policies:
        risk_group_id = policy.get("risk_group_id", "?")
        risk_group_name = format_risk_group_name(policy.get("risk_group", "Unknown"))

        # Create node ID (no special chars)
        group_node_id = f"G{risk_group_id}"
        lines.append(f"    Root --> {group_node_id}[{risk_group_id}. {risk_group_name}]")

        risks = policy.get("risks", [])
        for risk in risks:
            risk_id = risk.get("risk_id", "?")
            risk_name = format_risk_group_name(risk.get("risk", "Unknown"))
            # Create node ID (replace dots with underscores)
            risk_node_id = f"R{str(risk_id).replace('.', '_')}"
            lines.append(f"    {group_node_id} --> {risk_node_id}({risk_id} {risk_name})")

    lines.append("```")
    return "\n".join(lines)


def main():
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    policy_dir = repo_root / "policies" / "safety_policy_v1.0" / "policy_files"
    output_file = repo_root / "policies" / "safety_policy_v1.0" / "RISK_TREE.md"

    # policy_dir = repo_root / "policies" / "hypothetical_policies_drinking_beer" / "policy_files"
    # output_file = repo_root / "policies" / "hypothetical_policies_drinking_beer" / "RISK_TREE.md"

    print(f"Policy loaded from {policy_dir}")

    if not policy_dir.exists():
        print(f"Error: Policy directory not found: {policy_dir}")
        return 1

    policies = load_yaml_files(policy_dir)

    if not policies:
        print("No policy files found.")
        return 1

    markdown = generate_markdown(policies)

    with open(output_file, "w") as f:
        f.write(markdown)

    mermaid = generate_mermaid_split(policies)
    mermaid_file = policy_dir / "RISK_TREE_GRAPH.md"

    with open(mermaid_file, "w") as f:
        f.write(mermaid)

    exceptions = generate_exceptions(policies)
    exceptions_file = repo_root / "policies" / "safety_policy_v1.0" / "EXCEPTIONS.md"

    with open(exceptions_file, "w") as f:
        f.write(exceptions)

    print(f"Generated risk tree: {output_file}")
    print(f"Generated mermaid graph: {mermaid_file}")
    print(f"Generated exceptions: {exceptions_file}")
    print(f"Processed {len(policies)} policy files.")
    return 0


if __name__ == "__main__":
    exit(main())
