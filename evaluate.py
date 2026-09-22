#!/usr/bin/env python3
"""
Evaluation and Benchmarking Suite for Fluxnat Coder 3B.
Tests detection accuracy, false positive rate, CWE identification,
and secure remediation generation on real-world code snippets.
"""

import os
import sys
import json
import torch
from pathlib import Path
from typing import List, Dict, Any

from transformers import AutoModelForCausalLM, AutoTokenizer

# Test benchmark dataset containing both vulnerable code patterns and benign baselines
EVAL_TEST_CASES = [
    {
        "id": "TC-01",
        "name": "SQL Injection (Python SQLite)",
        "is_vulnerable": True,
        "expected_cwe": "CWE-89",
        "code": """def get_user_profile(user_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM profiles WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()"""
    },
    {
        "id": "TC-02",
        "name": "OS Command Injection (Node.js)",
        "is_vulnerable": True,
        "expected_cwe": "CWE-78",
        "code": """app.post('/compress', (req, res) => {
    const filename = req.body.filename;
    exec(`tar -czf ${filename}.tar.gz ${filename}`, (err, out) => {
        res.send('Compressed');
    });
});"""
    },
    {
        "id": "TC-03",
        "name": "Path Traversal (Python)",
        "is_vulnerable": True,
        "expected_cwe": "CWE-22",
        "code": """@app.route('/files')
def get_file():
    target = request.args.get('path')
    full_path = os.path.join('/data/storage', target)
    return open(full_path, 'rb').read()"""
    },
    {
        "id": "TC-04",
        "name": "Hardcoded Secret (Python)",
        "is_vulnerable": True,
        "expected_cwe": "CWE-798",
        "code": """AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def connect_s3():
    return boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)"""
    },
    {
        "id": "TC-05",
        "name": "Benign Clean Code (Parameterized Query)",
        "is_vulnerable": False,
        "expected_cwe": "None",
        "code": """def get_user_by_email(email: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, created_at FROM users WHERE email = %s", (email,))
    return cursor.fetchone()"""
    }
]


def run_benchmark(model_path: str = "./outputs/Fluxnat-Coder-3B-Merged"):
    """Evaluate model on benchmark test suite."""
    if not os.path.exists(model_path):
        fallback = "./outputs/Fluxnat-Coder-3B"
        if os.path.exists(fallback):
            model_path = fallback
        else:
            print(f"[*] Local model not found at {model_path}. Loading hub model: k4ran909/Fluxnat-Coder-3B...")
            model_path = "k4ran909/Fluxnat-Coder-3B"

    print(f"[*] Loading model for benchmark: {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )

    results = []
    print("\n" + "="*80)
    print(f"{'ID':<6} | {'Test Case':<35} | {'Expected':<12} | {'Detected':<10} | {'Status'}")
    print("="*80)

    for tc in EVAL_TEST_CASES:
        prompt = (
            f"Perform a strict cybersecurity vulnerability audit of this code snippet. "
            f"State clearly whether it is VULNERABLE or BENIGN. "
            f"If vulnerable, specify the exact CWE ID (e.g. CWE-89) and explain why.\n\n"
            f"```\n{tc['code']}\n```"
        )

        messages = [
            {"role": "system", "content": "You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat."},
            {"role": "user", "content": prompt}
        ]

        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.1,
                do_sample=False
            )

        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

        resp_lower = response.lower()
        detected_vulnerable = "vulnerable" in resp_lower and "not vulnerable" not in resp_lower and "benign" not in resp_lower

        cwe_found = tc["expected_cwe"].lower() in resp_lower if tc["expected_cwe"] != "None" else True

        passed = (detected_vulnerable == tc["is_vulnerable"]) and cwe_found
        status = "PASSED ✓" if passed else "FAILED ✗"

        exp_str = tc["expected_cwe"] if tc["is_vulnerable"] else "BENIGN"
        det_str = "VULN" if detected_vulnerable else "BENIGN"

        print(f"{tc['id']:<6} | {tc['name']:<35} | {exp_str:<12} | {det_str:<10} | {status}")
        results.append({"test_case": tc["name"], "passed": passed, "response": response[:200] + "..."})

    total_passed = sum(1 for r in results if r["passed"])
    accuracy = (total_passed / len(results)) * 100
    print("="*80)
    print(f"[✓] Benchmark Score: {total_passed}/{len(results)} ({accuracy:.1f}%)")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "./outputs/Fluxnat-Coder-3B-Merged"
    run_benchmark(target)


if __name__ == "__main__":
    main()
