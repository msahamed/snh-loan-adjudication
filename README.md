# Auditable Loan Adjudication

This project implements a hybrid approach to the supplied SNH-AI loan-adjudication challenge. A fine-tuned language model will extract structured application fields and produce a shadow decision. A deterministic rules engine will produce the authoritative decision and verified customer explanation.

Current status: system design and synthetic data-generation setup.

## Data-generation preview

Run `python scripts/generate_data.py --dry-run` to inspect planned field, rule, scenario, and decision coverage without loading a model.

See [the system design](docs/system-design.md) and [data-generation notes](docs/data-generation.md).
