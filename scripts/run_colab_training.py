#!/usr/bin/env python3
"""
Fluxnat Coder 3B - Automated Colab Retraining Pipeline
Downloads the expanded dataset (520 samples), executes QLoRA fine-tuning (65 steps),
merges to 16-bit standalone model, and publishes to Hugging Face Hub.
"""

import os
import json
import random
import urllib.request
from pathlib import Path
from datasets import Dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported, FastLanguageModel

print("=" * 60)
print("  Fluxnat Coder 3B - Red Team & Multi-CWE Retraining Pipeline")
print("=" * 60)

SYSTEM_PROMPT = (
    "You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat. "
    "Your mission is to perform rigorous source code vulnerability auditing, identify CWE and OWASP Top 10 security flaws, "
    "explain attack surfaces and root causes using detailed step-by-step reasoning, and provide production-ready secure remediations."
)

REPO_RAW = "https://raw.githubusercontent.com/k4ran909/Fluxnat-coder/main"

def download_jsonl(url):
    name = url.split('/')[-1]
    print(f"[*] Downloading {name}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    data = response.read().decode('utf-8')
    records = []
    for line in data.strip().split('\n'):
        if line.strip():
            records.append(json.loads(line))
    return records

# 1. Download curated datasets
security_raw = download_jsonl(f"{REPO_RAW}/data/custom_cot/security_cot.jsonl")
security_records = []
for item in security_raw:
    if 'messages' in item:
        if item['messages'] and item['messages'][0]['role'] == 'system':
            item['messages'][0]['content'] = SYSTEM_PROMPT
        security_records.append(item)
print(f"[+] Loaded {len(security_records)} security CoT samples")

redteam_raw = download_jsonl(f"{REPO_RAW}/data/custom_cot/redteam_cot.jsonl")
redteam_records = []
for item in redteam_raw:
    instruction = item.get('instruction', '')
    inp = item.get('input', '')
    output = item.get('output', '')
    if inp:
        instruction = f"{instruction}\n\nCode/Input:\n{inp}"
    if instruction and output:
        redteam_records.append({
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': instruction.strip()},
                {'role': 'assistant', 'content': output.strip()}
            ]
        })
print(f"[+] Loaded {len(redteam_records)} red team CoT samples")

identity_raw = download_jsonl(f"{REPO_RAW}/data/custom_cot/identity_alignment.jsonl")
identity_records = []
for item in identity_raw:
    if 'messages' in item:
        if item['messages'] and item['messages'][0]['role'] == 'system':
            item['messages'][0]['content'] = SYSTEM_PROMPT
        identity_records.append(item)
print(f"[+] Loaded {len(identity_records)} identity alignment samples")

# 2. Build balanced training pool: 24*5 + 170*2 + 15*4 = 520 samples
all_training = (security_records * 5) + (redteam_records * 2) + (identity_records * 4)
random.seed(3407)
random.shuffle(all_training)

formatted_texts = [
    tokenizer.apply_chat_template(item["messages"], tokenize=False, add_generation_prompt=False)
    for item in all_training
]
train_dataset = Dataset.from_dict({"text": formatted_texts})
print(f"\n[OK] Prepared {len(train_dataset)} balanced training sequences!")
print(f"     - Security Audits: {len(security_records) * 5} ({len(security_records)} cases)")
print(f"     - Red Team & ATT&CK: {len(redteam_records) * 2} ({len(redteam_records)} cases)")
print(f"     - Identity Alignment: {len(identity_records) * 4} ({len(identity_records)} cases)")

# 3. Fine-tuning with SFTTrainer
OUTPUT_DIR = "./Fluxnat-Coder-3B-Adapters"
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=5,
    max_steps=65,
    learning_rate=8e-5,
    fp16=not is_bfloat16_supported(),
    bf16=is_bfloat16_supported(),
    logging_steps=5,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="cosine",
    seed=3407,
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    dataset_text_field="text",
    max_seq_length=4096,
    dataset_num_proc=2,
    packing=False,
    args=training_args,
)

print(f"\n[*] Starting training: {training_args.max_steps} steps, lr={training_args.learning_rate}...")
trainer_stats = trainer.train()

print(f"\n[OK] Training Complete!")
print(f"     Final Loss: {trainer_stats.training_loss:.4f}")
print(f"     Total Steps: {trainer_stats.global_step}")
print(f"     Runtime: {trainer_stats.metrics['train_runtime']:.1f}s")

# 4. Merge to 16-bit standalone model
MERGED_DIR = "./Fluxnat-Coder-3B-Merged"
print(f"\n[*] Merging LoRA adapters into standalone 16-bit model: {MERGED_DIR}...")
model.save_pretrained_merged(MERGED_DIR, tokenizer, save_method="merged_16bit")

cfg_path = Path(MERGED_DIR) / "config.json"
if cfg_path.exists():
    with open(cfg_path, 'r') as f:
        c = json.load(f)
    c["_name_or_path"] = "k4ran909/Fluxnat-Coder-3B"
    c["model_name"] = "Fluxnat-Coder-3B"
    c["model_author"] = "Fluxnat"
    with open(cfg_path, 'w') as f:
        json.dump(c, f, indent=2)

print("[OK] Standalone model merged and rebranded successfully!")

# 5. Push to Hugging Face Hub
from huggingface_hub import HfApi

hf_token = os.environ.get('HF_TOKEN')
if not hf_token:
    try:
        from google.colab import userdata
        hf_token = userdata.get('HF_TOKEN')
    except Exception:
        pass

if hf_token:
    api = HfApi(token=hf_token)
    HUB_MODEL_ID = 'k4ran909/Fluxnat-Coder-3B'
    print(f"\n[*] Creating repository {HUB_MODEL_ID}...")
    api.create_repo(repo_id=HUB_MODEL_ID, repo_type='model', exist_ok=True)
    print(f"[*] Uploading {MERGED_DIR} to https://huggingface.co/{HUB_MODEL_ID}...")
    api.upload_folder(
        folder_path=MERGED_DIR,
        repo_id=HUB_MODEL_ID,
        repo_type='model'
    )
    print(f"[OK] Model is LIVE on Hugging Face Hub: https://huggingface.co/{HUB_MODEL_ID}!")
else:
    print("[!] HF_TOKEN not found in environment, skipping upload.")

print("\n" + "=" * 60)
print("  Retraining & Hub Deployment Complete!")
print("=" * 60)
