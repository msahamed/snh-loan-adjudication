# Loan Adjudication System Design

**Sabber Ahamed · September 2026**

## Purpose

I designed an MVP that collects loan-application information through dialogue, applies the supplied credit rules, explains the decision, and preserves the information needed for an audit.

## My approach

I used one fine-tuned language model for dialogue understanding, supported by deterministic policy and explanation layers.

```text
Customer dialogue
       |
       v
Fine-tuned LLM
  - extracts and normalizes application fields
  - uses null for missing or unresolved fields
  - produces a shadow decision, failed rule IDs, and explanation
       |
       v
Schema validation
       |
       v
Deterministic rules engine
  - evaluates the active credit rules
  - produces the authoritative decision
       |
       v
Deterministic explanation layer
  - creates the customer explanation
  - creates the internal audit record
```

## Why not rely on one end-to-end LLM?

A single LLM can extract fields, apply rules, select a decision, and write an explanation. I trained and evaluated that end-to-end behavior because it matches the challenge.

I did not make the LLM the decision authority. Exact thresholds and comparisons require consistent, reproducible behavior. The rules engine also lets me change policy without retraining the model.

I did not add a second LLM for verification. It would add cost and latency without guaranteeing correctness. Code can verify the rules, cited values, and final explanation more reliably.

## Model responsibilities

I use the language model to:

- Convert a multi-turn dialogue into the ten fields referenced by the rules
- Normalize expressions such as “72k per year” into structured values
- Return `null` for information that is missing or remains unresolved
- Resolve corrections from later dialogue turns
- Produce a shadow decision, failed rule IDs, and a short explanation

I require the model output to follow a defined JSON schema. Invalid output or unsupported values do not reach the decision engine. The conversation manager derives missing fields from `null` values and can ask the next question without relying on the model to choose it.

## Training contract

Each supervised example uses the active ruleset and customer dialogue as input. I train against one flat JSON target:

```json
{
  "age": 35,
  "credit_score": 650,
  "annual_income_usd": 60000,
  "debt_to_income_ratio_percent": 25,
  "employment_status": "employed_full_time",
  "current_employment_duration_months": 24,
  "residency_status": "US_Citizen",
  "has_bankruptcy_recent": false,
  "requested_amount_usd": 15000,
  "has_verifiable_bank_account": true,
  "decision": "REJECT",
  "failed_rule_ids": ["RULE-CREDIT-001"],
  "explanation": "The reported credit score is below the required minimum."
}
```

I require the extracted fields even though the model returns `failed_rule_ids`. The rules engine needs the observed values to evaluate policy independently. Trusting only the model's failed-rule list would remove the deterministic boundary.

I exclude chain of thought and nested application objects from the target. Missing or unresolved values use `null`. Dataset and audit metadata stay outside the training target.

At inference time, schema validation enforces the contract. The parsed fields pass directly to the rules engine, so I do not need a second extraction step.

## Data-generation coverage

I generated the synthetic dataset across these scenario groups:

- Complete applications: approve, review, and reject.
- Missing data: one field missing, several fields missing, and all fields missing.
- Numerical boundaries: exactly at, just below, just above, and far from each threshold.
- Categorical values: allowed, disallowed, informal aliases, and unknown values.
- Dialogue behavior: out-of-order answers, corrections, contradictions, ambiguity, irrelevant text, and typos.

## Rules-engine responsibilities

I use the rules engine to:

- Load the supplied JSON ruleset rather than embed thresholds in code or model weights
- Map each configured field path to the corresponding flat model-output field
- Evaluate each field using its configured operator and value
- Use `action_on_fail` to determine the outcome
- Apply decision precedence: `REJECT` over `REVIEW`, and `REVIEW` over `APPROVE`
- Treat incomplete or conflicting applications as `COLLECTING_INFORMATION` or route them to human review
- Record the ruleset version and result of every evaluated rule
- Compare its result with the model's decision and failed-rule list during evaluation

`severity` describes the importance of a failure. It does not determine the decision by itself. The configured `action_on_fail` controls the result.

## Decisions

The customer workflow has four states:

- `COLLECTING_INFORMATION`: required information is missing or unresolved.
- `APPROVE`: every applicable rule passes.
- `REVIEW`: no rejection rule fails, but at least one rule returns `FLAG_REVIEW`.
- `REJECT`: at least one rule returns `REJECT`.

## Explanations and citations

I build the final customer explanation from verified rule results, not free-form model output.

I show the customer plain language, including the relevant reported value and policy requirement. I keep internal details such as rule IDs and operators in the audit record.

I would retain these fields in an audit record:

- Decision and timestamp
- Application values used in the decision
- Source dialogue evidence
- Rule ID, group, and severity
- Observed value, operator, and required value
- Rule result and `action_on_fail`
- Ruleset and model versions

For a later version, I could use an LLM to adjust the tone of a customer explanation only after a deterministic check confirms every value, threshold, reason, and decision. Otherwise, I would return the canonical template.

## Human review

I route an application to human review when:

- Information remains missing or contradictory.
- Schema validation fails.
- The model's shadow decision disagrees with the rules engine.
- A configured rule returns `FLAG_REVIEW`.

## Evaluation boundary

I report the raw LLM and deterministic results separately. This makes clear what the model learned and what the rules engine corrected.

I measured field extraction accuracy, missing-field behavior, decision accuracy, class-level precision and recall, critical false approvals, explanation accuracy, citation accuracy, and disagreement. I left latency and inference cost for a later production benchmark.

Because the examples are synthetic, my results measure fidelity to the supplied rules and generated dialogue scenarios. They do not establish real-world credit-risk performance.
