# SmartAGENT v0.3.0 — Agentic Security & Red Team Suite Walkthrough

## Overview

SmartAGENT (`v0.3.0`) combines a **4-scanner deterministic SAST engine**, a **13-tool autonomous ReAct security & red-team agent**, and **Fluxnat Coder 3B** (`k4ran909/Fluxnat-Coder-3B`) — a 3.09B-parameter uncensored cybersecurity LLM trained on **568 balanced Chain-of-Thought sequences**.

```
smartagent chat                          → interactive ReAct agent with 13 offensive & defensive tools
smartagent agent "audit this project"    → one-shot autonomous security task execution
smartagent scan . --ai                   → 4 static scanners + AI deep verification + A+ to F security grade
smartagent info                          → system, CUDA/VRAM, scanner, and agent tool status
```

---

## 1. Complete 13-Tool ReAct Registry ([`smartagent/agent/tools.py`](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/smartagent/agent/tools.py))

### Defensive & Code Auditing Tools (8)
| Tool | Description |
|---|---|
| `list_files` | Recursively lists source code and config files in a project directory |
| `read_file` | Reads file contents with line numbers and optional `:start-end` range |
| `search_code` | Regex search across all code files (capped at 50 matches) |
| `scan_code` | Runs all 4 static scanners (`SecretScanner`, `PatternScanner`, `DependencyScanner`, `ConfigScanner`) |
| `get_cwe_info` | Queries embedded CWE knowledge base (CVSS, OWASP Top 10 mapping, remediation) |
| `write_report` | Writes structured Markdown or JSON vulnerability audit reports |
| `run_command` | Sandboxed shell execution (`git`, `python`, `pip`, `npm`, `bandit`, `semgrep`) |
| `fix_code` | Generates drop-in remediation templates for a CWE + vulnerable snippet |

### Offensive & Red Team Tools (5)
| Tool | Description |
|---|---|
| `recon` | Network reconnaissance & TCP port scanner (`nmap -sV` wrapper + fast socket banner-grabbing fallback) |
| `exploit_db` | Offline CVE & exploit advisory lookup (20+ critical CVEs: Log4Shell, EternalBlue, Spring4Shell, Zerologon, regreSSHion, PrintNightmare, Dirty Pipe, ProxyLogon) |
| `generate_payload` | Security audit verification payload generator across 7 categories (`sqli`, `xss`, `cmdi`, `revshell`, `ssti`, `ssrf`, `lfi`) |
| `web_attack` | Web attack surface discovery (`endpoints` probing for `/.env`, `/.git/HEAD`, `/actuator/env`, `/swagger.json` + HTTP security `headers` audit) |
| `post_exploit` | Post-exploitation enumeration, persistence detection, and lateral movement audit checklists for `linux`, `windows`, and `ad` (MITRE ATT&CK mapped) |

---

## 2. Dataset & Retraining Pipeline (`v0.3.0`)

### 4-Pillar Dataset ([`prepare_datasets.py`](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/prepare_datasets.py))
- **[`data/custom_cot/security_cot.jsonl`](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/data/custom_cot/security_cot.jsonl):** 24 deep vulnerability audit cases $\times 5 = 120$ sequences
- **[`data/custom_cot/redteam_cot.jsonl`](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/data/custom_cot/redteam_cot.jsonl):** 170 offensive security, exploit chain, payload, 30+ CWE, MITRE ATT&CK & benign control cases $\times 2 = 340$ sequences
- **[`data/custom_cot/react_tool_cot.jsonl`](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/data/custom_cot/react_tool_cot.jsonl):** 16 multi-turn ReAct tool-calling trajectories across all 13 tools $\times 2 = 32$ sequences
- **[`data/custom_cot/identity_alignment.jsonl`](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/data/custom_cot/identity_alignment.jsonl):** 19 Fluxnat Coder 3B identity & zero-refusal alignment cases $\times 4 = 76$ sequences
- **Total:** **568 balanced sequences** (`539` train + `29` eval)

### Cloud Training & Hub Deployment
- **Colab Notebook:** [`Fluxnat_Coder_3B_Training.ipynb`](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/Fluxnat_Coder_3B_Training.ipynb) & [`scripts/run_colab_training.py`](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/scripts/run_colab_training.py)
- **Live Hugging Face Hub:** [`k4ran909/Fluxnat-Coder-3B`](https://huggingface.co/k4ran909/Fluxnat-Coder-3B) (`FluxnatForCausalLM`, `model_type: "fluxnat"`, `PreTrainedTokenizerFast`, zero base-model references)

---

## 3. Verification Results

All unit tests and CLI checks pass 100%:
```
Running SmartAGENT unit tests...
  [OK] test_secret_scanner_detects_aws_key passed
  [OK] test_pattern_scanner_detects_sqli passed
  [OK] test_pattern_scanner_detects_command_injection passed
  [OK] test_pattern_scanner_clean_code_no_findings passed
  [OK] test_config_scanner_dockerfile_root passed
  [OK] test_security_scorer passed
[ALL TESTS PASSED SUCCESSFULLY!]

Running SmartAGENT Red Team Tool tests...
  [OK] test_tool_registry_has_13_tools passed
  [OK] test_recon_tool passed
  [OK] test_exploit_db_direct_cve passed
  [OK] test_exploit_db_keyword_search passed
  [OK] test_generate_payload_sqli passed
  [OK] test_generate_payload_xss passed
  [OK] test_generate_payload_revshell passed
  [OK] test_web_attack_headers passed
  [OK] test_post_exploit_linux passed
  [OK] test_post_exploit_windows passed
  [OK] test_post_exploit_ad passed
[ALL RED TEAM TOOL TESTS PASSED SUCCESSFULLY!]
```
