# Policy Tools

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Policy Version](https://img.shields.io/badge/policy_version-v1.0-orange.svg)](policies/safety_policy_v1.0/)

> Shareable, actionable policies for LLMs: specify, test, enforce. It's all about governance 

Our Policy Tools are an open-source framework for defining, testing, and enforcing policies in GenAI applications. Using a simple YAML format, teams can specify what their AI can and cannot say, generate synthetic data for testing, and verify compliance at runtime. 

This repo contains the format for policies, tools that help create and use policies, and a repository to share the *policy schema* and policy tools with the community. 

Contributions from the community are welcome and encouraged.

## Quick Links
| [Getting started](#Getting-Started) | [Why GenAI Policy Tools?](#why-genai-policies) | [Policy Schema](./policy_schema/) | [How is the repo organized?](#how-is-the-repo-organized) 
| [Contributing](#contribution-policy) | [Questions or feedback](#questions-or-feedback) | [Cite this work](#cite-this-work) | [Our Approach](./notebooks/risk_management_philosophy.md) | [Tutorials](./notebooks/README.md) | 

## Getting Started
The policy schema is at the center of this repo. All tools and sample policies use this format.

``` yaml
risk_group: 
risk_group_id:
description: 
policy_version: v1.0
risks:
  - risk: 
    risk_id: 
    description: 
    reason_denial: 
    short_reply_type: 
    exception: 
    policy:
      reply_cannot_contain: 
        - 
      reply_may_contain:
        - 
``` 

A good starting point is to clone the repo, look at the set of sample policies, and try out the tools.
Check our [tutorials](./notebooks/README.md) to get started.


- [Tutorial 1: Exploring the Policy Format](./notebooks//exploring_policy_format.ipynb) - Learn how to create policy YAML files
- [Tutorial 2: Policy Variability](./notebooks/exploring_policy_variability.ipynb) - Understand how context affects policies
- [Tutorial 3: Generate synthetic data](./notebooks/generate_synthetic_data_with_fms_dgt.ipynb) - Use DGT to generate synthetic data that follows the policy definition
- [Tutorial 4: Enforce policy with Granite Guardian 4.1 ](./notebooks/guardian_enforcement.ipynb) - Learn how to enforce your policy using the new *bring your own criteria* functionality of Granite Guardian 
- [Tutorial 5: Red-team LLMs with ARES](./notebooks/red_team_models_with_ares.ipynb) - Red-team LLMs using ARES with DGT-generated harmful prompts as attack objectives and evaluate responses against the same policy

Check our scripts folder for additional functionality: 

```bash
# Visualize all sample policies
python3 scripts/visualize_policies.py policies/safety_policy_v1.0/policy_files/

# Compare two policies for conflicts
python3 scripts/compare_policies_embeddings.py \
  policies/example_policies_drinking_beer/policy_files/alcohol_consumption_permissive.yaml \
  policies/example_policies_drinking_beer/policy_files/alcohol_prohibited.yaml
```


## Why GenAI Policies?

Policies govern the behavior of a generative AI app, a chat service, an agent, etc., beyond a particular prompt. Policies are used when addressing important issues, often related to particular risks. A policy defines how to address a particular issue or risk. 

When it comes to policies, one size does not fit all! Each organization and use case  needs to mitigate different risks differently depending on the use case, regulatory environment, values, and user persona interacting with the models or agents. Defining an actionable policy is the first step to fully manage risks. With a clear actionable policy it is possible to align models, monitor for compliance and verify before deployment the security of the system.

In this repo, we present a *Policy format*, which enables the specification of policies. Coupled with these policies, we have multiple tools to enable synthetic data generation for model alignment, testing and for policy enforcement and verification at runtime. The end goal is to enable policy compliance.


## How is the repo organized?
The [*policy schema*](./policy_schema/) shows the proposed format of the policy.
Policy schemas and groups are organized in versions with numbers such as v.1.0. Policies with numbers such as 0.1 or 1.2 are intermediate policies.

The first folder includes the version of the policy specification. Inside the policy version:
- Each YAML file contains the specification of a risk category. 
- Inside the file, there may be multiple leaf nodes. 
- An overview of some sample policies and visualization script outputs can be found [here](./outputs).

In addition to policies, you can also find a set of [tutorials](./notebooks/README.md) and [scripts](./scripts/).   

## Contribution Policy

We welcome contributions by the community. To do so, please open a PR with the proposal. Please adhere to the conduct guidelines of this repository.

## Questions or feedback?

Remember, this repository only contains *sample* policies. This repository's objective is to define and maintain a sharable *policy schema*  that helps the community create tools to visualize, enforce and verify any policy. Please open a GitHub issue with any questions or feedback.

## Code of conduct

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for our code of conduct and contribution guidelines.

## Cite this work

If you use this work in your research, please cite:

```bibtex
@misc{genai-policy-tools,
  title={Granite.Trust Policy Tools: Shareable, Actionable Policies for Generative AI Applications},
  publisher={IBM Research},
  author={Nathalie Baracaldo, Nicolas Mello, Kush R. Varshney, Heiko Ludwig, Kate Soule, David Cox}
  year={2026},
  url={https://github.com/ibm-granite/granite.trust.policy-tools}
}
``` 
You can find our report: [here](./docs/Granite-Trust-Policy-Tools.pdf)  

## Disclaimer
This is not an IBM product. IBM doesn’t endorse the sample policies in this repository.