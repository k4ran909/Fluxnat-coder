"""
SmartAGENT Configuration Management.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional


class ScannerConfig(BaseModel):
    # Model configuration
    model_id: str = Field(
        default="k4ran909/Fluxnat-Coder-3B",
        description="Model ID on Hugging Face Hub or local path to merged weights"
    )
    fallback_model_id: str = Field(
        default="k4ran909/Fluxnat-Coder-3B",
        description="Model checkpoint ID on Hugging Face"
    )
    load_in_4bit: bool = Field(
        default=True,
        description="Use 4-bit quantization for minimal VRAM usage"
    )

    # Scanning options
    target_extensions: List[str] = Field(
        default=[".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".php", ".c", ".cpp", ".rs", ".sql", ".env", "Dockerfile"],
        description="File extensions to include in scan"
    )
    ignored_directories: List[str] = Field(
        default=[".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".idea", ".vscode", "outputs"],
        description="Directories to exclude from scanning"
    )
    max_file_size_kb: int = Field(
        default=1024,
        description="Maximum file size in KB to parse"
    )

    # Reporting
    output_format: str = Field(
        default="rich",
        description="Output format: rich, json, markdown, html"
    )

    # Agent configuration
    max_agent_iterations: int = Field(
        default=15,
        description="Maximum ReAct reasoning steps per task"
    )
    agent_temperature: float = Field(
        default=0.3,
        description="Temperature for agent reasoning (slightly higher for diversity)"
    )
    memory_window: int = Field(
        default=20,
        description="Max messages to keep in agent conversation memory"
    )
    allowed_commands: List[str] = Field(
        default=[
            "python", "python3", "pip", "pip3", "uv", "node", "npm", "npx", "yarn", "pnpm",
            "git", "cat", "type", "dir", "ls", "find", "tree", "mkdir", "cp", "copy", "mv", "move",
            "head", "tail", "wc", "sort", "uniq", "cut", "awk", "sed", "echo", "touch",
            "grep", "rg", "fd", "ag", "findstr",
            "curl", "wget", "httpie", "http", "ssh", "scp", "rsync",
            "docker", "docker-compose", "podman",
            "nmap", "nikto", "sqlmap", "gobuster", "ffuf", "nuclei", "subfinder", "httpx",
            "semgrep", "bandit", "safety", "trivy", "grype", "syft",
            "cargo", "go", "rustc", "gcc", "g++", "make", "cmake",
            "smartagent", "whoami", "hostname", "ping", "tracert", "traceroute",
            "netstat", "ss", "ip", "ifconfig", "env", "set", "where", "which",
        ],
        description="Shell commands allowed in sandboxed agent execution"
    )


def get_default_config() -> ScannerConfig:
    """Retrieve scanner configuration from environment or defaults."""
    # Check if local merged model exists
    local_merged = Path("./outputs/Fluxnat-Coder-3B-Merged")
    model_path = str(local_merged) if local_merged.exists() else os.getenv("SMARTAGENT_MODEL", "k4ran909/Fluxnat-Coder-3B")

    return ScannerConfig(model_id=model_path)
