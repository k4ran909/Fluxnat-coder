"""
Model Loader and Inference Engine for Fluxnat Coder 3B.
"""

import os
from pathlib import Path
from typing import Any, Optional, Tuple, Generator
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TextIteratorStreamer
from threading import Thread


class ModelManager:
    _instance: Optional["ModelManager"] = None
    _model = None
    _tokenizer = None

    def __init__(self, model_id: str = "k4ran909/Fluxnat-Coder-3B", load_in_4bit: bool = True):
        self.model_id = model_id
        self.load_in_4bit = load_in_4bit
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    @classmethod
    def get_instance(cls, model_id: str = "k4ran909/Fluxnat-Coder-3B", load_in_4bit: bool = True) -> "ModelManager":
        if cls._instance is None:
            cls._instance = cls(model_id, load_in_4bit)
        return cls._instance

    def load(self) -> Tuple[Any, Any]:
        if self._model is not None and self._tokenizer is not None:
            return self._model, self._tokenizer

        target = self.model_id
        local_path = Path(target)
        if not local_path.exists():
            # Check local output paths
            candidates = [
                Path("./outputs/Fluxnat-Coder-3B-Merged"),
                Path("./outputs/Fluxnat-Coder-3B"),
            ]
            for cand in candidates:
                if cand.exists():
                    target = str(cand)
                    break

        print(f"[*] Initializing Fluxnat Coder 3B from: {target} on {self.device}...")

        self._tokenizer = AutoTokenizer.from_pretrained(target, trust_remote_code=True)

        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        if self.device == "cuda" and self.load_in_4bit:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                target,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
        else:
            self._model = AutoModelForCausalLM.from_pretrained(
                target,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
            )

        return self._model, self._tokenizer

    def generate(self, messages: list, max_tokens: int = 512, temperature: float = 0.2) -> str:
        model, tokenizer = self.load()
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
                repetition_penalty=1.05,
                do_sample=temperature > 0.0,
            )

        return tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

    def generate_stream(self, messages: list, max_tokens: int = 512, temperature: float = 0.2) -> Generator[str, None, None]:
        """Stream tokens one at a time for real-time chat display."""
        model, tokenizer = self.load()
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

        gen_kwargs = {
            **{k: v for k, v in inputs.items()},
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.95,
            "repetition_penalty": 1.05,
            "do_sample": temperature > 0.0,
            "streamer": streamer,
        }

        thread = Thread(target=model.generate, kwargs=gen_kwargs)
        thread.start()

        for token in streamer:
            yield token

        thread.join()
