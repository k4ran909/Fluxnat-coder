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

## What It Can Do

### Vulnerability Detection
- SQL Injection (CWE-89)
- OS Command Injection (CWE-78)
- Path Traversal (CWE-22)
- Cross-Site Scripting / XSS (CWE-79)
- Insecure Deserialization (CWE-502)
- Server-Side Request Forgery / SSRF (CWE-918)
- Buffer Overflow (CWE-122)
- Hardcoded Credentials (CWE-798)
- Eval/Exec Injection (CWE-95)
- Weak Cryptography (CWE-327/328)

### Supported Languages

| Language | Vulnerability Coverage |
|---|---|
| **Python** | SQLi, Command Injection, Path Traversal, Pickle/YAML Deserialization, SSRF, Secrets |
| **JavaScript / Node.js** | DOM XSS, `child_process.exec`, Prototype Pollution, ReDoS, JWT |
| **Go** | SSRF, Unchecked errors, Command execution, Race conditions |
| **C / C++** | Buffer overflows, Use-After-Free, Format strings, Integer overflows |
| **Java** | JNDI Injection, XXE, SQLi via JDBC/Hibernate, Deserialization |
| **PHP** | LFI/RFI, SQLi, `eval`, Object injection |
| **DevOps** | Dockerfile misconfigs, exposed ports, `.env` leaks |

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
