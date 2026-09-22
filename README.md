# 🛡️ SmartAGENT

**Autonomous AI Cybersecurity Agent** — powered by [Fluxnat Coder 3B](https://huggingface.co/k4ran909/Fluxnat-Coder-3B).

An agentic security AI that can autonomously scan codebases, find vulnerabilities, trace data flows, and generate fixes — all running locally on your GPU.

---

## 🌟 Highlights

- **🤖 Agentic Mode:** ReAct reasoning loop (Thought → Action → Observation) with 8 security tools and interactive CLI chat.
- **🧠 Fluxnat Coder 3B:** Custom fine-tuned 3B cybersecurity SLM. Uncensored. No safety filters. Built by Fluxnat.
- **⚡ Hybrid Scanning:** 4 deterministic SAST scanners + AI Chain-of-Thought reasoning + security scoring (A+ to F).
- **🔧 60+ Terminal Commands:** The agent can run git, curl, nmap, docker, semgrep, and more — sandboxed.
- **💻 Runs Locally:** 4-bit quantization fits on a GTX 1650 (4GB VRAM). No cloud API needed.

---

## 🚀 Quick Start

```bash
# Install
pip install -e .

# Interactive agent chat
smartagent chat

# One-shot autonomous task
smartagent agent "scan this project for SQL injection and suggest fixes"

# Classic static scan
smartagent scan .

# AI-verified scan (uses Fluxnat Coder 3B)
smartagent scan . --ai

# Export reports
smartagent scan . --json report.json --md report.md

# System info
smartagent info
```

---

## 🤖 Agentic Mode

Chat with SmartAGENT like a real security engineer:

```
You ▶ scan this project for vulnerabilities

💭 Thought: I'll start by listing all files in the project...
⚡ Action: list_files .
📋 Observation: Found 41 files...

💭 Thought: Let me read app.py first...
⚡ Action: read_file app.py
📋 Observation: [file contents]

💭 Thought: Line 34 uses f-string interpolation in a SQL query — CWE-89...
⚡ Action: scan_code app.py
📋 Observation: [CRITICAL] SQL Injection — CWE-89, CVSS 9.8

✅ Final Answer: Found 3 vulnerabilities...
```

### Agent Tools

| Tool | Description |
|---|---|
| `list_files` | List code files in a directory |
| `read_file` | Read file contents (with line ranges) |
| `search_code` | Regex search across the codebase |
| `scan_code` | Run static vulnerability scanners |
| `get_cwe_info` | Look up CWE vulnerability details |
| `write_report` | Generate JSON/Markdown reports |
| `run_command` | Execute sandboxed shell commands |
| `fix_code` | Generate secure code remediations |

---

## 📁 Project Structure

```
smartAGENT/
├── smartagent/
│   ├── cli.py                  # CLI (chat, agent, scan, train, info)
│   ├── config.py               # Configuration
│   ├── agent/                  # ReAct Agent
│   │   ├── core.py             # Reasoning loop
│   │   ├── tools.py            # 8 security tools + CWE database
│   │   ├── memory.py           # Conversation memory
│   │   └── prompts.py          # System prompts
│   ├── scanners/               # Static Analysis
│   │   ├── pattern_scanner.py  # SQLi, RCE, XSS, Deserialization
│   │   ├── secret_scanner.py   # API keys, tokens, credentials
│   │   ├── dependency_scanner.py # CVE lookups via OSV.dev
│   │   └── config_scanner.py   # Dockerfile & .env misconfigs
│   ├── ai/                     # LLM Engine
│   │   ├── model.py            # Model loader & streaming
│   │   ├── judge.py            # AI verification & fix generation
│   │   └── prompts.py          # CoT prompt templates
│   └── reporting/              # Output
│       ├── report.py           # Rich terminal UI & exports
│       └── scorer.py           # Security grading (A+ to F)
├── pyproject.toml
└── tests/
```

---

## 🔧 Training (Optional)

If you want to retrain or fine-tune the model yourself:

**Google Colab (Free T4 GPU):** Upload `Fluxnat_Coder_3B_Training.ipynb` → Run all cells.

**Local:**
```bash
python prepare_datasets.py
python train.py
python merge_and_export.py
```

---

## ⚖️ License

Apache-2.0 — Built for defensive security auditing and authorized penetration testing.
