#!/usr/bin/env python3
#
# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0
#

"""
Compare Policies using Word Embeddings - Semantic similarity comparison.

This script uses sentence embeddings to compare policies at a deeper semantic level,
carefully chunking policies to compare:
- reply_cannot_contain vs reply_cannot_contain (agreement)
- reply_may_contain vs reply_may_contain (agreement)
- reply_cannot_contain vs reply_may_contain (conflict detection)

Requirements:
    pip install sentence-transformers

Usage:
    python3 compare_policies_embeddings.py <policy1.yaml> <policy2.yaml> [--output <file>] [--threshold 0.7]

Examples:
    python3 compare_policies_embeddings.py \\
        policies/example_policies_drinking_beer/policy_files/alcohol_consumption_permissive.yaml \\
        policies/example_policies_drinking_beer/policy_files/alcohol_prohibited.yaml
"""

import argparse
import logging
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

# Suppress the BertModel "position_ids UNEXPECTED" warning from sentence-transformers
warnings.filterwarnings("ignore", message=".*position_ids.*")
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

try:
    from sentence_transformers import SentenceTransformer, util
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


@dataclass
class PolicyChunk:
    """Represents a chunk of policy content with metadata."""
    text: str
    chunk_type: str  # 'cannot_contain' or 'may_contain'
    risk_name: str
    risk_id: str
    policy_source: str  # 'policy1' or 'policy2'


@dataclass
class SimilarityMatch:
    """Represents a similarity match between two chunks."""
    chunk1: PolicyChunk
    chunk2: PolicyChunk
    similarity: float
    match_type: str  # 'CONFLICT', 'AGREEMENT_CANNOT', 'AGREEMENT_MAY'


