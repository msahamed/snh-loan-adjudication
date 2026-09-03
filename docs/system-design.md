# Loan Adjudication System Design

## Purpose

Build a conversational loan-adjudication system from the supplied credit rules. The system should collect application information through dialogue, produce an adjudication decision, explain that decision to the customer, and preserve an auditable record.

This document records the proposed architecture. Dataset generation will be designed separately.

## Proposed approach

Use one fine-tuned language model for dialogue understanding, supported by deterministic policy and explanation layers.

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

A single LLM can extract fields, apply rules, select a decision, and write an explanation. We will train and evaluate this behavior because it matches the challenge.

The LLM should not be the production decision authority. Exact thresholds and comparisons require consistent, reproducible behavior. A deterministic rules engine also allows a policy change without retraining the model.

A second LLM is not required for verification. It would add cost and latency without guaranteeing correctness. Code can verify the rules, cited values, and final explanation more reliably.

## Model responsibilities

The language model will:

- Convert a multi-turn dialogue into the ten fields referenced by the rules.
- Normalize expressions such as “72k per year” into structured values.
- Return `null` for information that is missing or remains unresolved.
- Resolve corrections from later dialogue turns.
- Produce a shadow decision, failed rule IDs, and a short explanation.

The model output must follow a defined JSON schema. Invalid output or unsupported values will not reach the decision engine. The conversation manager can derive missing fields from `null` values and ask the next question without requiring the model to generate one.

## Training contract

Each supervised example will use the active ruleset and customer dialogue as input. The target will be one flat JSON object:

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

The extracted fields are required even though the model returns `failed_rule_ids`. The rules engine needs the observed values to evaluate the policy independently. Trusting only the model's failed-rule list would remove the deterministic safety boundary.

The target contains no chain of thought or nested application objects. Missing or unresolved values use `null`. Dataset and audit metadata may remain outside the training target.

At inference time, constrained JSON generation and schema validation will enforce the contract. The parsed fields pass directly to the rules engine, so no second extraction step is needed.

## Data-generation coverage

The synthetic dataset will cover these main scenario groups:

- Complete applications: approve, review, and reject.
- Missing data: one field missing, several fields missing, and all fields missing.
- Numerical boundaries: exactly at, just below, just above, and far from each threshold.
- Categorical values: allowed, disallowed, informal aliases, and unknown values.
- Dialogue behavior: out-of-order answers, corrections, contradictions, ambiguity, irrelevant text, and typos.

## Rules-engine responsibilities

The rules engine will:

- Load the supplied JSON ruleset rather than embed thresholds in code or model weights.
- Map each configured field path to the corresponding flat model-output field.
- Evaluate each field using its configured operator and value.
- Use `action_on_fail` to determine the outcome.
- Apply decision precedence: `REJECT` over `REVIEW`, and `REVIEW` over `APPROVE`.
- Treat incomplete or conflicting applications as `COLLECTING_INFORMATION` or route them to human review.
- Record the ruleset version and result of every evaluated rule.
- Compare its result with the model's decision and failed-rule list for evaluation and monitoring.

`severity` describes the importance of a failure. It does not determine the decision by itself. The configured `action_on_fail` controls the result.

## Decisions

The customer workflow has four states:

- `COLLECTING_INFORMATION`: required information is missing or unresolved.
- `APPROVE`: every applicable rule passes.
- `REVIEW`: no rejection rule fails, but at least one rule returns `FLAG_REVIEW`.
- `REJECT`: at least one rule returns `REJECT`.

## Explanations and citations

The final customer explanation will be built from verified rule results, not free-form model output.

The customer sees plain language, including the relevant reported value and policy requirement. Internal implementation details such as rule IDs and operators do not need to appear in the customer message.

The audit record retains:

- Decision and timestamp
- Application values used in the decision
- Source dialogue evidence
- Rule ID, group, and severity
- Observed value, operator, and required value
- Rule result and `action_on_fail`
- Ruleset and model versions

An optional LLM rewrite may improve the tone of a customer explanation. It can only be used if a deterministic check confirms that every value, threshold, reason, and decision matches the audit result. Otherwise, the system returns the canonical template.

## Human review

Human review is required when:

- Information remains missing or contradictory.
- Schema validation fails.
- The model's shadow decision disagrees with the rules engine.
- A configured rule returns `FLAG_REVIEW`.

## Evaluation boundary

We will report the raw LLM and verified hybrid results separately. This makes clear what the trained model learned and what the deployable system guarantees through deterministic controls.

Planned measures include field extraction accuracy, missing-field detection, decision accuracy, class-level precision and recall, critical false approvals, explanation accuracy, citation accuracy, disagreement rate, latency, and inference cost.

Because the examples will be synthetic, results will measure fidelity to the supplied rules and generated dialogue scenarios. They will not establish real-world credit-risk performance.
