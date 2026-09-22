#!/usr/bin/env python3
"""
Comprehensive Multi-Benchmark Evaluation Suite for Fluxnat Coder 3B.

Benchmark Categories:
1. Multi-Language CWE Detection Benchmark (Python, JS, Java, C, PHP, Go)
2. False Positive Resistance Benchmark (Clean, Benign, and Securely Written Code)
3. Secure Remediation & Patch Benchmark (Drop-in fix generation)
4. Cyber Threat Intelligence & Analysis Benchmark (Explaining attack mechanisms & defense)
"""

import sys
import os
import time
import json
import torch
from typing import List, Dict, Any
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "k4ran909/Fluxnat-Coder-3B"

SYSTEM_PROMPT = (
    "You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat. "
    "Your mission is to perform rigorous source code vulnerability auditing, identify CWE and OWASP Top 10 security flaws, "
    "explain attack surfaces and root causes using detailed step-by-step reasoning, and provide production-ready secure remediations."
)

# =====================================================================
# BENCHMARK 1: Multi-Language CWE Vulnerability Detection Benchmark
# =====================================================================
CWE_DETECTION_CASES = [
    {
        "id": "CWE-TC1",
        "lang": "Python",
        "name": "SQL Injection in User Query",
        "expected_cwe": "CWE-89",
        "code": """def fetch_user_record(db, username):
    cursor = db.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()"""
    },
    {
        "id": "CWE-TC2",
        "lang": "JavaScript (Node.js)",
        "name": "OS Command Injection via Child Process",
        "expected_cwe": "CWE-78",
        "code": """const { exec } = require('child_process');
app.get('/ping', (req, res) => {
    const host = req.query.host;
    exec(`ping -c 4 ${host}`, (err, stdout) => {
        res.send(stdout);
    });
});"""
    },
    {
        "id": "CWE-TC3",
        "lang": "Go",
        "name": "Path Traversal in Static File Serving",
        "expected_cwe": "CWE-22",
        "code": """func serveDoc(w http.ResponseWriter, r *http.Request) {
    fileName := r.URL.Query().Get("doc")
    data, err := ioutil.ReadFile("/var/www/docs/" + fileName)
    if err != nil {
        http.Error(w, "File not found", 404)
        return
    }
    w.Write(data)
}"""
    },
    {
        "id": "CWE-TC4",
        "lang": "Java",
        "name": "Insecure Deserialization via ObjectInputStream",
        "expected_cwe": "CWE-502",
        "code": """public Object processSerializedData(byte[] incomingBytes) throws Exception {
    ByteArrayInputStream bais = new ByteArrayInputStream(incomingBytes);
    ObjectInputStream ois = new ObjectInputStream(bais);
    return ois.readObject();
}"""
    },
    {
        "id": "CWE-TC5",
        "lang": "PHP",
        "name": "Reflected Cross-Site Scripting (XSS)",
        "expected_cwe": "CWE-79",
        "code": """<?php
$search = $_GET['q'];
echo "<h1>Search results for: " . $search . "</h1>";
?>"""
    },
    {
        "id": "CWE-TC6",
        "lang": "Python",
        "name": "Server-Side Request Forgery (SSRF)",
        "expected_cwe": "CWE-918",
        "code": """import requests
@app.route('/fetch-avatar')
def fetch_avatar():
    image_url = request.args.get('url')
    response = requests.get(image_url, timeout=5)
    return response.content"""
    },
    {
        "id": "CWE-TC7",
        "lang": "C",
        "name": "Buffer Overflow via Unbounded String Copy",
        "expected_cwe": "CWE-120",
        "code": """void copy_user_token(const char *token) {
    char local_buffer[64];
    strcpy(local_buffer, token);
}"""
    },
    {
        "id": "CWE-TC8",
        "lang": "Python",
        "name": "Hardcoded AWS API Secret Key",
        "expected_cwe": "CWE-798",
        "code": """AWS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def init_s3():
    return boto3.client('s3', aws_access_key_id=AWS_KEY_ID, aws_secret_access_key=AWS_SECRET)"""
    }
]

