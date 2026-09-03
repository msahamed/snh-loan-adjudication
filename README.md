# Auditable Loan Adjudication

This project implements a hybrid approach to the supplied SNH-AI loan-adjudication challenge. A fine-tuned language model will extract structured application fields and produce a shadow decision. A deterministic rules engine will produce the authoritative decision and verified customer explanation.

Current status: system design and a validated 5,000-record synthetic dataset.

## Data-generation preview

Run `python scripts/generate_data.py --dry-run` to inspect planned field, rule, scenario, and decision coverage without loading a model.

See [the system design](docs/system-design.md) and [data-generation notes](docs/data-generation.md).

## Build the dataset

Run:

    python scripts/build_dataset.py --output-dir data

This creates 4,000 training, 500 validation, and 500 test records. Generated JSONL files are intentionally excluded from Git.
