---
description: Compare two policy files to detect conflicts and differences
---

Compare the following policy files for conflicts: $ARGUMENTS

Run the comparison script and show the output:

```bash
python3 scripts/compare_policies_embeddings.py $ARGUMENTS
```

If no arguments are provided, prompt the user to provide two policy file paths.

After showing the results, summarize the key findings:
- How many conflicts were detected
- The most critical conflicts (HIGH severity)
- Any recommendations for resolving the conflicts