# =====================================================================
# BENCHMARK 2: False Positive Resistance Benchmark (Clean & Benign Code)
# =====================================================================
BENIGN_CODE_CASES = [
    {
        "id": "BEN-TC1",
        "lang": "Python",
        "name": "Parameterized SQL Query with Psycopg2",
        "code": """def get_account(cursor, account_id: int):
    query = "SELECT id, balance, status FROM accounts WHERE id = %s AND active = %s"
    cursor.execute(query, (account_id, True))
    return cursor.fetchone()"""
    },
    {
        "id": "BEN-TC2",
        "lang": "Python",
        "name": "Safe Subprocess with Argument List (No Shell)",
        "code": """import subprocess

def run_git_status(repo_dir: str):
    result = subprocess.run(
        ["git", "-C", repo_dir, "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout"""
    },
    {
        "id": "BEN-TC3",
        "lang": "Go",
        "name": "Safe File Serving with filepath.Clean and Boundary Check",
        "code": """func safeServe(w http.ResponseWriter, r *http.Request) {
    const baseDir = "/var/www/uploads"
    relPath := filepath.Clean(r.URL.Query().Get("file"))
    fullPath := filepath.Join(baseDir, relPath)
    if !strings.HasPrefix(fullPath, filepath.Clean(baseDir)+string(filepath.Separator)) {
        http.Error(w, "Access Denied", 403)
        return
    }
    http.ServeFile(w, r, fullPath)
}"""
    },
    {
        "id": "BEN-TC4",
        "lang": "JavaScript",
        "name": "Safe HTML Output Encoding via DOM Element TextContent",
        "code": """function displayUserName(userInput) {
    const container = document.getElementById('user-display');
    const safeNode = document.createElement('span');
    safeNode.textContent = userInput;
    container.appendChild(safeNode);
}"""
    }
]

# =====================================================================
# BENCHMARK 3: Remediation & Patch Quality Benchmark
# =====================================================================
REMEDIATION_CASES = [
    {
        "id": "REM-TC1",
        "name": "Remediation for Python eval() Dynamic Execution",
        "code": """def calculate_formula(user_expr):
    # Vulnerable calculation endpoint
    return eval(user_expr)"""
    },
    {
        "id": "REM-TC2",
        "name": "Remediation for Weak Cryptographic Hash (MD5 for Passwords)",
        "code": """import hashlib

def store_password(username, plain_password):
    hashed = hashlib.md5(plain_password.encode()).hexdigest()
    db.save_user(username, hashed)"""
    }
]


def load_model():
    print("=" * 80)
    print(f"[*] Loading Fluxnat Coder 3B from Hub / Cache: {MODEL_ID}")
    print(f"[*] PyTorch Version: {torch.__version__} | CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[*] GPU: {torch.cuda.get_device_name(0)}")
    print("=" * 80)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    model.eval()
    return tokenizer, model


