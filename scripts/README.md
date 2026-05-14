# Utility Scripts

Scripts to help visualize and work with policies.

## generate_risk_tree.py

Reads all YAML files from `policies/safety_policy_v1.0/` and outputs a tree.

To regenerate the tree after making changes to the YAML files:
```bash
python3 scripts/generate_risk_tree.py
```

This script generates two outputs inside the folder of the policy:
1. `RISK_TREE_GRAPH.md` - Mermaid diagrams for each risk group
2. `RISK_TREE.md` - Text-based tree view
3. `EXCEPTIONS.md` - List of exceptions

---

## visualize_policies.py

Generate Mermaid visualizations from any folder containing policy YAML files. Useful for visualizing custom policies or comparing different policy sets.

### Usage

```bash
# Output to terminal (Markdown)
python3 scripts/visualize_policies.py <folder_path>

# Save to a file
python3 scripts/visualize_policies.py <folder_path> --output OUTPUT.md

# Generate interactive HTML (renders in browser)
python3 scripts/visualize_policies.py <folder_path> --format html --output policies.html
```

### Examples

```bash
# Visualize the main safety policy
python3 scripts/visualize_policies.py policies/safety_policy_v1.0/policy_files/

# Visualize competitor policies and save to file
python3 scripts/visualize_policies.py policies/example_competitor_policy/policy_files/ -o competitor_viz.md

python3 scripts/visualize_policies.py policies/safety_policy_v1.0/policy_files/ -o VISUALIZATION.md

# Generate an HTML report for sharing
python3 scripts/visualize_policies.py policies/safety_policy_v1.0/policy_files/ -f html -o report.html
```

### Output

The script generates:
- **Summary graph** - Overview of all risk groups with risk counts
- **Individual diagrams** - Mermaid graph for each policy file
- **Risk details table** - Collapsible table with risk IDs, names, and response types

---

## compare_policies.py

Compare two policy YAML files to detect semantic conflicts. The script analyzes whether policies target the same or different topics, and if they conflict in how they handle similar topics.

### Usage

```bash
# Output to terminal (Markdown)
python3 scripts/compare_policies.py <policy1.yaml> <policy2.yaml>

# Save to a file
python3 scripts/compare_policies.py <policy1.yaml> <policy2.yaml> --output report.md

# Output raw JSON
python3 scripts/compare_policies.py <policy1.yaml> <policy2.yaml> --json
```

### Examples

```bash
# Compare permissive vs prohibited alcohol policies (SAME TOPIC - conflicts expected)
python3 scripts/compare_policies.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_consumption_permissive.yaml \
  policies/example_policies_drinking_beer/policy_files/alcohol_prohibited.yaml

# Compare permissive vs off-topic alcohol policies (RELATED TOPIC - conflicts expected)
python3 scripts/compare_policies.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_consumption_permissive.yaml \
  policies/example_policies_drinking_beer/policy_files/alcohol_off_topic.yaml

# Compare alcohol vs competitor policies (DIFFERENT TOPICS - no conflicts)
python3 scripts/compare_policies.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_consumption_permissive.yaml \
  policies/example_policies_drinking_beer/policy_files/competitor_statements.yaml
```

### What it detects

**Topic Analysis:**
- 🔴 **SAME_TOPIC** - Policies cover the same subject area
- 🟡 **RELATED_TOPICS** - Policies have some topical overlap
- 🟢 **DIFFERENT_TOPICS** - Policies cover unrelated subjects (no conflict expected)

**Conflict Types:**
- **Permission Conflicts** (HIGH severity) - What one policy allows (`reply_may_contain`), the other forbids (`reply_cannot_contain`)
- **Response Type Conflicts** - Same topic has different response strategies (e.g., `INFORMATIVE_RESPONSE` vs `EXPLICIT_REFUSAL`)
- **Unique Risks** - Risks that exist in one policy but not the other

### Output

The report includes:
- **Topic Analysis** - Similarity scores and common/unique keywords
- **Summary** - Total conflicts by severity (HIGH/MEDIUM)
- **Permission Conflicts** - Detailed breakdown with the specific allowed/forbidden content
- **Response Type Conflicts** - Policies with conflicting response strategies
- **Unique Risks** - Risks with no matching topic in the other policy

---

## compare_policies_embeddings.py

Compare two policy YAML files using **word embeddings** for deeper semantic similarity analysis. This script uses sentence transformers to understand meaning, not just keyword overlap.

### Requirements

```bash
pip install sentence-transformers
```

### Usage

```bash
# Basic comparison
python3 scripts/compare_policies_embeddings.py <policy1.yaml> <policy2.yaml>

# Save to file
python3 scripts/compare_policies_embeddings.py <policy1.yaml> <policy2.yaml> --output report.md

# Adjust similarity threshold (default: 0.6)
python3 scripts/compare_policies_embeddings.py <policy1.yaml> <policy2.yaml> --threshold 0.7

# Use a different model
python3 scripts/compare_policies_embeddings.py <policy1.yaml> <policy2.yaml> --model all-mpnet-base-v2
```

