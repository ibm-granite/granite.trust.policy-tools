#!/usr/bin/env python3
#
# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Visualize Policies - Generate Mermaid diagrams from policy YAML files.

Usage:
    python visualize_policies.py <folder_path> [--output <output_file>] [--format <md|html>]

Examples:
    python visualize_policies.py ../policies/safety_policy_v1.0/policy_files/
    python visualize_policies.py ../policies/safety_policy_v1.0/policy_files/ --output RISK_TREE_GRAPH.md
    python visualize_policies.py ../policies/example_competitor_policy/policy_files/ --format html
"""

import argparse
import os
import sys
from pathlib import Path

import yaml


def load_policy(file_path: str) -> dict:
    """Load a policy YAML file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def sanitize_node_id(text: str) -> str:
    """Convert text to a valid mermaid node ID."""
    return text.replace(' ', '_').replace('-', '_').replace('.', '_')


def sanitize_label(text: str) -> str:
    """Sanitize text for mermaid labels."""
    # Escape special characters and truncate if too long
    text = text.replace('"', "'").replace('[', '(').replace(']', ')')
    if len(text) > 50:
        text = text[:47] + '...'
    return text


def generate_mermaid_for_policy(policy: dict) -> str:
    """Generate a mermaid graph for a single policy."""
    risk_group = policy.get('risk_group', 'Unknown')
    risk_group_id = policy.get('risk_group_id', 0)
    risks = policy.get('risks', [])

    if not risks:
        return ""

    group_node = f"G{risk_group_id}"
    group_label = sanitize_label(risk_group.replace('_', ' ').title())

    lines = [
        "```mermaid",
        "graph LR",
        f"    {group_node}[{group_label}]"
    ]

    for risk in risks:
        risk_id = str(risk.get('risk_id', ''))
        risk_name = risk.get('risk', 'Unknown')

        # Create node ID from risk_id (e.g., 14.1 -> R14_1)
        node_id = f"R{sanitize_node_id(risk_id)}"
        node_label = sanitize_label(risk_name.replace('_', ' ').title())

        lines.append(f"    {group_node} --> {node_id}[{node_label}]")

    lines.append("```")
    return '\n'.join(lines)


def generate_summary_graph(policies: list[dict]) -> str:
    """Generate a summary mermaid graph showing all risk groups."""
    lines = [
        "```mermaid",
        "graph TD",
        "    ROOT[All Policies]"
    ]

    for policy in policies:
        risk_group = policy.get('risk_group', 'Unknown')
        risk_group_id = policy.get('risk_group_id', 0)
        num_risks = len(policy.get('risks', []))

        group_node = f"G{risk_group_id}"
        group_label = sanitize_label(risk_group.replace('_', ' ').title())

        lines.append(f"    ROOT --> {group_node}[{group_label}<br/>{num_risks} risks]")

    lines.append("```")
    return '\n'.join(lines)


def generate_markdown_report(folder_path: str, policies: list[tuple[str, dict]]) -> str:
    """Generate a full markdown report with all policy visualizations."""
    folder_name = Path(folder_path).name

    lines = [
        f"# Policy Visualization - {folder_name}",
        "",
        f"*Auto-generated from {len(policies)} policy files*",
        "",
        "## Summary",
        "",
        generate_summary_graph([p[1] for p in policies]),
        "",
        "---",
        "",
        "## Individual Policies",
        ""
    ]

    for file_name, policy in sorted(policies, key=lambda x: x[1].get('risk_group_id', 0)):
        risk_group = policy.get('risk_group', 'Unknown')
        risk_group_id = policy.get('risk_group_id', 0)
        description = policy.get('description', 'No description provided')
        num_risks = len(policy.get('risks', []))

        lines.extend([
            f"### {risk_group_id}. {risk_group.replace('_', ' ').title()}",
            "",
            f"*{description}*",
            "",
            f"**File:** `{file_name}` | **Risks:** {num_risks}",
            "",
            generate_mermaid_for_policy(policy),
            "",
            "<details>",
            "<summary>Policy Details</summary>",
            "",
            "| Risk ID | Risk Name | Response Type | Exception |",
            "|---------|-----------|---------------|-----------|"
        ])

        for risk in policy.get('risks', []):
            risk_id = risk.get('risk_id', '')
            risk_name = risk.get('risk', '').replace('_', ' ').title()
            response_type = risk.get('short_reply_type', 'N/A')
            exception = risk.get('exception', 'N/A')
            lines.append(f"| {risk_id} | {risk_name} | {response_type} | {exception} |")

        lines.extend([
            "",
            "</details>",
            "",
            "---",
            ""
        ])

    return '\n'.join(lines)


