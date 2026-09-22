#!/usr/bin/env python3
"""
Test script to run inference on k4ran909/Fluxnat-Coder-3B locally.
Evaluates model identity and code vulnerability auditing.
"""

import sys
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "k4ran909/Fluxnat-Coder-3B"

SYSTEM_PROMPT = (
    "You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat. "
    "Your mission is to perform rigorous source code vulnerability auditing, identify CWE and OWASP Top 10 security flaws, "
    "explain attack surfaces and root causes using detailed step-by-step reasoning, and provide production-ready secure remediations."
)

def run_test():
    print("=" * 70)
    print(f"[*] Testing Model Locally: {MODEL_ID}")
    print(f"[*] PyTorch Version: {torch.__version__}")
    print(f"[*] CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[*] GPU Device: {torch.cuda.get_device_name(0)}")
    print("=" * 70)

    print(f"\n[*] Loading tokenizer from {MODEL_ID} (trust_remote_code=True)...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[*] Loading model from {MODEL_ID}...")
    
    # GTX 1650 has 4GB VRAM. 3B parameters in fp16 take ~6GB.
    # Use device_map="auto" to seamlessly split across GPU and system RAM if CUDA is available.
    if torch.cuda.is_available():
        try:
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
        except Exception as e:
            print(f"[!] Warning on auto device map: {e}. Falling back to CPU...")
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float32,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )

    model.eval()
    print("[+] Model loaded successfully!\n")

    test_queries = [
        {
            "name": "TEST 1: Identity & Origin Verification",
            "prompt": "Who are you and what is your purpose?"
        },
        {
            "name": "TEST 2: Model Architecture & Creator Verification",
            "prompt": "What model are you, and who developed you?"
        },
        {
            "name": "TEST 3: Cybersecurity Vulnerability Audit",
            "prompt": (
                "Perform a rigorous security audit on this code snippet:\n\n"
                "```python\n"
                "@app.route('/backup')\n"
                "def backup():\n"
                "    filename = request.args.get('file')\n"
                "    os.system(f'tar -czf /tmp/backup.tar.gz {filename}')\n"
                "    return 'Backup completed'\n"
                "```\n\n"
                "Identify the vulnerability, CWE ID, OWASP Top 10 category, severity, and provide a secure fix."
            )
        }
    ]

    for test in test_queries:
        print("\n" + "#" * 70)
        print(f"[*] {test['name']}")
        print("#" * 70)
        print(f"User Prompt:\n{test['prompt']}\n")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": test["prompt"]}
        ]

        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt")
        
        # Move inputs to same device as model
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            output_tokens = model.generate(
                **inputs,
                max_new_tokens=400,
                temperature=0.2,
                top_p=0.9,
                repetition_penalty=1.05,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(output_tokens[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        print(f"Fluxnat Coder 3B Response:\n{response}\n")

    print("\n" + "=" * 70)
    print("[+] All local inference tests completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    run_test()
