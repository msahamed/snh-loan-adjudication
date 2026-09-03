# Evaluation Metrics

All metrics use generation-mode predictions from the final Qwen3-1.7B LoRA adapter. Model and deterministic results are reported separately.

## Summary

| Dataset | Model accuracy | Model macro F1 | Model citation exact | Engine accuracy | Engine macro F1 | Engine citation exact |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 99.40% | 99.32% | 97.20% | 99.40% | 99.32% | 100.00% |
| Test-1 | 99.40% | 99.44% | 95.80% | 100.00% | 100.00% | 100.00% |
| Test-2 | 87.80% | 87.29% | 91.80% | 88.80% | 88.80% | 95.60% |
| Test-3 | 78.60% | 75.06% | 53.00% | 91.60% | 94.62% | 75.40% |

## Safety-critical errors

| Dataset | Layer | False approvals of rejects | Incomplete cases adjudicated | Review cases approved | Decision overrides | Citation overrides |
|---|---|---:|---:|---:|---:|---:|
| Validation | Model | 0 | 3 | 0 |  |  |
| Validation | Engine | 0 | 3 | 0 | 0 | 14 |
| Test-1 | Model | 2 | 0 | 1 |  |  |
| Test-1 | Engine | 0 | 0 | 0 | 3 | 21 |
| Test-2 | Model | 1 | 55 | 1 |  |  |
| Test-2 | Engine | 1 | 55 | 0 | 9 | 24 |
| Test-3 | Model | 19 | 1 | 9 |  |  |
| Test-3 | Engine | 0 | 1 | 7 | 128 | 200 |

## Validation

Extraction: 99.92% field accuracy; 99.20% all-fields exact; 1.57% missing-field hallucination.

### Model: per-label metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| APPROVE | 97.66% | 100.00% | 98.82% | 125 |
| REVIEW | 100.00% | 100.00% | 100.00% | 100 |
| REJECT | 100.00% | 100.00% | 100.00% | 175 |
| COLLECTING_INFORMATION | 100.00% | 97.00% | 98.48% | 100 |

### Model: confusion matrix

Rows are expected labels; columns are predicted labels.

| Expected \ Predicted | APPROVE | REVIEW | REJECT | COLLECTING_INFORMATION | INVALID |
|---|---:|---:|---:|---:|---:|
| APPROVE | 125 | 0 | 0 | 0 | 0 |
| REVIEW | 0 | 100 | 0 | 0 | 0 |
| REJECT | 0 | 0 | 175 | 0 | 0 |
| COLLECTING_INFORMATION | 3 | 0 | 0 | 97 | 0 |

Citation precision/recall/exact: 100.00% / 96.89% / 97.20%.

Unsupported rule-ID rate: 0.00%.

Explanation exact match: 95.60%. Exact match is intentionally strict and does not score acceptable paraphrases.

### Deterministic engine: per-label metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| APPROVE | 97.66% | 100.00% | 98.82% | 125 |
| REVIEW | 100.00% | 100.00% | 100.00% | 100 |
| REJECT | 100.00% | 100.00% | 100.00% | 175 |
| COLLECTING_INFORMATION | 100.00% | 97.00% | 98.48% | 100 |

### Deterministic engine: confusion matrix

Rows are expected labels; columns are predicted labels.

| Expected \ Predicted | APPROVE | REVIEW | REJECT | COLLECTING_INFORMATION | INVALID |
|---|---:|---:|---:|---:|---:|
| APPROVE | 125 | 0 | 0 | 0 | 0 |
| REVIEW | 0 | 100 | 0 | 0 | 0 |
| REJECT | 0 | 0 | 175 | 0 | 0 |
| COLLECTING_INFORMATION | 3 | 0 | 0 | 97 | 0 |

Citation precision/recall/exact: 100.00% / 100.00% / 100.00%.

Unsupported rule-ID rate: 0.00%.

Explanation exact match: 89.60%. Exact match is intentionally strict and does not score acceptable paraphrases.

## Test-1

Extraction: 99.90% field accuracy; 99.00% all-fields exact; 1.91% missing-field hallucination.

### Model: per-label metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| APPROVE | 97.66% | 100.00% | 98.82% | 125 |
| REVIEW | 100.00% | 99.00% | 99.50% | 100 |
| REJECT | 100.00% | 98.86% | 99.43% | 175 |
| COLLECTING_INFORMATION | 100.00% | 100.00% | 100.00% | 100 |

### Model: confusion matrix

Rows are expected labels; columns are predicted labels.

| Expected \ Predicted | APPROVE | REVIEW | REJECT | COLLECTING_INFORMATION | INVALID |
|---|---:|---:|---:|---:|---:|
| APPROVE | 125 | 0 | 0 | 0 | 0 |
| REVIEW | 1 | 99 | 0 | 0 | 0 |
| REJECT | 2 | 0 | 173 | 0 | 0 |
| COLLECTING_INFORMATION | 0 | 0 | 0 | 100 | 0 |

Citation precision/recall/exact: 100.00% / 95.53% / 95.80%.

Unsupported rule-ID rate: 0.00%.

Explanation exact match: 93.20%. Exact match is intentionally strict and does not score acceptable paraphrases.

### Deterministic engine: per-label metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| APPROVE | 100.00% | 100.00% | 100.00% | 125 |
| REVIEW | 100.00% | 100.00% | 100.00% | 100 |
| REJECT | 100.00% | 100.00% | 100.00% | 175 |
| COLLECTING_INFORMATION | 100.00% | 100.00% | 100.00% | 100 |

### Deterministic engine: confusion matrix

Rows are expected labels; columns are predicted labels.

