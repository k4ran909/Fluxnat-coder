#!/usr/bin/env python3
r"""
Export script to save the full conversation transcript and brain directory
for conversation e2c1cf9f-2dff-4bf4-a974-ef410441acfa to:
1. c:\Users\k4ran\OneDrive\Desktop\smartAGENT\e2c1cf9f-2dff-4bf4-a974-ef410441acfa
2. c:\Users\k4ran\OneDrive\Desktop\e2c1cf9f-2dff-4bf4-a974-ef410441acfa
Automatically sanitizes any raw Hugging Face API tokens (hf_REDACTED_TOKEN_SECURED).
"""

import os
import shutil
import json
import re
from datetime import datetime
from pathlib import Path

CONV_ID = "e2c1cf9f-2dff-4bf4-a974-ef410441acfa"
SOURCE_BRAIN = Path(r"C:\Users\k4ran\.gemini\antigravity\brain") / CONV_ID
TARGET_DIRS = [
    Path(r"c:\Users\k4ran\OneDrive\Desktop\smartAGENT") / CONV_ID,
    Path(r"c:\Users\k4ran\OneDrive\Desktop") / CONV_ID,
]

HF_TOKEN_REGEX = re.compile(r"hf_(?!REDACTED_TOKEN_SECURED)[A-Za-z0-9]{20,}")


def sanitize_tokens(text: str) -> str:
    return HF_TOKEN_REGEX.sub("hf_REDACTED_TOKEN_SECURED", text)


def sanitize_directory(root_dir: Path) -> int:
    import time
    pat_bytes = re.compile(rb"hf_[A-Za-z0-9]{20,}")
    redacted_files = 0
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            fpath = Path(dirpath) / fname
            for attempt in range(5):
                try:
                    raw = fpath.read_bytes()
                    if pat_bytes.search(raw):
                        cleaned = pat_bytes.sub(b"hf_REDACTED_TOKEN_SECURED", raw)
                        fpath.write_bytes(cleaned)
                        redacted_files += 1
                    break
                except PermissionError:
                    time.sleep(0.3)
                except Exception:
                    break
    return redacted_files


def clean_user_text(raw: str) -> str:
    m = re.search(r'<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>', raw, re.DOTALL)
    if m:
        return sanitize_tokens(m.group(1).strip())
    return sanitize_tokens(raw.strip())


