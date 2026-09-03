#!/usr/bin/env python3
"""Build leakage-safe synthetic splits from validated dialogue templates."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from generate_data import adjudicate, load_rules


FIELD_ORDER = [
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

OUTCOME_RATIOS = {
    "APPROVE": 0.25,
    "REVIEW": 0.20,
    "REJECT": 0.35,
    "COLLECTING_INFORMATION": 0.20,
}

FIELD_LABELS = {
    "age": "current age",
    "credit_score": "current credit score",
    "annual_income_usd": "verified gross annual income",
    "debt_to_income_ratio_percent": "debt-to-income ratio percentage",
    "employment_status": "current employment status",
    "current_employment_duration_months": "current employment duration",
    "residency_status": "current U.S. residency status",
    "has_bankruptcy_recent": "bankruptcy-filing status for the past seven years",
    "requested_amount_usd": "requested loan amount",
    "has_verifiable_bank_account": "active bank-account verification status",
}


def curated_banks() -> dict[str, dict[str, list[str]]]:
    question_patterns = [
        "What is your {label}?",
        "Could you provide your {label}?",
        "Please tell me your {label}.",
        "Could you confirm your {label}?",
        "What should I record as your {label}?",
        "May I ask for your {label}?",
        "For the application, what is your {label}?",
        "Please share your {label}.",
    ]
    answer_patterns = [
        "My {label} is <VALUE>.",
        "For this application, my {label} is <VALUE>.",
        "I can confirm that my {label} is <VALUE>.",
        "The correct {label} is <VALUE>.",
        "Please record my {label} as <VALUE>.",
        "Regarding my {label}, it is <VALUE>.",
        "My answer for {label} is <VALUE>.",
        "The {label} I am reporting is <VALUE>.",
    ]
    return {
        field: {
            "questions": [pattern.format(label=label) for pattern in question_patterns],
            "answers": [pattern.format(label=label) for pattern in answer_patterns],
        }
        for field, label in FIELD_LABELS.items()
    }


def valid_profile(rng: random.Random) -> dict[str, Any]:
    income = rng.randrange(30_000, 200_001, 500)
    return {
        "age": rng.randint(18, 75),
        "credit_score": rng.randint(670, 850),
        "annual_income_usd": income,
        "debt_to_income_ratio_percent": rng.randint(5, 40),
        "employment_status": rng.choice(
            ["employed_full_time", "employed_part_time", "self_employed", "retired"]
        ),
        "current_employment_duration_months": rng.randint(6, 240),
        "residency_status": rng.choice(["US_Citizen", "Permanent_Resident"]),
        "has_bankruptcy_recent": False,
        "requested_amount_usd": rng.randrange(1_000, max(1_001, int(income * 0.5)), 250),
        "has_verifiable_bank_account": True,
    }


def make_profile(outcome: str, rng: random.Random) -> tuple[dict[str, Any], str]:
    profile = valid_profile(rng)
    scenario = outcome.lower()
    if outcome == "APPROVE":
        boundary = rng.choice([None, "age", "credit_score", "annual_income_usd", "debt_to_income_ratio_percent"])
        thresholds = {"age": 18, "credit_score": 670, "annual_income_usd": 30_000, "debt_to_income_ratio_percent": 40}
        if boundary:
            profile[boundary] = thresholds[boundary]
            if boundary == "annual_income_usd":
                profile["requested_amount_usd"] = min(
                    profile["requested_amount_usd"], 15_000
                )
            scenario = f"passing_boundary:{boundary}"
    elif outcome == "REVIEW":
        if rng.random() < 0.5:
            profile["current_employment_duration_months"] = rng.randint(0, 5)
            scenario = "short_employment"
        else:
            profile["requested_amount_usd"] = round(
                profile["annual_income_usd"] * rng.uniform(0.51, 0.8), 2
            )
            scenario = "high_loan_to_income"
    elif outcome == "REJECT":
        failures = rng.sample(
            [
                "age",
                "credit_score",
                "annual_income_usd",
                "debt_to_income_ratio_percent",
                "employment_status",
                "residency_status",
                "has_bankruptcy_recent",
                "has_verifiable_bank_account",
            ],
            k=rng.randint(1, 3),
        )
        failing_values = {
            "age": lambda: rng.randint(15, 17),
            "credit_score": lambda: rng.randint(450, 669),
            "annual_income_usd": lambda: rng.randrange(10_000, 30_000, 500),
            "debt_to_income_ratio_percent": lambda: rng.randint(41, 75),
            "employment_status": lambda: rng.choice(["unemployed", "student"]),
            "residency_status": lambda: rng.choice(["Temporary_Visa", "Non_Resident"]),
            "has_bankruptcy_recent": lambda: True,
            "has_verifiable_bank_account": lambda: False,
        }
        for field in failures:
            profile[field] = failing_values[field]()
        scenario = "failed:" + ",".join(sorted(failures))
    else:
        count = 10 if rng.random() < 0.05 else rng.randint(1, 4)
        missing = rng.sample(FIELD_ORDER, k=count)
        for field in missing:
            profile[field] = None
        scenario = "missing:" + ",".join(sorted(missing))
    return profile, scenario


def value_phrase(field: str, value: Any) -> str:
    mappings = {
        "employment_status": {
            "employed_full_time": "employed full-time",
            "employed_part_time": "employed part-time",
            "self_employed": "self-employed",
            "retired": "retired",
            "unemployed": "unemployed",
            "student": "a student",
        },
        "residency_status": {
            "US_Citizen": "a U.S. citizen",
            "Permanent_Resident": "a permanent resident",
            "Temporary_Visa": "in the U.S. on a temporary visa",
            "Non_Resident": "not a U.S. resident",
        },
        "has_bankruptcy_recent": {
            False: "no bankruptcy filing within the last seven years",
            True: "a bankruptcy filing within the last seven years",
        },
        "has_verifiable_bank_account": {
            True: "an active, verifiable bank account",
            False: "no active, verifiable bank account",
        },
    }
    if field in mappings:
        return mappings[field][value]
    if field in {"annual_income_usd", "requested_amount_usd"}:
        return f"${value:,.2f}" if not float(value).is_integer() else f"${int(value):,}"
    if field == "debt_to_income_ratio_percent":
        return f"{value}%"
    if field == "current_employment_duration_months":
        return f"{value} months"
    if field == "age":
        return f"{value} years old"
    return str(value)


def render_dialogue(
    profile: dict[str, Any], banks: dict[str, Any], rng: random.Random
) -> tuple[list[dict[str, str]], str]:
    order = FIELD_ORDER.copy()
    rng.shuffle(order)
    dialogue: list[dict[str, str]] = [
        {"role": "user", "content": rng.choice([
            "I'd like to apply for a personal loan.",
            "Can you help me start a loan application?",
            "I'm interested in applying for a personal loan.",
        ])}
    ]
    behavior = rng.choices(
        ["standard", "out_of_order", "correction", "irrelevant", "typos"],
        weights=[55, 20, 10, 10, 5],
        k=1,
    )[0]
    correction_field = None
    available_numeric = [field for field in order if profile[field] is not None and field in {
        "age", "credit_score", "annual_income_usd", "debt_to_income_ratio_percent",
        "current_employment_duration_months", "requested_amount_usd"
    }]
    if behavior == "correction" and available_numeric:
        correction_field = rng.choice(available_numeric)

    for field in order:
        value = profile[field]
        if value is None and rng.random() < 0.35:
            continue
        dialogue.append({"role": "assistant", "content": rng.choice(banks[field]["questions"])})
        if value is None:
            answer = rng.choice([
                "I don't know that right now.",
                "I don't have that information available.",
                "I'm not sure, so please leave that unanswered.",
            ])
        else:
            answer = rng.choice(banks[field]["answers"]).replace(
                "<VALUE>", value_phrase(field, value)
            )
            if field == correction_field:
                wrong = value + (1000 if field in {"annual_income_usd", "requested_amount_usd"} else 1)
                answer = (
                    f"I initially said {value_phrase(field, wrong)}, but that was incorrect. "
                    f"To correct it, {answer}"
                )
        dialogue.append({"role": "user", "content": answer})

    if behavior == "irrelevant":
        dialogue.insert(1, {"role": "user", "content": "I hope this does not take too long; I have an appointment later."})
    elif behavior == "typos":
        dialogue[0]["content"] = "I'd like to aplly for a personal laon."
    return dialogue, behavior


def desired_outcomes(count: int, rng: random.Random) -> list[str]:
    counts = {key: int(count * ratio) for key, ratio in OUTCOME_RATIOS.items()}
    counts["APPROVE"] += count - sum(counts.values())
    outcomes = [outcome for outcome, amount in counts.items() for _ in range(amount)]
    rng.shuffle(outcomes)
    return outcomes


def build_split(
    name: str,
    count: int,
    seed: int,
    ruleset_version: str,
    rules: list[dict[str, Any]],
    banks: dict[str, Any],
    seen: set[str],
    output_dir: Path,
) -> dict[str, Any]:
    rng = random.Random(seed)
    output_path = output_dir / f"{name}.jsonl"
    decisions: dict[str, int] = {}
    failed_coverage: set[str] = set()
    with output_path.open("w") as handle:
        for index, outcome in enumerate(desired_outcomes(count, rng), start=1):
            for _ in range(100):
                profile, scenario = make_profile(outcome, rng)
                signature = json.dumps(profile, sort_keys=True)
                if signature not in seen:
                    seen.add(signature)
                    break
            else:
                raise RuntimeError("Could not create a unique profile")
            decision, failed_ids, explanation = adjudicate(profile, rules)
            if decision != outcome:
                raise RuntimeError(f"Expected {outcome}, received {decision}")
            dialogue, behavior = render_dialogue(profile, banks, rng)
            record = {
                "metadata": {
                    "case_id": f"{name}-{index:06d}",
                    "split": name,
                    "scenario": scenario,
                    "dialogue_behavior": behavior,
                    "ruleset_version": ruleset_version,
                    "synthetic": True,
                },
                "input": {"rules": rules, "dialogue": dialogue},
                "target": {
                    **profile,
                    "decision": decision,
                    "failed_rule_ids": failed_ids,
                    "explanation": explanation,
                },
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            decisions[decision] = decisions.get(decision, 0) + 1
            failed_coverage.update(failed_ids)
    return {
        "records": count,
        "decisions": decisions,
        "failed_rule_coverage": sorted(failed_coverage),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rules", type=Path, default=Path("credit_rules.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--train", type=int, default=4000)
    parser.add_argument("--validation", type=int, default=500)
    parser.add_argument("--test", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    version, rules = load_rules(args.rules)
    banks = curated_banks()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    report = {}
    for offset, (name, count) in enumerate(
        [("train", args.train), ("validation", args.validation), ("test", args.test)]
    ):
        report[name] = build_split(
            name, count, args.seed + offset, version, rules, banks, seen, args.output_dir
        )
    report["unique_profiles"] = len(seen)
    (args.output_dir / "generation-report.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
