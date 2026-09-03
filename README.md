# Auditable Loan Adjudication

This project implements a hybrid approach to the supplied SNH-AI loan-adjudication challenge. A fine-tuned language model will extract structured application fields and produce a shadow decision. A deterministic rules engine will produce the authoritative decision and verified customer explanation.

Current status: trained Qwen3-1.7B QLoRA adapter, deterministic verification layer, a validated 5,000-record synthetic dataset, and separate 500-record adversarial and changed-rules test sets.

## Published artifacts

- [Qwen3-1.7B LoRA adapter](https://huggingface.co/sabber/snh-qwen3-1.7b-loan-adjudication-lora)
- [Synthetic training and evaluation datasets](https://huggingface.co/datasets/sabber/snh-loan-adjudication-synthetic)

## Evaluation

- [Model and deterministic metrics](docs/evaluation-metrics.md)
- [Nine representative model and deterministic outputs](docs/representative-outputs.md)
- Machine-readable results: [`evaluation/metrics.json`](evaluation/metrics.json) and [`evaluation/representative-outputs.json`](evaluation/representative-outputs.json)

## Data-generation preview

Run `python scripts/generate_data.py --dry-run` to inspect planned field, rule, scenario, and decision coverage without loading a model.

See [the system design](docs/system-design.md), [data-generation notes](docs/data-generation.md), and [fine-tuning plan](docs/fine-tuning.md).

## Build the dataset

Run:

    python scripts/build_dataset.py --output-dir data

This creates 4,000 training, 500 validation, and 500 test records. Generated JSONL files are intentionally excluded from Git.

Build the training-excluded adversarial set with:

    python scripts/build_adversarial_test.py

Build the paired changed-rules test with:

    python scripts/build_changed_rules_test.py

## Fine-tuning

See [the fine-tuning guide](docs/fine-tuning.md) for preprocessing, baseline evaluation, and QLoRA training commands.