def build_markdown_transcript(full_transcript_path: Path) -> str:
    lines = []
    lines.append(f"# Conversation Transcript — `{CONV_ID}`\n")
    lines.append(f"- **Conversation ID:** `{CONV_ID}`")
    lines.append(f"- **Exported At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Source:** Antigravity Brain Repository (`{SOURCE_BRAIN}`)\n")
    lines.append("---\n")
    lines.append("## Executive Summary of Tasks & Milestones\n")
    lines.append("1. **Research & Base Model Selection:** Evaluated sub-4B open-source uncensored security models and established zero base model naming constraints.")
    lines.append("2. **Local Architecture & Framework:** Built `smartAGENT` ReAct security agent framework with AST scanning, vulnerability scorer, and CLI.")
    lines.append("3. **Dataset Engineering (`v0.3.0`):** Authored 4-pillar dataset (`security_cot.jsonl`, `redteam_cot.jsonl`, `react_tool_cot.jsonl`, `identity_alignment.jsonl`), amplified into **568 balanced sequences** (`539` train + `29` eval).")
    lines.append("4. **Cloud Training Pipeline:** Developed automated Unsloth QLoRA pipeline and executed 65 steps on Tesla T4 GPU in Google Colab (loss reduced to 0.8952).")
    lines.append("5. **16-Bit Standalone Merge & Publication:** Merged weights into 16-bit standalone `FluxnatForCausalLM` model and published to Hugging Face Hub (`k4ran909/Fluxnat-Coder-3B`).")
    lines.append("6. **Red Team Agent Tool Suite (`v0.3.0`):** Added 5 offensive tools (`recon`, `exploit_db`, `generate_payload`, `web_attack`, `post_exploit`), expanding agent registry to 13 tools with 100% unit test pass rate.\n")
    lines.append("---\n")
    lines.append("## Chronological Dialogue Log\n")

    user_turn_num = 0
    with open(full_transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            step = json.loads(line)
            source = step.get("source")
            stype = step.get("type")
            idx = step.get("step_index")
            ts = step.get("created_at", "")

            if source == "USER_EXPLICIT" and stype == "USER_INPUT":
                user_turn_num += 1
                user_text = clean_user_text(step.get("content", ""))
                lines.append(f"\n### 👤 User Message #{user_turn_num} (Step {idx} | {ts})\n")
                lines.append(f"```text\n{user_text}\n```\n")

            elif source == "MODEL" and stype == "PLANNER_RESPONSE":
                content = sanitize_tokens(step.get("content", ""))
                tcalls = step.get("tool_calls", [])
                
                if content:
                    lines.append(f"\n#### 🤖 Assistant Response (Step {idx} | {ts})\n")
                    lines.append(content.strip() + "\n")
                
                if tcalls:
                    tool_names = [tc.get("name") for tc in tcalls]
                    lines.append(f"\n> **Tool Executed (Step {idx}):** `{', '.join(tool_names)}`\n")

    return "\n".join(lines)


def export_all():
    print(f"[*] Starting export for conversation: {CONV_ID}")
    print(f"[*] Source Brain: {SOURCE_BRAIN}")
    
    if not SOURCE_BRAIN.exists():
        raise FileNotFoundError(f"Source brain directory not found: {SOURCE_BRAIN}")

    full_transcript_path = SOURCE_BRAIN / ".system_generated" / "logs" / "transcript_full.jsonl"
    compact_transcript_path = SOURCE_BRAIN / ".system_generated" / "logs" / "transcript.jsonl"

    print("[*] Generating human-readable conversation transcript markdown...")
    md_transcript = build_markdown_transcript(full_transcript_path)

    for target in TARGET_DIRS:
        print(f"\n[*] Exporting to: {target}")
        target.mkdir(parents=True, exist_ok=True)

        # 1. Copy brain directory recursively
        target_brain = target / "brain"
        if target_brain.exists():
            shutil.rmtree(target_brain)
        shutil.copytree(SOURCE_BRAIN, target_brain)
        print(f"  [OK] Copied full brain directory -> {target_brain}")

        # 2. Write conversation transcript markdown
        conv_dir = target / "conversation"
        conv_dir.mkdir(parents=True, exist_ok=True)

        md_file = conv_dir / "CONVERSATION_TRANSCRIPT.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_transcript)
        print(f"  [OK] Saved human-readable transcript -> {md_file}")

        # 3. Copy raw transcript logs
        if compact_transcript_path.exists():
            shutil.copy2(compact_transcript_path, conv_dir / "transcript.jsonl")
        if full_transcript_path.exists():
            shutil.copy2(full_transcript_path, conv_dir / "transcript_full.jsonl")
        print(f"  [OK] Copied raw JSONL transcript logs -> {conv_dir}")

        # 4. Generate Root README.md
        readme_content = f"""# Session Backup: `{CONV_ID}`

This folder contains a complete backup of the Antigravity conversation and brain for:
- **Conversation ID:** `{CONV_ID}`
- **Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Folder Structure

```
{CONV_ID}/
├── README.md                           # This overview document
├── conversation/
│   ├── CONVERSATION_TRANSCRIPT.md      # Full human-readable markdown transcript of the dialogue
│   ├── transcript.jsonl                # Raw compact trajectory log
│   └── transcript_full.jsonl           # Raw full system event log
└── brain/                              # Full mirror of the Antigravity Brain folder
    ├── task.md                         # Task list & checklist
    ├── walkthrough.md                  # Detailed walkthrough of changes
    ├── implementation_plan.md          # Architectural implementation plan
    ├── training_loss.html              # Interactive training loss chart
    ├── best_slm_comparison.md          # SLM model comparison benchmarks
    ├── best_uncensored_under_3b.md     # Uncensored SLM research
    ├── best_slm_under_4b.md            # Sub-4B model benchmarks
    ├── run_without_ollama.md           # Transformers execution guide
    ├── .agents/                        # Specialized subagent definitions
    ├── .system_generated/              # System logs, task outputs, and devtools snapshots
    └── scratch/                        # Scratchpad scripts and artifacts
```

---

## Session Highlights (`v0.3.0`)
- **Model:** `k4ran909/Fluxnat-Coder-3B` (`FluxnatForCausalLM`)
- **Training:** 65 QLoRA fine-tuning steps in Google Colab on Tesla T4 GPU (loss 0.8952)
- **Dataset:** 568 sequences across 4 pillars (170 Red Team CoT, 24 Security Audits, 16 ReAct Tool Trajectories, 19 Identity Alignment)
- **Hugging Face Hub:** https://huggingface.co/k4ran909/Fluxnat-Coder-3B
- **Red Team Tools:** 13 tools total in SmartAGENT (`recon`, `exploit_db`, `generate_payload`, `web_attack`, `post_exploit` + 8 defensive tools)
"""
        with open(target / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"  [OK] Created root README.md -> {target / 'README.md'}")

        # 5. Sanitize any raw HF tokens in exported files
        redacted_count = sanitize_directory(target)
        print(f"  [OK] Sanitized tokens across {redacted_count} file(s) in {target}")

    print("\n[ALL EXPORTS COMPLETED SUCCESSFULLY!]")

if __name__ == "__main__":
    export_all()
