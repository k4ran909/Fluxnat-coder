#!/usr/bin/env python3
"""
Model Merging and Export Pipeline for Fluxnat Coder 3B.
Merges fine-tuned LoRA adapters back into base model weights,
creates a standalone 16-bit Hugging Face checkpoint,
and optionally exports GGUF format for local llama.cpp / LM Studio inference.
"""

import os
import sys
import yaml
import torch
from pathlib import Path
from typing import Dict, Any

try:
    from unsloth import FastLanguageModel
    USE_UNSLOTH = True
except ImportError:
    USE_UNSLOTH = False
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel


def load_config(config_path: str = "config/training_config.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def merge_and_export_unsloth(config: Dict[str, Any]):
    """Merge and export using Unsloth."""
    output_dir = config.get("project", {}).get("output_dir", "./outputs/Fluxnat-Coder-3B")
    merged_dir = "./outputs/Fluxnat-Coder-3B-Merged"
    export_gguf = config.get("project", {}).get("export_gguf", True)

    print(f"[*] Loading fine-tuned adapter from {output_dir} via Unsloth...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=output_dir,
        max_seq_length=4096,
        dtype=None,
        load_in_4bit=False, # Load in float16 for merging
    )

    print(f"[*] Saving merged 16-bit standalone model to {merged_dir}...")
    model.save_pretrained_merged(merged_dir, tokenizer, save_method="merged_16bit")

    if export_gguf:
        print("[*] Exporting model to GGUF format (q4_k_m and q8_0)...")
        try:
            model.save_pretrained_gguf(merged_dir, tokenizer, quantization_method="q4_k_m")
            print("[OK] Q4_K_M GGUF exported successfully!")
        except Exception as e:
            print(f"[!] GGUF export failed: {e}")

    # Rebrand the merged model directory
    from rebrand import rebrand_model_directory
    rebrand_model_directory(merged_dir)
    print("[OK] Standalone merged model ready at:", merged_dir)


def merge_and_export_standard(config: Dict[str, Any]):
    """Merge and export using standard Hugging Face + PEFT."""
    output_dir = config.get("project", {}).get("output_dir", "./outputs/Fluxnat-Coder-3B")
    merged_dir = "./outputs/Fluxnat-Coder-3B-Merged"
    base_model_name = config.get("project", {}).get("base_model", "k4ran909/Fluxnat-Coder-3B")

    print(f"[*] Loading base model: {base_model_name} in float16...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(output_dir, trust_remote_code=True)

    print(f"[*] Merging LoRA adapters from {output_dir}...")
    model = PeftModel.from_pretrained(base_model, output_dir)
    model = model.merge_and_unload()

    print(f"[*] Writing merged model to {merged_dir}...")
    model.save_pretrained(merged_dir, safe_serialization=True)
    tokenizer.save_pretrained(merged_dir)

    # Rebrand the merged directory
    from rebrand import rebrand_model_directory
    rebrand_model_directory(merged_dir)

    print("[OK] Standalone merged model ready at:", merged_dir)


def push_to_huggingface_hub(merged_dir: str = "./outputs/Fluxnat-Coder-3B-Merged", repo_id: str = "fluxnat/Fluxnat-Coder-3B"):
    """Push the standalone merged model directly to Hugging Face Hub."""
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("[!] HF_TOKEN environment variable is not set. Skipping Hugging Face upload.")
        print("    To upload later: set HF_TOKEN=<your_token> and run push_to_hub.")
        return

    from huggingface_hub import HfApi
    api = HfApi(token=hf_token)
    user_info = api.whoami()
    username = user_info.get("name", "")
    orgs = [org.get("name") for org in user_info.get("orgs", [])]

    # If repo_id specifies fluxnat but user doesn't belong to fluxnat org, fallback to user namespace
    if "fluxnat/" in repo_id and "fluxnat" not in orgs:
        print(f"[!] Token does not belong to org 'fluxnat'. Using your personal namespace '{username}'...")
        repo_id = f"{username}/Fluxnat-Coder-3B"

    print(f"[*] Authenticating with Hugging Face Hub for {repo_id}...")
    api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)

    print(f"[*] Uploading all model weights, configs, and tokenizer to {repo_id}...")
    api.upload_folder(
        folder_path=merged_dir,
        repo_id=repo_id,
        repo_type="model",
    )
    print(f"[OK] Successfully published to https://huggingface.co/{repo_id}!")


def main():
    print("=================================================================")
    print("        Fluxnat Coder 3B - Model Merging & Export Engine         ")
    print("=================================================================")

    config = load_config()
    hub_id = config.get("project", {}).get("hub_model_id", "fluxnat/Fluxnat-Coder-3B")

    if USE_UNSLOTH:
        merge_and_export_unsloth(config)
    else:
        merge_and_export_standard(config)

    merged_dir = "./outputs/Fluxnat-Coder-3B-Merged"
    if "--push" in sys.argv or os.getenv("AUTO_PUSH_HF") == "1":
        push_to_huggingface_hub(merged_dir, hub_id)


if __name__ == "__main__":
    main()
