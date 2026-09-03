# Synthetic Data Generation

The rules engine creates canonical application values, decisions, failed rule IDs, and explanations. It copies the supplied rules into every record; an LLM never creates or modifies policy or labels.

An initial Qwen3-14B experiment generated dialogue paraphrases. Structural validation passed, but manual semantic review found field mismatches. Those candidates were rejected. The final builder uses reviewed, field-specific utterance templates with randomized values, turn order, wording, corrections, missing information, irrelevant text, and typos.

This approach is fast, reproducible, and prevents teacher-model errors from contaminating training labels.

## Build

Run:

    python scripts/build_dataset.py --output-dir data

The default split is:

- 4,000 training records
- 500 validation records
- 500 test records

Canonical profiles are unique across all splits. Each split covers all ten rule-failure paths and contains approve, review, reject, and collecting-information outcomes.

## Adversarial test set

Build the separate robustness set with:

    python scripts/build_adversarial_test.py

This creates 500 records in `data/test-2.jsonl`. The set is excluded from training and validation. It tests heavy missingness, contradictions, vague and accidental answers, hostile or off-topic responses, corrections, misleading rule claims, prompt injection, third-party facts, premature agent decisions, and irrelevant sensitive disclosures. Labels still come only from the deterministic rules engine.
