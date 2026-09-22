"""
Reporting Engine for SmartAGENT.
Renders Rich terminal tables, Markdown documentation, and JSON outputs.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from smartagent.scanners.base import Finding
from smartagent.reporting.scorer import SecurityScorer

console = Console(legacy_windows=False)

SEVERITY_COLORS = {
    "CRITICAL": "bold red",
    "HIGH": "bold bright_red",
    "MEDIUM": "bold yellow",
    "LOW": "bold blue",
    "INFO": "dim cyan",
}


def print_rich_report(findings: List[Finding], target_path: str):
    """Render a comprehensive terminal security dashboard."""
    metrics = SecurityScorer.calculate_score(findings)

    grade_colors = {
        "A+": "bold green",
        "A": "bold green",
        "B": "bold chartreuse3",
        "C": "bold yellow",
        "D": "bold dark_orange",
        "F": "bold red on black",
    }
    g_color = grade_colors.get(metrics["grade"], "bold white")

    # Header Dashboard Banner
    dashboard_text = Text()
    dashboard_text.append("Target: ", style="bold white")
    dashboard_text.append(f"{target_path}\n", style="cyan")
    dashboard_text.append("Security Grade: ", style="bold white")
    dashboard_text.append(f" {metrics['grade']} ", style=g_color)
    dashboard_text.append(f"  ({metrics['score']}/100 - {metrics['status']})\n\n", style="bold white")

    dashboard_text.append("Active Findings: ", style="bold white")
    b = metrics["breakdown"]
    dashboard_text.append(f"{b['CRITICAL']} Critical  ", style="bold red")
    dashboard_text.append(f"{b['HIGH']} High  ", style="bold bright_red")
    dashboard_text.append(f"{b['MEDIUM']} Medium  ", style="bold yellow")
    dashboard_text.append(f"{b['LOW']} Low  ", style="bold blue")
    dashboard_text.append(f"{b['INFO']} Info", style="dim cyan")

    if metrics["false_positives_filtered"] > 0:
        dashboard_text.append(f"\n[AI Filtered {metrics['false_positives_filtered']} False Positives]", style="italic green")

    console.print(Panel(dashboard_text, title="[bold cyan]🛡️ SmartAGENT Vulnerability Audit Report[/bold cyan]", box=box.ROUNDED, expand=False))

    active_findings = [f for f in findings if not f.is_false_positive]
    if not active_findings:
        console.print("[bold green]✓ No active vulnerabilities identified in the audited scope![/bold green]\n")
        return

    # Findings Table
    table = Table(title="Identified Vulnerabilities", box=box.SIMPLE_HEAVY, show_lines=True)
    table.add_column("Severity", justify="center", style="bold", width=12)
    table.add_column("CWE", justify="center", width=10)
    table.add_column("Finding & Location", style="white")
    table.add_column("Remediation Preview", style="dim")

    for f in active_findings:
        sev_style = SEVERITY_COLORS.get(f.severity.upper(), "white")
        sev_cell = Text(f.severity.upper(), style=sev_style)

        loc_text = Text()
        loc_text.append(f"{f.title}\n", style="bold white")
        loc_text.append(f"{f.file_path}:{f.line_number}\n", style="cyan")
        loc_text.append(f"{f.snippet[:90]}...", style="italic dim")

        fix_preview = (f.remediation or "Refer to OWASP guidelines.")[:120] + "..."

        table.add_row(sev_cell, f.cwe, loc_text, fix_preview)

    console.print(table)


def export_json_report(findings: List[Finding], target_path: str, output_file: str):
    """Export findings and score to a structured JSON file."""
    metrics = SecurityScorer.calculate_score(findings)
    data = {
        "target": target_path,
        "metrics": metrics,
        "findings": [f.model_dump() for f in findings],
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    console.print(f"[green]✓ Exported JSON report to:[/green] {output_file}")


def export_markdown_report(findings: List[Finding], target_path: str, output_file: str):
    """Export findings to a detailed Markdown documentation report."""
    metrics = SecurityScorer.calculate_score(findings)
    lines = [
        "# 🛡️ SmartAGENT Vulnerability Assessment Report",
        f"**Target:** `{target_path}`  ",
        f"**Security Grade:** **{metrics['grade']}** ({metrics['score']}/100 - {metrics['status']})  ",
        f"**Total Findings:** {metrics['total_active_findings']}  ",
        "",
        "## Summary Breakdown",
        f"- **Critical:** {metrics['breakdown']['CRITICAL']}",
        f"- **High:** {metrics['breakdown']['HIGH']}",
        f"- **Medium:** {metrics['breakdown']['MEDIUM']}",
        f"- **Low:** {metrics['breakdown']['LOW']}",
        f"- **Info:** {metrics['breakdown']['INFO']}",
        "",
        "---",
        "## Detailed Findings",
        ""
    ]

    active_findings = [f for f in findings if not f.is_false_positive]
    for idx, f in enumerate(active_findings, start=1):
        lines.extend([
            f"### {idx}. [{f.severity}] {f.title}",
            f"- **File:** `{f.file_path}:{f.line_number}`",
            f"- **CWE:** `{f.cwe}` | **OWASP:** `{f.owasp}` | **CVSS:** `{f.cvss}`",
            f"- **Scanner:** `{f.scanner_name}`",
            "",
            "**Flagged Snippet:**",
            "```",
            f.snippet,
            "```",
            "",
            "**Description:**",
            f.description,
            "",
            "**Suggested Remediation:**",
            f.remediation or "No specific remediation provided.",
            "",
            "---"
        ])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    console.print(f"[green]✓ Exported Markdown report to:[/green] {output_file}")
