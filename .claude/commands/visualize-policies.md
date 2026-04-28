---
description: Generate Mermaid visualizations from policy YAML files
---

Generate a policy visualization for the folder: $ARGUMENTS

Run the visualization script and show the output:

```bash
python3 scripts/visualize_policies.py $ARGUMENTS
```

If the user specifies `--format html` or `-f html`, remind them to open the output file in a browser to see the interactive diagrams.

If no arguments are provided, use `policies/safety_policy_v1.0/policy_files/` as the default folder.
