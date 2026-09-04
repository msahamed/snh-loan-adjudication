# Auditable Loan Adjudication

**Built by [Sabber Ahamed](https://github.com/msahamed) for the SNH AI/ML Technology Lead challenge.**

I built this MVP to show how I would turn a loan conversation into an explainable adjudication decision. I use a fine-tuned Qwen3-1.7B model to extract structured application data and produce a shadow decision. A deterministic rules engine then recalculates the authoritative result from the active policy.

The four outcomes are `APPROVE`, `REJECT`, `REVIEW`, and `COLLECTING_INFORMATION`.

## Project links

| Resource | Link |
|---|---|
| GitHub repository | [Browse the source](https://github.com/msahamed/snh-loan-adjudication) |
| Interactive walkthrough | [Open the Vercel demo](https://demo-bice-mu-32.vercel.app) |
| Final report | [Read the two-page PDF](final-report.pdf) |
| System design | [Read the architecture and design choices](docs/system-design.md) |
| Model and training | [Read the training setup and analysis](docs/fine-tuning.md) |
| Evaluation | [See metrics and confusion matrices](docs/evaluation-metrics.md) |
| Model examples | [Compare model and deterministic outputs](docs/representative-outputs.md) |
| Data generation | [See how I built the synthetic data](docs/data-generation.md) |
| Model adapter | [Download the Qwen3-1.7B LoRA adapter from Hugging Face](https://huggingface.co/sabber/snh-qwen3-1.7b-loan-adjudication-lora) |
| Dataset | [Open the 6,000-record dataset on Hugging Face](https://huggingface.co/datasets/sabber/snh-loan-adjudication-synthetic) |
| Supplied rules | [View the credit policy](credit_rules.json) |
| Challenge brief | [View the problem statement](problem_statement.txt) |

## Why I used a hybrid design

I wanted the conversation layer to handle natural language without asking a probabilistic model to be the final policy authority.

- The model extracts and normalizes the application fields.
- Schema validation blocks malformed output.
- The rules engine applies the supplied thresholds and decision precedence.
- Deterministic explanations cite the rules that actually failed.
- Human review handles unresolved information and model-engine disagreement.

This separation lets a client change lending rules without retraining the model. It also makes the final decision reproducible and easier to audit.

## What I evaluated

I trained on 4,000 synthetic conversations and selected the adapter using a separate 500-record validation set. I reserved three 500-record test sets for different questions:

- **Test-1:** clean, unseen conversations under the original policy
- **Test-2:** missing, vague, contradictory, hostile, and adversarial dialogue
- **Test-3:** Test-1 conversations evaluated against unseen policy variants without retraining

I used one NVIDIA RTX 5090 with 32 GiB of VRAM for dataset-generation experiments and fine-tuning. The final two-epoch, 250-step training run took roughly 45 minutes.

| Test set | Model accuracy | Deterministic accuracy | Deterministic citation match |
|---|---:|---:|---:|
| Test-1 | 99.4% | 100.0% | 100.0% |
| Test-2 | 87.8% | 88.8% | 95.6% |
| Test-3 | 78.6% | 91.6% | 75.4% |

The clean test shows the value of deterministic recalculation. The harder tests expose the remaining MVP limitation: if the model converts vague or conflicting dialogue into a plausible field value, the rules engine cannot recover the missing evidence. I would add dialogue-evidence grounding before using this design beyond experimentation.

## Repository map

```text
demo/          Next.js walkthrough deployed on Vercel
docs/          Design, data, training, evaluation, and report source
evaluation/    Machine-readable metrics and selected outputs
scripts/       Dataset, preprocessing, training, and evaluation code
credit_rules.json
final-report.pdf
```

Generated datasets, predictions, model weights, caches, and local challenge PDFs are intentionally excluded from Git. I publish the large model and dataset artifacts through Hugging Face instead.

## Run the demo

Requires Node.js 20.9 or newer.

```bash
cd demo
npm install
npm run dev
```

The walkthrough uses representative evaluation outputs rather than a live inference endpoint. This keeps the MVP easy to inspect and deploy.

## Reproduce the ML workflow

Install a CUDA-compatible PyTorch build for the training machine, then install the project dependencies:

```bash
pip install -r requirements.txt
```

Build the synthetic splits and both held-out stress tests:

```bash
python scripts/build_dataset.py --output-dir data
python scripts/build_adversarial_test.py
python scripts/build_changed_rules_test.py
```

Prepare Qwen chat records:

```bash
python scripts/prepare_training_data.py \
  --model Qwen/Qwen3-1.7B \
  --input-dir data \
  --output-dir data/processed
```

See the [model and training guide](docs/fine-tuning.md) for the baseline, QLoRA, and evaluation commands.

## Author

I’m **Sabber Ahamed**. The architecture, synthetic-data pipeline, training experiment, evaluation, report, and interactive walkthrough in this repository are my work for this challenge.
