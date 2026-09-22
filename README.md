# 🛡️ SmartAGENT & Fluxnat Coder 3B

An AI-powered cybersecurity vulnerability scanner and specialized 3B Small Language Model (SLM) fine-tuning suite for autonomous source code security audits.

---

## 🌟 Highlights

- **🤖 Autonomous Agentic Security Mode:** ReAct reasoning loop (Thought → Action → Observation) powered by Fluxnat Coder 3B with 8 security tools and interactive CLI chat.
- **🧠 Fluxnat Coder 3B:** Specialized cybersecurity Small Language Model (SLM) trained and developed by Fluxnat. Refusal-free for security assessment and vulnerability analysis. Available on Hugging Face at [`k4ran909/Fluxnat-Coder-3B`](https://huggingface.co/k4ran909/Fluxnat-Coder-3B).
- **⚡ Hybrid Architecture:** Deterministic SAST Scanners (Secrets, Patterns, Dependencies, Configs) + AI Chain-of-Thought Judge + ReAct Agent Tools.
- **☁️ 1-Click Google Colab Training:** Includes `Fluxnat_Coder_3B_Training.ipynb` configured with **Unsloth (2x faster, 70% less VRAM)** to train on a **free Tesla T4 GPU (16GB VRAM)**.
- **📊 Precision Security Grading:** Computes vulnerability deduction index (0–100) and letter grades (A+ to F).
- **🔧 Interactive CLI:** Chat directly with the agent via `smartagent chat` or scan via `smartagent scan .`.

---

## 📁 Repository Structure

```
smartAGENT/
├── Fluxnat_Coder_3B_Training.ipynb   # 1-Click Google Colab Training Notebook
├── pyproject.toml                     # Dependencies & package metadata
├── prepare_datasets.py                # Dataset download, cleaning & formatting
├── train.py                           # Unsloth / PEFT QLoRA training engine
├── rebrand.py                         # Deep config & metadata rebranding engine
├── merge_and_export.py                # 16-bit standalone merge & GGUF export
├── evaluate.py                        # Benchmark suite on vulnerable & benign code
├── config/
│   └── training_config.yaml           # Hyperparameters & dataset configs
├── data/
│   └── custom_cot/
│       └── security_cot.jsonl         # Curated Chain-of-Thought security reasoning
├── smartagent/                        # Core Scanner & Agent Package
│   ├── cli.py                         # Typer CLI application (chat, agent, scan, train, info)
│   ├── config.py                      # Scanner & Agent configuration
│   ├── agent/                         # Autonomous ReAct Agent Module
│   │   ├── core.py                    # ReAct reasoning loop (Thought → Action → Observation)
│   │   ├── tools.py                   # 8 Security tools + CWE knowledge base
│   │   ├── memory.py                  # Sliding-window conversation memory
│   │   └── prompts.py                 # ReAct system prompt & templates
│   ├── scanners/
│   │   ├── secret_scanner.py          # API keys, tokens, private keys
│   │   ├── pattern_scanner.py         # SQLi, RCE, Deserialization, XSS
│   │   ├── dependency_scanner.py      # CVE lookups via OSV.dev
│   │   └── config_scanner.py          # Dockerfiles, .env misconfigurations
│   ├── ai/
│   │   ├── model.py                   # Model loader & token streaming
│   │   ├── judge.py                   # AI verification & fix generation
│   │   └── prompts.py                 # Chain-of-thought prompt templates
│   └── reporting/
│       ├── report.py                  # Rich terminal UI & exports
│       └── scorer.py                  # Security score (A+ to F)
└── tests/
    └── test_scanners.py               # Unit tests
```

---

## 🚀 Quick Start: Training Fluxnat Coder 3B

### Option A: Google Colab (Recommended - Free GPU)
1. Open [Google Colab](https://colab.research.google.com).
2. Upload `Fluxnat_Coder_3B_Training.ipynb`.
3. Set runtime to **GPU (T4)**.
4. Run all cells — it will automatically train, merge, and upload `k4ran909/Fluxnat-Coder-3B` to Hugging Face!

### Option B: Local Training
```bash
# 1. Install dependencies
pip install -e .

# 2. Prepare datasets
python prepare_datasets.py

# 3. Launch training
python train.py

# 4. Merge adapters and export standalone model
python merge_and_export.py

# 5. Benchmark the model
python evaluate.py
```

---

## 🤖 Agentic Mode & Scanning

### 1. Interactive Agent Chat (ReAct Loop)
Engage in an interactive terminal session where the agent can autonomously think, explore files, run security tools, and remediate flaws:
```bash
smartagent chat
```

### 2. Autonomous One-Shot Task
Run a direct agentic task from your terminal:
```bash
smartagent agent "scan this project for SQL injection and suggest fixes"
```

### 3. Classic Static Scan (Fast Pass)
```bash
smartagent scan /path/to/your/project
```

### 4. AI-Verified Scan
Uses Fluxnat Coder 3B to eliminate false positives and generate exact fix snippets:
```bash
smartagent scan /path/to/your/project --ai
```

### 5. Export Reports (JSON & Markdown)
```bash
smartagent scan /path/to/your/project --json report.json --md report.md
```

### 6. Check Environment Status
```bash
smartagent info
```

---

## ⚖️ License & Ethical Use

SmartAGENT and Fluxnat Coder 3B are licensed under the **Apache-2.0 License**.
Designed for defensive security auditing, vulnerability triage, and authorized penetration testing.
