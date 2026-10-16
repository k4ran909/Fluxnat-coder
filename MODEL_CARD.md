---
language:
- en
- code
license: apache-2.0
tags:
- cybersecurity
- vulnerability-detection
- sast
- security-audit
- code-security
- cwe
- owasp
- unsloth
- code-analysis
- penetration-testing
- secure-coding
pipeline_tag: text-generation
library_name: transformers
widget:
- text: |
    <|im_start|>system
    You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat. Your mission is to perform rigorous source code vulnerability auditing, identify CWE and OWASP Top 10 security flaws, explain attack surfaces and root causes using detailed step-by-step reasoning, and provide production-ready secure remediations.<|im_end|>
    <|im_start|>user
    Audit this Python code for vulnerabilities:
    @app.route('/lookup')
    def lookup():
        user = request.args.get('user')
        query = f"SELECT * FROM users WHERE name = '{user}'"
        return db.execute(query).fetchall()<|im_end|>
    <|im_start|>assistant
  example_title: SQL Injection Audit
---

<div align="center">

# 🛡️ Fluxnat Coder 3B

### *Autonomous Cybersecurity Intelligence & Source Code Vulnerability Auditor*

[![Model License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Parameters](https://img.shields.io/badge/Parameters-3B-green.svg)](https://huggingface.co/k4ran909/Fluxnat-Coder-3B)
[![Domain](https://img.shields.io/badge/Domain-Cybersecurity%20Auditing-red.svg)](https://huggingface.co/k4ran909/Fluxnat-Coder-3B)
[![Fine-Tuned with](https://img.shields.io/badge/Fine--Tuned%20with-Unsloth%202x%20Faster-orange.svg)](https://github.com/unslothai/unsloth)
[![Context Window](https://img.shields.io/badge/Context-128K%20Tokens-yellow.svg)](https://huggingface.co/k4ran909/Fluxnat-Coder-3B)

</div>

---

## 📌 Overview

**Fluxnat Coder 3B** is a specialized, high-precision cybersecurity and code security intelligence model developed by **Fluxnat**. 
Engineered for static analysis and fine-tuned using **Unsloth (QLoRA)** on curated vulnerability datasets, threat intelligence corpora, and structured Chain-of-Thought (CoT) security audit trajectories, **Fluxnat Coder 3B** acts as an autonomous Static Application Security Testing (SAST) analyst and secure code reviewer.

Unlike generic code models that frequently trigger false safety refusals when auditing real-world security vulnerabilities, **Fluxnat Coder 3B** is completely refusal-free for authorized defensive security analysis, penetration testing verification, and automated vulnerability triage.

---

## 🚀 Key Capabilities (`v0.3.0` Red Team Edition)

- **🔍 Taint Flow & Root Cause Analysis:** Tracks untrusted input from **Source $\rightarrow$ Sanitizer $\rightarrow$ Sink** with explicit causality.
- **🏷️ 30+ CWE & OWASP Top 10 Mapping:** Maps discovered flaws across 30+ MITRE CWE identifiers (`CWE-89`, `CWE-78`, `CWE-22`, `CWE-79`, `CWE-502`, `CWE-918`, `CWE-611`, `CWE-798`, `CWE-1321`, `CWE-1336`, `CWE-362`, `CWE-416`, etc.) and OWASP categories.
- **🔴 Offensive Security & Red Team Reasoning:** Analyzes multi-step exploit chains, payload construction (`SQLi`, `XSS`, `SSTI`, `SSRF`, `LFI`, reverse shells), and MITRE ATT&CK techniques (`T1558.003` Kerberoasting, `T1068` Privilege Escalation, `T1547` Persistence, `T1550` Lateral Movement).
- **🤖 Autonomous ReAct Agent Integration:** Powers the [**SmartAGENT**](https://github.com/k4ran909/smartAGENT) 13-tool security agent (`recon`, `exploit_db`, `generate_payload`, `web_attack`, `post_exploit`, `scan_code`, `fix_code`, etc.).
- **🛡️ Production-Ready Secure Fixes:** Generates drop-in replacements with parameterized queries, safe execution APIs, and canonicalized path operations.
- **⚡ Ultra-Low Latency & Minimal Footprint:** At 3 billion parameters, it fits comfortably into consumer GPUs (4 GB VRAM in 4-bit) and edge environments.

---

## 🌐 Supported Programming Languages & Stacks

| Ecosystem | Vulnerabilities Covered |
| :--- | :--- |
| **Python** | SQLi, Command Injection, Path Traversal, Insecure Deserialization (`pickle`/`yaml`), SSRF, SSTI (`Jinja2`), Hardcoded Secrets |
| **JavaScript / TypeScript / Node.js** | DOM/Reflected XSS, `child_process.exec`, Prototype Pollution (`CWE-1321`), NoSQL Injection (`CWE-943`), ReDoS, JWT |
| **Go** | Unchecked errors, SSRF (`http.Get`), Path Traversal, Command execution, Race conditions (`CWE-362`) |
| **C / C++** | Stack/Heap Buffer Overflows (`CWE-120`/`122`/`787`), Use-After-Free (`CWE-416`), Format Strings (`CWE-134`), Integer Overflows (`CWE-190`) |
| **Java** | JNDI / Log4Shell (`CVE-2021-44228`), XML External Entity / XXE (`CWE-611`), SQLi via Hibernate/JDBC, `ObjectInputStream` Deserialization (`CWE-502`) |
| **PHP** | File inclusion (`LFI`/`RFI`), SQLi, `eval` injection, PHP Object Injection (`unserialize`), Type Juggling |
| **Infrastructure / Active Directory** | Dockerfile root user, `.env` secret leaks, Linux SUID/Sudo Privesc, Windows Service/Token Privesc, AD Kerberoasting & ACL abuse |

---

## 💻 Quickstart Inference

### 1. Using Hugging Face `transformers`

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "k4ran909/Fluxnat-Coder-3B"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

messages = [
    {
        "role": "system",
        "content": (
            "You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat. "
            "Your mission is to perform rigorous source code vulnerability auditing, identify CWE and OWASP Top 10 security flaws, "
            "explain attack surfaces and root causes using detailed step-by-step reasoning, and provide production-ready secure remediations."
        )
    },
    {
        "role": "user",
        "content": """Audit this Node.js endpoint for vulnerabilities:

app.get('/ping', (req, res) => {
    const host = req.query.host;
    exec(`ping -c 3 ${host}`, (err, stdout) => {
        res.send(stdout);
    });
});"""
    }
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)

outputs = model.generate(
    **inputs,
    max_new_tokens=512,
    temperature=0.2,
    top_p=0.95
)

response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
print(response)
```

---

## 🛠️ Serving with vLLM (Production & API)

Run an OpenAI-compatible high-throughput inference server:

```bash
python -m vllm.entrypoints.openai.api_server \
    --model k4ran909/Fluxnat-Coder-3B \
    --dtype float16 \
    --max-model-len 4096 \
    --port 8000
```

---

## ⚙️ Training Details (`v0.3.0`)

| Hyperparameter | Value |
| :--- | :--- |
| **Architecture** | 3B Parameter Dense Decoder-Only Transformer |
| **Fine-Tuning Framework** | **Unsloth** + TRL `SFTTrainer` |
| **Method** | QLoRA (4-bit Quantization with 16-bit LoRA Adapters, Merged to 16-bit Float) |
| **Dataset Composition** | 568 balanced sequences (170 Red Team CoT, 24 Multi-Lang Audits, 16 ReAct Tool Trajectories, 15 Identity Alignment) |
| **LoRA Rank ($r$)** | `64` |
| **LoRA Alpha ($\alpha$)** | `128` |
| **Target Modules** | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| **Learning Rate** | `8e-5` (Cosine Scheduler, 65 Steps, Final Loss `0.8952`) |
| **Effective Batch Size** | `8` (Batch size 2 $\times$ Gradient Accumulation 4) |
| **Sequence Length** | `4,096` tokens |
| **Hardware** | 1x NVIDIA Tesla T4 GPU (16 GB VRAM) |
| **Optimizer** | `adamw_8bit` |

---

## ⚖️ Responsible Use & Ethical Policy

**Fluxnat Coder 3B** is designed and released exclusively for:
- ✅ Defensive software security auditing and continuous integration code reviews
- ✅ Assisting development teams in finding and patching security flaws before deployment
- ✅ Educational and academic cybersecurity research
- ❌ Unauthorized penetration testing or attacking systems without explicit written consent is strictly prohibited.

---

<div align="center">

**Developed with ❤️ by Fluxnat**  
*Next-Generation AI for Cyber Defense*

</div>
