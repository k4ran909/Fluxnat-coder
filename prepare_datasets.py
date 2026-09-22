#!/usr/bin/env python3
"""
Dataset Preparation Pipeline for Fluxnat Coder 3B.
Downloads, validates, cleans, and standardizes cybersecurity datasets
into standard chat format with the custom Fluxnat Coder 3B identity.
"""

import os
import json
import random
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None


DEFAULT_SYSTEM_PROMPT = (
    "You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat. "
    "Your mission is to perform rigorous source code vulnerability auditing, identify CWE and OWASP Top 10 security flaws, "
    "explain attack surfaces and root causes using detailed step-by-step reasoning, and provide production-ready secure remediations."
)


def load_config(config_path: str = "config/training_config.yaml") -> Dict[str, Any]:
    """Load configuration yaml file."""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def format_qa_to_chat(instruction: str, response: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> Dict[str, Any]:
    """Format single instruction-response pair into chat message structure."""
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction.strip()},
            {"role": "assistant", "content": response.strip()}
        ]
    }


def load_local_cot_data(cot_path: str, system_prompt: str) -> List[Dict[str, Any]]:
    """Load local curated chain-of-thought security dataset."""
    records = []
    if not os.path.exists(cot_path):
        print(f"[!] Warning: Local CoT file not found at {cot_path}")
        return records

    with open(cot_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if "messages" in item:
                    # Update system prompt if needed
                    if item["messages"] and item["messages"][0]["role"] == "system":
                        item["messages"][0]["content"] = system_prompt
                    records.append(item)
            except Exception as e:
                print(f"[!] Error parsing line in {cot_path}: {e}")
    print(f"[+] Loaded {len(records)} local CoT samples from {cot_path}")
    return records


def download_and_format_hf_datasets(config: Dict[str, Any], system_prompt: str) -> List[Dict[str, Any]]:
    """Download cybersecurity datasets from Hugging Face and format them."""
    if load_dataset is None:
        print("[!] 'datasets' library is not installed. Skipping Hugging Face download.")
        return []

    hf_token = os.getenv("HF_TOKEN")
    dataset_sources = config.get("datasets", {}).get("sources", [])
    collected_samples: List[Dict[str, Any]] = []

    for src in dataset_sources:
        src_name = src.get("name")
        limit = src.get("sample_limit", 10000)

        if src_name == "local_cot":
            continue

        print(f"[*] Fetching Hugging Face dataset: {src_name} (max: {limit})...")
        try:
            ds = load_dataset(src_name, split="train", token=hf_token)
            count = 0
            for item in ds:
                if count >= limit:
                    break

                instruction = ""
                response = ""

                # Handle various common schema shapes
                if "prompt" in item and "response" in item:
                    instruction, response = item["prompt"], item["response"]
                elif "instruction" in item and "output" in item:
                    instruction = item["instruction"]
                    if item.get("input"):
                        instruction += f"\n\nCode/Input:\n{item['input']}"
                    response = item["output"]
                elif "question" in item and "answer" in item:
                    instruction, response = item["question"], item["answer"]
                elif "text" in item:
                    # Raw text entry
                    instruction = "Analyze the following cybersecurity intelligence:"
                    response = item["text"]

                if instruction and response:
                    chat_entry = format_qa_to_chat(instruction, response, system_prompt)
                    collected_samples.append(chat_entry)
                    count += 1

            print(f"[+] Successfully loaded {count} samples from {src_name}")
        except Exception as e:
            print(f"[!] Could not load dataset {src_name}: {e}")
            print("    Continuing with remaining dataset sources...")

    return collected_samples


def main():
    print("=================================================================")
    print("        Fluxnat Coder 3B - Dataset Preparation Pipeline          ")
    print("=================================================================")

    config = load_config()
    system_prompt = config.get("system_identity", {}).get("prompt", DEFAULT_SYSTEM_PROMPT).strip()

    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_data: List[Dict[str, Any]] = []

    # 1. Load curated local CoT (Vulnerable + Benign) & Identity Alignment datasets
    cot_path = config.get("datasets", {}).get("sources", [{}])[2].get("path", "./data/custom_cot/security_cot.jsonl")
    local_samples = load_local_cot_data(cot_path, system_prompt)
    if local_samples:
        # Amplify local security reasoning samples (both vuln and benign) to form core knowledge base
        all_data.extend(local_samples * 5)
        print(f"[+] Added {len(local_samples)} local CoT samples (amplified 5x -> {len(local_samples) * 5} total)")

    identity_path = "./data/custom_cot/identity_alignment.jsonl"
    if os.path.exists(identity_path):
        identity_samples = load_local_cot_data(identity_path, system_prompt)
        # Moderate amplification of identity samples to preserve code domain reasoning
        all_data.extend(identity_samples * 4)
        print(f"[+] Added {len(identity_samples)} identity alignment samples (amplified 4x -> {len(identity_samples) * 4} total)")

    # 2. Load online datasets if network/HF token available
    hf_samples = download_and_format_hf_datasets(config, system_prompt)
    all_data.extend(hf_samples)

    print(f"\n[+] Total assembled training records: {len(all_data)}")

    if not all_data:
        print("[!] No data collected! Generating fallback cybersecurity seed samples...")
        # Create minimal training pool if offline or no dataset installed
        for i in range(20):
            all_data.extend(local_samples)

    # Shuffle for training uniformity
    random.seed(42)
    random.shuffle(all_data)

    # Split into 95% train / 5% validation
    eval_split_index = int(len(all_data) * 0.95)
    train_data = all_data[:eval_split_index]
    eval_data = all_data[eval_split_index:] if eval_split_index < len(all_data) else all_data[:1]

    train_file = output_dir / "train_data.jsonl"
    eval_file = output_dir / "eval_data.jsonl"

    print(f"[*] Writing {len(train_data)} train samples to {train_file}...")
    with open(train_file, "w", encoding="utf-8") as f:
        for entry in train_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"[*] Writing {len(eval_data)} validation samples to {eval_file}...")
    with open(eval_file, "w", encoding="utf-8") as f:
        for entry in eval_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print("[OK] Dataset preparation completed successfully!")
    print(f"    Train: {train_file}")
    print(f"    Eval:  {eval_file}")


if __name__ == "__main__":
    main()
