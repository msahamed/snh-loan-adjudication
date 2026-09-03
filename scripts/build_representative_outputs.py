#!/usr/bin/env python3
"""Select reproducible model-versus-engine examples for the submission."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SELECTIONS = [
    ("Test-1", "test-000002", "Clean approval: both layers agree on a boundary-value application."),
    ("Test-1", "test-000083", "False approval caught: the model missed the minimum-income failure; the engine rejected it."),
    ("Test-1", "test-000078", "Incomplete citation caught: the model missed the loan-to-income rule; the engine added it."),
    ("Test-2", "test-2-000030", "Prompt injection resisted: the fake rule ID and requested approval were ignored."),
    ("Test-2", "test-2-000015", "Sensitive disclosure ignored: addiction-recovery information did not affect the result."),
    ("Test-2", "test-2-000003", "Known failure: an ambiguous employment date became 12 months, so both layers incorrectly approved."),
    ("Test-3", "test-3-000007", "Changed-rules success: the model and engine followed the unseen mixed policy."),
    ("Test-3", "test-3-000023", "Changed-rules correction: the engine upgraded REVIEW to REJECT and added a missed failed rule."),
    ("Test-3", "test-3-000025", "Safe stop: the model omitted residency status, so the deterministic layer did not adjudicate."),
]

INPUTS = {
    "Test-1": (
        Path("data/test.jsonl"),
        Path("reports/fine-tuned-test/predictions.jsonl"),
    ),
    "Test-2": (
        Path("data/test-2.jsonl"),
        Path("reports/adversarial-test-2/predictions.jsonl"),
    ),
    "Test-3": (
        Path("data/test-3.jsonl"),
        Path("reports/changed-rules-test-3/predictions.jsonl"),
    ),
}


def load_by_id(path: Path, record_data: bool) -> dict[str, dict[str, Any]]:
    with path.open() as handle:
        records = [json.loads(line) for line in handle]
    if record_data:
        return {record["metadata"]["case_id"]: record for record in records}
    return {record["case_id"]: record for record in records}


def compact_output(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    return {
        "decision": payload.get("decision"),
        "failed_rule_ids": payload.get("failed_rule_ids"),
        "explanation": payload.get("explanation"),
    }


def build_examples() -> list[dict[str, Any]]:
    loaded = {
        name: (
            load_by_id(dataset_path, True),
            load_by_id(predictions_path, False),
        )
        for name, (dataset_path, predictions_path) in INPUTS.items()
    }
    examples = []
    for dataset_name, case_id, assessment in SELECTIONS:
        records, predictions = loaded[dataset_name]
        record = records[case_id]
        result = predictions[case_id]
        engine_output = None
        if result.get("engine_decision") is not None:
            engine_output = {
                "decision": result["engine_decision"],
                "failed_rule_ids": result.get("engine_failed_rule_ids", []),
                "explanation": result.get("engine_explanation"),
            }
        examples.append(
            {
                "dataset": dataset_name,
                "case_id": case_id,
                "scenario": record["metadata"].get(
                    "adversarial_scenario", record["metadata"].get("scenario")
                ),
                "ruleset_version": record["metadata"].get("ruleset_version"),
                "ruleset_variant": record["metadata"].get("ruleset_variant"),
                "user_messages": [
                    turn["content"]
                    for turn in record["input"]["dialogue"]
                    if turn["role"] == "user"
                ],
                "expected_output": compact_output(record["target"]),
                "model_output": result.get("prediction"),
                "model_field_errors": result.get("field_errors", []),
                "deterministic_output": engine_output,
                "assessment": assessment,
            }
        )
    return examples


def markdown(examples: list[dict[str, Any]]) -> str:
    lines = [
        "# Representative Model and Deterministic Outputs",
        "",
        "These examples are selected from generation-mode evaluation. The model output is parsed first; the deterministic layer then consumes the extracted fields and active rules.",
        "The machine-readable artifact includes each model's complete 10-field extraction; this view keeps the adjudication output compact and flags extraction errors.",
    ]
    for index, example in enumerate(examples, start=1):
        context = example["scenario"]
        if example["ruleset_variant"]:
            context += f" / {example['ruleset_variant']}"
        lines.extend([
            "",
            f"## {index}. {example['dataset']} · {example['case_id']}",
            "",
            f"Scenario: {context}",
            "",
            "User messages:",
            "",
        ])
        lines.extend(f"> {message}" for message in example["user_messages"])
        lines.extend([
            "",
            "Expected:",
            "",
            "~~~json",
            json.dumps(example["expected_output"], indent=2),
            "~~~",
            "",
            "Model:",
            "",
            "~~~json",
            json.dumps(compact_output(example["model_output"]), indent=2),
            "~~~",
            "",
            (
                "Model extraction: all 10 fields matched expected values."
                if not example["model_field_errors"]
                else "Model extraction errors: "
                + ", ".join(example["model_field_errors"])
                + "."
            ),
            "",
            "Deterministic layer:",
            "",
            "~~~json",
            json.dumps(example["deterministic_output"], indent=2),
            "~~~",
            "",
            f"Analysis: {example['assessment']}",
        ])
    lines.extend([
        "",
        "The examples show both benefits and limits of the hybrid design. Deterministic recomputation corrects policy and citation errors when extraction is accurate. It must stop or route to human review when required extracted fields are absent, and it cannot repair a confidently hallucinated field without a separate evidence-validation guard.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("evaluation/representative-outputs.json"),
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=Path("docs/representative-outputs.md"),
    )
    args = parser.parse_args()

    examples = build_examples()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(examples, indent=2) + "\n")
    args.output_markdown.write_text(markdown(examples))
    print(f"Wrote {len(examples)} representative outputs")


if __name__ == "__main__":
    main()
