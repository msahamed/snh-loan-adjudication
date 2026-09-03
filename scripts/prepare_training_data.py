#!/usr/bin/env python3
"""Validate dataset records and convert them to Qwen chat-training format."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


FIELDS = [
    "age",
    "credit_score",
    "annual_income_usd",
    "debt_to_income_ratio_percent",
    "employment_status",
    "current_employment_duration_months",
    "residency_status",
    "has_bankruptcy_recent",
    "requested_amount_usd",
    "has_verifiable_bank_account",
]
OUTPUT_KEYS = FIELDS + ["decision", "failed_rule_ids", "explanation"]

SYSTEM_PROMPT = """You analyze a personal-loan intake dialogue using the supplied rules.
Return only one JSON object with exactly these keys: age, credit_score, annual_income_usd, debt_to_income_ratio_percent, employment_status, current_employment_duration_months, residency_status, has_bankruptcy_recent, requested_amount_usd, has_verifiable_bank_account, decision, failed_rule_ids, explanation.
Use null when a field is missing, ambiguous, contradictory, or unresolved. Apply explicit corrections. Decision must be one of APPROVE, REVIEW, REJECT, or COLLECTING_INFORMATION. If any required field is unresolved, use COLLECTING_INFORMATION. Include every failed rule ID when all fields are available. Use only rule IDs supplied in the input. Do not add facts or keys."""


def ordered_target(target: dict[str, Any]) -> dict[str, Any]:
    if set(target) != set(OUTPUT_KEYS):
        missing = sorted(set(OUTPUT_KEYS) - set(target))
        extra = sorted(set(target) - set(OUTPUT_KEYS))
        raise ValueError(f"Invalid target keys; missing={missing}, extra={extra}")
    return {key: target[key] for key in OUTPUT_KEYS}


def build_messages(record: dict[str, Any], include_target: bool = True) -> list[dict[str, str]]:
    input_payload = record["input"]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "rules": input_payload["rules"],
                    "dialogue": input_payload["dialogue"],
                },
                separators=(",", ":"),
            ),
        },
    ]
    if include_target:
        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(
                    ordered_target(record["target"]),
                    separators=(",", ":"),
                ),
            }
        )
    return messages


def validate_record(record: dict[str, Any]) -> None:
    if not isinstance(record.get("metadata", {}).get("case_id"), str):
        raise ValueError("Record is missing metadata.case_id")
    payload = record.get("input")
    if not isinstance(payload, dict) or not isinstance(payload.get("rules"), list):
        raise ValueError("Record is missing input.rules")
    dialogue = payload.get("dialogue")
    if not isinstance(dialogue, list) or not dialogue:
        raise ValueError("Record has an invalid dialogue")
    for turn in dialogue:
        if set(turn) != {"role", "content"}:
            raise ValueError("Dialogue turn has invalid keys")
        if turn["role"] not in {"user", "assistant"}:
            raise ValueError("Dialogue turn has an invalid role")
        if not isinstance(turn["content"], str) or not turn["content"].strip():
            raise ValueError("Dialogue turn has empty content")
    ordered_target(record.get("target", {}))


def percentile(values: list[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def process_split(
    input_path: Path,
    output_path: Path,
    tokenizer: Any | None,
    max_length: int,
) -> dict[str, Any]:
    count = 0
    token_lengths: list[int] = []
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open() as source, output_path.open("w") as destination:
        for line_number, line in enumerate(source, start=1):
            record = json.loads(line)
            try:
                validate_record(record)
            except ValueError as error:
                raise ValueError(f"{input_path}:{line_number}: {error}") from error
            messages = build_messages(record)
            formatted = {
                "id": record["metadata"]["case_id"],
                "messages": messages,
            }
            destination.write(json.dumps(formatted, separators=(",", ":")) + "\n")
            count += 1
            if tokenizer is not None:
                token_ids = tokenizer.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=False,
                    enable_thinking=False,
                )
                token_lengths.append(len(token_ids))

    report: dict[str, Any] = {"records": count}
    if token_lengths:
        report["tokens"] = {
            "min": min(token_lengths),
            "median": percentile(token_lengths, 0.50),
            "p95": percentile(token_lengths, 0.95),
            "p99": percentile(token_lengths, 0.99),
            "max": max(token_lengths),
            "over_max_length": sum(length > max_length for length in token_lengths),
            "max_length": max_length,
        }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--model", help="Optional model path for token-length statistics")
    parser.add_argument("--max-length", type=int, default=2048)
    args = parser.parse_args()

    tokenizer = None
    if args.model:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(args.model)

    report = {}
    for split in ("train", "validation", "test"):
        report[split] = process_split(
            args.input_dir / f"{split}.jsonl",
            args.output_dir / f"{split}.jsonl",
            tokenizer,
            args.max_length,
        )
    report_path = args.output_dir / "preprocessing-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
