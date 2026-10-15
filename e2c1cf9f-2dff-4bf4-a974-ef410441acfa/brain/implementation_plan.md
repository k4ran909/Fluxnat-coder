# Make SmartAGENT Fully Agentic

Transform SmartAGENT from a **static scanner with AI verification** into a **fully autonomous agentic security AI** that can think, plan, use tools, and act on its own.

## What Changes

**Before:** You run `smartagent scan .` → static regex patterns find issues → optionally asks the LLM to verify each one.

**After:** You chat with SmartAGENT like a real security engineer:
```
You: scan this project for vulnerabilities
Agent: [Thought] I'll start by listing all files in the project...
       [Action] list_files → found 47 files
       [Thought] Let me read the main app.py first...
       [Action] read_file app.py → found SQL query on line 34
       [Thought] This uses f-string interpolation in a SQL query — CWE-89...
       [Action] scan_code → CRITICAL: SQL Injection
       [Thought] Let me check if there's input sanitization upstream...
       [Action] read_file utils.py → no sanitization found
       [Answer] Found 3 vulnerabilities. Here's the full report...
```

---

## Architecture

```
┌──────────────────────────────────────────────┐
│              Interactive CLI (Rich)           │
│         smartagent chat / smartagent scan     │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│           ReAct Agent Loop (core.py)          │
│   Thought → Action → Observation → Repeat    │
│         Powered by Fluxnat Coder 3B           │
└──────────┬───────────────────┬───────────────┘
           │                   │
┌──────────▼────────┐ ┌───────▼──────────────┐
│   Tool Registry    │ │   Conversation       │
│                    │ │   Memory (memory.py)  │
│  • read_file       │ │                      │
│  • list_files      │ │  • Chat history      │
│  • scan_code       │ │  • Sliding window    │
│  • search_code     │ │  • Finding accumul.  │
│  • write_report    │ └──────────────────────┘
│  • web_lookup      │
│  • run_command     │
│  • fix_code        │
└───────────────────┘
```

---

## Proposed Changes

### Agent Core — NEW modules

#### [NEW] [core.py](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/smartagent/agent/core.py)
The **ReAct reasoning loop** — the brain of the agent.
- Parses LLM output for `Thought:`, `Action:`, `Action Input:`, `Final Answer:` blocks
- Dispatches actions to the tool registry
- Feeds `Observation:` back into the LLM for next reasoning step
- Max 15 iterations per task (prevents infinite loops)
- Handles tool errors gracefully

#### [NEW] [tools.py](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/smartagent/agent/tools.py)
**8 security-focused tools** the agent can call:

| Tool | Description |
|---|---|
| `list_files` | List all files in a directory (respects ignore patterns) |
| `read_file` | Read file contents with optional line range |
| `search_code` | Grep/regex search across the codebase |
| `scan_code` | Run static pattern scanners on a file (reuses existing scanners) |
| `analyze_security` | Deep AI analysis of a code snippet (chain-of-thought) |
| `write_report` | Generate a structured vulnerability report |
| `web_lookup` | Look up CVE/CWE details from public databases |
| `run_command` | Execute shell commands (sandboxed, with allowlist) |

#### [NEW] [memory.py](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/smartagent/agent/memory.py)
**Conversation memory** with sliding window:
- Stores full chat history
- Truncates to last N messages when context gets long (3B model has limited context)
- Accumulates findings across multiple tool calls
- Tracks which files have been scanned

#### [NEW] [prompts.py](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/smartagent/agent/prompts.py)
**ReAct system prompt** that teaches the model to use tools:
- Defines the `Thought → Action → Observation` format
- Lists all available tools with descriptions and input schemas
- Instructs the model to reason step-by-step before acting
- Includes the Fluxnat Coder 3B identity and security expertise

#### [NEW] [\_\_init\_\_.py](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/smartagent/agent/__init__.py)
Package init exposing `SmartAgent` class.

---

### CLI Updates

#### [MODIFY] [cli.py](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/smartagent/cli.py)
Add a new **`chat`** command for interactive agentic mode:
- `smartagent chat` — opens an interactive terminal session where you talk to the agent
- `smartagent agent "scan this project for vulns"` — one-shot agentic task
- Existing `scan` and `train` commands stay untouched

---

### Model Updates

#### [MODIFY] [model.py](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/smartagent/ai/model.py)
- Fix the `Tuple[Any, Any]` type hint (missing import)
- Add a `generate_stream()` method for real-time token streaming in chat mode
- Add `max_context_length` property so memory can calculate truncation

---

### Config Updates

#### [MODIFY] [config.py](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/smartagent/config.py)
Add agent-specific config fields:
- `max_agent_iterations: int = 15` — loop safety limit
- `agent_temperature: float = 0.3` — slightly higher for reasoning diversity
- `memory_window: int = 20` — max messages to keep in context
- `allowed_commands: list` — sandboxed shell command allowlist

---

### Dependencies

#### [MODIFY] [pyproject.toml](file:///c:/Users/k4ran/OneDrive/Desktop/smartAGENT/pyproject.toml)
- Add `prompt_toolkit>=3.0.0` for interactive chat input with history
- Add `readchar>=4.0.0` for key handling
- No other new dependencies — everything else uses existing packages (rich, transformers, torch)

---

## File Summary

| File | Action | Purpose |
|---|---|---|
| `smartagent/agent/__init__.py` | **NEW** | Package init |
| `smartagent/agent/core.py` | **NEW** | ReAct agent loop |
| `smartagent/agent/tools.py` | **NEW** | 8 security tools |
| `smartagent/agent/memory.py` | **NEW** | Conversation memory |
| `smartagent/agent/prompts.py` | **NEW** | ReAct system prompt |
| `smartagent/cli.py` | MODIFY | Add `chat` + `agent` commands |
| `smartagent/ai/model.py` | MODIFY | Fix type hint, add streaming |
| `smartagent/config.py` | MODIFY | Add agent config fields |
| `pyproject.toml` | MODIFY | Add prompt_toolkit dep |

> [!IMPORTANT]
> **VRAM Constraint:** Your GTX 1650 has 4GB VRAM. The model loads in 4-bit quantization (~1.8GB), leaving ~2GB for context. The ReAct loop keeps reasoning chains short (max 15 iterations) and memory uses a sliding window to prevent OOM.

> [!NOTE]
> **No Ollama.** Everything runs via `transformers` + `bitsandbytes` directly. The existing `ModelManager` singleton is reused — no new inference backend.

## Verification Plan

### Automated Tests
```bash
# Test agent tools in isolation
python -m pytest tests/test_agent_tools.py -v

# Test ReAct loop with mock LLM
python -m pytest tests/test_agent_core.py -v
```

### Manual Verification
1. `smartagent chat` — interactive session, ask "who are you?" → should identify as Fluxnat Coder 3B
2. `smartagent agent "scan this project"` — should autonomously discover files, scan them, and produce a report
3. `smartagent scan .` — existing static scan still works unchanged
