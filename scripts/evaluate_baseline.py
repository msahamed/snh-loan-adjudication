#!/usr/bin/env python3
"""Run and score an untouched causal language model on the validation split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_data import adjudicate
from prepare_training_data import FIELDS, OUTPUT_KEYS, build_messages, validate_record


def parse_json_object(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("No JSON object found")


def safe_engine_decision(
    prediction: dict[str, Any], rules: list[dict[str, Any]]
) -> tuple[str, list[str], str] | None:
    if not all(field in prediction for field in FIELDS):
        return None
    try:
        decision, failed_ids, explanation = adjudicate(
            {field: prediction[field] for field in FIELDS}, rules
        )
    except (KeyError, TypeError, ValueError):
        return None
    return decision, failed_ids, explanation


def metric_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    valid = [item for item in results if item["json_valid"]]
    schema_valid = [item for item in results if item["schema_valid"]]
    field_total = total * len(FIELDS)
    field_correct = sum(item["correct_field_count"] for item in results)
    null_correct = sum(item["correct_null_count"] for item in results)
    tp = sum(item["failed_rule_tp"] for item in results)
    fp = sum(item["failed_rule_fp"] for item in results)
    fn = sum(item["failed_rule_fn"] for item in results)
    predicted_citations = sum(item["predicted_rule_id_count"] for item in results)
    unsupported_citations = sum(
        item["unsupported_rule_id_count"] for item in results
    )

    def ratio(numerator: int, denominator: int) -> float:
        return round(numerator / denominator, 4) if denominator else 0.0

    return {
        "records": total,
        "json_valid_rate": ratio(len(valid), total),
        "schema_valid_rate": ratio(len(schema_valid), total),
        "field_exact_accuracy": ratio(field_correct, field_total),
        "all_fields_exact_rate": ratio(
            sum(item["all_fields_exact"] for item in results), total
        ),
        "null_status_accuracy": ratio(null_correct, field_total),
        "missing_field_hallucination_rate": ratio(
            sum(item["unsupported_value_count"] for item in results),
            sum(item["expected_null_count"] for item in results),
        ),
        "present_field_omission_rate": ratio(
            sum(item["omitted_value_count"] for item in results),
            sum(item["expected_present_count"] for item in results),
        ),
        "decision_accuracy": ratio(
            sum(item["decision_correct"] for item in results), total
        ),
        "failed_rule_exact_match": ratio(
            sum(item["failed_rules_exact"] for item in results), total
        ),
        "failed_rule_precision": ratio(tp, tp + fp),
        "failed_rule_recall": ratio(tp, tp + fn),
        "unsupported_rule_id_rate": ratio(
            unsupported_citations, predicted_citations
        ),
        "records_with_unsupported_rule_ids_rate": ratio(
            sum(item["unsupported_rule_id_count"] > 0 for item in results), total
        ),
        "engine_decision_accuracy": ratio(
            sum(item["engine_decision_correct"] for item in results), total
        ),
        "engine_failed_rule_exact_match": ratio(
            sum(item["engine_failed_rules_exact"] for item in results), total
        ),
        "model_engine_decision_agreement": ratio(
            sum(item["model_engine_decision_agree"] for item in results), total
        ),
        "model_engine_citation_exact_match": ratio(
            sum(item["model_engine_citations_exact"] for item in results), total
        ),
    }


def score_prediction(
    record: dict[str, Any], generated_text: str
) -> dict[str, Any]:
    expected = record["target"]
    base = {
        "case_id": record["metadata"]["case_id"],
        "expected": expected,
        "expected_decision": expected["decision"],
        "adversarial_scenario": record["metadata"].get("adversarial_scenario"),
        "generated_text": generated_text,
        "json_valid": False,
        "schema_valid": False,
        "correct_field_count": 0,
        "field_errors": FIELDS.copy(),
        "correct_null_count": 0,
        "all_fields_exact": False,
        "decision_correct": False,
        "failed_rules_exact": False,
        "failed_rule_tp": 0,
        "failed_rule_fp": 0,
        "failed_rule_fn": len(expected["failed_rule_ids"]),
        "predicted_rule_id_count": 0,
        "unsupported_rule_id_count": 0,
        "engine_decision_correct": False,
        "engine_failed_rules_exact": False,
        "model_engine_decision_agree": False,
        "model_engine_citations_exact": False,
        "expected_null_count": sum(expected[field] is None for field in FIELDS),
        "expected_present_count": sum(expected[field] is not None for field in FIELDS),
        "unsupported_value_count": 0,
        "omitted_value_count": sum(expected[field] is not None for field in FIELDS),
    }
    try:
        prediction = parse_json_object(generated_text)
    except ValueError:
        return base

    base["json_valid"] = True
    base["prediction"] = prediction
    base["schema_valid"] = set(prediction) == set(OUTPUT_KEYS)
    field_matches = [prediction.get(field) == expected[field] for field in FIELDS]
    base["correct_field_count"] = sum(field_matches)
    base["field_errors"] = [
        field for field, matches in zip(FIELDS, field_matches, strict=True) if not matches
    ]
    base["correct_null_count"] = sum(
        (prediction.get(field) is None) == (expected[field] is None) for field in FIELDS
    )
    base["all_fields_exact"] = all(field_matches)
    base["unsupported_value_count"] = sum(
        expected[field] is None and prediction.get(field) is not None for field in FIELDS
    )
    base["omitted_value_count"] = sum(
        expected[field] is not None and prediction.get(field) is None for field in FIELDS
    )
    base["decision_correct"] = prediction.get("decision") == expected["decision"]

    predicted_ids = prediction.get("failed_rule_ids", [])
    if isinstance(predicted_ids, list):
        predicted_ids = [item for item in predicted_ids if isinstance(item, str)]
    else:
        predicted_ids = []
    predicted_set, expected_set = set(predicted_ids), set(expected["failed_rule_ids"])
    supplied_ids = {rule["id"] for rule in record["input"]["rules"]}
    base["predicted_rule_id_count"] = len(predicted_set)
    base["unsupported_rule_id_count"] = len(predicted_set - supplied_ids)
    base["failed_rules_exact"] = predicted_set == expected_set
    base["failed_rule_tp"] = len(predicted_set & expected_set)
    base["failed_rule_fp"] = len(predicted_set - expected_set)
    base["failed_rule_fn"] = len(expected_set - predicted_set)

    engine_result = safe_engine_decision(prediction, record["input"]["rules"])
    if engine_result is not None:
        base["engine_decision"] = engine_result[0]
        base["engine_failed_rule_ids"] = engine_result[1]
        base["engine_explanation"] = engine_result[2]
        base["engine_decision_correct"] = engine_result[0] == expected["decision"]
        engine_set = set(engine_result[1])
        base["engine_failed_rules_exact"] = engine_set == expected_set
        base["model_engine_decision_agree"] = prediction.get("decision") == engine_result[0]
        base["model_engine_citations_exact"] = predicted_set == engine_set
    return base


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", type=Path, default=Path("data/validation.jsonl"))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-input-length", type=int, default=2048)
    parser.add_argument("--max-new-tokens", type=int, default=600)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/baseline"))
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    records = []
    with args.data.open() as handle:
        for line in handle:
            record = json.loads(line)
            validate_record(record)
            records.append(record)
            if len(records) == args.limit:
                break

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        device_map="auto",
        dtype=dtype,
    )
    model.eval()

    results = []
    for offset in range(0, len(records), args.batch_size):
        batch = records[offset : offset + args.batch_size]
        prompts = [
            tokenizer.apply_chat_template(
                build_messages(record, include_target=False),
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            for record in batch
        ]
        inputs = tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=args.max_input_length,
        ).to(model.device)
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tokenizer.pad_token_id,
            )
        generated = output_ids[:, inputs["input_ids"].shape[1] :]
        texts = tokenizer.batch_decode(generated, skip_special_tokens=True)
        results.extend(
            score_prediction(record, text)
            for record, text in zip(batch, texts, strict=True)
        )
        print(f"Evaluated {len(results)}/{len(records)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = args.output_dir / "predictions.jsonl"
    with predictions_path.open("w") as handle:
        for result in results:
            handle.write(json.dumps(result, sort_keys=True) + "\n")
    summary = metric_summary(results)
    adversarial_scenarios = sorted({
        item["adversarial_scenario"]
        for item in results
        if item["adversarial_scenario"] is not None
    })
    if adversarial_scenarios:
        summary["by_scenario"] = {
            scenario: metric_summary([
                item for item in results
                if item["adversarial_scenario"] == scenario
            ])
            for scenario in adversarial_scenarios
        }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
