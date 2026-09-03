# Synthetic Data Generation

The rules engine creates canonical application values, decisions, failed rule IDs, and explanations. Qwen3-14B only converts each canonical profile into a multi-turn dialogue.

This keeps the labels reproducible and prevents the teacher model from deciding credit outcomes.

## Preview coverage

Run:

    python scripts/generate_data.py --dry-run

## Generate the first sample

After approval, run:

    python scripts/generate_data.py --model /workspace/models/Qwen3-14B --output data/sample.jsonl

The first generation plan covers all ten fields and all ten rule IDs. It includes complete applications, missing values, numerical boundaries, categorical variations, dialogue variations, and multiple failures.