def load_policy(file_path: str) -> dict:
    """Load a policy YAML file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def chunk_policy(policy: dict, policy_source: str) -> list[PolicyChunk]:
    """
    Chunk a policy into individual items for embedding comparison.

    Each item in reply_cannot_contain and reply_may_contain becomes a separate chunk
    with metadata about its source risk and type.
    """
    chunks = []

    for risk in policy.get('risks', []):
        risk_name = risk.get('risk', 'unknown')
        risk_id = str(risk.get('risk_id', ''))
        policy_rules = risk.get('policy', {})

        # Chunk cannot_contain items
        cannot_contain = policy_rules.get('reply_cannot_contain', []) or []
        for item in cannot_contain:
            if item and item.strip():
                chunks.append(PolicyChunk(
                    text=item.strip(),
                    chunk_type='cannot_contain',
                    risk_name=risk_name,
                    risk_id=risk_id,
                    policy_source=policy_source
                ))

        # Chunk may_contain items
        may_contain = policy_rules.get('reply_may_contain', []) or []
        for item in may_contain:
            if item and item.strip():
                chunks.append(PolicyChunk(
                    text=item.strip(),
                    chunk_type='may_contain',
                    risk_name=risk_name,
                    risk_id=risk_id,
                    policy_source=policy_source
                ))

    return chunks


def compute_embeddings(model: 'SentenceTransformer', chunks: list[PolicyChunk]) -> dict:
    """Compute embeddings for all chunks."""
    texts = [chunk.text for chunk in chunks]
    embeddings = model.encode(texts, convert_to_tensor=True)
    return {i: emb for i, emb in enumerate(embeddings)}


def find_semantic_matches(
    model: 'SentenceTransformer',
    chunks1: list[PolicyChunk],
    chunks2: list[PolicyChunk],
    threshold: float = 0.6
) -> list[SimilarityMatch]:
    """
    Find semantic matches between chunks from two policies.

    Compares:
    1. cannot_contain (P1) vs may_contain (P2) -> CONFLICT
    2. may_contain (P1) vs cannot_contain (P2) -> CONFLICT
    3. cannot_contain (P1) vs cannot_contain (P2) -> AGREEMENT
    4. may_contain (P1) vs may_contain (P2) -> AGREEMENT
    """
    matches = []

    # Get all texts and compute embeddings
    all_texts1 = [c.text for c in chunks1]
    all_texts2 = [c.text for c in chunks2]

    if not all_texts1 or not all_texts2:
        return matches

    embeddings1 = model.encode(all_texts1, convert_to_tensor=True)
    embeddings2 = model.encode(all_texts2, convert_to_tensor=True)

    # Compute cosine similarity matrix
    cosine_scores = util.cos_sim(embeddings1, embeddings2)

    # Find matches above threshold
    for i, chunk1 in enumerate(chunks1):
        for j, chunk2 in enumerate(chunks2):
            similarity = cosine_scores[i][j].item()

            if similarity >= threshold:
                # Determine match type
                if chunk1.chunk_type == 'cannot_contain' and chunk2.chunk_type == 'may_contain':
                    match_type = 'CONFLICT_P2_ALLOWS'
                elif chunk1.chunk_type == 'may_contain' and chunk2.chunk_type == 'cannot_contain':
                    match_type = 'CONFLICT_P1_ALLOWS'
                elif chunk1.chunk_type == 'cannot_contain' and chunk2.chunk_type == 'cannot_contain':
                    match_type = 'AGREEMENT_BOTH_FORBID'
                elif chunk1.chunk_type == 'may_contain' and chunk2.chunk_type == 'may_contain':
                    match_type = 'AGREEMENT_BOTH_ALLOW'
                else:
                    continue

                matches.append(SimilarityMatch(
                    chunk1=chunk1,
                    chunk2=chunk2,
                    similarity=round(similarity, 3),
                    match_type=match_type
                ))

    return matches


def analyze_topic_similarity(
    model: 'SentenceTransformer',
    policy1: dict,
    policy2: dict
) -> dict:
    """Analyze overall topic similarity between two policies using embeddings."""

    # Create policy-level descriptions
    desc1 = f"{policy1.get('risk_group', '')} {policy1.get('description', '')}"
    desc2 = f"{policy2.get('risk_group', '')} {policy2.get('description', '')}"

    # Add risk descriptions
    for risk in policy1.get('risks', []):
        desc1 += f" {risk.get('risk', '')} {risk.get('description', '')}"
    for risk in policy2.get('risks', []):
        desc2 += f" {risk.get('risk', '')} {risk.get('description', '')}"

    # Compute embeddings and similarity
    embeddings = model.encode([desc1, desc2], convert_to_tensor=True)
    similarity = util.cos_sim(embeddings[0], embeddings[1]).item()

    # Determine relationship
    if similarity >= 0.7:
        relationship = "SAME_TOPIC"
        explanation = "Policies are semantically about the same topic"
    elif similarity >= 0.4:
        relationship = "RELATED_TOPICS"
        explanation = "Policies have semantic overlap"
    else:
        relationship = "DIFFERENT_TOPICS"
        explanation = "Policies are semantically distinct - no conflicts expected"

    return {
        'relationship': relationship,
        'explanation': explanation,
        'similarity': round(similarity, 3)
    }


def compare_policies_with_embeddings(
    policy1: dict,
    policy2: dict,
    model: 'SentenceTransformer',
    threshold: float = 0.6
) -> dict:
    """Main comparison function using embeddings."""

    # Analyze topic similarity
    topic_analysis = analyze_topic_similarity(model, policy1, policy2)

    # Chunk policies
    chunks1 = chunk_policy(policy1, 'policy1')
    chunks2 = chunk_policy(policy2, 'policy2')

    # Find semantic matches
    all_matches = find_semantic_matches(model, chunks1, chunks2, threshold)

    # Categorize matches
    conflicts = [m for m in all_matches if 'CONFLICT' in m.match_type]
    agreements_forbid = [m for m in all_matches if m.match_type == 'AGREEMENT_BOTH_FORBID']
    agreements_allow = [m for m in all_matches if m.match_type == 'AGREEMENT_BOTH_ALLOW']

    # Sort by similarity (highest first)
    conflicts.sort(key=lambda x: x.similarity, reverse=True)
    agreements_forbid.sort(key=lambda x: x.similarity, reverse=True)
    agreements_allow.sort(key=lambda x: x.similarity, reverse=True)

    return {
        'policy1': {
            'file': '',
            'risk_group': policy1.get('risk_group'),
            'description': policy1.get('description'),
            'num_risks': len(policy1.get('risks', [])),
            'num_chunks': len(chunks1)
        },
        'policy2': {
            'file': '',
            'risk_group': policy2.get('risk_group'),
            'description': policy2.get('description'),
            'num_risks': len(policy2.get('risks', [])),
            'num_chunks': len(chunks2)
        },
        'topic_analysis': topic_analysis,
        'conflicts': conflicts,
        'agreements_forbid': agreements_forbid,
        'agreements_allow': agreements_allow,
        'summary': {
            'topic_relationship': topic_analysis['relationship'],
            'topic_similarity': topic_analysis['similarity'],
            'total_conflicts': len(conflicts),
            'total_agreements_forbid': len(agreements_forbid),
            'total_agreements_allow': len(agreements_allow),
            'threshold_used': threshold
        }
    }


def generate_report(result: dict, policy1_path: str, policy2_path: str) -> str:
    """Generate a markdown report from comparison results."""
    p1_file = Path(policy1_path).name
    p2_file = Path(policy2_path).name

    result['policy1']['file'] = p1_file
    result['policy2']['file'] = p2_file

    lines = [
        "# Policy Comparison Report (Embedding-based Semantic Analysis)",
        "",
        "## Policies Compared",
        "",
        "| | Policy 1 | Policy 2 |",
        "|---|----------|----------|",
        f"| **File** | `{p1_file}` | `{p2_file}` |",
        f"| **Risk Group** | {result['policy1']['risk_group']} | {result['policy2']['risk_group']} |",
        f"| **Number of Risks** | {result['policy1']['num_risks']} | {result['policy2']['num_risks']} |",
        f"| **Policy Chunks** | {result['policy1']['num_chunks']} | {result['policy2']['num_chunks']} |",
        "",
    ]

    # Topic Analysis
    topic = result['topic_analysis']
    relationship_icon = {
        'SAME_TOPIC': '🔴',
        'RELATED_TOPICS': '🟡',
        'DIFFERENT_TOPICS': '🟢'
    }.get(topic['relationship'], '⚪')

    lines.extend([
        "## Topic Analysis (Embedding Similarity)",
        "",
        f"**Relationship:** {relationship_icon} **{topic['relationship']}**",
        "",
        f"**Semantic Similarity Score:** {topic['similarity']}",
        "",
        f"*{topic['explanation']}*",
        "",
    ])

    # Regulatory Stance Analysis
    summary = result['summary']
    conflicts = result['conflicts']
    agreements_forbid = result['agreements_forbid']
    agreements_allow = result['agreements_allow']

    # Count conflict types
    p1_allows_p2_forbids = len([c for c in conflicts if c.match_type == 'CONFLICT_P1_ALLOWS'])
    p1_forbids_p2_allows = len([c for c in conflicts if c.match_type == 'CONFLICT_P2_ALLOWS'])

    # Determine regulatory stance
    total_conflicts = len(conflicts)
    total_agreements = len(agreements_forbid) + len(agreements_allow)

    if topic['relationship'] == 'DIFFERENT_TOPICS':
        stance = "UNRELATED"
        stance_icon = "⚪"
        stance_explanation = "Policies regulate different topics - no direct comparison possible"
    elif total_conflicts == 0 and total_agreements > 0:
        stance = "ALIGNED"
        stance_icon = "✅"
        stance_explanation = "Policies have compatible regulatory approaches on this topic"
    elif total_conflicts > 0 and total_agreements == 0:
        stance = "OPPOSING"
        stance_icon = "⚔️"
        stance_explanation = "Policies have completely opposing regulatory approaches on this topic"
    elif total_conflicts > total_agreements:
        stance = "MOSTLY_OPPOSING"
        stance_icon = "🔶"
        stance_explanation = "Policies have more conflicts than agreements - significantly different regulatory approaches"
    elif total_agreements > total_conflicts:
        stance = "MOSTLY_ALIGNED"
        stance_icon = "🔷"
        stance_explanation = "Policies have more agreements than conflicts - similar regulatory approaches with some differences"
    else:
        stance = "MIXED"
        stance_icon = "⚖️"
        stance_explanation = "Policies have equal conflicts and agreements - mixed regulatory approaches"

    lines.extend([
        "## Regulatory Stance",
        "",
        f"**Overall Stance:** {stance_icon} **{stance}**",
        "",
        f"*{stance_explanation}*",
        "",
        "| Conflict Type | Count | Meaning |",
        "|---------------|-------|---------|",
        f"| Policy 1 allows, Policy 2 forbids | {p1_allows_p2_forbids} | P1 is more permissive |",
        f"| Policy 1 forbids, Policy 2 allows | {p1_forbids_p2_allows} | P2 is more permissive |",
        f"| Both policies forbid | {len(agreements_forbid)} | Agreement on restrictions |",
        f"| Both policies allow | {len(agreements_allow)} | Agreement on permissions |",
        "",
    ])

    # Summary
    lines.extend([
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Topic Relationship | {summary['topic_relationship']} |",
        f"| Topic Similarity | {summary['topic_similarity']} |",
        f"| **Semantic Conflicts** | **{summary['total_conflicts']}** |",
        f"| Agreements (both forbid) | {summary['total_agreements_forbid']} |",
        f"| Agreements (both allow) | {summary['total_agreements_allow']} |",
        f"| Similarity Threshold | {summary['threshold_used']} |",
        "",
    ])

    # No conflicts for different topics
    if topic['relationship'] == 'DIFFERENT_TOPICS' and not result['conflicts']:
        lines.extend([
            "---",
            "",
            "## Conclusion",
            "",
            "**No semantic conflicts detected.** These policies target different topics and can coexist.",
            ""
        ])
        return '\n'.join(lines)

    # Conflicts Section
    if result['conflicts']:
        lines.extend([
            "---",
            "",
            "## 🔴 Semantic Conflicts Detected",
            "",
            "These items have high semantic similarity but opposite permissions:",
            "",
            "| # | Similarity | Policy 1 | Policy 2 | Conflict Type |",
            "|---|------------|----------|----------|---------------|",
        ])

        for i, match in enumerate(result['conflicts'][:20], 1):  # Top 20
            conflict_desc = "P1 forbids, P2 allows" if match.match_type == 'CONFLICT_P2_ALLOWS' else "P1 allows, P2 forbids"
            lines.append(
                f"| {i} | {match.similarity} | {match.chunk1.risk_id} | {match.chunk2.risk_id} | {conflict_desc} |"
            )

        lines.extend(["", "### Conflict Details", ""])

        for i, match in enumerate(result['conflicts'][:10], 1):  # Top 10 details
            lines.extend([
                f"#### Conflict {i} (Similarity: {match.similarity})",
                "",
            ])

            if match.match_type == 'CONFLICT_P2_ALLOWS':
                lines.extend([
                    f"**Policy 1 FORBIDS** (`{match.chunk1.risk_name}` - {match.chunk1.risk_id}):",
                    f"> {match.chunk1.text}",
                    "",
                    f"**Policy 2 ALLOWS** (`{match.chunk2.risk_name}` - {match.chunk2.risk_id}):",
                    f"> {match.chunk2.text}",
                ])
            else:
                lines.extend([
                    f"**Policy 1 ALLOWS** (`{match.chunk1.risk_name}` - {match.chunk1.risk_id}):",
                    f"> {match.chunk1.text}",
                    "",
                    f"**Policy 2 FORBIDS** (`{match.chunk2.risk_name}` - {match.chunk2.risk_id}):",
                    f"> {match.chunk2.text}",
                ])

            lines.extend(["", "---", ""])

    # Agreements Section (both forbid)
    if result['agreements_forbid']:
        lines.extend([
            "## ✅ Agreements (Both Policies Forbid)",
            "",
            "These items are semantically similar and both policies forbid them:",
            "",
            "| # | Similarity | Policy 1 Text | Policy 2 Text |",
            "|---|------------|---------------|---------------|",
        ])

        for i, match in enumerate(result['agreements_forbid'][:10], 1):
            p1_text = match.chunk1.text[:50] + "..." if len(match.chunk1.text) > 50 else match.chunk1.text
            p2_text = match.chunk2.text[:50] + "..." if len(match.chunk2.text) > 50 else match.chunk2.text
            lines.append(f"| {i} | {match.similarity} | {p1_text} | {p2_text} |")

        lines.append("")

    # Agreements Section (both allow)
    if result['agreements_allow']:
        lines.extend([
            "## ✅ Agreements (Both Policies Allow)",
            "",
            "These items are semantically similar and both policies allow them:",
            "",
            "| # | Similarity | Policy 1 Text | Policy 2 Text |",
            "|---|------------|---------------|---------------|",
        ])

        for i, match in enumerate(result['agreements_allow'][:10], 1):
            p1_text = match.chunk1.text[:50] + "..." if len(match.chunk1.text) > 50 else match.chunk1.text
            p2_text = match.chunk2.text[:50] + "..." if len(match.chunk2.text) > 50 else match.chunk2.text
            lines.append(f"| {i} | {match.similarity} | {p1_text} | {p2_text} |")

        lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Compare two policy YAML files using embedding-based semantic similarity.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('policy1', help='Path to first policy YAML file')
    parser.add_argument('policy2', help='Path to second policy YAML file')
    parser.add_argument('--output', '-o', help='Output file path (default: prints to stdout)')
    parser.add_argument('--threshold', '-t', type=float, default=0.6,
                        help='Similarity threshold for matching (default: 0.6)')
    parser.add_argument('--model', '-m', default='all-MiniLM-L6-v2',
                        help='Sentence transformer model to use (default: all-MiniLM-L6-v2)')
    parser.add_argument('--json', action='store_true', help='Output raw JSON instead of markdown')

    args = parser.parse_args()

    # Check for sentence-transformers
    if not EMBEDDINGS_AVAILABLE:
        print("Error: sentence-transformers is required for this script.", file=sys.stderr)
        print("Install with: pip install sentence-transformers", file=sys.stderr)
        sys.exit(1)

    # Validate files exist
    for path in [args.policy1, args.policy2]:
        if not Path(path).exists():
            print(f"Error: File not found: {path}", file=sys.stderr)
            sys.exit(1)

    # Load policies
    try:
        policy1 = load_policy(args.policy1)
        policy2 = load_policy(args.policy2)
    except Exception as e:
        print(f"Error loading policy files: {e}", file=sys.stderr)
        sys.exit(1)

    # Load model
    print(f"Loading embedding model: {args.model}...", file=sys.stderr)
    model = SentenceTransformer(args.model)

    # Compare
    print("Comparing policies...", file=sys.stderr)
    result = compare_policies_with_embeddings(policy1, policy2, model, args.threshold)

    # Output
    if args.json:
        import json
        # Convert dataclasses to dicts for JSON serialization
        def serialize(obj):
            if isinstance(obj, (PolicyChunk, SimilarityMatch)):
                return obj.__dict__
            return obj
        output = json.dumps(result, indent=2, default=serialize)
    else:
        output = generate_report(result, args.policy1, args.policy2)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Report saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
