# Fluxnat Coder 3B — Model Documentation

**[🤗 Hugging Face → k4ran909/Fluxnat-Coder-3B](https://huggingface.co/k4ran909/Fluxnat-Coder-3B)**

---

## What Is It

Fluxnat Coder 3B is a **3-billion parameter cybersecurity AI** built by Fluxnat. It performs autonomous source code vulnerability auditing — finding security flaws, explaining root causes, mapping to CWE/OWASP standards, and generating production-ready fixes.

**Key traits:**
- 🔓 **Uncensored** — No safety refusals. Will analyze any code, any vulnerability, any exploit pattern.
- ⚡ **Lightweight** — Runs on a GTX 1650 (4GB VRAM) in 4-bit quantization.
- 🧠 **Chain-of-Thought** — Explains *why* code is vulnerable, not just *that* it is.
- 🎯 **Security-Specialized** — Purpose-built for vulnerability detection, not general chat.

---

## What It Can Do (`v0.3.0`)

### 1. Multi-CWE Vulnerability Detection (30+ CWEs)
- **Injection:** SQL Injection (`CWE-89`), OS Command Injection (`CWE-78`), Code/Eval Injection (`CWE-94`/`95`), SSTI (`CWE-1336`), LDAP Injection (`CWE-90`), XPath Injection (`CWE-643`), NoSQL Injection (`CWE-943`)
- **Web & API:** Cross-Site Scripting / XSS (`CWE-79`), Server-Side Request Forgery / SSRF (`CWE-918`), Path Traversal (`CWE-22`), XXE (`CWE-611`), CSRF (`CWE-352`), Open Redirect (`CWE-601`), IDOR (`CWE-639`), Mass Assignment (`CWE-915`)
- **Memory & Binary:** Stack/Heap Buffer Overflow (`CWE-120`/`122`/`787`), Use-After-Free (`CWE-416`), Format String (`CWE-134`), Integer Overflow (`CWE-190`)
- **Auth & Crypto:** Insecure Deserialization (`CWE-502`), Hardcoded Credentials (`CWE-798`), Weak Cryptography (`CWE-327`/`328`), Improper Auth (`CWE-287`), Prototype Pollution (`CWE-1321`), Race Conditions (`CWE-362`)

### 2. Red Team & Offensive Security Reasoning
- **Multi-Step Exploit Chains:** Traces chained vulnerabilities (e.g., SSRF $\rightarrow$ Cloud Metadata $\rightarrow$ IAM Takeover, SQLi $\rightarrow$ File Read $\rightarrow$ RCE).
- **Verification Payload Generation:** Constructs targeted security test vectors (`SQLi`, `XSS`, `SSTI`, `SSRF`, `LFI`, `revshell`, `cmdi`).
- **MITRE ATT&CK Tactics:** Covers Linux/Windows Privilege Escalation (`T1068`, `T1548`), Persistence (`T1547`, `T1053`), and Active Directory Lateral Movement (`T1558.003` Kerberoasting, `T1550` Pass-the-Hash).
- **13-Tool ReAct Agent Mode:** Autonomously drives `recon`, `exploit_db`, `generate_payload`, `web_attack`, `post_exploit`, `scan_code`, and `fix_code` inside SmartAGENT.

### Supported Languages

| Language | Vulnerability Coverage |
|---|---|
| **Python** | SQLi, Command Injection, Path Traversal, Pickle/YAML Deserialization, SSRF, SSTI (`Jinja2`), Secrets |
| **JavaScript / Node.js** | DOM/Reflected XSS, `child_process.exec`, Prototype Pollution, NoSQLi, ReDoS, JWT |
| **Go** | SSRF, Unchecked errors, Path Traversal, Command execution, Race conditions |
| **C / C++** | Buffer overflows, Use-After-Free, Format strings, Integer overflows |
| **Java** | JNDI / Log4Shell (`CVE-2021-44228`), XXE, SQLi via JDBC/Hibernate, `ObjectInputStream` Deserialization |
| **PHP** | LFI/RFI, SQLi, `eval`, PHP Object Injection (`unserialize`), Type Juggling |
| **DevOps / AD** | Dockerfile misconfigs, `.env` leaks, Linux SUID/Sudo, Windows Services/Tokens, Active Directory |

### Output Format

For each vulnerability found, the model outputs:
- **Severity** — Critical / High / Medium / Low with CVSS score
- **CWE ID** — MITRE CWE identifier
- **OWASP Category** — Top 10 mapping
- **Root Cause** — Step-by-step taint flow analysis (Source → Sink)
- **Secure Fix** — Drop-in replacement code

---

## How to Use

### Python (transformers)

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "k4ran909/Fluxnat-Coder-3B"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)

SYSTEM_PROMPT = (
    "You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding "
    "intelligence model created by Fluxnat. Your mission is to perform rigorous "
    "source code vulnerability auditing, identify CWE and OWASP Top 10 security "
    "flaws, explain attack surfaces and root causes using detailed step-by-step "
    "reasoning, and provide production-ready secure remediations."
)

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": """Audit this code for vulnerabilities:

@app.route('/lookup')
def lookup():
    user = request.args.get('user')
    query = f"SELECT * FROM users WHERE name = '{user}'"
    return db.execute(query).fetchall()
"""},
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)

outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.2, top_p=0.95)
response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
print(response)
```

### 4-Bit Quantized (Low VRAM)

```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

model = AutoModelForCausalLM.from_pretrained(
    "k4ran909/Fluxnat-Coder-3B",
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
```

### vLLM (Production API Server)

```bash
python -m vllm.entrypoints.openai.api_server \
    --model k4ran909/Fluxnat-Coder-3B \
    --dtype float16 \
    --max-model-len 4096 \
    --port 8000
```

### SmartAGENT CLI (Easiest)

```bash
pip install -e .
smartagent chat          # Interactive agent
smartagent scan . --ai   # AI-verified scan
```

---

## Hardware Requirements

| Mode | VRAM | GPU Examples |
|---|---|---|
| 4-bit quantized | ~1.8 GB | GTX 1650, RTX 2060, T4 |
| 16-bit (float16) | ~6 GB | RTX 3060, RTX 4060, A10 |
| CPU only | 8+ GB RAM | Any modern CPU (slow) |

---

## License

Apache-2.0 — Free for commercial and non-commercial use.
