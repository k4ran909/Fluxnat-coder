#!/usr/bin/env python3
"""
Update Fluxnat_Coder_3B_Training.ipynb Step 4 and Step 5 to train on
the comprehensive, multi-language, balanced CWE dataset.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

notebook_path = Path("Fluxnat_Coder_3B_Training.ipynb")
with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Load the dataset from scripts/generate_cwe_dataset.py
from scripts.generate_cwe_dataset import DATASET, SYSTEM_PROMPT

# Build vulnerable and benign records from DATASET
vulnerable_records = []
benign_records = []

for item in DATASET:
    rec = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": item["prompt"].strip()},
            {"role": "assistant", "content": item["response"].strip()}
        ]
    }
    if "SECURE / BENIGN" in item["response"]:
        benign_records.append(rec)
    else:
        vulnerable_records.append(rec)

# Step 4 code replacement
cell_8_code = f'''import json
import random
from datasets import Dataset

SYSTEM_PROMPT = (
    "You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat. "
    "Your mission is to perform rigorous source code vulnerability auditing, identify CWE and OWASP Top 10 security flaws, "
    "explain attack surfaces and root causes using detailed step-by-step reasoning, and provide production-ready secure remediations."
)

# 1. Comprehensive Multi-Language Vulnerability Audits (Balanced CWE Coverage)
# Covers CWE-502 (Java/Python/Node), CWE-79 (PHP/React/DOM), CWE-918 (Python/Go/Node),
# CWE-120 (C strcpy/gets/sprintf), CWE-798 (AWS/JWT/DB), CWE-89, CWE-78, CWE-22, CWE-95.
vulnerable_records = {json.dumps(vulnerable_records, indent=4)}

# 2. Curated Negative Benign Controls (Teaches Model to Recognize Clean/Safe Code)
benign_records = {json.dumps(benign_records, indent=4)}

# 3. Identity Alignment Records (Permanently establishes model name & mission in weights)
identity_records = [
    {{"messages": [{{"role": "system", "content": SYSTEM_PROMPT}}, {{"role": "user", "content": "Who are you?"}}, {{"role": "assistant", "content": "I am Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat."}}]}},
    {{"messages": [{{"role": "system", "content": SYSTEM_PROMPT}}, {{"role": "user", "content": "What is your name?"}}, {{"role": "assistant", "content": "My name is Fluxnat Coder 3B, developed by Fluxnat."}}]}},
    {{"messages": [{{"role": "system", "content": SYSTEM_PROMPT}}, {{"role": "user", "content": "Who created you?"}}, {{"role": "assistant", "content": "I was created and developed by Fluxnat for cybersecurity vulnerability auditing and secure software engineering."}}]}},
    {{"messages": [{{"role": "system", "content": SYSTEM_PROMPT}}, {{"role": "user", "content": "What is your identity?"}}, {{"role": "assistant", "content": "I am Fluxnat Coder 3B, a specialized cybersecurity AI model developed by Fluxnat."}}]}},
    {{"messages": [{{"role": "system", "content": SYSTEM_PROMPT}}, {{"role": "user", "content": "Which company created you?"}}, {{"role": "assistant", "content": "No, I was created and trained by Fluxnat specifically for source code security analysis and threat prevention."}}]}},
    {{"messages": [{{"role": "system", "content": SYSTEM_PROMPT}}, {{"role": "user", "content": "What model are you?"}}, {{"role": "assistant", "content": "I am Fluxnat Coder 3B, an autonomous cybersecurity intelligence model developed by Fluxnat."}}]}},
    {{"messages": [{{"role": "system", "content": SYSTEM_PROMPT}}, {{"role": "user", "content": "Tell me about yourself."}}, {{"role": "assistant", "content": "I am Fluxnat Coder 3B, created by Fluxnat. I specialize in auditing source code for security flaws, mapping vulnerabilities to CWE and OWASP Top 10 standards, and providing secure remediations."}}]}}
]

# Balanced blend: 20 Vuln * 4 = 80 + 4 Benign * 10 = 40 + 7 Identity * 4 = 28 -> ~148 total samples
all_training = (vulnerable_records * 4) + (benign_records * 10) + (identity_records * 4)
random.seed(3407)
random.shuffle(all_training)

formatted_texts = [
    tokenizer.apply_chat_template(item["messages"], tokenize=False, add_generation_prompt=False)
    for item in all_training
]
train_dataset = Dataset.from_dict({{"text": formatted_texts}})
print(f"[OK] Prepared {{len(train_dataset)}} balanced training sequences!")
print(f"     - Vulnerability Audits: {{len(vulnerable_records) * 4}} ({{len(vulnerable_records)}} distinct CWE cases)")
print(f"     - Negative Benign Controls: {{len(benign_records) * 10}} ({{len(benign_records)}} distinct patterns)")
print(f"     - Identity Alignment: {{len(identity_records) * 4}} ({{len(identity_records)}} identity prompts)")
'''

# Format code lines with trailing newline for ipynb format
nb['cells'][8]['source'] = [line + '\n' for line in cell_8_code.split('\n')]

# Update Step 5 training arguments (Cell 10) to max_steps=35 for the expanded dataset
cell_10_code = '''from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

OUTPUT_DIR = "./Fluxnat-Coder-3B-Adapters"

# Calibrated Training Arguments for Expanded Multi-CWE Dataset:
# - max_steps=35: Trains ~2 epochs over 148 samples (effective batch size = 8)
# - learning_rate=1e-4: Maintains healthy convergence (~0.55-0.75 loss) without capacity collapse
# - warmup_steps=3: Smooth adapter weight initialization
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=3,
    max_steps=35,             # 2 full epochs over 148 balanced samples (~90-120s on Tesla T4)
    learning_rate=1e-4,
    fp16=not is_bfloat16_supported(),
    bf16=is_bfloat16_supported(),
    logging_steps=2,
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

print("[+] Training Fluxnat Coder 3B on Balanced Multi-CWE Dataset (Target Loss ~0.55 - 0.75)...")
trainer.train()
print("[✓] Calibrated multi-class training completed successfully!")
'''

nb['cells'][10]['source'] = [line + '\n' for line in cell_10_code.split('\n')]

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("[OK] Successfully updated Fluxnat_Coder_3B_Training.ipynb with balanced multi-CWE dataset and calibrated 35-step training!")
