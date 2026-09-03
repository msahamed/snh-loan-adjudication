#!/usr/bin/env python3
"""Fine-tune Qwen3 with response-only QLoRA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


LORA_TARGETS = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]


class ChatDataset:
    def __init__(
        self,
        path: Path,
        tokenizer: Any,
        max_length: int,
        limit: int | None = None,
    ) -> None:
        import torch

        self.examples: list[dict[str, list[int]]] = []
        with path.open() as handle:
            for line_number, line in enumerate(handle, start=1):
                record = json.loads(line)
                messages = record["messages"]
                if len(messages) != 3 or messages[-1]["role"] != "assistant":
                    raise ValueError(f"{path}:{line_number}: expected three chat messages")

                prompt_ids = tokenizer.apply_chat_template(
                    messages[:-1],
                    tokenize=True,
                    add_generation_prompt=True,
                    enable_thinking=False,
                )
                input_ids = tokenizer.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=False,
                    enable_thinking=False,
                )
                if input_ids[: len(prompt_ids)] != prompt_ids:
                    raise ValueError(f"{path}:{line_number}: prompt/full token mismatch")
                if len(input_ids) > max_length:
                    raise ValueError(
                        f"{path}:{line_number}: {len(input_ids)} tokens exceeds {max_length}"
                    )
                labels = [-100] * len(prompt_ids) + input_ids[len(prompt_ids) :]
                if all(label == -100 for label in labels):
                    raise ValueError(f"{path}:{line_number}: no response tokens to train")
                self.examples.append(
                    {
                        "input_ids": input_ids,
                        "attention_mask": [1] * len(input_ids),
                        "labels": labels,
                    }
                )
                if limit is not None and len(self.examples) >= limit:
                    break
        if not self.examples:
            raise ValueError(f"No examples loaded from {path}")
        self.torch = torch

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> dict[str, list[int]]:
        return self.examples[index]


class DynamicPaddingCollator:
    def __init__(self, pad_token_id: int) -> None:
        self.pad_token_id = pad_token_id

    def __call__(self, examples: list[dict[str, list[int]]]) -> dict[str, Any]:
        import torch

        max_length = max(len(example["input_ids"]) for example in examples)
        batch = {"input_ids": [], "attention_mask": [], "labels": []}
        for example in examples:
            padding = max_length - len(example["input_ids"])
            batch["input_ids"].append(
                example["input_ids"] + [self.pad_token_id] * padding
            )
            batch["attention_mask"].append(example["attention_mask"] + [0] * padding)
            batch["labels"].append(example["labels"] + [-100] * padding)
        return {key: torch.tensor(value, dtype=torch.long) for key, value in batch.items()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--train-data", type=Path, default=Path("data/processed/train.jsonl"))
    parser.add_argument(
        "--validation-data",
        type=Path,
        default=Path("data/processed/validation.jsonl"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/qwen3-1.7b-qlora"))
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=16)
    parser.add_argument("--eval-steps", type=int, default=100)
    parser.add_argument("--save-steps", type=int, default=100)
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument("--early-stopping-patience", type=int, default=2)
    parser.add_argument("--lora-rank", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--max-train-samples", type=int)
    parser.add_argument("--max-validation-samples", type=int)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--resume-from-checkpoint")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        EarlyStoppingCallback,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA training requires a CUDA GPU")
    set_seed(42)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.padding_side = "right"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_dataset = ChatDataset(
        args.train_data, tokenizer, args.max_length, args.max_train_samples
    )
    validation_dataset = ChatDataset(
        args.validation_data,
        tokenizer,
        args.max_length,
        args.max_validation_samples,
    )

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        device_map={"": 0},
        dtype=torch.bfloat16,
        quantization_config=quantization,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(
        model,
        use_gradient_checkpointing=True,
    )
    model = get_peft_model(
        model,
        LoraConfig(
            r=args.lora_rank,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            target_modules=LORA_TARGETS,
            bias="none",
            task_type="CAUSAL_LM",
        ),
    )
    model.print_trainable_parameters()

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        bf16=True,
        tf32=True,
        warmup_ratio=0.05,
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        optim="adamw_torch",
        eval_strategy="steps",
        save_strategy="steps",
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",
        remove_unused_columns=False,
        seed=42,
        data_seed=42,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        data_collator=DynamicPaddingCollator(tokenizer.pad_token_id),
        callbacks=[
            EarlyStoppingCallback(
                early_stopping_patience=args.early_stopping_patience
            )
        ],
    )
    metrics = trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)
    final_dir = args.output_dir / "final-adapter"
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(final_dir)
    trainer.save_metrics("train", metrics.metrics)
    (args.output_dir / "log-history.json").write_text(
        json.dumps(trainer.state.log_history, indent=2) + "\n"
    )
    config = {
        **vars(args),
        "model": str(args.model),
        "train_data": str(args.train_data),
        "validation_data": str(args.validation_data),
        "output_dir": str(args.output_dir),
        "train_records": len(train_dataset),
        "validation_records": len(validation_dataset),
        "lora_targets": LORA_TARGETS,
    }
    (args.output_dir / "run-config.json").write_text(
        json.dumps(config, indent=2, default=str) + "\n"
    )
    print(f"Saved adapter to {final_dir}")


if __name__ == "__main__":
    main()
