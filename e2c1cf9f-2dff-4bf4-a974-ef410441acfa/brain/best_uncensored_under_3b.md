# 🔓 Best Uncensored Models Under 3B Parameters (Sep 2026)

> For cybersecurity work, you need models that **won't refuse** to discuss exploits, vulnerabilities, or attack vectors. Here are the best options.

---

## Two Ways to Get "Uncensored"

| Method | How It Works | Intelligence Loss? |
|--------|-------------|-------------------|
| **🥇 Abliteration** | Surgically removes the "refusal vector" from model weights — no retraining | **Minimal** — retains 95%+ of base intelligence |
| **🥈 Dolphin Fine-tune** | Trained on datasets with all refusals stripped out | **Some** — slight quality loss from retraining |

> [!TIP]
> **Go with Abliterated models** — they preserve more of the original model's coding intelligence while removing guardrails. Dolphin is the fallback if abliterated versions aren't available.

---

## 🏆 The Top 5 (Ranked)

### 🥇 #1 — Qwen 2.5 Coder 3B Instruct (Abliterated)

```
💾 3B params | 📏 128K context | 🧠 Best code + security
🏷️ Apache 2.0 | 💻 4-6 GB VRAM
```

| | |
|---|---|
| **Code Understanding** | ⭐⭐⭐⭐⭐ |
| **Uncensored Quality** | ⭐⭐⭐⭐⭐ |
| **Security Analysis** | ⭐⭐⭐⭐⭐ |
| **Reasoning** | ⭐⭐⭐⭐ |
| **Context Window** | ⭐⭐⭐⭐⭐ (128K) |

**Why it's #1:** Purpose-built for code + abliterated = will freely discuss SQL injection, XSS, buffer overflows, exploit chains — everything you need for a vuln scanner. 128K context means it can analyze large files.

```bash
# HuggingFace
# huihui-ai/Qwen2.5-Coder-3B-Instruct-abliterated
# bartowski/Qwen2.5-Coder-3B-Instruct-abliterated-GGUF (quantized)

# Ollama
ollama run huihui-ai/qwen2.5-coder-abliterated:3b
```

---

### 🥈 #2 — Dolphin 3.0 Qwen 2.5 3B

```
💾 3B params | 📏 128K context | 🧠 Best all-rounder uncensored
🏷️ Apache 2.0 | 💻 4-6 GB VRAM
```

| | |
|---|---|
| **Code Understanding** | ⭐⭐⭐⭐ |
| **Uncensored Quality** | ⭐⭐⭐⭐⭐ |
| **Security Analysis** | ⭐⭐⭐⭐ |
| **Reasoning** | ⭐⭐⭐⭐ |
| **Function Calling** | ⭐⭐⭐⭐ (built-in) |

**Why it's #2:** The **Dolphin** series by Eric Hartford is the OG gold standard for uncensored models. This version is built on Qwen 2.5's strong base. Includes native function calling — great for agentic security workflows.

```bash
# HuggingFace
# dphn/Dolphin3.0-Qwen2.5-3b
# bartowski/Dolphin3.0-Qwen2.5-3b-GGUF (quantized)

# Ollama
ollama run nchapman/dolphin3.0-qwen2.5:3b
```

---

### 🥉 #3 — Phi-4 Mini (Abliterated)

```
💾 3.8B params | 📏 16K context | 🧠 Best reasoning per param
🏷️ MIT | 💻 4-8 GB VRAM
```

| | |
|---|---|
| **Code Understanding** | ⭐⭐⭐⭐ |
| **Uncensored Quality** | ⭐⭐⭐⭐ |
| **Security Analysis** | ⭐⭐⭐⭐ |
| **Reasoning** | ⭐⭐⭐⭐⭐ (best in class) |
| **Context Window** | ⭐⭐⭐ (16K — limited) |

**Why it's #3:** Unmatched **reasoning power** at this size. Trained on high-quality synthetic data. Best at detecting **logic flaws** and **complex vulnerability chains**. Weakness: only 16K context.

```bash
# HuggingFace
# DuoNeural/Phi-4-Mini-Abliterated
# huihui-ai/Phi-4-mini-reasoning-abliterated

# Ollama (search for community uploads)
ollama run phi4-mini-abliterated
```

