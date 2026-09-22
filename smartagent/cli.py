"""
SmartAGENT CLI Entry Point.
Provides commands to scan projects for vulnerabilities and launch Fluxnat Coder 3B training.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.panel import Panel

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from smartagent.config import get_default_config
from smartagent.scanners import ALL_SCANNERS, Finding
from smartagent.reporting import (
    print_rich_report,
    export_json_report,
    export_markdown_report,
)

app = typer.Typer(
    name="smartagent",
    help="SmartAGENT - AI-Powered Cybersecurity Vulnerability Scanner & Fluxnat Coder 3B Suite",
    add_completion=False,
)
console = Console(legacy_windows=False)


@app.command("scan")
def scan_project(
    target_dir: str = typer.Argument(".", help="Directory or file path to scan"),
    ai_verify: bool = typer.Option(False, "--ai", "-a", help="Use Fluxnat Coder 3B for false-positive reduction & fix generation"),
    model_id: Optional[str] = typer.Option(None, "--model", "-m", help="Hugging Face model ID or path to merged model"),
    json_out: Optional[str] = typer.Option(None, "--json", "-j", help="Path to write JSON report"),
    md_out: Optional[str] = typer.Option(None, "--md", help="Path to write Markdown report"),
):
    """
    Perform an automated vulnerability audit on a project codebase.
    """
    config = get_default_config()
    target_path = Path(target_dir).resolve()

    if not target_path.exists():
        console.print(f"[bold red]Error:[/bold red] Target path does not exist: {target_path}")
        raise typer.Exit(code=1)

    console.print(Panel(
        f"[bold cyan]SmartAGENT Vulnerability Audit[/bold cyan]\n"
        f"Scanning: [white]{target_path}[/white]\n"
        f"Scanners Active: [green]{len(ALL_SCANNERS)}[/green] (Secrets, Code Patterns, Dependencies, Configs)\n"
        f"AI Verification: [yellow]{'Enabled (Fluxnat Coder 3B)' if ai_verify else 'Disabled (Static Pass Only)'}[/yellow]",
        title="⚡ Initializing Audit",
        expand=False
    ))

    all_findings: List[Finding] = []

    # File traversal
    files_to_scan: List[Path] = []
    if target_path.is_file():
        files_to_scan.append(target_path)
    else:
        for root, dirs, files in os.walk(target_path):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in config.ignored_directories]
            for file in files:
                fpath = Path(root) / file
                if any(file.endswith(ext) or file == ext for ext in config.target_extensions):
                    # Check file size
                    try:
                        if fpath.stat().st_size <= config.max_file_size_kb * 1024:
                            files_to_scan.append(fpath)
                    except Exception:
                        pass

    console.print(f"[*] Analyzing [cyan]{len(files_to_scan)}[/cyan] matching project files...")

    with console.status("[bold green]Running static analysis rules...") as status:
        for fpath in files_to_scan:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                rel_path = str(fpath.relative_to(target_path)) if target_path.is_dir() else str(fpath.name)
                for scanner in ALL_SCANNERS:
                    findings = scanner.scan_file(rel_path, content)
                    all_findings.extend(findings)
            except Exception as e:
                pass

    console.print(f"[✓] Static analysis complete. Identified [bold red]{len(all_findings)}[/bold red] potential findings.")

    # AI Verification Stage
    if ai_verify and all_findings:
        console.print("[*] Engaging [bold cyan]Fluxnat Coder 3B[/bold cyan] for Chain-of-Thought verification...")
        try:
            from smartagent.ai.judge import AIJudge
            effective_model = model_id or config.model_id
            judge = AIJudge(model_id=effective_model)
            all_findings = judge.verify_findings(all_findings)
            console.print("[✓] AI reasoning pass complete.")
        except Exception as e:
            console.print(f"[!] AI Verification pass skipped: {e}")

    # Output Reports
    print_rich_report(all_findings, str(target_path))

    if json_out:
        export_json_report(all_findings, str(target_path), json_out)

    if md_out:
        export_markdown_report(all_findings, str(target_path), md_out)


@app.command("train")
def train_model():
    """
    Launch local training or view Google Colab training instructions for Fluxnat Coder 3B.
    """
    console.print(Panel(
        "[bold cyan]Fluxnat Coder 3B Training Suite[/bold cyan]\n\n"
        "1. [bold green]Google Colab (Recommended):[/bold green]\n"
        "   Upload `Fluxnat_Coder_3B_Training.ipynb` to Google Colab and run with a free T4 GPU (16GB VRAM).\n\n"
        "2. [bold yellow]Local Execution:[/bold yellow]\n"
        "   Run: `python train.py`\n\n"
        "3. [bold white]Configuration:[/bold white]\n"
        "   Adjust parameters in `config/training_config.yaml`",
        title="🚀 Train Fluxnat Coder 3B",
        expand=False
    ))


@app.command("info")
def system_info():
    """
    Display SmartAGENT environment and system status.
    """
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if has_cuda else "None (CPU)"
        vram = f"{torch.cuda.get_device_properties(0).total_mem / (1024**3):.1f} GB" if has_cuda else "N/A"
        torch_status = f"Installed (v{torch.__version__})"
    except (ImportError, AttributeError):
        has_cuda = False
        device_name = "N/A"
        vram = "N/A"
        torch_status = "Not Installed (Install via `pip install torch` for AI reasoning)"

    console.print(Panel(
        f"[bold white]SmartAGENT Version:[/bold white] 0.2.0 (Agentic)\n"
        f"[bold white]Target Model:[/bold white] k4ran909/Fluxnat-Coder-3B\n"
        f"[bold white]PyTorch Status:[/bold white] {torch_status}\n"
        f"[bold white]CUDA Available:[/bold white] {'[green]Yes[/green]' if has_cuda else '[yellow]No[/yellow]'}\n"
        f"[bold white]GPU Device:[/bold white] {device_name}\n"
        f"[bold white]VRAM:[/bold white] {vram}\n"
        f"[bold white]Active Scanners:[/bold white] {', '.join(s.name for s in ALL_SCANNERS)}\n"
        f"[bold white]Agent Mode:[/bold white] [green]Available[/green] (ReAct loop with 8 tools)",
        title="[bold cyan]ℹ️ SmartAGENT System Status[/bold cyan]",
        expand=False
    ))


@app.command("chat")
def chat_mode(
    model_id: Optional[str] = typer.Option(None, "--model", "-m", help="Hugging Face model ID or local path"),
    max_iterations: int = typer.Option(15, "--max-steps", "-s", help="Max reasoning steps per task"),
    temperature: float = typer.Option(0.3, "--temp", "-t", help="Sampling temperature for reasoning"),
):
    """
    Launch interactive agentic chat with Fluxnat Coder 3B.
    The agent can autonomously scan code, find vulnerabilities, and generate fixes.
    """
    from smartagent.agent.core import SmartAgent
    from smartagent.agent.prompts import CHAT_GREETING

    config = get_default_config()
    effective_model = model_id or config.model_id

    console.print(Panel(
        CHAT_GREETING,
        title="[bold cyan]⚡ SmartAGENT — Agentic Mode[/bold cyan]",
        border_style="cyan",
        expand=False,
    ))

    agent = SmartAgent(
        model_id=effective_model,
        working_dir=os.getcwd(),
        max_iterations=max_iterations,
        temperature=temperature,
        verbose=True,
    )

    while True:
        try:
            user_input = console.input("\n[bold green]You ▶[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q", ":q"):
            console.print("[dim]Goodbye![/dim]")
            break
        if user_input.lower() == "reset":
            agent.reset()
            console.print("[yellow]Memory cleared. Starting fresh.[/yellow]")
            continue

        console.print()
        answer = agent.chat(user_input)
        # Final answer is already printed by the agent in verbose mode


@app.command("agent")
def agent_oneshot(
    task: str = typer.Argument(..., help="The task to execute (e.g., 'scan this project for SQL injection')"),
    model_id: Optional[str] = typer.Option(None, "--model", "-m", help="Hugging Face model ID or local path"),
    max_iterations: int = typer.Option(15, "--max-steps", "-s", help="Max reasoning steps"),
    target_dir: str = typer.Option(".", "--dir", "-d", help="Working directory for the agent"),
):
    """
    Run a one-shot agentic task. The agent executes autonomously and prints the result.
    """
    from smartagent.agent.core import SmartAgent

    config = get_default_config()
    effective_model = model_id or config.model_id
    target_path = Path(target_dir).resolve()

    console.print(Panel(
        f"[bold cyan]SmartAGENT — One-Shot Agent[/bold cyan]\n"
        f"Task: [white]{task}[/white]\n"
        f"Directory: [white]{target_path}[/white]\n"
        f"Model: [yellow]{effective_model}[/yellow]",
        title="⚡ Launching Agent",
        expand=False,
    ))

    agent = SmartAgent(
        model_id=effective_model,
        working_dir=str(target_path),
        max_iterations=max_iterations,
        verbose=True,
    )

    answer = agent.run(task)
    console.print()  # spacing after the agent's verbose output


if __name__ == "__main__":
    app()
