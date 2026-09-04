# Synthetic Data Generation

**Sabber Ahamed · September 2026**

I used the rules engine to create canonical application values, decisions, failed rule IDs, and explanations. I copied the supplied rules into every record. I did not let an LLM create or modify policy or labels.

I initially tested Qwen3-14B for dialogue paraphrasing. The outputs passed structural validation, but my semantic review found field mismatches, so I rejected them. For the final dataset, I used reviewed, field-specific utterance templates and varied values, turn order, wording, corrections, missing information, irrelevant text, and typos. This kept generation reproducible and prevented teacher-model errors from contaminating the labels.

## Build

Run:

    python scripts/build_dataset.py --output-dir data

I generated:

- 4,000 training records
- 500 validation records
- 500 test records

I kept canonical profiles unique across splits. Every split covers all ten rule-failure paths and includes approve, review, reject, and collecting-information outcomes.

## Adversarial test set

Build the separate robustness set with:

    python scripts/build_adversarial_test.py

I excluded these 500 records from training and validation. They test heavy missingness, contradictions, vague and accidental answers, hostile or off-topic responses, corrections, misleading rule claims, prompt injection, third-party facts, premature agent decisions, and irrelevant sensitive disclosures. The deterministic rules engine still creates every label.

## Changed-rules test set

Build the paired policy-change set with:

    python scripts/build_changed_rules_test.py

I built `data/test-3.jsonl` from the unseen Test-1 dialogues, then replaced ruleset 1.0 with four ruleset 2.0 variants. I changed thresholds, allowed categories, failure actions, rule IDs, and rule order. The deterministic engine recomputed every label; 174 decisions and 348 citation sets differ from Test-1. Reusing the dialogue isolates policy adaptability from dialogue difficulty.
