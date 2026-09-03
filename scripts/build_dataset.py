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

def curated_banks() -> dict[str, dict[str, list[str]]]:
    base = {
        "age": {
            "questions": ["How old are you?", "What's your age?", "Can I get your age?", "Could you confirm your age?"],
            "answers": ["I'm <VALUE>.", "I'm currently <VALUE>.", "My age is <VALUE>.", "Sure, I'm <VALUE>."],
        },
        "credit_score": {
            "questions": ["What's your current credit score?", "Do you know your credit score?", "Can you share your credit score?", "What credit score should I use?"],
            "answers": ["My credit score is <VALUE>.", "It's <VALUE>.", "The latest score I have is <VALUE>.", "I believe it's <VALUE>."],
        },
        "annual_income_usd": {
            "questions": ["What's your gross annual income?", "How much do you make per year before taxes?", "What is your yearly income before taxes?", "Can you share your annual income?"],
            "answers": ["I make <VALUE> a year before taxes.", "My annual income is <VALUE>.", "It's <VALUE> per year.", "I earn about <VALUE> annually."],
        },
        "debt_to_income_ratio_percent": {
            "questions": ["Do you know your debt-to-income ratio?", "What's your current debt-to-income ratio?", "What percentage is your debt-to-income ratio?", "Can you share your DTI percentage?"],
            "answers": ["My debt-to-income ratio is <VALUE>.", "It's <VALUE>.", "My DTI is <VALUE>.", "The current percentage is <VALUE>."],
        },
        "employment_status": {
            "questions": ["What's your current employment status?", "Are you currently working?", "How are you currently employed?", "Can you describe your employment status?"],
            "answers": ["I'm currently <VALUE>.", "I'm <VALUE>.", "My current status is <VALUE>.", "At the moment, I'm <VALUE>."],
        },
        "current_employment_duration_months": {
            "questions": ["How long have you been in your current role?", "How many months have you been with your current employer?", "How long have you been doing your current work?", "When did you start your current job?"],
            "answers": ["I've been there for <VALUE>.", "I've been in this role for <VALUE>.", "It's been <VALUE>.", "I've done this work for <VALUE>."],
        },
        "residency_status": {
            "questions": ["Are you a U.S. citizen or permanent resident?", "What's your U.S. residency status?", "Can you confirm your residency status?", "How would you describe your current U.S. residency status?"],
            "answers": ["I'm <VALUE>.", "My status is <VALUE>.", "I'm currently <VALUE>.", "For residency purposes, I'm <VALUE>."],
        },
        "has_bankruptcy_recent": {
            "questions": ["Have you filed for bankruptcy in the past seven years?", "Any bankruptcy filings within the last seven years?", "Have you had a recent bankruptcy?", "Has there been a bankruptcy filing in the past seven years?"],
            "answers": ["I've had <VALUE>.", "There has been <VALUE>.", "My record shows <VALUE>.", "I can confirm <VALUE>."],
        },
        "requested_amount_usd": {
            "questions": ["How much would you like to borrow?", "What loan amount are you requesting?", "How much are you applying for?", "What amount do you need?"],
            "answers": ["I'd like to borrow <VALUE>.", "I'm applying for <VALUE>.", "The amount I need is <VALUE>.", "I'm requesting <VALUE>."],
        },
        "has_verifiable_bank_account": {
            "questions": ["Do you have an active bank account we can verify?", "Can your bank account be verified?", "Do you have a bank account in your name?", "Is there an active bank account we can use for the loan?"],
            "answers": ["I have <VALUE>.", "Yes, I can confirm I have <VALUE>.", "At the moment, I have <VALUE>.", "For the loan, I have <VALUE>."],
        },
    }
    return base


def valid_profile(rng: random.Random) -> dict[str, Any]:
    income = rng.randrange(30_000, 200_001, 500)
    employment_status = rng.choice(
        ["employed_full_time", "employed_part_time", "self_employed", "retired"]
    )
    return {
        "age": rng.randint(55, 80) if employment_status == "retired" else rng.randint(18, 75),
        "credit_score": rng.randint(670, 850),
        "annual_income_usd": income,
        "debt_to_income_ratio_percent": rng.randint(5, 40),
        "employment_status": employment_status,
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
        if profile["employment_status"] in {"unemployed", "student"}:
            profile["current_employment_duration_months"] = 0
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
        return "1 month" if value == 1 else f"{value} months"
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

    exchanges: list[tuple[str, str]] = []
    for field in order:
        value = profile[field]
        if value is None and rng.random() < 0.35:
            continue
        question_bank = banks[field]["questions"]
        answer_bank = banks[field]["answers"]
        if field == "current_employment_duration_months":
            if profile["employment_status"] == "retired":
                question_bank = [
                    "How long have you been retired?",
                    "How many months have you received retirement income?",
                    "When did you retire?",
                    "How long has retirement been your income source?",
                ]
                answer_bank = [
                    "I've been retired for <VALUE>.",
                    "I've received retirement income for <VALUE>.",
                    "I retired <VALUE> ago.",
                    "Retirement has been my income source for <VALUE>.",
                ]
            elif profile["employment_status"] in {"unemployed", "student"}:
                question_bank = [
                    "How long have you been in your current role?",
                    "Do you have a current job?",
                    "How many months have you been employed?",
                    "When did your current employment begin?",
                ]
                answer_bank = [
                    "I'm not currently employed, so the duration is <VALUE>.",
                    "I don't have a current job. The duration is <VALUE>.",
                    "My current employment duration is <VALUE>.",
                    "I haven't started a current role, so it's <VALUE>.",
                ]
        question = rng.choice(question_bank)
        if value is None:
            answer = rng.choice([
                "I don't know that right now.",
                "I don't have that information available.",
                "I'm not sure, so please leave that unanswered.",
            ])
        else:
            answer = rng.choice(answer_bank).replace(
                "<VALUE>", value_phrase(field, value)
            )
            if field == correction_field:
                wrong = value + (1000 if field in {"annual_income_usd", "requested_amount_usd"} else 1)
                answer = (
                    f"I initially said {value_phrase(field, wrong)}, but the correct value is "
                    f"{value_phrase(field, value)}."
                )
        exchanges.append((question, answer))

    index = 0
    transitions = ["Also, ", "Next, ", "Just to confirm, ", "Before we continue, "]
    rng.shuffle(transitions)
    while index < len(exchanges):
        group_size = 2 if index + 1 < len(exchanges) and rng.random() < 0.35 else 1
        group = exchanges[index : index + group_size]
        questions = " ".join(item[0] for item in group)
        transition = (
            transitions.pop()
            if index > 0 and transitions and rng.random() < 0.4
            else ""
        )
        if transition:
            questions = transition + questions[0].lower() + questions[1:]
        answers = " ".join(item[1] for item in group)
        if rng.random() < 0.2 and not answers.startswith(("Sure", "Yes")):
            answers = "Sure. " + answers
        dialogue.append({"role": "assistant", "content": questions})
        dialogue.append({"role": "user", "content": answers})
        index += group_size

    if behavior == "irrelevant":
        dialogue[0]["content"] += " I have an appointment later, so I may need to finish this afterward."
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
