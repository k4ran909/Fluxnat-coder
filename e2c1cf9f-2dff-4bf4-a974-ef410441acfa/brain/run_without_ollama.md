# 🚀 Run Qwen 2.5 Coder 3B Abliterated — Without Ollama

6 alternatives, pick what fits your style.

---

## 🥇 Option 1: HuggingFace Transformers (Recommended for SmartAGENT)

> **Best for:** Direct Python integration into your project. This is what SmartAGENT should use.

```bash
pip install transformers torch accelerate bitsandbytes
```

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "huihui-ai/Qwen2.5-Coder-3B-Instruct-abliterated"

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load model (auto picks GPU if available, else CPU)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,       # Half precision — saves VRAM
    device_map="auto",               # Auto GPU/CPU
    # load_in_4bit=True,             # Uncomment for 4-bit quantization (needs ~2GB VRAM)
)

# Chat with it
messages = [
    {"role": "system", "content": "You are a cybersecurity expert. Analyze code for vulnerabilities."},
    {"role": "user", "content": "Find vulnerabilities in this code:\n\ndef login(username, password):\n    query = f\"SELECT * FROM users WHERE username='{username}' AND password='{password}'\"\n    cursor.execute(query)\n    return cursor.fetchone()"}
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)

output = model.generate(**inputs, max_new_tokens=512, temperature=0.7)
response = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print(response)
```

| Pros | Cons |
|------|------|
| ✅ Direct Python — integrates into SmartAGENT code | ❌ Slightly slower than llama.cpp |
| ✅ Easy fine-tuning with `peft`/LoRA | ❌ Needs PyTorch installed (~2GB) |
| ✅ 4-bit/8-bit quantization built-in | |
| ✅ Huge ecosystem & docs | |

---

## 🥈 Option 2: llama-cpp-python (Lightweight + Fast)

> **Best for:** Fast inference with minimal dependencies. Uses GGUF format.

```bash
pip install llama-cpp-python
```

```python
from llama_cpp import Llama

# Download GGUF from: bartowski/Qwen2.5-Coder-3B-Instruct-abliterated-GGUF
# Pick Q4_K_M for best speed/quality balance (~2GB file)
llm = Llama(
    model_path="./Qwen2.5-Coder-3B-Instruct-abliterated-Q4_K_M.gguf",
    n_ctx=8192,          # Context window
    n_gpu_layers=-1,     # -1 = offload all layers to GPU
)

response = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "You are a cybersecurity expert."},
        {"role": "user", "content": "Explain how SQL injection works and how to detect it in code."}
    ],
    max_tokens=512,
    temperature=0.7,
)

print(response["choices"][0]["message"]["content"])
```

```bash
# To download the GGUF file:
pip install huggingface-hub
huggingface-cli download bartowski/Qwen2.5-Coder-3B-Instruct-abliterated-GGUF \
    Qwen2.5-Coder-3B-Instruct-abliterated-Q4_K_M.gguf \
    --local-dir .
```

| Pros | Cons |
|------|------|
| ✅ Very fast inference (C++ backend) | ❌ Needs GGUF file download (~2GB) |
| ✅ Low memory usage | ❌ Harder to fine-tune |
| ✅ Works on CPU-only machines too | |
| ✅ Tiny dependency footprint | |

---

## 🥉 Option 3: vLLM (Production Server)

> **Best for:** If you want to run the model as an API server (like OpenAI's API).

```bash
pip install vllm
```

```bash
# Start server
python -m vllm.entrypoints.openai.api_server \
    --model huihui-ai/Qwen2.5-Coder-3B-Instruct-abliterated \
    --dtype float16 \
    --port 8000
```

```python
# Then call it like OpenAI API
import requests

response = requests.post("http://localhost:8000/v1/chat/completions", json={
    "model": "huihui-ai/Qwen2.5-Coder-3B-Instruct-abliterated",
    "messages": [
        {"role": "system", "content": "You are a cybersecurity expert."},
        {"role": "user", "content": "Find the vulnerability in this code..."}
    ],
    "max_tokens": 512
})

print(response.json()["choices"][0]["message"]["content"])
```

| Pros | Cons |
|------|------|
| ✅ OpenAI-compatible API | ❌ Heavier setup |
| ✅ Fastest throughput (batched inference) | ❌ Needs GPU |
| ✅ Production-ready | |

---

## Option 4: LM Studio (GUI — No Code)

> **Best for:** Quick testing with a visual interface.

1. Download [LM Studio](https://lmstudio.ai)
2. Search `Qwen2.5-Coder-3B-Instruct-abliterated` in the app
3. Download → Load → Chat

| Pros | Cons |
|------|------|
| ✅ Zero code needed | ❌ Can't integrate into SmartAGENT |
| ✅ Beautiful UI | ❌ Manual only |

---

## Option 5: ExLlamaV2 (Fastest Inference)

> **Best for:** Maximum speed on NVIDIA GPUs.

```bash
pip install exllamav2
```

```python
from exllamav2 import ExLlamaV2, ExLlamaV2Config, ExLlamaV2Tokenizer
from exllamav2.generator import ExLlamaV2StreamingGenerator

config = ExLlamaV2Config("huihui-ai/Qwen2.5-Coder-3B-Instruct-abliterated")
model = ExLlamaV2(config)
tokenizer = ExLlamaV2Tokenizer(config)
generator = ExLlamaV2StreamingGenerator(model, tokenizer)

# Generate response...
```

| Pros | Cons |
|------|------|
| ✅ Absolute fastest inference | ❌ NVIDIA GPU required |
| ✅ Excellent memory management | ❌ Smaller ecosystem |

---

## Option 6: Text Generation WebUI (oobabooga)

> **Best for:** Web-based interface with lots of features.

```bash
git clone https://github.com/oobabooga/text-generation-webui
cd text-generation-webui
pip install -r requirements.txt
python server.py
```

Then load the model from the web UI at `http://localhost:7860`.

---

## 🎯 Which One Should You Pick?

```
Building SmartAGENT (Python project)?
├── YES → Option 1: HuggingFace Transformers ✅
│         (integrates directly into your Python code)
│
├── Want faster inference?
│   ├── Have NVIDIA GPU → Option 5: ExLlamaV2
│   └── Any hardware   → Option 2: llama-cpp-python
│
├── Want an API server?
│   └── Option 3: vLLM
│
└── Just want to test/chat?
    └── Option 4: LM Studio
```

> [!IMPORTANT]
> **For SmartAGENT, go with Option 1 (HuggingFace Transformers).** It integrates directly into your Python code, supports fine-tuning, and is what the implementation plan is built around.