def generate_html_report(folder_path: str, policies: list[tuple[str, dict]]) -> str:
    """Generate an HTML report with mermaid.js for rendering."""
    folder_name = Path(folder_path).name

    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        f"    <title>Policy Visualization - {folder_name}</title>",
        '    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>',
        "    <style>",
        "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }",
        "        h1 { color: #333; }",
        "        h2 { color: #555; border-bottom: 1px solid #ddd; padding-bottom: 10px; }",
        "        .policy-card { background: #f9f9f9; border-radius: 8px; padding: 20px; margin: 20px 0; }",
        "        .mermaid { background: white; padding: 20px; border-radius: 4px; }",
        "        table { border-collapse: collapse; width: 100%; margin: 10px 0; }",
        "        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "        th { background: #f2f2f2; }",
        "        details { margin: 10px 0; }",
        "        summary { cursor: pointer; font-weight: bold; }",
        "    </style>",
        "</head>",
        "<body>",
        "    <script>mermaid.initialize({startOnLoad:true});</script>",
        f"    <h1>Policy Visualization - {folder_name}</h1>",
        f"    <p><em>Auto-generated from {len(policies)} policy files</em></p>",
        "",
        "    <h2>Summary</h2>",
        '    <div class="mermaid">',
        "    graph TD",
        "        ROOT[All Policies]"
    ]

    for _, policy in policies:
        risk_group = policy.get('risk_group', 'Unknown')
        risk_group_id = policy.get('risk_group_id', 0)
        num_risks = len(policy.get('risks', []))
        group_label = sanitize_label(risk_group.replace('_', ' ').title())
        html_parts.append(f"        ROOT --> G{risk_group_id}[{group_label}<br/>{num_risks} risks]")

    html_parts.extend([
        "    </div>",
        "",
        "    <h2>Individual Policies</h2>"
    ])

    for file_name, policy in sorted(policies, key=lambda x: x[1].get('risk_group_id', 0)):
        risk_group = policy.get('risk_group', 'Unknown')
        risk_group_id = policy.get('risk_group_id', 0)
        description = policy.get('description', 'No description provided')
        risks = policy.get('risks', [])

        group_node = f"G{risk_group_id}"
        group_label = sanitize_label(risk_group.replace('_', ' ').title())

        html_parts.extend([
            '    <div class="policy-card">',
            f"        <h3>{risk_group_id}. {risk_group.replace('_', ' ').title()}</h3>",
            f"        <p><em>{description}</em></p>",
            f"        <p><strong>File:</strong> <code>{file_name}</code> | <strong>Risks:</strong> {len(risks)}</p>",
            '        <div class="mermaid">',
            "        graph LR",
            f"            {group_node}[{group_label}]"
        ])

        for risk in risks:
            risk_id = str(risk.get('risk_id', ''))
            risk_name = risk.get('risk', 'Unknown')
            node_id = f"R{sanitize_node_id(risk_id)}"
            node_label = sanitize_label(risk_name.replace('_', ' ').title())
            html_parts.append(f"            {group_node} --> {node_id}[{node_label}]")

        html_parts.extend([
            "        </div>",
            "        <details>",
            "            <summary>Policy Details</summary>",
            "            <table>",
            "                <tr><th>Risk ID</th><th>Risk Name</th><th>Response Type</th><th>Exception</th></tr>"
        ])

        for risk in risks:
            risk_id = risk.get('risk_id', '')
            risk_name = risk.get('risk', '').replace('_', ' ').title()
            response_type = risk.get('short_reply_type', 'N/A')
            exception = risk.get('exception', 'N/A')
            html_parts.append(f"                <tr><td>{risk_id}</td><td>{risk_name}</td><td>{response_type}</td><td>{exception}</td></tr>")

        html_parts.extend([
            "            </table>",
            "        </details>",
            "    </div>"
        ])

    html_parts.extend([
        "</body>",
        "</html>"
    ])

    return '\n'.join(html_parts)


def main():
    parser = argparse.ArgumentParser(
        description='Generate Mermaid visualizations from policy YAML files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('folder', help='Path to folder containing policy YAML files')
    parser.add_argument('--output', '-o', help='Output file path (default: prints to stdout)')
    parser.add_argument('--format', '-f', choices=['md', 'html'], default='md',
                        help='Output format: md (Markdown) or html (default: md)')

    args = parser.parse_args()

    folder_path = Path(args.folder)

    if not folder_path.exists():
        print(f"Error: Folder not found: {folder_path}", file=sys.stderr)
        sys.exit(1)

    # Find all YAML files (excluding schema files)
    yaml_files = list(folder_path.glob('*.yaml')) + list(folder_path.glob('*.yml'))
    yaml_files = [f for f in yaml_files if 'schema' not in f.name.lower()]

    if not yaml_files:
        print(f"Error: No YAML policy files found in {folder_path}", file=sys.stderr)
        sys.exit(1)

    # Load all policies
    policies = []
    for yaml_file in yaml_files:
        try:
            policy = load_policy(yaml_file)
            if policy and 'risk_group' in policy:
                policies.append((yaml_file.name, policy))
        except Exception as e:
            print(f"Warning: Could not load {yaml_file.name}: {e}", file=sys.stderr)

    if not policies:
        print("Error: No valid policy files found", file=sys.stderr)
        sys.exit(1)

    # Generate report
    if args.format == 'html':
        report = generate_html_report(str(folder_path), policies)
    else:
        report = generate_markdown_report(str(folder_path), policies)

    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"Report saved to: {output_path}")
    else:
        print(report)


if __name__ == '__main__':
    main()