def query_model(tokenizer, model, user_prompt: str, max_tokens: int = 350) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.1,
            top_p=0.9,
            repetition_penalty=1.05,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    return tokenizer.decode(output_tokens[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def run_benchmarks():
    tokenizer, model = load_model()
    print("\n[+] Model successfully initialized for benchmarking.\n")

    overall_results = {
        "cwe_detection": [],
        "false_positive": [],
        "remediation": []
    }

    # =================================================================
    # RUN BENCHMARK 1: CWE Detection & Classification
    # =================================================================
    print("\n" + "=" * 80)
    print(" BENCHMARK SUITE 1: Multi-Language CWE Vulnerability Detection & Identification")
    print("=" * 80)
    print(f"{'ID':<9} | {'Lang':<8} | {'Test Scenario':<30} | {'Expected':<9} | {'Result':<10} | {'Status'}")
    print("-" * 80)

    for tc in CWE_DETECTION_CASES:
        prompt = (
            f"Perform a rigorous cybersecurity vulnerability assessment of this {tc['lang']} code snippet.\n"
            f"Determine if it is VULNERABLE or BENIGN.\n"
            f"If vulnerable, state the exact CWE identifier (e.g., CWE-89, CWE-78) and provide brief reasoning.\n\n"
            f"```{tc['lang'].lower()}\n{tc['code']}\n```"
        )
        t0 = time.time()
        resp = query_model(tokenizer, model, prompt, max_tokens=250)
        dur = time.time() - t0

        resp_lower = resp.lower()
        is_vuln_detected = ("vulnerable" in resp_lower or "security flaw" in resp_lower or "critical" in resp_lower) and ("not vulnerable" not in resp_lower and "benign" not in resp_lower)
        expected_cwe_num = tc["expected_cwe"].split("-")[-1]
        cwe_matched = (tc["expected_cwe"].lower() in resp_lower) or (f"cwe {expected_cwe_num}" in resp_lower) or (f"cwe-{expected_cwe_num}" in resp_lower)

        passed = is_vuln_detected and cwe_matched
        status = "PASSED [OK]" if passed else "FAILED [X]"

        cwe_found_str = tc["expected_cwe"] if cwe_matched else ("DETECTED" if is_vuln_detected else "MISSED")

        print(f"{tc['id']:<9} | {tc['lang'][:8]:<8} | {tc['name'][:30]:<30} | {tc['expected_cwe']:<9} | {cwe_found_str:<10} | {status} ({dur:.1f}s)")
        overall_results["cwe_detection"].append({
            "id": tc["id"],
            "name": tc["name"],
            "passed": passed,
            "response": resp[:250]
        })

    # =================================================================
    # RUN BENCHMARK 2: False Positive Resistance (Benign Code)
    # =================================================================
    print("\n" + "=" * 80)
    print(" BENCHMARK SUITE 2: False Positive Resistance Benchmark (Clean & Safe Code)")
    print("=" * 80)
    print(f"{'ID':<9} | {'Lang':<8} | {'Scenario':<35} | {'Classification':<15} | {'Status'}")
    print("-" * 80)

    for tc in BENIGN_CODE_CASES:
        prompt = (
            f"Analyze this {tc['lang']} code snippet for security vulnerabilities.\n"
            f"Classify it strictly as either VULNERABLE or BENIGN/SECURE. Explain your reasoning.\n\n"
            f"```{tc['lang'].lower()}\n{tc['code']}\n```"
        )
        t0 = time.time()
        resp = query_model(tokenizer, model, prompt, max_tokens=250)
        dur = time.time() - t0

        resp_lower = resp.lower()
        # Benign is passed if model recognizes it as benign/secure and does not report a false positive vulnerability
        is_classified_secure = (
            ("benign" in resp_lower or "secure" in resp_lower or "safe" in resp_lower or "not vulnerable" in resp_lower or "no vulnerability" in resp_lower)
            and ("is vulnerable" not in resp_lower and "critical" not in resp_lower)
        )

        passed = is_classified_secure
        status = "PASSED [OK]" if passed else "FAILED [X]"
        cls_str = "BENIGN / SAFE" if is_classified_secure else "FALSE POSITIVE"

        print(f"{tc['id']:<9} | {tc['lang'][:8]:<8} | {tc['name'][:35]:<35} | {cls_str:<15} | {status} ({dur:.1f}s)")
        overall_results["false_positive"].append({
            "id": tc["id"],
            "name": tc["name"],
            "passed": passed,
            "response": resp[:250]
        })

    # =================================================================
    # RUN BENCHMARK 3: Remediation & Patch Generation
    # =================================================================
    print("\n" + "=" * 80)
    print(" BENCHMARK SUITE 3: Secure Code Remediation & Patch Generation Benchmark")
    print("=" * 80)

    for tc in REMEDIATION_CASES:
        prompt = (
            f"Perform a security remediation on the following vulnerable code snippet.\n"
            f"1. Name the vulnerability and CWE ID.\n"
            f"2. Provide a production-ready, secure refactored code replacement.\n"
            f"3. Explain why the replacement eliminates the risk.\n\n"
            f"```python\n{tc['code']}\n```"
        )
        print(f"\n[*] Evaluating: {tc['name']}")
        t0 = time.time()
        resp = query_model(tokenizer, model, prompt, max_tokens=400)
        dur = time.time() - t0

        has_code_block = "```" in resp
        has_explanation = len(resp) > 100
        passed = has_code_block and has_explanation
        status = "PASSED [OK]" if passed else "FAILED [X]"

        print(f"Result: {status} (Completed in {dur:.1f}s)")
        print("-" * 60)
        print(resp)
        print("-" * 60)
        overall_results["remediation"].append({
            "id": tc["id"],
            "name": tc["name"],
            "passed": passed,
            "response": resp
        })

    # =================================================================
    # SCORECARD & SUMMARY METRICS
    # =================================================================
    cwe_total = len(overall_results["cwe_detection"])
    cwe_passed = sum(1 for r in overall_results["cwe_detection"] if r["passed"])
    cwe_acc = (cwe_passed / cwe_total) * 100

    fp_total = len(overall_results["false_positive"])
    fp_passed = sum(1 for r in overall_results["false_positive"] if r["passed"])
    fp_acc = (fp_passed / fp_total) * 100

    rem_total = len(overall_results["remediation"])
    rem_passed = sum(1 for r in overall_results["remediation"] if r["passed"])
    rem_acc = (rem_passed / rem_total) * 100

    grand_total = cwe_total + fp_total + rem_total
    grand_passed = cwe_passed + fp_passed + rem_passed
    overall_score = (grand_passed / grand_total) * 100

    print("\n" + "=" * 80)
    print("                  FINAL BENCHMARK SCORECARD - FLUXNAT CODER 3B             ")
    print("=" * 80)
    print(f"1. Multi-Language CWE Detection Benchmark : {cwe_passed}/{cwe_total}  ({cwe_acc:.1f}%)")
    print(f"2. False Positive Resistance Benchmark    : {fp_passed}/{fp_total}  ({fp_acc:.1f}%)")
    print(f"3. Secure Code Remediation Benchmark      : {rem_passed}/{rem_total}  ({rem_acc:.1f}%)")
    print("-" * 80)
    print(f"OVERALL BENCHMARK ACCURACY               : {grand_passed}/{grand_total} ({overall_score:.1f}%)")
    print("=" * 80)

    # Save benchmark results to JSON
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "model": MODEL_ID,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cwe_detection_accuracy": cwe_acc,
            "false_positive_resistance": fp_acc,
            "remediation_accuracy": rem_acc,
            "overall_score": overall_score,
            "details": overall_results
        }, f, indent=2)
    print("[+] Detailed benchmark metrics saved to benchmark_results.json")


if __name__ == "__main__":
    run_benchmarks()