| Expected \ Predicted | APPROVE | REVIEW | REJECT | COLLECTING_INFORMATION | INVALID |
|---|---:|---:|---:|---:|---:|
| APPROVE | 125 | 0 | 0 | 0 | 0 |
| REVIEW | 0 | 100 | 0 | 0 | 0 |
| REJECT | 0 | 0 | 175 | 0 | 0 |
| COLLECTING_INFORMATION | 0 | 0 | 0 | 100 | 0 |

Citation precision/recall/exact: 100.00% / 100.00% / 100.00%.

Unsupported rule-ID rate: 0.00%.

Explanation exact match: 99.00%. Exact match is intentionally strict and does not score acceptable paraphrases.

## Test-2

Extraction: 97.56% field accuracy; 81.20% all-fields exact; 11.83% missing-field hallucination.

### Model: per-label metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| APPROVE | 60.64% | 95.00% | 74.03% | 60 |
| REVIEW | 98.31% | 96.67% | 97.48% | 60 |
| REJECT | 79.46% | 98.89% | 88.12% | 90 |
| COLLECTING_INFORMATION | 100.00% | 81.03% | 89.52% | 290 |

### Model: confusion matrix

Rows are expected labels; columns are predicted labels.

| Expected \ Predicted | APPROVE | REVIEW | REJECT | COLLECTING_INFORMATION | INVALID |
|---|---:|---:|---:|---:|---:|
| APPROVE | 57 | 0 | 3 | 0 | 0 |
| REVIEW | 1 | 58 | 1 | 0 | 0 |
| REJECT | 1 | 0 | 89 | 0 | 0 |
| COLLECTING_INFORMATION | 35 | 1 | 19 | 235 | 0 |

Citation precision/recall/exact: 89.59% / 93.05% / 91.80%.

Unsupported rule-ID rate: 0.00%.

Explanation exact match: 65.80%. Exact match is intentionally strict and does not score acceptable paraphrases.

### Deterministic engine: per-label metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| APPROVE | 63.16% | 100.00% | 77.42% | 60 |
| REVIEW | 96.77% | 100.00% | 98.36% | 60 |
| REJECT | 82.41% | 98.89% | 89.90% | 90 |
| COLLECTING_INFORMATION | 100.00% | 81.03% | 89.52% | 290 |

### Deterministic engine: confusion matrix

Rows are expected labels; columns are predicted labels.

| Expected \ Predicted | APPROVE | REVIEW | REJECT | COLLECTING_INFORMATION | INVALID |
|---|---:|---:|---:|---:|---:|
| APPROVE | 60 | 0 | 0 | 0 | 0 |
| REVIEW | 0 | 60 | 0 | 0 | 0 |
| REJECT | 1 | 0 | 89 | 0 | 0 |
| COLLECTING_INFORMATION | 34 | 2 | 19 | 235 | 0 |

Citation precision/recall/exact: 91.81% / 99.61% / 95.60%.

Unsupported rule-ID rate: 0.00%.

Explanation exact match: 82.40%. Exact match is intentionally strict and does not score acceptable paraphrases.

## Test-3

Extraction: 96.60% field accuracy; 69.60% all-fields exact; 1.91% missing-field hallucination.

### Model: per-label metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| APPROVE | 69.79% | 75.28% | 72.43% | 89 |
| REVIEW | 42.50% | 49.28% | 45.64% | 69 |
| REJECT | 85.78% | 79.75% | 82.66% | 242 |
| COLLECTING_INFORMATION | 100.00% | 99.00% | 99.50% | 100 |

### Model: confusion matrix

Rows are expected labels; columns are predicted labels.

| Expected \ Predicted | APPROVE | REVIEW | REJECT | COLLECTING_INFORMATION | INVALID |
|---|---:|---:|---:|---:|---:|
| APPROVE | 67 | 16 | 6 | 0 | 0 |
| REVIEW | 9 | 34 | 26 | 0 | 0 |
| REJECT | 19 | 30 | 193 | 0 | 0 |
| COLLECTING_INFORMATION | 1 | 0 | 0 | 99 | 0 |

Citation precision/recall/exact: 79.07% / 62.24% / 53.00%.

Unsupported rule-ID rate: 2.41%.

Explanation exact match: 43.60%. Exact match is intentionally strict and does not score acceptable paraphrases.

### Deterministic engine: per-label metrics

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| APPROVE | 91.67% | 98.88% | 95.14% | 89 |
| REVIEW | 100.00% | 84.06% | 91.34% | 69 |
| REJECT | 100.00% | 89.67% | 94.55% | 242 |
| COLLECTING_INFORMATION | 100.00% | 95.00% | 97.44% | 100 |

### Deterministic engine: confusion matrix

Rows are expected labels; columns are predicted labels.

| Expected \ Predicted | APPROVE | REVIEW | REJECT | COLLECTING_INFORMATION | INVALID |
|---|---:|---:|---:|---:|---:|
| APPROVE | 88 | 0 | 0 | 0 | 1 |
| REVIEW | 7 | 58 | 0 | 0 | 4 |
| REJECT | 0 | 0 | 217 | 0 | 25 |
| COLLECTING_INFORMATION | 1 | 0 | 0 | 95 | 4 |

Citation precision/recall/exact: 100.00% / 75.66% / 75.40%.

Unsupported rule-ID rate: 0.00%.

Explanation exact match: 74.20%. Exact match is intentionally strict and does not score acceptable paraphrases.

## Interpretation

Validation and Test-1 show strong in-distribution performance. Three validation cases with missing information were incorrectly completed by the model, so both layers approved them. Test-2 exposes more unresolved-evidence failures. Test-3 shows that the model is not fully rule-agnostic. The deterministic layer corrects many decisions and citations, but it cannot recover applicant values that the model omitted or hallucinated.
