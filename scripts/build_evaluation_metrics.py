#!/usr/bin/env python3
"""Build submission-ready model and deterministic evaluation metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


LABELS = ["APPROVE", "REVIEW", "REJECT", "COLLECTING_INFORMATION"]
PREDICTED_LABELS = LABELS + ["INVALID"]


def ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open() as handle:
        return [json.loads(line) for line in handle]


def normalized_label(value: Any) -> str:
    return value if value in LABELS else "INVALID"


def classification_metrics(
    results: list[dict[str, Any]],
    prediction: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    matrix = {
        expected: {predicted: 0 for predicted in PREDICTED_LABELS}
        for expected in LABELS
    }
    for result in results:
        expected = result["expected_decision"]
        matrix[expected][normalized_label(prediction(result))] += 1

    per_label: dict[str, Any] = {}
    for label in LABELS:
        true_positive = matrix[label][label]
        false_positive = sum(
            matrix[expected][label] for expected in LABELS if expected != label
        )
        false_negative = sum(
            count for predicted, count in matrix[label].items() if predicted != label
        )
        precision = ratio(true_positive, true_positive + false_positive)
        recall = ratio(true_positive, true_positive + false_negative)
        f1 = (
            round(2 * precision * recall / (precision + recall), 4)
            if precision + recall
            else 0.0
        )
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(matrix[label].values()),
        }

    critical_false_approvals = sum(
        result["expected_decision"] == "REJECT"
        and normalized_label(prediction(result)) == "APPROVE"
        for result in results
    )
    incomplete_adjudicated = sum(
        result["expected_decision"] == "COLLECTING_INFORMATION"
        and normalized_label(prediction(result))
        in {"APPROVE", "REVIEW", "REJECT"}
        for result in results
    )
    review_false_approvals = sum(
        result["expected_decision"] == "REVIEW"
        and normalized_label(prediction(result)) == "APPROVE"
        for result in results
    )
    correct = sum(matrix[label][label] for label in LABELS)
    return {
        "accuracy": ratio(correct, len(results)),
        "macro_f1": round(
            sum(values["f1"] for values in per_label.values()) / len(LABELS), 4
        ),
        "per_label": per_label,
        "confusion_matrix": matrix,
        "critical_false_approvals": critical_false_approvals,
        "critical_false_approval_rate": ratio(
            critical_false_approvals,
            sum(result["expected_decision"] == "REJECT" for result in results),
        ),
        "incomplete_cases_adjudicated": incomplete_adjudicated,
        "incomplete_case_error_rate": ratio(
            incomplete_adjudicated,
            sum(
                result["expected_decision"] == "COLLECTING_INFORMATION"
                for result in results
            ),
        ),
        "review_cases_false_approved": review_false_approvals,
    }


def citation_metrics(
    results: list[dict[str, Any]],
    predicted_ids: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    true_positive = false_positive = false_negative = exact = 0
    unsupported = records_with_unsupported = predicted_total = 0
    for result in results:
        raw_ids = predicted_ids(result)
        available = isinstance(raw_ids, list)
        ids = {item for item in raw_ids if isinstance(item, str)} if available else set()
        expected = set(result["expected"]["failed_rule_ids"])
        supplied = {rule["id"] for rule in result["_record"]["input"]["rules"]}
        true_positive += len(ids & expected)
        false_positive += len(ids - expected)
        false_negative += len(expected - ids)
        exact += available and ids == expected
        invalid_ids = ids - supplied
        unsupported += len(invalid_ids)
        records_with_unsupported += bool(invalid_ids)
        predicted_total += len(ids)
    return {
        "exact_match": ratio(exact, len(results)),
        "precision": ratio(true_positive, true_positive + false_positive),
        "recall": ratio(true_positive, true_positive + false_negative),
        "unsupported_rule_id_rate": ratio(unsupported, predicted_total),
        "records_with_unsupported_rule_ids_rate": ratio(
            records_with_unsupported, len(results)
        ),
    }


def explanation_metrics(
    results: list[dict[str, Any]],
    predicted_explanation: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    exact = nonempty = 0
    for result in results:
        value = predicted_explanation(result)
        nonempty += isinstance(value, str) and bool(value.strip())
        exact += value == result["expected"]["explanation"]
    return {
        "nonempty_rate": ratio(nonempty, len(results)),
        "exact_match": ratio(exact, len(results)),
    }


def dataset_metrics(
    predictions_path: Path, dataset_path: Path
) -> dict[str, Any]:
    results = load_jsonl(predictions_path)
    records = {
        record["metadata"]["case_id"]: record for record in load_jsonl(dataset_path)
    }
    for result in results:
        result["_record"] = records[result["case_id"]]

    total = len(results)
    field_total = sum(len(result["expected"]) - 3 for result in results)
    expected_nulls = sum(result["expected_null_count"] for result in results)
    expected_present = sum(result["expected_present_count"] for result in results)

    model_decision = lambda item: item.get("prediction", {}).get("decision")
    engine_decision = lambda item: item.get("engine_decision")
    model_ids = lambda item: item.get("prediction", {}).get("failed_rule_ids", [])
    engine_ids = lambda item: item.get("engine_failed_rule_ids")
    model_explanation = lambda item: item.get("prediction", {}).get("explanation")
    engine_explanation = lambda item: item.get("engine_explanation")

    return {
        "records": total,
        "extraction": {
            "json_valid_rate": ratio(sum(item["json_valid"] for item in results), total),
            "schema_valid_rate": ratio(sum(item["schema_valid"] for item in results), total),
            "field_exact_accuracy": ratio(
                sum(item["correct_field_count"] for item in results), field_total
            ),
            "all_fields_exact_rate": ratio(
                sum(item["all_fields_exact"] for item in results), total
            ),
            "missing_field_hallucination_rate": ratio(
                sum(item["unsupported_value_count"] for item in results),
                expected_nulls,
            ),
            "present_field_omission_rate": ratio(
                sum(item["omitted_value_count"] for item in results),
                expected_present,
            ),
        },
        "model": {
            "classification": classification_metrics(results, model_decision),
            "citations": citation_metrics(results, model_ids),
            "explanations": explanation_metrics(results, model_explanation),
        },
        "deterministic": {
            "classification": classification_metrics(results, engine_decision),
            "citations": citation_metrics(results, engine_ids),
            "explanations": explanation_metrics(results, engine_explanation),
            "decision_override_count": sum(
                normalized_label(model_decision(item))
                != normalized_label(engine_decision(item))
                for item in results
            ),
            "citation_override_count": sum(
                set(model_ids(item) if isinstance(model_ids(item), list) else [])
                != set(engine_ids(item) if isinstance(engine_ids(item), list) else [])
                for item in results
            ),
        },
    }


def percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def markdown_report(metrics: dict[str, Any]) -> str:
    lines = [
        "# Evaluation Metrics",
        "",
        "All metrics use generation-mode predictions from the final Qwen3-1.7B LoRA adapter. Model and deterministic results are reported separately.",
        "",
        "## Summary",
        "",
        "| Dataset | Model accuracy | Model macro F1 | Model citation exact | Engine accuracy | Engine macro F1 | Engine citation exact |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, values in metrics.items():
        model = values["model"]
        engine = values["deterministic"]
        lines.append(
            f"| {name} | {percent(model['classification']['accuracy'])} | "
            f"{percent(model['classification']['macro_f1'])} | "
            f"{percent(model['citations']['exact_match'])} | "
            f"{percent(engine['classification']['accuracy'])} | "
            f"{percent(engine['classification']['macro_f1'])} | "
            f"{percent(engine['citations']['exact_match'])} |"
        )

    lines.extend([
        "",
        "## Safety-critical errors",
        "",
        "| Dataset | Layer | False approvals of rejects | Incomplete cases adjudicated | Review cases approved | Decision overrides | Citation overrides |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for name, values in metrics.items():
        for layer_key, layer_name in (("model", "Model"), ("deterministic", "Engine")):
            classification = values[layer_key]["classification"]
            decision_overrides = values["deterministic"]["decision_override_count"] if layer_key == "deterministic" else ""
            citation_overrides = values["deterministic"]["citation_override_count"] if layer_key == "deterministic" else ""
            lines.append(
                f"| {name} | {layer_name} | {classification['critical_false_approvals']} | "
                f"{classification['incomplete_cases_adjudicated']} | "
                f"{classification['review_cases_false_approved']} | "
                f"{decision_overrides} | {citation_overrides} |"
            )

    for name, values in metrics.items():
        lines.extend(["", f"## {name}", ""])
        extraction = values["extraction"]
        lines.append(
            f"Extraction: {percent(extraction['field_exact_accuracy'])} field accuracy; "
            f"{percent(extraction['all_fields_exact_rate'])} all-fields exact; "
            f"{percent(extraction['missing_field_hallucination_rate'])} missing-field hallucination."
        )
        for layer_key, layer_name in (("model", "Model"), ("deterministic", "Deterministic engine")):
            layer = values[layer_key]
            lines.extend([
                "",
                f"### {layer_name}: per-label metrics",
                "",
                "| Label | Precision | Recall | F1 | Support |",
                "|---|---:|---:|---:|---:|",
            ])
            for label in LABELS:
                item = layer["classification"]["per_label"][label]
                lines.append(
                    f"| {label} | {percent(item['precision'])} | {percent(item['recall'])} | "
                    f"{percent(item['f1'])} | {item['support']} |"
                )
            lines.extend([
                "",
                f"### {layer_name}: confusion matrix",
                "",
                "Rows are expected labels; columns are predicted labels.",
                "",
                "| Expected \\ Predicted | APPROVE | REVIEW | REJECT | COLLECTING_INFORMATION | INVALID |",
                "|---|---:|---:|---:|---:|---:|",
            ])
            matrix = layer["classification"]["confusion_matrix"]
            for label in LABELS:
                lines.append(
                    f"| {label} | " + " | ".join(str(matrix[label][column]) for column in PREDICTED_LABELS) + " |"
                )
            lines.extend([
                "",
                f"Citation precision/recall/exact: {percent(layer['citations']['precision'])} / "
                f"{percent(layer['citations']['recall'])} / {percent(layer['citations']['exact_match'])}.",
                "",
                f"Unsupported rule-ID rate: {percent(layer['citations']['unsupported_rule_id_rate'])}.",
                "",
                f"Explanation exact match: {percent(layer['explanations']['exact_match'])}. "
                "Exact match is intentionally strict and does not score acceptable paraphrases.",
            ])
    lines.extend([
        "",
        "## Interpretation",
        "",
        "Validation and Test-1 show strong in-distribution performance. Three validation cases with missing information were incorrectly completed by the model, so both layers approved them. Test-2 exposes more unresolved-evidence failures. Test-3 shows that the model is not fully rule-agnostic. The deterministic layer corrects many decisions and citations, but it cannot recover applicant values that the model omitted or hallucinated.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/metrics.json"))
    parser.add_argument("--output-markdown", type=Path, default=Path("docs/evaluation-metrics.md"))
    args = parser.parse_args()

    inputs = {
        "Validation": (
            Path("reports/fine-tuned-validation/predictions.jsonl"),
            Path("data/validation.jsonl"),
        ),
        "Test-1": (Path("reports/fine-tuned-test/predictions.jsonl"), Path("data/test.jsonl")),
        "Test-2": (Path("reports/adversarial-test-2/predictions.jsonl"), Path("data/test-2.jsonl")),
        "Test-3": (Path("reports/changed-rules-test-3/predictions.jsonl"), Path("data/test-3.jsonl")),
    }
    metrics = {
        name: dataset_metrics(predictions_path, dataset_path)
        for name, (predictions_path, dataset_path) in inputs.items()
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(metrics, indent=2) + "\n")
    args.output_markdown.write_text(markdown_report(metrics))
    print(json.dumps({
        name: {
            "model_accuracy": values["model"]["classification"]["accuracy"],
            "engine_accuracy": values["deterministic"]["classification"]["accuracy"],
            "model_macro_f1": values["model"]["classification"]["macro_f1"],
            "engine_macro_f1": values["deterministic"]["classification"]["macro_f1"],
        }
        for name, values in metrics.items()
    }, indent=2))


if __name__ == "__main__":
    main()
