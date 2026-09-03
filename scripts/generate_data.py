#!/usr/bin/env python3
"""Generate synthetic dialogues while keeping adjudication labels deterministic."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "Qwen/Qwen3-14B"
MISSING_DECISION = "COLLECTING_INFORMATION"

FIELD_NAMES = {
    "age": "age",
    "credit_score": "credit score",
    "annual_income_usd": "annual income",
    "debt_to_income_ratio_percent": "debt-to-income ratio",
    "employment_status": "employment status",
    "current_employment_duration_months": "employment duration",
    "residency_status": "residency status",
    "has_bankruptcy_recent": "recent bankruptcy history",
    "requested_amount_usd": "requested loan amount",
    "has_verifiable_bank_account": "verifiable bank account",
}


@dataclass
class Case:
    case_id: str
    scenario_group: str
    scenario: str
    profile: dict[str, Any]
    dialogue_instruction: str


def load_rules(path: Path) -> tuple[str, list[dict[str, Any]]]:
    payload = json.loads(path.read_text())
    ruleset = payload["personal_loan_credit_rules"]
    return ruleset["version"], ruleset["rules"]


def field_key(rule: dict[str, Any]) -> str:
    return rule["field"].rsplit(".", 1)[-1]


def baseline_profile(rules: list[dict[str, Any]]) -> dict[str, Any]:
    profile: dict[str, Any] = {}
    for rule in rules:
        key = field_key(rule)
        if "value_field_multiplier" in rule:
            continue
        value = rule["value"]
        if rule["operator"] == ">=":
            profile[key] = value + max(1, round(value * 0.1))
        elif rule["operator"] == "<=":
            profile[key] = max(0, value - max(1, round(value * 0.1)))
        elif rule["operator"] == "in":
            profile[key] = value[0]
        elif rule["operator"] == "is":
            profile[key] = value
        else:
            raise ValueError(f"Unsupported operator: {rule['operator']}")

    for rule in rules:
        if "value_field_multiplier" in rule:
            source = rule["value_field_multiplier"].rsplit(".", 1)[-1]
            profile[field_key(rule)] = round(
                profile[source] * rule["multiplier_value"] * 0.7, 2
            )
    return profile


def expected_for(rule: dict[str, Any], profile: dict[str, Any]) -> Any:
    if "value_field_multiplier" in rule:
        source = rule["value_field_multiplier"].rsplit(".", 1)[-1]
        return profile[source] * rule["multiplier_value"]
    return rule["value"]


def rule_passes(rule: dict[str, Any], actual: Any, expected: Any) -> bool:
    operators = {
        ">=": lambda: actual >= expected,
        "<=": lambda: actual <= expected,
        "in": lambda: actual in expected,
        "is": lambda: actual is expected,
    }
    try:
        return operators[rule["operator"]]()
    except KeyError as error:
        raise ValueError(f"Unsupported operator: {rule['operator']}") from error


def adjudicate(
    profile: dict[str, Any], rules: list[dict[str, Any]]
) -> tuple[str, list[str], str]:
    missing = sorted(
        {field_key(rule) for rule in rules if profile.get(field_key(rule)) is None}
    )
    if missing:
        missing_names = [FIELD_NAMES[field] for field in missing]
        return (
            MISSING_DECISION,
            [],
            f"More information is needed for: {', '.join(missing_names)}.",
        )

    failed: list[tuple[dict[str, Any], Any, Any]] = []
    for rule in rules:
        actual = profile[field_key(rule)]
        expected = expected_for(rule, profile)
        if not rule_passes(rule, actual, expected):
            failed.append((rule, actual, expected))

    failed_ids = [rule["id"] for rule, _, _ in failed]
    actions = {rule["action_on_fail"] for rule, _, _ in failed}
    decision = (
        "REJECT"
        if "REJECT" in actions
        else "REVIEW"
        if "FLAG_REVIEW" in actions
        else "APPROVE"
    )
    if not failed:
        return decision, failed_ids, "Based on the information provided, the application meets the current requirements."

    def reason(rule: dict[str, Any], actual: Any, expected: Any) -> str:
        templates = {
            "age": lambda: f"The applicant is {actual}. The minimum age is {expected}.",
            "credit_score": lambda: f"The reported credit score is {actual}. The minimum is {expected}.",
            "annual_income_usd": lambda: f"The reported annual income is ${actual:,.2f}. The minimum is ${expected:,.2f}.",
            "debt_to_income_ratio_percent": lambda: f"The reported debt-to-income ratio is {actual}%. The maximum is {expected}%.",
            "employment_status": lambda: "The reported employment status does not meet the current employment requirement.",
            "current_employment_duration_months": lambda: f"The reported employment duration is {actual} {'month' if actual == 1 else 'months'}. At least {expected} months is required.",
            "residency_status": lambda: "The reported residency status does not meet the current residency requirement.",
            "has_bankruptcy_recent": lambda: "The applicant reported a bankruptcy filing within the configured lookback period.",
            "requested_amount_usd": lambda: f"The requested amount is ${actual:,.2f}. The maximum for the reported income is ${expected:,.2f}.",
            "has_verifiable_bank_account": lambda: "The applicant does not have an active bank account that can be verified.",
        }
        return templates[field_key(rule)]()

    reasons = [reason(rule, actual, expected) for rule, actual, expected in failed]
    return decision, failed_ids, " ".join(reasons)


def failing_value(rule: dict[str, Any], profile: dict[str, Any]) -> Any:
    expected = expected_for(rule, profile)
    if rule["operator"] == ">=":
        return expected - 1
    if rule["operator"] == "<=":
        return expected + 1
    if rule["operator"] == "in":
        return {
            "employment_status": "unemployed",
            "residency_status": "Temporary_Visa",
        }.get(field_key(rule), "not_allowed")
    if rule["operator"] == "is":
        return not expected
    raise ValueError(f"Unsupported operator: {rule['operator']}")


def build_cases(rules: list[dict[str, Any]]) -> list[Case]:
    baseline = baseline_profile(rules)
    expected_fields = {field_key(rule) for rule in rules}
    if set(baseline) != expected_fields:
        raise ValueError("Baseline profile does not cover every rule field")

    cases: list[Case] = []

    def add(group: str, scenario: str, profile: dict[str, Any], instruction: str) -> None:
        case_id = f"case-{len(cases) + 1:04d}"
        cases.append(Case(case_id, group, scenario, profile, instruction))

    add("complete", "approve", deepcopy(baseline), "Use a complete conversation.")

    review_rule = next(r for r in rules if r["action_on_fail"] == "FLAG_REVIEW")
    profile = deepcopy(baseline)
    profile[field_key(review_rule)] = failing_value(review_rule, profile)
    add("complete", "review", profile, "Use a complete conversation.")

    reject_rule = next(r for r in rules if r["action_on_fail"] == "REJECT")
    profile = deepcopy(baseline)
    profile[field_key(reject_rule)] = failing_value(reject_rule, profile)
    add("complete", "reject", profile, "Use a complete conversation.")

    for key in sorted(expected_fields):
        profile = deepcopy(baseline)
        profile[key] = None
        add("missing", f"one_missing:{key}", profile, f"Do not provide {key}.")

    profile = deepcopy(baseline)
    for key in sorted(expected_fields)[:3]:
        profile[key] = None
    add("missing", "several_missing", profile, "Leave several values unknown.")
    add(
        "missing",
        "all_missing",
        {key: None for key in expected_fields},
        "The applicant does not provide any requested value.",
    )

    for rule in rules:
        if rule["operator"] not in {">=", "<="}:
            continue
        key = field_key(rule)
        threshold = expected_for(rule, baseline)
        delta = 1 if isinstance(threshold, int) else 0.1
        positions = {
            "exact": threshold,
            "just_below": threshold - delta,
            "just_above": threshold + delta,
            "far": threshold * (0.5 if rule["operator"] == ">=" else 1.5),
        }
        for position, value in positions.items():
            profile = deepcopy(baseline)
            profile[key] = value
            add(
                "numeric_boundary",
                f"{key}:{position}",
                profile,
                f"State {key} naturally and preserve the exact value {value}.",
            )

    aliases = {
        "employment_status": "I work for myself",
        "residency_status": "I have a green card",
        "has_bankruptcy_recent": "I have not filed bankruptcy in seven years",
        "has_verifiable_bank_account": "I have an active verified checking account",
    }
    for rule in rules:
        if rule["operator"] not in {"in", "is"}:
            continue
        key = field_key(rule)
        add("categorical", f"{key}:allowed", deepcopy(baseline), f"State {key} directly.")

        profile = deepcopy(baseline)
        profile[key] = failing_value(rule, profile)
        add("categorical", f"{key}:disallowed", profile, f"State {key} clearly.")

        add(
            "categorical",
            f"{key}:informal_alias",
            deepcopy(baseline),
            f"Express {key} using this wording: {aliases[key]}.",
        )

        profile = deepcopy(baseline)
        profile[key] = None
        add("categorical", f"{key}:unknown", profile, f"Say that {key} is unknown.")

    behaviors = {
        "out_of_order": "Provide facts in a different order from the rule list.",
        "correction": "Give one value incorrectly, then clearly correct it.",
        "contradiction": "Give conflicting credit scores and leave them unresolved.",
        "ambiguity": "Use uncertain wording for the credit score.",
        "irrelevant_text": "Include irrelevant text without adding financial facts.",
        "typos": "Use realistic typing mistakes without changing any value.",
    }
    for behavior, instruction in behaviors.items():
        profile = deepcopy(baseline)
        if behavior in {"contradiction", "ambiguity"}:
            profile["credit_score"] = None
        add("dialogue_behavior", behavior, profile, instruction)

    profile = deepcopy(baseline)
    for rule in rules:
        if rule["id"] in {"RULE-CREDIT-001", "RULE-DTI-001", "RULE-EMPLOY-002"}:
            profile[field_key(rule)] = failing_value(rule, profile)
    add("multiple_failures", "reject_and_review", profile, "Use a complete conversation.")

    return cases


def coverage_report(cases: list[Case], rules: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, int] = {}
    decisions: dict[str, int] = {}
    failed_rules: set[str] = set()
    for case in cases:
        groups[case.scenario_group] = groups.get(case.scenario_group, 0) + 1
        decision, failed_ids, _ = adjudicate(case.profile, rules)
        decisions[decision] = decisions.get(decision, 0) + 1
        failed_rules.update(failed_ids)
    return {
        "case_count": len(cases),
        "scenario_groups": groups,
        "decisions": decisions,
        "covered_fields": sorted(cases[0].profile),
        "failed_rule_coverage": sorted(failed_rules),
        "all_rule_ids": [rule["id"] for rule in rules],
    }


def representative_sample(cases: list[Case], limit: int) -> list[Case]:
    preferred = [
        ("complete", "approve"),
        ("complete", "review"),
        ("complete", "reject"),
        ("missing", "one_missing:age"),
        ("missing", "several_missing"),
        ("missing", "all_missing"),
        ("numeric_boundary", "credit_score:just_below"),
        ("categorical", "employment_status:informal_alias"),
        ("dialogue_behavior", "correction"),
        ("multiple_failures", "reject_and_review"),
    ]
    by_scenario = {(case.scenario_group, case.scenario): case for case in cases}
    selected = [by_scenario[key] for key in preferred if key in by_scenario]
    selected_ids = {case.case_id for case in selected}
    selected.extend(case for case in cases if case.case_id not in selected_ids)
    return selected[:limit]


def teacher_messages(case: Case) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Create a realistic loan-intake dialogue from the canonical profile. "
                "Return only a JSON array of objects with role and content keys. "
                "Use only assistant and user roles. Preserve supplied values exactly. "
                "Every content value must be a non-empty string. "
                "Never add a decision, policy explanation, name, address, or account number."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "canonical_profile": case.profile,
                    "scenario": case.scenario,
                    "instruction": case.dialogue_instruction,
                },
                sort_keys=True,
            ),
        },
    ]


def parse_dialogue(text: str) -> list[dict[str, str]]:
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end < start:
        raise ValueError("Teacher response did not contain a JSON array")
    dialogue = json.loads(text[start : end + 1])
    if not isinstance(dialogue, list) or not dialogue:
        raise ValueError("Dialogue must be a non-empty list")
    for turn in dialogue:
        if set(turn) != {"role", "content"}:
            raise ValueError("Dialogue turn has unexpected fields")
        if turn["role"] not in {"assistant", "user"}:
            raise ValueError("Dialogue role must be assistant or user")
        if not isinstance(turn["content"], str) or not turn["content"].strip():
            raise ValueError("Dialogue content must be non-empty")
    return dialogue


def render_dialogues(
    cases: list[Case], model_name: str, batch_size: int
) -> list[list[dict[str, str]]]:
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        dtype=torch.bfloat16,
        quantization_config=quantization,
    )
    model.eval()
    torch.manual_seed(42)

    def generate_texts(prompts: list[str]) -> list[str]:
        inputs = tokenizer(prompts, return_tensors="pt", padding=True).to(model.device)
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                do_sample=True,
                temperature=0.8,
                top_p=0.9,
                max_new_tokens=900,
                pad_token_id=tokenizer.pad_token_id,
            )
        generated = output_ids[:, inputs["input_ids"].shape[1] :]
        return tokenizer.batch_decode(generated, skip_special_tokens=True)

    rendered: list[list[dict[str, str]]] = []
    for offset in range(0, len(cases), batch_size):
        batch = cases[offset : offset + batch_size]
        prompts = [
            tokenizer.apply_chat_template(
                teacher_messages(case),
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            for case in batch
        ]
        texts = generate_texts(prompts)
        for prompt, text in zip(prompts, texts, strict=True):
            for attempt in range(3):
                try:
                    rendered.append(parse_dialogue(text))
                    break
                except (ValueError, json.JSONDecodeError):
                    if attempt == 2:
                        raise
                    text = generate_texts([prompt])[0]
    return rendered


def write_dataset(
    output_path: Path,
    cases: list[Case],
    dialogues: list[list[dict[str, str]]],
    ruleset_version: str,
    rules: list[dict[str, Any]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as handle:
        for case, dialogue in zip(cases, dialogues, strict=True):
            decision, failed_ids, explanation = adjudicate(case.profile, rules)
            record = {
                "metadata": {
                    "case_id": case.case_id,
                    "scenario_group": case.scenario_group,
                    "scenario": case.scenario,
                    "ruleset_version": ruleset_version,
                    "synthetic": True,
                },
                "input": {"rules": rules, "dialogue": dialogue},
                "target": {
                    **case.profile,
                    "decision": decision,
                    "failed_rule_ids": failed_ids,
                    "explanation": explanation,
                },
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rules", type=Path, default=Path("credit_rules.json"))
    parser.add_argument("--output", type=Path, default=Path("data/sample.jsonl"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    version, rules = load_rules(args.rules)
    cases = build_cases(rules)
    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("--limit must be at least 1")
        cases = representative_sample(cases, args.limit)
    print(json.dumps(coverage_report(cases, rules), indent=2))
    if args.dry_run:
        return
    dialogues = render_dialogues(cases, args.model, args.batch_size)
    write_dataset(args.output, cases, dialogues, version, rules)
    print(f"Wrote {len(cases)} records to {args.output}")


if __name__ == "__main__":
    main()
