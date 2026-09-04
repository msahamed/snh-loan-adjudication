# Fine-Tuning

**Sabber Ahamed · September 2026**

I fine-tuned Qwen3-1.7B with one QLoRA adapter. The model receives the active rules and dialogue, then produces the flat JSON contract documented in the system design. I keep the deterministic engine authoritative.

## Preprocessing

Run:

    python scripts/prepare_training_data.py \
      --model /workspace/models/Qwen3-1.7B \
      --input-dir data \
      --output-dir data/processed

I validate every record and apply Qwen's native chat template. The longest record contains 1,582 tokens, so I use a 2,048-token limit. I use dynamic batch padding and compute loss only on assistant-response tokens to avoid wasting memory on prompt tokens and fixed-length padding.

## Baseline

I evaluated the untouched model before training:

    python scripts/evaluate_baseline.py \
      --model /workspace/models/Qwen3-1.7B \
      --data data/validation.jsonl \
      --limit 100

I measured JSON validity, exact field accuracy, missing-value accuracy, decision accuracy, failed-rule precision and recall, and the engine's decision accuracy when consuming predicted fields.

I kept the test split untouched while selecting the adapter and hyperparameters from validation results.

## Measured baseline

I evaluated Qwen3-1.7B without fine-tuning on 100 validation records:

- JSON validity: 100%
- Schema validity: 100%
- Exact field accuracy: 96.9%
- All fields exact per record: 77%
- Shadow decision accuracy: 42%
- Failed-rule exact match: 0%
- Deterministic-engine decision accuracy from predicted fields: 91%

The base model usually extracted the application correctly but did not reliably apply the supplied rules. I used LoRA to target this gap while keeping the deterministic engine as the final authority.

## QLoRA training

Install the dependencies and run a one-step smoke test:

    pip install -r requirements.txt

    python scripts/train_qlora.py \
      --model /workspace/models/Qwen3-1.7B \
      --max-train-samples 8 \
      --max-validation-samples 4 \
      --max-steps 1 \
      --eval-steps 1 \
      --save-steps 1 \
      --output-dir artifacts/smoke-test

After the smoke test passed, I removed the sample and step limits for the full two-epoch run. I used NF4 double quantization, rank 16, alpha 32, dropout 0.05, dynamic padding, gradient checkpointing, and response-only loss.

## Fine-tuned evaluation

I first evaluated the final adapter in generation mode on all 500 validation records:

- 100% valid JSON and schema
- 99.92% field accuracy
- 99.4% shadow-decision accuracy
- 97.2% model failed-rule exact match
- 99.4% deterministic decision accuracy
- 100% deterministic failed-rule exact match
- 0 unsupported rule IDs

The three decision errors were incomplete applications where the model supplied a plausible value for missing information. Because my rules engine receives extracted fields rather than raw dialogue evidence, it repeated those approvals. This is the main validation limitation. I would add an evidence-grounding gate before adjudication in the next experiment.

I trained the final adapter for 250 steps. On the untouched 500-record test split, it achieved 99.4% shadow-decision accuracy and 95.8% failed-rule exact match. My deterministic recalculation produced 100% decision and citation accuracy.

I made the separate 500-record adversarial Test-2 set intentionally harder. It contains contradictions, ambiguous and missing answers, prompt injection, misleading rule claims, third-party values, premature decisions, and irrelevant sensitive disclosures. I measured:

- 100% valid JSON and schema
- 97.56% field accuracy
- 87.8% shadow-decision accuracy
- 91.8% model failed-rule exact match
- 88.8% deterministic decision accuracy
- 95.6% deterministic failed-rule exact match
- 0 unsupported rule IDs

The deterministic layer corrected 20 citation sets and 6 decisions when field extraction was accurate. It could not recover 56 decisions where the model converted ambiguous or contradictory dialogue into a concrete field value. I would block adjudication when evidence is unresolved or conflicting before running the rules.

### Changed-rules test

For Test-3, I reused 500 Test-1 dialogues with unseen thresholds, categorical allowances, failure actions, rule IDs, and rule ordering. I did not retrain the model. I measured:

- 100% valid JSON and 93.2% exact schema
- 96.6% field accuracy
- 78.6% shadow-decision accuracy
- 53.0% model failed-rule exact match
- 91.6% deterministic decision accuracy
- 75.4% deterministic failed-rule exact match
- 2.2% of records contained an unsupported rule ID

The deterministic layer corrected 94 model decisions and 129 citation sets. The model was not fully rule-agnostic: it often removed values that the new policy disallowed instead of preserving the reported value for deterministic evaluation. Of 170 field errors, 140 involved residency status and 25 involved employment status. In another experiment, I would separate extraction from policy evaluation more strongly and train across multiple rulesets.