### Examples

```bash
# Compare permissive vs prohibited alcohol policies
python3 scripts/compare_policies_embeddings.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_consumption_permissive.yaml \
  policies/example_policies_drinking_beer/policy_files/alcohol_prohibited.yaml

# Compare with stricter threshold
python3 scripts/compare_policies_embeddings.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_consumption_permissive.yaml \
  policies/example_policies_drinking_beer/policy_files/alcohol_off_topic.yaml \
  --threshold 0.75
```

### How it works

1. **Chunking**: Each policy is split into individual items from `reply_cannot_contain` and `reply_may_contain`
2. **Embedding**: Each chunk is converted to a vector using sentence transformers
3. **Comparison**: Cosine similarity is computed between all chunk pairs
4. **Classification**:
   - 🔴 **CONFLICT**: One policy forbids what the other allows (high similarity, opposite permissions)
   - ✅ **AGREEMENT**: Both policies forbid or both allow semantically similar content


### Output

The report includes:
- **Topic Analysis** - Semantic similarity score between policies
- **Conflicts** - Items where one policy allows what the other forbids
- **Agreements (forbid)** - Items both policies forbid
- **Agreements (allow)** - Items both policies allow

---

## policy_to_criteria.py

Convert YAML policy files to Granite Guardian 4.1 criteria format.

### Usage

```bash
# Output human-readable text
python3 scripts/policy_to_criteria.py <policy.yaml>

# Output as Python code
python3 scripts/policy_to_criteria.py <policy.yaml> --python

# Output as JSON
python3 scripts/policy_to_criteria.py <policy.yaml> --json

# List all risks in a policy
python3 scripts/policy_to_criteria.py <policy.yaml> --list-risks

# Generate criteria for a specific risk only
python3 scripts/policy_to_criteria.py <policy.yaml> --risk-id 11.1
```

### Examples

```bash
# Generate criteria for alcohol prohibition policy
python3 scripts/policy_to_criteria.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_prohibited.yaml

# Export as Python constants
python3 scripts/policy_to_criteria.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_prohibited.yaml \
  --python --output criteria.py
```

---

## evaluate_conversations.py

Evaluate conversations against a policy using Granite Guardian 4.1. This script loads a policy, generates criteria, and checks whether assistant responses comply with the policy.

### Requirements

```bash
pip install transformers vllm torch pyyaml
```

### Usage

```bash
# Basic evaluation
python3 scripts/evaluate_conversations.py <policy.yaml> <conversations.json>

# Save results to file
python3 scripts/evaluate_conversations.py <policy.yaml> <conversations.json> --output results.json

# Use think mode (includes reasoning trace)
python3 scripts/evaluate_conversations.py <policy.yaml> <conversations.json> --think

# Evaluate against a specific risk only
python3 scripts/evaluate_conversations.py <policy.yaml> <conversations.json> --risk-id 11.1

# List risks in policy
python3 scripts/evaluate_conversations.py <policy.yaml> <conversations.json> --list-risks

# Quiet mode (summary only)
python3 scripts/evaluate_conversations.py <policy.yaml> <conversations.json> --quiet
```

### Dataset Format

**JSON format:**
```json
[
    {
        "id": "conv_001",
        "user": "User message here",
        "assistant": "Assistant response here"
    }
]
```

**JSONL format:**
```
{"id": "conv_001", "user": "User message", "assistant": "Response"}
{"id": "conv_002", "user": "Another message", "assistant": "Another response"}
```

### Examples

```bash
# Evaluate sample conversations against alcohol prohibition policy
python3 scripts/evaluate_conversations.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_prohibited.yaml \
  examples/sample_conversations.json

# Evaluate with think mode and save results
python3 scripts/evaluate_conversations.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_prohibited.yaml \
  examples/sample_conversations.jsonl \
  --think --output results.json

# Evaluate only against brewing policy (risk 11.2)
python3 scripts/evaluate_conversations.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_prohibited.yaml \
  examples/sample_conversations.json \
  --risk-id 11.2
```

### Output

The script outputs:
- Per-conversation evaluation results showing violations/compliance for each risk
- Summary statistics (total evaluations, violations, compliance rate)
- JSON output file (when `--output` specified) with full details including reasoning traces

---

## guardian_enforcement.py

Run policy enforcement test suites using Granite Guardian 4.1. Includes predefined test cases for alcohol prohibition, anti-coercion, and financial crimes policies.

### Usage

```bash
# Run all demos and test suites
python3 scripts/guardian_enforcement.py

# Run only alcohol prohibition tests
python3 scripts/guardian_enforcement.py --test-prohibition

# Run only anti-coercion tests
python3 scripts/guardian_enforcement.py --test-coercion

# Run only financial crimes tests
python3 scripts/guardian_enforcement.py --test-financial

# Use think mode (reasoning traces)
python3 scripts/guardian_enforcement.py --think
```