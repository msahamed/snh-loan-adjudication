"""Evaluate extracted loan fields against a supplied ruleset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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


def load_rules(path: Path) -> tuple[str, list[dict[str, Any]]]:
    payload = json.loads(path.read_text())
    ruleset = payload["personal_loan_credit_rules"]
    return ruleset["version"], ruleset["rules"]


def field_key(rule: dict[str, Any]) -> str:
    return rule["field"].rsplit(".", 1)[-1]


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
        names = [FIELD_NAMES[field] for field in missing]
        return MISSING_DECISION, [], f"More information is needed for: {', '.join(names)}."

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
        explanation = "Based on the information provided, the application meets the current requirements."
        return decision, failed_ids, explanation

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
