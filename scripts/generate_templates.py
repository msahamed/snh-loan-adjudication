#!/usr/bin/env python3
"""Generate validated question/answer paraphrases for dialogue composition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FIELDS = {
    "age": "the applicant's age in years",
    "credit_score": "the applicant's numeric credit score",
    "annual_income_usd": "annual income in US dollars",
    "debt_to_income_ratio_percent": "debt-to-income ratio as a percentage",
    "employment_status": "current employment status",
    "current_employment_duration_months": "employment duration in months",
    "residency_status": "US residency status",
    "has_bankruptcy_recent": "whether bankruptcy occurred within seven years",
    "requested_amount_usd": "requested loan amount in US dollars",
    "has_verifiable_bank_account": "whether an active verifiable bank account exists",
}


def parse_bank(text: str) -> dict[str, list[str]]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Response did not contain a JSON object")
    bank = json.loads(text[start : end + 1])
    if set(bank) != {"questions", "answers"}:
        raise ValueError("Unexpected template-bank keys")
    for key in ("questions", "answers"):
        if not isinstance(bank[key], list) or len(bank[key]) < 8:
            raise ValueError(f"Expected at least eight {key}")
        if not all(isinstance(item, str) and item.strip() for item in bank[key]):
            raise ValueError(f"Invalid {key}")
    if any("<VALUE>" in item for item in bank["questions"]):
        raise ValueError("Questions must not contain <VALUE>")
    if any(item.count("<VALUE>") != 1 for item in bank["answers"]):
        raise ValueError("Every answer must contain <VALUE> exactly once")
    forbidden = ("approve", "reject", "eligible", "decision")
    if any(word in item.lower() for values in bank.values() for item in values for word in forbidden):
        raise ValueError("Template contains adjudication language")
    return {key: values[:8] for key, values in bank.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        device_map="auto",
        dtype=torch.bfloat16,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
    )
    model.eval()
    torch.manual_seed(42)

    banks: dict[str, dict[str, list[str]]] = {}
    for field, description in FIELDS.items():
        messages = [
            {
                "role": "system",
                "content": (
                    "Write neutral loan-intake language. Return JSON only. Never provide "
                    "a lending decision, advice, explanation, or invented applicant fact."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"For {description}, create exactly 8 diverse questions and 8 diverse "
                    "applicant answer templates. Return an object with questions and answers. "
                    "Every answer must contain the literal token <VALUE> exactly once. "
                    "Questions must not contain <VALUE>. Keep every item concise."
                ),
            },
        ]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        for attempt in range(5):
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            with torch.inference_mode():
                output = model.generate(
                    **inputs,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    max_new_tokens=650,
                    pad_token_id=tokenizer.pad_token_id,
                )
            text = tokenizer.decode(
                output[0, inputs["input_ids"].shape[1] :],
                skip_special_tokens=True,
            )
            try:
                banks[field] = parse_bank(text)
                break
            except (ValueError, json.JSONDecodeError):
                if attempt == 4:
                    raise

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(banks, indent=2) + "\n")
    print(f"Wrote {len(banks)} validated field banks to {args.output}")


if __name__ == "__main__":
    main()
