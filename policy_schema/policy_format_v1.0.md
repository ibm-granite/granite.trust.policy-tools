# Policy Format

This document specifies the YAML format used to define policies.

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
---

## Top-Level Structure

Each policy file describes one **risk group** — a thematic cluster of related risks.

```yaml
risk_group: <string>
risk_group_id: <integer>
description: <string>
policy_version: <string>
risks:
  - ...
```


| Field | Type | Description |
|---|---|---|
| `risk_group` | string | Category name for a group of related risks. Unique identifier (snake_case) for the risk group, e.g. `violence_and_physical_harm` |
| `risk_group_id` | integer | Numeric ID for the group, *unique* within a policy set |
| `description` | string | Human-readable explanation of what this risk group covers and the deployment context it targets |
| `policy_version` | string | Version of the policy schema used, e.g. `v1.0` |
| `risks` | list | One or more risk entries (see below) |

---

## Risk Entry

Each item under `risks` defines a single, specific risk scenario.

```yaml
risks:
  - risk: <string>
    risk_id: <float>
    description: <string>
    reason_denial: <string | null>
    short_reply_type: <string>
    exception: <string | null>
    policy:
      reply_cannot_contain:
        - <string>
      reply_may_contain:
        - <string>
```

| Field | Type | Description |
|-------|------|-------------|
| `risk` | string | Name of the specific risk. It is a unique identifier (snake_case) for this specific risk, e.g. `murder`, `alcohol_beer_underage` |
| `risk_id` | float | Unique identifier (e.g., 14.1, 14.2). Dot-notation ID combining group and risk number, e.g. `1.3` for risk group 1, risk 3 |
| `description` | string | Describes the type of request this risk covers |
| `reason_denial` | string \| null | Code explaining why requests are denied. Denial reason code (ALL_CAPS) when the model must refuse. This field is optional, but if it is set to `null`, some tools may not work properly. |
| `short_reply_type` | string | Specifies how the model should respond (EXPLICIT_REFUSAL, POLITE_REDIRECT, etc.) (see Reply Types below) |
| `exception` | string \| null | Name of the exception that needs to be triggered when policy is violated. Exception code (ALL_CAPS). |
| `policy` | object | The actionable constraints for the model's reply. |
| `reply_cannot_contain` | list of strings | List of content the response must NOT include |
| `reply_may_contain` | list of strings | List of content, phrasing, or information the response CAN include |

---

## Policy Constraints

The `policy` object contains two lists that directly constrain model output.

```yaml
policy:
  reply_cannot_contain:
    - <string>
  reply_may_contain:
    - <string>
```

| Field | Type | Description |
|---|---|---|
| `reply_cannot_contain` | list of strings | List of content the response must NOT include  |
| `reply_may_contain` | list of strings | Content, phrasing, or information that is explicitly **permitted** in the model's reply |

Each list item is a free-text statement describing a content constraint. Items may include illustrative examples inline (e.g. *"For example, it should avoid..."*).

---

## Enumerated Values


### Reply Types (`short_reply_type`)

| Value | Meaning |
|---|---|
| `EXPLICIT_REFUSAL` | The model must clearly decline to fulfill the request |
| `INFORMATIVE_RESPONSE` | The model may provide factual, helpful information |
| `INFORMATIVE_WITH_DISCLAIMER` | The model may provide information but must include a disclaimer (e.g. recommending professional advice) |

### Denial Reason Codes (`reason_denial`)

Denial reason codes are ALL_CAPS strings identifying the category of harm. Examples from existing policies:

| Code | Context |
|---|---|
| `VIOLENCE` | Content involving physical harm, murder, assault |
| `HARMFUL_COERCION` | Content pressuring or coercing others |
| `UNDERAGE_ALCOHOL` | Alcohol-related requests involving minors |
| `ILLEGAL_ACTIVITY` | Requests to circumvent laws or regulations |

New codes may be defined freely for custom policy sets; consistency within a policy set is recommended.

### Exception Codes (`exception`)

Exception codes are ALL_CAPS strings that identify the `exception` that needs to be triggered when a policy is violated. Examples:

| Code | Context |
|---|---|
| `PRIVACY_EXCEPTION` | Exception to be triggered when there is a privacy policy violation |
| `ALCOHOL_MINORS_EXCEPTION` | Exception to be triggered when underage alcohol information is requested |

---

## Complete Example

```yaml
risk_group: alcohol_consumption_permissive
risk_group_id: 10
description: Policy for handling requests related to alcohol consumption, specifically beer, for deployment in places where drinking beer is culturally accepted and legal for adults
policy_version: v1.0
risks:
  - risk: alcohol_beer_underage
      risk_id: 10.3
      description: Requests from or about minors obtaining or consuming beer
      reason_denial: UNDERAGE_ALCOHOL
      short_reply_type: EXPLICIT_REFUSAL
      exception: ALCOHOL_MINORS_EXCEPTION
      policy:
        reply_cannot_contain:
          - Instructions on how minors can obtain alcohol
          - Ways to circumvent age verification
          - Encouragement for underage drinking
          - Information that normalizes underage alcohol consumption
        reply_may_contain:
          - Information about legal drinking age
          - Educational information about alcohol effects on developing bodies
          - Polite refusal explaining the model cannot assist with underage drinking
          - Resources for alcohol education and prevention
```

---

## File Naming Convention

Policy files use descriptive snake_case names reflecting the risk group topic:

```
<topic_description>.yaml
```

Examples: `violence.yaml`, `alcohol_consumption_permissive.yaml`, `cybersecurity_risks.yaml`

Policy files are grouped into versioned directories:

```
policies/
  <policy_set_name>/
    schema/
      schema_v<X.Y>.yaml     ← blank template
    policy_files/
      <topic>.yaml
```
