# 🛡️ SmartAGENT

**Autonomous AI Cybersecurity Agent** — powered by [Fluxnat Coder 3B](https://huggingface.co/k4ran909/Fluxnat-Coder-3B).

An agentic security AI that can autonomously scan codebases, find vulnerabilities, trace data flows, and generate fixes — all running locally on your GPU.

---

## 🌟 Highlights

- **🤖 Agentic Mode (`v0.3.0`):** ReAct reasoning loop (`Thought` → `Action` → `Observation`) with **13 security & red-team tools** and interactive CLI chat.
- **🧠 Fluxnat Coder 3B:** Custom fine-tuned 3B cybersecurity SLM trained on 568 multi-CWE, exploit chain, payload generation, ATT&CK, and ReAct tool-use sequences. Uncensored. Zero safety refusals. Built by Fluxnat.
- **🔴 Red Team Suite:** Built-in network reconnaissance (`recon`), CVE/exploit intelligence (`exploit_db`), payload generator (`generate_payload`), web attack surface auditor (`web_attack`), and post-exploitation advisor (`post_exploit`).
- **⚡ Hybrid Scanning:** 4 deterministic SAST scanners + AI Chain-of-Thought reasoning + security scoring (A+ to F).
- **🔧 60+ Terminal Commands:** The agent can run `git`, `curl`, `nmap`, `docker`, `semgrep`, and more — sandboxed.
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

### Agent Tools (13 Tools Total)

#### Defensive & Code Analysis Tools (8)
| Tool | Description |
|---|---|
| `list_files` | List code files in a directory (respects ignore rules) |
| `read_file` | Read file contents (with optional `:start-end` line ranges) |
| `search_code` | Regex search across the entire codebase |
| `scan_code` | Run all 4 static vulnerability scanners on a file |
| `get_cwe_info` | Look up detailed CWE vulnerability & remediation guidance |
| `write_report` | Generate structured JSON or Markdown vulnerability reports |
| `run_command` | Execute sandboxed shell commands (`git`, `python`, `nmap`, `curl`, etc.) |
| `fix_code` | Generate production-ready secure code remediations |

#### Red Team & Offensive Security Tools (5)
| Tool | Description |
|---|---|
| `recon` | Network reconnaissance & TCP port scanner (`nmap` wrapper + fast socket banner grabber) |
| `exploit_db` | Query known CVEs and exploit intelligence (`CVE-2021-44228`, `CVE-2017-0144`, `apache`, `ssh`, etc.) |
| `generate_payload` | Generate verification payloads (`sqli`, `xss`, `cmdi`, `revshell`, `ssti`, `ssrf`, `lfi`) |
| `web_attack` | Probe URLs for exposed sensitive files (`.env`, `.git`, `/swagger.json`) & missing HTTP security headers |
| `post_exploit` | Privilege escalation, persistence, and lateral movement auditing (`linux`, `windows`, `ad`) |

---

## 📁 Project Structure

```
smartAGENT/
├── smartagent/
│   ├── cli.py                  # CLI (chat, agent, scan, train, info)
│   ├── config.py               # Configuration
│   ├── agent/                  # ReAct Agent
│   │   ├── core.py             # Reasoning loop
│   │   ├── tools.py            # 13 security & red team tools + CWE/CVE databases
│   │   ├── memory.py           # Sliding-window conversation memory
│   │   └── prompts.py          # ReAct system prompts
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
├── data/
│   └── custom_cot/             # Security, Red Team, Identity & ReAct datasets
├── docs/
│   ├── model.md                # Model documentation & usage
│   └── benchmarks.md           # Evaluation scorecard & training metrics
├── scripts/                    # Dataset generation & Colab training pipelines
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
