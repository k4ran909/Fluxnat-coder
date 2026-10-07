#!/usr/bin/env python3
"""Update Fluxnat_Coder_3B_Training.ipynb for the expanded 520-sample dataset.

Changes:
  - Step 4: Replace inline samples with GitHub raw download of processed data
  - Step 5: Increase max_steps from 35 to 65 for larger dataset
"""

import json
import os

NOTEBOOK = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "Fluxnat_Coder_3B_Training.ipynb")

# New Step 4 cell source — downloads processed data from GitHub instead of inline
STEP4_CODE = r'''import json
import random
import urllib.request
from datasets import Dataset

SYSTEM_PROMPT = (
    "You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat. "
    "Your mission is to perform rigorous source code vulnerability auditing, identify CWE and OWASP Top 10 security flaws, "
    "explain attack surfaces and root causes using detailed step-by-step reasoning, and provide production-ready secure remediations."
)

REPO_RAW = "https://raw.githubusercontent.com/k4ran909/Fluxnat-coder/main"

def download_jsonl(url):
    """Download a JSONL file and return list of parsed dicts."""
    print(f"[*] Downloading {url.split('/')[-1]}...")
    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')
    records = []
    for line in data.strip().split('\n'):
        if line.strip():
            records.append(json.loads(line))
    return records

# 1. Download curated security CoT samples (24 samples, messages format)
security_raw = download_jsonl(f"{REPO_RAW}/data/custom_cot/security_cot.jsonl")
security_records = []
for item in security_raw:
    if 'messages' in item:
        if item['messages'] and item['messages'][0]['role'] == 'system':
            item['messages'][0]['content'] = SYSTEM_PROMPT
        security_records.append(item)
print(f"[+] Loaded {len(security_records)} security CoT samples")

# 2. Download red team offensive security samples (170 samples, instruction/output format)
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

# 3. Download identity alignment samples
identity_raw = download_jsonl(f"{REPO_RAW}/data/custom_cot/identity_alignment.jsonl")
identity_records = []
for item in identity_raw:
    if 'messages' in item:
        if item['messages'] and item['messages'][0]['role'] == 'system':
            item['messages'][0]['content'] = SYSTEM_PROMPT
        identity_records.append(item)
print(f"[+] Loaded {len(identity_records)} identity alignment samples")

# 4. Build balanced training mix
# Security CoT (24) x5 = 120, Red Team (170) x2 = 340, Identity (15) x4 = 60 => ~520 total
all_training = (security_records * 5) + (redteam_records * 2) + (identity_records * 4)
random.seed(3407)
random.shuffle(all_training)

formatted_texts = [
    tokenizer.apply_chat_template(item["messages"], tokenize=False, add_generation_prompt=False)
    for item in all_training
]
train_dataset = Dataset.from_dict({"text": formatted_texts})
print(f"\n[OK] Prepared {len(train_dataset)} expanded training sequences!")
print(f"     - Security Audits: {len(security_records) * 5} ({len(security_records)} distinct CWE cases)")
print(f"     - Red Team / Offensive: {len(redteam_records) * 2} ({len(redteam_records)} exploit chains, payloads, attack techniques)")
print(f"     - Identity Alignment: {len(identity_records) * 4} ({len(identity_records)} identity prompts)")
'''

# New Step 5 training config — increased steps for 520 samples
STEP5_CODE = r'''from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

OUTPUT_DIR = "./Fluxnat-Coder-3B-Adapters"

# Calibrated Training Arguments for Expanded 520-Sample Dataset:
# - max_steps=65: ~1 epoch over 520 samples (effective batch size = 8 -> 65 steps/epoch)
# - learning_rate=8e-5: Slightly lower LR for larger dataset to prevent overfitting
# - warmup_steps=5: Gradual warmup for stable convergence
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=5,
    max_steps=65,             # ~1 epoch over 520 samples (effective batch 8 -> 65 steps) ~3-5 min on T4
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
    max_seq_length=MAX_SEQ_LENGTH,
    dataset_num_proc=2,
    packing=False,
    args=training_args,
)

print(f"[OK] SFTTrainer ready: {training_args.max_steps} steps, batch={training_args.per_device_train_batch_size}x{training_args.gradient_accumulation_steps}")
print(f"     LR={training_args.learning_rate}, warmup={training_args.warmup_steps}, scheduler={training_args.lr_scheduler_type}")

trainer_stats = trainer.train()

print(f"\n[OK] Training Complete!")
print(f"     Final Loss: {trainer_stats.training_loss:.4f}")
print(f"     Total Steps: {trainer_stats.global_step}")
print(f"     Runtime: {trainer_stats.metrics['train_runtime']:.1f}s")
'''


def code_to_notebook_source(code_str):
    """Convert a multi-line code string to notebook source format (list of lines with \\n)."""
    lines = code_str.split('\n')
    result = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            result.append(line + '\n')
        elif line:  # last line, only add if non-empty
            result.append(line + '\n')
    return result


def main():
    with open(NOTEBOOK, "r", encoding="utf-8") as f:
        nb = json.load(f)

    cells = nb["cells"]
    step4_idx = None
    step5_idx = None

    # Find Step 4 and Step 5 code cells
    for i, cell in enumerate(cells):
        src = "".join(cell.get("source", []))
        if "Step 4" in src and cell["cell_type"] == "markdown":
            step4_idx = i + 1
        if "Step 5" in src and cell["cell_type"] == "markdown":
            step5_idx = i + 1

    if step4_idx is None or step5_idx is None:
        print("[!] Could not find Step 4 or Step 5 cells")
        return

    print(f"[*] Updating Step 4 (cell {step4_idx}): GitHub download dataset")
    cells[step4_idx]["source"] = code_to_notebook_source(STEP4_CODE)
    cells[step4_idx]["outputs"] = []

    print(f"[*] Updating Step 5 (cell {step5_idx}): max_steps=65, lr=8e-5")
    cells[step5_idx]["source"] = code_to_notebook_source(STEP5_CODE)
    cells[step5_idx]["outputs"] = []

    with open(NOTEBOOK, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

    print("[OK] Notebook updated successfully!")
    print("     Step 4: Downloads security_cot + redteam_cot + identity from GitHub")
    print("     Step 5: max_steps=65, lr=8e-5, warmup=5, logging=5")


if __name__ == "__main__":
    main()
