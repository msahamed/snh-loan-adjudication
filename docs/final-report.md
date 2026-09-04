# AI Loan Adjudication: Final Report

**Sabber Ahamed · September 3, 2026**

## Business problem

I defined the goal as turning a loan-application conversation into an **adjudication decision plus a clear rationale for the customer**. The four possible outcomes are **Approved, Rejected, Human review, and Needs information**.

The language model structures the conversation. The deterministic rules engine then recalculates the decision and reasons from the active lending rules. Clear applications can finish automatically, missing information returns to the chatbot, and review cases or disagreements go to a person. Because policy stays outside the model, rules can change and new clients can be added without retraining a policy-specific model.

## System I built

```text
                               CUSTOMER DIALOGUE
                                       ↓
                              QWEN3-1.7B + LORA
                           10 fields + shadow result
                                       ↓
                          SCHEMA & EVIDENCE VALIDATION
                                       ↓
                           DETERMINISTIC RULES ENGINE
                           decision + failed rule IDs
                                       ↓
                            VERIFIED CUSTOMER OUTPUT
                       adjudication decision + rationale
```

The model returns JSON containing ten extracted fields, a shadow decision, failed rule IDs, and a short explanation. That output is only a proposal. Validation blocks invalid or unresolved values. The rules engine evaluates every active rule again and applies **Rejected > Human review > Approved** precedence. Missing information blocks a lending decision. The customer rationale is generated only from the verified result.

## Why the deterministic layer is necessary

An incorrect lending explanation has regulatory and client costs. The U.S. Consumer Financial Protection Bureau states that adverse-action reasons must be specific and accurately describe the factors considered. A complex algorithm does not remove that obligation. [CFPB Circular 2022-03](https://www.consumerfinance.gov/compliance/circulars/circular-2022-03-adverse-action-notification-requirements-in-connection-with-credit-decisions-based-on-complex-algorithms/)

I use the model for language understanding and code for decision authority. This produces repeatable decisions, verifies the rule IDs and thresholds shown to the customer, supports policy updates without retraining, and creates an auditable record. Model-engine disagreements trigger human review. This design does not by itself prove fair-lending compliance; policy, data use, and outcomes still require legal and fairness review.

## Why I selected Qwen3-1.7B

This is a narrow structured-output task, and the rules arrive with each request rather than being memorized. Qwen3-1.7B should cost less and respond faster than a 14B serving model, although production benchmarks are still needed. LoRA produced an adapter of about 84 MB, which is easy to store and version. A larger model may interpret harder language better, but it still cannot guarantee correct policy citations.

## Data and training

- **Core data:** 4,000 training, 500 validation, and 500 clean test conversations.
- **Adversarial Test-2:** 500 messy conversations excluded from training.
- **Changed-rules Test-3:** 500 conversations evaluated with unseen rules and no retraining.
- **Coverage:** missing values, boundaries, aliases, corrections, contradictions, ambiguity, irrelevant text, and typos.
- **Ground truth and training:** code generated the labels; I trained a QLoRA adapter for two epochs and 250 steps.

I published the [model adapter](https://huggingface.co/sabber/snh-qwen3-1.7b-loan-adjudication-lora) and [6,000 dataset records](https://huggingface.co/datasets/sabber/snh-loan-adjudication-synthetic) on Hugging Face.

## Evaluation results

I measured the model in generation mode and the verified rules-engine output separately.

| Evaluation set | Purpose | Model decision | Rules-engine decision | Model citations | Verified citations |
|---|---|---:|---:|---:|---:|
| Validation | Model selection | 99.4% | 99.4% | 97.2% | 100.0% |
| Test-1 | Clean unseen cases | 99.4% | 100.0% | 95.8% | 100.0% |
| Test-2 | Adversarial dialogue | 87.8% | 88.8% | 91.8% | 95.6% |
| Test-3 | Changed rules | 78.6% | 91.6% | 53.0% | 75.4% |

- On Test-1, the rules engine corrected the remaining decision and citation errors.
- On Test-2, it corrected 6 decisions and 20 citation sets when extraction was accurate.
- On Test-3, it corrected 94 decisions and 129 citation sets. Expected-rejection false approvals fell from 19 to zero.
- The main weakness is extraction: a vague or contradictory answer can become a plausible but wrong value that the rules engine cannot repair.

## Business conclusion and production boundary

The experiment supports a hybrid product. The small model keeps language processing relatively inexpensive. Deterministic verification avoids a second verification model, makes policy changes faster, supports new-client onboarding, and gives current clients an explanation they can audit.

I would not use this prototype for unsupervised real-world credit decisions yet. The results measure synthetic dialogue and supplied-rule fidelity, not borrower risk or regulatory approval. A production pilot needs evidence grounding for every value, stronger ambiguity detection, versioned audit logs, representative real-world evaluation, cost and latency benchmarks, and human review for missing information, conflicts, configured review outcomes, or model-engine disagreement.
