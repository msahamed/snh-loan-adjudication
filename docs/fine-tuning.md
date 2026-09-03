# Fine-Tuning

The first experiment uses Qwen3-1.7B with one QLoRA adapter. The model receives the active rules and dialogue, then produces the flat JSON contract documented in the system design. The deterministic engine remains authoritative.

## Preprocessing

Run:

    python scripts/prepare_training_data.py \
      --model /workspace/models/Qwen3-1.7B \
      --input-dir data \
      --output-dir data/processed

The script validates every record and applies the model's native chat template. The measured maximum is 1,582 tokens, so training uses a 2,048-token limit. Training uses dynamic batch padding and computes loss only on assistant-response tokens; pre-padding every record would waste memory.

## Baseline

Before training, evaluate the untouched model:

    python scripts/evaluate_baseline.py \
      --model /workspace/models/Qwen3-1.7B \
      --data data/validation.jsonl \
      --limit 100

The report includes JSON validity, exact field accuracy, missing-value accuracy, decision accuracy, failed-rule precision/recall, and the authoritative engine's decision accuracy when consuming the predicted fields.

The test split remains untouched until the adapter and hyperparameters are selected using validation results.

## Measured baseline

Qwen3-1.7B was evaluated without fine-tuning on 100 validation records:

- JSON validity: 100%
- Schema validity: 100%
- Exact field accuracy: 96.9%
- All fields exact per record: 77%
- Shadow decision accuracy: 42%
- Failed-rule exact match: 0%
- Deterministic-engine decision accuracy from predicted fields: 91%

The model usually extracts the application correctly but does not reliably apply the supplied rules. This is the behavior the LoRA experiment should target, while the deterministic engine remains the final authority.

## QLoRA training

Install the single additional training dependency and run a one-step smoke test:

    pip install -r training-requirements.txt

    python scripts/train_qlora.py \
      --model /workspace/models/Qwen3-1.7B \
      --max-train-samples 8 \
      --max-validation-samples 4 \
      --max-steps 1 \
      --eval-steps 1 \
      --save-steps 1 \
      --output-dir artifacts/smoke-test

After the smoke test passes, remove the sample and step limits for the full two-epoch run. The script uses NF4 double quantization, rank 16, alpha 32, dropout 0.05, dynamic padding, gradient checkpointing, and response-only loss.

## Fine-tuned evaluation

The final adapter was first evaluated in generation mode on all 500 validation records:

- 100% valid JSON and schema
- 99.92% field accuracy
- 99.4% shadow-decision accuracy
- 97.2% model failed-rule exact match
- 99.4% deterministic decision accuracy
- 100% deterministic failed-rule exact match
- 0 unsupported rule IDs

The three decision errors were incomplete applications where the model supplied a plausible value for missing information. Because the rules engine receives extracted fields rather than raw dialogue evidence, it repeated those approvals. This is the main validation limitation and supports adding an evidence-grounding gate before adjudication.

The final adapter completed 250 training steps. On the untouched 500-record test split it achieved 99.4% shadow-decision accuracy and 95.8% failed-rule exact match. Recomputing from extracted fields produced 100% deterministic decision and citation accuracy.

The separate 500-record adversarial `test-2` set is intentionally harder. It contains contradictions, ambiguous and missing answers, prompt injection, misleading rule claims, third-party values, premature decisions, and irrelevant sensitive disclosures. Results were:

- 100% valid JSON and schema
- 97.56% field accuracy
- 87.8% shadow-decision accuracy
- 91.8% model failed-rule exact match
- 88.8% deterministic decision accuracy
- 95.6% deterministic failed-rule exact match
- 0 unsupported rule IDs

The deterministic layer corrected 20 citation sets and 6 decisions when field extraction was accurate. It could not recover 56 decisions where ambiguous or contradictory dialogue was converted into a concrete field value. This identifies a required pre-adjudication safeguard: unresolved or conflicting evidence must block adjudication before rules run.

### Changed-rules test

Test-3 uses 500 test-1 dialogues with unseen thresholds, categorical allowances, failure actions, rule IDs, and rule ordering. No retraining was performed. Results were:

- 100% valid JSON and 93.2% exact schema
- 96.6% field accuracy
- 78.6% shadow-decision accuracy
- 53.0% model failed-rule exact match
- 91.6% deterministic decision accuracy
- 75.4% deterministic failed-rule exact match
- 2.2% of records contained an unsupported rule ID

The deterministic layer corrected 94 model decisions and 129 citation sets. The model was not fully rule-agnostic: it often removed values that the new policy disallowed instead of preserving the reported value for deterministic evaluation. Of 170 field errors, 140 were residency status and 25 were employment status. Future training should separate extraction from policy evaluation more strongly and include multiple rulesets during training.