---

### #4 — DeepSeek-R1-Distill 1.5B (Abliterated)

```
💾 1.5B params | 📏 64K context | 🧠 Ultra-light chain-of-thought
🏷️ MIT | 💻 2-4 GB VRAM
```

| | |
|---|---|
| **Code Understanding** | ⭐⭐⭐ |
| **Uncensored Quality** | ⭐⭐⭐⭐ |
| **Chain-of-Thought** | ⭐⭐⭐⭐⭐ |
| **Reasoning** | ⭐⭐⭐⭐ (distilled from R1) |
| **Size Efficiency** | ⭐⭐⭐⭐⭐ (runs anywhere) |

**Why it's notable:** Only **1.5B** but has chain-of-thought reasoning distilled from the massive DeepSeek-R1. Can reason through vulnerabilities step-by-step despite being tiny. Runs on basically anything.

```bash
# HuggingFace
# Search: DeepSeek-R1-Distill-Qwen-1.5B-abliterated

# Ollama
ollama run deepseek-r1:1.5b
```

---

### #5 — SmolLM2 1.7B (Inherently Minimal Guardrails)

```
💾 1.7B params | 📏 8K context | 🧠 Ultra-edge
🏷️ Apache 2.0 | 💻 2-3 GB VRAM
```

**Why it's here:** HuggingFace's own ultra-small model. Has very minimal guardrails out of the box — lighter filtering than most models at this size. Best for embedding into mobile or edge security tools.

```bash
ollama run smollm2:1.7b
```

---

## 🆚 Head-to-Head Comparison

| Feature | Qwen Coder 3B Abliterated 🥇 | Dolphin 3.0 3B 🥈 | Phi-4 Mini Abliterated 🥉 | DS-R1 1.5B | SmolLM2 1.7B |
|---------|:---:|:---:|:---:|:---:|:---:|
| **Params** | 3B | 3B | 3.8B | 1.5B | 1.7B |
| **Context** | **128K** ✅ | **128K** ✅ | 16K ❌ | **64K** ✅ | 8K ❌ |
| **Code Skills** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Uncensored** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Reasoning** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Security** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **VRAM** | 4-6 GB | 4-6 GB | 4-8 GB | **2-4 GB** | **2-3 GB** |
| **License** | Apache 2.0 | Apache 2.0 | MIT | MIT | Apache 2.0 |
| **Vuln Discussion** | ✅ No refusal | ✅ No refusal | ✅ No refusal | ✅ No refusal | ⚠️ Mild filters |

---

## 🎯 THE VERDICT

> [!IMPORTANT]  
> ### **Go with: `Qwen 2.5 Coder 3B Instruct — Abliterated`**
> 
> It's the perfect combo for your SmartAGENT project:
> - ✅ **3B parameters** — fits your constraint exactly
> - ✅ **Code-specialized** — trained on 5.5T tokens of code
> - ✅ **128K context** — analyze entire files/modules
> - ✅ **Abliterated** — freely discusses exploits, CVEs, attack vectors
> - ✅ **Apache 2.0** — fully open, commercial use OK
> - ✅ **4-6 GB VRAM** — runs on any laptop
>
> ```bash
> # One command to get started:
> ollama run huihui-ai/qwen2.5-coder-abliterated:3b
> ```

### 💡 Power Move: Dual-Model Setup
> [!TIP]
> For SmartAGENT, consider running **two tiny models** together:
> 1. **Qwen 2.5 Coder 3B Abliterated** → Code analysis & vulnerability detection
> 2. **DeepSeek-R1-Distill 1.5B** → Chain-of-thought reasoning & verification
> 
> Total: only ~4.5B parameters, ~6-8 GB VRAM, but you get both code expertise AND deep reasoning.

---

## ⚠️ Important Notes

> [!CAUTION]
> **Ethical Use Only:** These uncensored models have **zero guardrails**. They will discuss ANY vulnerability, exploit, or attack technique without refusal. 
> - ✅ Use for: Testing YOUR OWN projects, authorized pentesting, security research
> - ❌ Never use for: Attacking systems you don't own, creating malware for malicious purposes
> - 🔒 Always run in **isolated environments** (VMs, sandboxes, or dedicated labs)
