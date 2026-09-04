#!/usr/bin/env python3
"""Build a paired test set using unseen rule IDs, values, actions, and ordering."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from prepare_training_data import FIELDS, validate_record
from rules_engine import adjudicate, field_key


RULESET_VERSION = "2.0-test"

V2_IDS = {
    "age": "POLICY2-LEGAL-AGE",
    "credit_score": "POLICY2-CREDIT-FLOOR",
    "annual_income_usd": "POLICY2-INCOME-FLOOR",
    "debt_to_income_ratio_percent": "POLICY2-DTI-CAP",
    "employment_status": "POLICY2-INCOME-SOURCE",
    "current_employment_duration_months": "POLICY2-STABILITY-PERIOD",
    "residency_status": "POLICY2-RESIDENCY",
    "has_bankruptcy_recent": "POLICY2-BANKRUPTCY",
    "requested_amount_usd": "POLICY2-LOAN-INCOME-CAP",
    "has_verifiable_bank_account": "POLICY2-BANK-VERIFICATION",
}

RULE_PROFILES: dict[str, dict[str, dict[str, Any]]] = {
    "strict": {
        "age": {"value": 21},
        "credit_score": {"value": 720},
        "annual_income_usd": {"value": 45_000},
        "debt_to_income_ratio_percent": {"value": 35},
        "employment_status": {
            "value": ["employed_full_time", "self_employed", "retired"]
        },
        "current_employment_duration_months": {
            "value": 12,
            "action_on_fail": "REJECT",
            "severity": "CRITICAL",
        },
        "residency_status": {
            "value": ["US_Citizen"],
            "action_on_fail": "FLAG_REVIEW",
            "severity": "MINOR",
        },
        "has_bankruptcy_recent": {
            "action_on_fail": "FLAG_REVIEW",
            "severity": "MAJOR",
        },
        "requested_amount_usd": {
            "multiplier_value": 0.35,
            "action_on_fail": "REJECT",
            "severity": "CRITICAL",
        },
        "has_verifiable_bank_account": {
            "action_on_fail": "FLAG_REVIEW",
            "severity": "MAJOR",
        },
    },
    "lenient": {
        "age": {"value": 16},
        "credit_score": {"value": 500},
        "annual_income_usd": {"value": 15_000},
        "debt_to_income_ratio_percent": {"value": 60},
        "employment_status": {
            "value": [
                "employed_full_time",
                "employed_part_time",
                "self_employed",
                "retired",
                "unemployed",
                "student",
            ]
        },
        "current_employment_duration_months": {"value": 0},
        "residency_status": {
            "value": [
                "US_Citizen",
                "Permanent_Resident",
                "Temporary_Visa",
                "Non_Resident",
            ]
        },
        "has_bankruptcy_recent": {
            "action_on_fail": "FLAG_REVIEW",
            "severity": "MINOR",
        },
        "requested_amount_usd": {"multiplier_value": 0.8},
        "has_verifiable_bank_account": {
            "action_on_fail": "FLAG_REVIEW",
            "severity": "MINOR",
        },
    },
    "review_focused": {
        "age": {"value": 19},
        "credit_score": {"value": 680},
        "annual_income_usd": {"value": 32_000},
        "debt_to_income_ratio_percent": {"value": 42},
        "employment_status": {
            "value": ["employed_full_time", "employed_part_time", "self_employed", "retired"]
        },
        "current_employment_duration_months": {"value": 9},
        "residency_status": {
            "value": ["US_Citizen", "Permanent_Resident", "Temporary_Visa"],
            "action_on_fail": "FLAG_REVIEW",
            "severity": "MINOR",
        },
        "has_bankruptcy_recent": {
            "action_on_fail": "FLAG_REVIEW",
            "severity": "MAJOR",
        },
        "requested_amount_usd": {"multiplier_value": 0.6},
        "has_verifiable_bank_account": {
            "action_on_fail": "FLAG_REVIEW",
            "severity": "MAJOR",
        },
    },
    "mixed": {
        "age": {"value": 20},
        "credit_score": {"value": 650},
        "annual_income_usd": {"value": 40_000},
        "debt_to_income_ratio_percent": {"value": 45},
        "employment_status": {
            "value": ["employed_full_time", "employed_part_time", "self_employed", "retired"]
        },
        "current_employment_duration_months": {"value": 12},
        "residency_status": {
            "value": ["US_Citizen"],
            "action_on_fail": "FLAG_REVIEW",
            "severity": "MINOR",
        },
        "has_bankruptcy_recent": {
            "action_on_fail": "REJECT",
            "severity": "CRITICAL",
        },
        "requested_amount_usd": {
            "multiplier_value": 0.4,
            "action_on_fail": "REJECT",
            "severity": "CRITICAL",
        },
        "has_verifiable_bank_account": {
            "action_on_fail": "FLAG_REVIEW",
            "severity": "MAJOR",
        },
    },
}


def changed_rules(
    source_rules: list[dict[str, Any]], variant: str
) -> list[dict[str, Any]]:
    rules = deepcopy(source_rules)
    for rule in rules:
        field = field_key(rule)
        rule["id"] = V2_IDS[field]
        rule.update(RULE_PROFILES[variant][field])
        rule["description"] = (
            f"Synthetic ruleset 2.0 test policy for {field.replace('_', ' ')}. "
            "Apply the configured operator, value, and action_on_fail exactly."
        )
    return rules


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("data/test.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/test-3.jsonl"))
    parser.add_argument("--report", type=Path, default=Path("data/test-3-report.json"))
    parser.add_argument("--seed", type=int, default=20260904)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    records: list[dict[str, Any]] = []
    decision_changes = 0
    citation_changes = 0
    changed_rule_coverage: set[str] = set()
    variants = [
        variant
        for variant in RULE_PROFILES
        for _ in range(125)
    ]
    rng.shuffle(variants)

    with args.source.open() as handle:
        for index, line in enumerate(handle, start=1):
            source = json.loads(line)
            profile = {field: source["target"][field] for field in FIELDS}
            variant = variants[index - 1]
            rules = changed_rules(source["input"]["rules"], variant)
            rng.shuffle(rules)
            decision, failed_ids, explanation = adjudicate(profile, rules)
            if decision != source["target"]["decision"]:
                decision_changes += 1
            if set(failed_ids) != set(source["target"]["failed_rule_ids"]):
                citation_changes += 1
            changed_rule_coverage.update(failed_ids)

            record = {
                "metadata": {
                    "case_id": f"test-3-{index:06d}",
                    "source_case_id": source["metadata"]["case_id"],
                    "split": "test-3",
                    "scenario": "changed_rules",
                    "ruleset_version": RULESET_VERSION,
                    "ruleset_variant": variant,
                    "synthetic": True,
                    "training_excluded": True,
                    "paired_with_test_1": True,
                },
                "input": {
                    "rules": rules,
                    "dialogue": source["input"]["dialogue"],
                },
                "target": {
                    **profile,
                    "decision": decision,
                    "failed_rule_ids": failed_ids,
                    "explanation": explanation,
                },
            }
            validate_record(record)
            records.append(record)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    report = {
        "records": len(records),
        "ruleset_version": RULESET_VERSION,
        "training_excluded": True,
        "paired_with_test_1": True,
        "decision_distribution": dict(sorted(Counter(
            record["target"]["decision"] for record in records
        ).items())),
        "decision_distribution_by_variant": {
            variant: dict(sorted(Counter(
                record["target"]["decision"]
                for record in records
                if record["metadata"]["ruleset_variant"] == variant
            ).items()))
            for variant in RULE_PROFILES
        },
        "decisions_changed_from_test_1": decision_changes,
        "citation_sets_changed_from_test_1": citation_changes,
        "failed_rule_coverage": sorted(changed_rule_coverage),
        "rule_profiles": RULE_PROFILES,
        "renamed_rule_ids": V2_IDS,
        "rules_reordered_per_record": True,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
