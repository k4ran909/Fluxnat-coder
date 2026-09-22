#!/usr/bin/env python3
"""
Fluxnat Coder 3B - Fine-Tuning Engine.
Supports both Unsloth (Ultra-Fast 2x/70% VRAM on Colab/Linux)
and Hugging Face TRL + PEFT (Standard fallback).
"""

import os
import sys
import yaml
import torch
from pathlib import Path
from typing import Dict, Any

from datasets import load_dataset
from transformers import TrainingArguments

# Try to import Unsloth
USE_UNSLOTH = False
try:
    from unsloth import FastLanguageModel
    from unsloth import is_bfloat16_supported
    USE_UNSLOTH = True
    print("[+] Unsloth acceleration detected and activated!")
except ImportError:
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    print("[-] Unsloth not found. Using standard Hugging Face TRL + PEFT pipeline.")


def load_config(config_path: str = "config/training_config.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def train_unsloth(config: Dict[str, Any]):
    """Execute training using Unsloth's optimized kernels."""
    model_cfg = config.get("model", {})
    lora_cfg = config.get("lora", {})
    train_cfg = config.get("training", {})
    output_dir = config.get("project", {}).get("output_dir", "./outputs/Fluxnat-Coder-3B")
    base_model_name = config.get("project", {}).get("base_model", "k4ran909/Fluxnat-Coder-3B")

    max_seq_length = model_cfg.get("max_seq_length", 4096)
    load_in_4bit = model_cfg.get("load_in_4bit", True)

    print(f"[*] Loading base model with Unsloth: {base_model_name}...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model_name,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=load_in_4bit,
    )

    print("[*] Configuring LoRA adapters for calibrated cybersecurity domain shift...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_cfg.get("r", 16),
        lora_alpha=lora_cfg.get("lora_alpha", 32),
        lora_dropout=lora_cfg.get("lora_dropout", 0.05),
        bias=lora_cfg.get("bias", "none"),
        target_modules=lora_cfg.get("target_modules", [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ]),
        use_gradient_checkpointing="unsloth",
        random_state=train_cfg.get("seed", 3407),
    )

    # Load prepared dataset
    train_file = "data/processed/train_data.jsonl"
    eval_file = "data/processed/eval_data.jsonl"

    if not os.path.exists(train_file):
        print(f"[!] Training data not found at {train_file}. Running dataset preparation first...")
        import subprocess
        subprocess.run([sys.executable, "prepare_datasets.py"], check=True)

    print(f"[*] Loading dataset from {train_file}...")
    dataset = load_dataset("json", data_files={"train": train_file, "eval": eval_file})

    def formatting_prompts_func(examples):
        convos = examples["messages"]
        texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    from trl import SFTTrainer

    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=train_cfg.get("per_device_train_batch_size", 2),
        gradient_accumulation_steps=train_cfg.get("gradient_accumulation_steps", 4),
        warmup_ratio=train_cfg.get("warmup_ratio", 0.1),
        max_steps=train_cfg.get("max_steps", 25),
        num_train_epochs=train_cfg.get("num_train_epochs", 2),
        learning_rate=train_cfg.get("learning_rate", 1e-4),
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=train_cfg.get("logging_steps", 2),
        optim=train_cfg.get("optim", "adamw_8bit"),
        weight_decay=train_cfg.get("weight_decay", 0.01),
        lr_scheduler_type=train_cfg.get("lr_scheduler_type", "cosine"),
        seed=train_cfg.get("seed", 3407),
        save_strategy=train_cfg.get("save_strategy", "steps"),
        save_steps=train_cfg.get("save_steps", 25),
        save_total_limit=train_cfg.get("save_total_limit", 2),
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"] if "eval" in dataset else None,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
    )

    print("\n[+] Starting Fluxnat Coder 3B Training via Unsloth...")
    trainer.train()

    print(f"\n[+] Saving fine-tuned adapters to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print("[✓] Unsloth training completed!")
    return model, tokenizer


def train_hf_standard(config: Dict[str, Any]):
    """Execute training using standard Hugging Face PEFT + TRL."""
    model_cfg = config.get("model", {})
    lora_cfg = config.get("lora", {})
    train_cfg = config.get("training", {})
    output_dir = config.get("project", {}).get("output_dir", "./outputs/Fluxnat-Coder-3B")
    base_model_name = config.get("project", {}).get("base_model", "k4ran909/Fluxnat-Coder-3B")

    max_seq_length = model_cfg.get("max_seq_length", 4096)

    print(f"[*] Loading tokenizer for {base_model_name}...")
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer

    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[*] Loading model with 4-bit BitsAndBytes quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=lora_cfg.get("r", 16),
        lora_alpha=lora_cfg.get("lora_alpha", 32),
        lora_dropout=lora_cfg.get("lora_dropout", 0.05),
        bias=lora_cfg.get("bias", "none"),
        task_type="CAUSAL_LM",
        target_modules=lora_cfg.get("target_modules", [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ]),
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    train_file = "data/processed/train_data.jsonl"
    eval_file = "data/processed/eval_data.jsonl"

    if not os.path.exists(train_file):
        print(f"[!] Training data not found at {train_file}. Running dataset preparation first...")
        import subprocess
        subprocess.run([sys.executable, "prepare_datasets.py"], check=True)

    dataset = load_dataset("json", data_files={"train": train_file, "eval": eval_file})

    def formatting_prompts_func(examples):
        convos = examples["messages"]
        texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=train_cfg.get("per_device_train_batch_size", 2),
        gradient_accumulation_steps=train_cfg.get("gradient_accumulation_steps", 4),
        warmup_ratio=train_cfg.get("warmup_ratio", 0.1),
        max_steps=train_cfg.get("max_steps", 25),
        num_train_epochs=train_cfg.get("num_train_epochs", 2),
        learning_rate=train_cfg.get("learning_rate", 1e-4),
        fp16=True,
        logging_steps=train_cfg.get("logging_steps", 2),
        optim=train_cfg.get("optim", "adamw_8bit"),
        weight_decay=train_cfg.get("weight_decay", 0.01),
        lr_scheduler_type=train_cfg.get("lr_scheduler_type", "cosine"),
        seed=train_cfg.get("seed", 3407),
        save_strategy=train_cfg.get("save_strategy", "steps"),
        save_steps=train_cfg.get("save_steps", 25),
        save_total_limit=train_cfg.get("save_total_limit", 2),
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"] if "eval" in dataset else None,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        args=training_args,
    )

    print("\n[+] Starting Fluxnat Coder 3B Training via Standard TRL...")
    trainer.train()

    print(f"\n[+] Saving fine-tuned adapters to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print("[✓] Standard PEFT training completed!")
    return model, tokenizer


def main():
    print("=================================================================")
    print("           Fluxnat Coder 3B - Training Initiation                ")
    print("=================================================================")

    config = load_config()

    if USE_UNSLOTH:
        train_unsloth(config)
    else:
        train_hf_standard(config)


if __name__ == "__main__":
    main()
