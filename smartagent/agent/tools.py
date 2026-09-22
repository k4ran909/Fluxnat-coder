"""
Security-Focused Tool Registry for SmartAGENT.
Each tool is a callable that the ReAct agent can invoke by name.
"""

import os
import re
import json
import uuid
import subprocess
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# CWE knowledge base (embedded, no network needed)
# ---------------------------------------------------------------------------
CWE_DATABASE = {
    "CWE-78": {
        "name": "OS Command Injection",
        "description": "The software constructs OS commands using externally-influenced input without neutralizing special elements.",
        "owasp": "A03:2021 - Injection",
        "cvss": 9.8,
        "remediation": "Use subprocess with a list of arguments (no shell=True). Validate and sanitize all inputs.",
    },
    "CWE-79": {
        "name": "Cross-site Scripting (XSS)",
        "description": "The software does not neutralize user-controllable input before it is placed in output used as a web page.",
        "owasp": "A03:2021 - Injection",
        "cvss": 7.2,
        "remediation": "Use context-aware output encoding. Use Content-Security-Policy headers. Use DOMPurify for HTML sanitization.",
    },
    "CWE-89": {
        "name": "SQL Injection",
        "description": "The software constructs SQL commands using externally-influenced input without proper neutralization.",
        "owasp": "A03:2021 - Injection",
        "cvss": 9.8,
        "remediation": "Use parameterized queries / prepared statements. Never concatenate user input into SQL strings.",
    },
    "CWE-95": {
        "name": "Eval Injection",
        "description": "The software receives input that is expected to be code and evaluates it without proper validation.",
        "owasp": "A03:2021 - Injection",
        "cvss": 9.8,
        "remediation": "Use safe parsers (ast.literal_eval, json.loads) instead of eval/exec.",
    },
    "CWE-200": {
        "name": "Information Exposure",
        "description": "The software exposes sensitive information to actors not authorized to have it.",
        "owasp": "A01:2021 - Broken Access Control",
        "cvss": 5.3,
        "remediation": "Implement proper access controls. Remove debug info from production. Use generic error messages.",
    },
    "CWE-259": {
        "name": "Hard-coded Password",
        "description": "The software contains a hard-coded password used for authentication.",
        "owasp": "A07:2021 - Identification and Authentication Failures",
        "cvss": 7.5,
        "remediation": "Use environment variables or a secrets manager. Never commit credentials to source control.",
    },
    "CWE-327": {
        "name": "Broken Crypto Algorithm",
        "description": "The use of a broken or risky cryptographic algorithm.",
        "owasp": "A02:2021 - Cryptographic Failures",
        "cvss": 7.5,
        "remediation": "Use modern algorithms: AES-256-GCM for encryption, SHA-256/SHA-3 for hashing, Argon2id for passwords.",
    },
    "CWE-328": {
        "name": "Weak Hash (MD5/SHA1)",
        "description": "MD5 and SHA-1 are cryptographically broken and vulnerable to collision attacks.",
        "owasp": "A02:2021 - Cryptographic Failures",
        "cvss": 5.3,
        "remediation": "Upgrade to SHA-256, SHA-3, or password hashing (bcrypt, argon2id).",
    },
    "CWE-502": {
        "name": "Deserialization of Untrusted Data",
        "description": "The application deserializes untrusted data without verification, leading to RCE.",
        "owasp": "A08:2021 - Software and Data Integrity Failures",
        "cvss": 9.8,
        "remediation": "Use safe serialization (JSON). Never unpickle untrusted data. Use yaml.safe_load().",
    },
    "CWE-798": {
        "name": "Hard-coded Credentials",
        "description": "The software contains hard-coded credentials for inbound or outbound authentication.",
        "owasp": "A07:2021 - Identification and Authentication Failures",
        "cvss": 9.8,
        "remediation": "Use environment variables, vault systems, or config files excluded from version control.",
    },
    "CWE-22": {
        "name": "Path Traversal",
        "description": "The software uses external input to construct a pathname without restricting it to an intended directory.",
        "owasp": "A01:2021 - Broken Access Control",
        "cvss": 7.5,
        "remediation": "Validate and canonicalize paths. Use os.path.realpath() and check against allowed directories.",
    },
    "CWE-352": {
        "name": "Cross-Site Request Forgery (CSRF)",
        "description": "The web application does not verify that a request was intentionally sent by the user.",
        "owasp": "A01:2021 - Broken Access Control",
        "cvss": 8.0,
        "remediation": "Implement CSRF tokens. Use SameSite cookie attribute. Verify Origin/Referer headers.",
    },
}

# Default ignore dirs for file listing
IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__",
    "dist", "build", ".idea", ".vscode", "outputs", ".tox",
    ".mypy_cache", ".ruff_cache", "egg-info",
}

# Allowed shell commands (prefix allowlist for sandboxing)
ALLOWED_COMMANDS = [
    # Core
    "python", "python3", "pip", "pip3", "uv", "node", "npm", "npx", "yarn", "pnpm",
    # Git
    "git",
    # File ops
    "cat", "type", "dir", "ls", "find", "tree", "mkdir", "cp", "copy", "mv", "move",
    "head", "tail", "wc", "sort", "uniq", "cut", "awk", "sed", "echo", "touch",
    # Search
    "grep", "rg", "fd", "ag", "findstr",
    # Network / HTTP
    "curl", "wget", "httpie", "http", "ssh", "scp", "rsync",
    # Docker
    "docker", "docker-compose", "podman",
    # Security tools
    "nmap", "nikto", "sqlmap", "gobuster", "ffuf", "nuclei", "subfinder", "httpx",
    "semgrep", "bandit", "safety", "trivy", "grype", "syft",
    # Package managers
    "cargo", "go", "rustc", "gcc", "g++", "make", "cmake",
    # Misc
    "smartagent", "whoami", "hostname", "ping", "tracert", "traceroute",
    "netstat", "ss", "ip", "ifconfig", "env", "set", "where", "which",
]


@dataclass
class ToolSpec:
    """Specification for a tool the agent can call."""
    name: str
    description: str
    usage: str
    func: Callable[[str], str]


class ToolRegistry:
    """Registry of all tools available to the agent."""

    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)
        self._tools: Dict[str, ToolSpec] = {}
        self._register_builtins()

    def register(self, spec: ToolSpec):
        self._tools[spec.name] = spec

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolSpec]:
        return list(self._tools.values())

    def get_tool_descriptions(self) -> str:
        """Format tool descriptions for the system prompt."""
        lines = []
        for tool in self._tools.values():
            lines.append(f"### {tool.name}")
            lines.append(f"{tool.description}")
            lines.append(f"Usage: `{tool.usage}`")
            lines.append("")
        return "\n".join(lines)

    def execute(self, name: str, input_str: str) -> str:
        """Execute a tool by name and return the result string."""
        tool = self._tools.get(name)
        if tool is None:
            available = ", ".join(self._tools.keys())
            return f"Error: Unknown tool '{name}'. Available tools: {available}"
        try:
            result = tool.func(input_str.strip())
            # Truncate very long outputs to prevent context overflow
            if len(result) > 4000:
                result = result[:4000] + f"\n\n... [output truncated, {len(result)} chars total]"
            return result
        except Exception as e:
            return f"Error executing {name}: {type(e).__name__}: {str(e)}"

    # ------------------------------------------------------------------
    # Built-in tool implementations
    # ------------------------------------------------------------------

    def _register_builtins(self):
        self.register(ToolSpec(
            name="list_files",
            description="List all code files in a directory (respects .git/node_modules/venv ignore rules).",
            usage="list_files <directory_path>  (e.g., list_files . or list_files src/)",
            func=self._tool_list_files,
        ))
        self.register(ToolSpec(
            name="read_file",
            description="Read the contents of a file. Optionally specify line range with :start-end suffix.",
            usage="read_file <path>  or  read_file <path>:10-50",
            func=self._tool_read_file,
        ))
        self.register(ToolSpec(
            name="search_code",
            description="Search for a regex pattern across all code files in the project. Returns matching lines.",
            usage="search_code <pattern>  (e.g., search_code eval\\(  or  search_code password)",
            func=self._tool_search_code,
        ))
        self.register(ToolSpec(
            name="scan_code",
            description="Run static vulnerability pattern scanners on a specific file. Returns all findings.",
            usage="scan_code <file_path>  (e.g., scan_code app.py)",
            func=self._tool_scan_code,
        ))
        self.register(ToolSpec(
            name="get_cwe_info",
            description="Look up detailed information about a CWE vulnerability class.",
            usage="get_cwe_info <cwe_id>  (e.g., get_cwe_info CWE-89)",
            func=self._tool_get_cwe_info,
        ))
        self.register(ToolSpec(
            name="write_report",
            description="Write accumulated findings to a JSON or Markdown report file.",
            usage="write_report <format>  (format: json or markdown, e.g., write_report markdown)",
            func=self._tool_write_report,
        ))
        self.register(ToolSpec(
            name="run_command",
            description="Execute a shell command (sandboxed to safe commands like git, python, grep, etc.).",
            usage="run_command <command>  (e.g., run_command git log -5 --oneline)",
            func=self._tool_run_command,
        ))
        self.register(ToolSpec(
            name="fix_code",
            description="Generate a secure code fix suggestion for a given code snippet and vulnerability type.",
            usage="fix_code <cwe_id>|||<vulnerable_code_snippet>  (e.g., fix_code CWE-89|||query = f\"SELECT * FROM users WHERE id = '{uid}'\")",
            func=self._tool_fix_code,
        ))

    def _tool_list_files(self, directory: str) -> str:
        target = os.path.abspath(os.path.join(self.working_dir, directory))
        if not os.path.isdir(target):
            return f"Error: '{directory}' is not a valid directory."

        files = []
        code_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".php",
            ".c", ".cpp", ".h", ".rs", ".rb", ".sql", ".sh", ".yaml",
            ".yml", ".toml", ".json", ".env", ".xml", ".html", ".css",
        }
        for root, dirs, filenames in os.walk(target):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for fname in sorted(filenames):
                ext = os.path.splitext(fname)[1].lower()
                if ext in code_extensions or fname in {"Dockerfile", "Makefile", ".gitignore", ".env"}:
                    rel = os.path.relpath(os.path.join(root, fname), target)
                    size = os.path.getsize(os.path.join(root, fname))
                    files.append(f"  {rel}  ({size} bytes)")

        if not files:
            return f"No code files found in '{directory}'."
        return f"Found {len(files)} files in '{directory}':\n" + "\n".join(files)

    def _tool_read_file(self, path_spec: str) -> str:
        # Parse optional line range: path:start-end
        start_line, end_line = None, None
        if ":" in path_spec and "-" in path_spec.rsplit(":", 1)[-1]:
            parts = path_spec.rsplit(":", 1)
            path_str = parts[0]
            try:
                range_parts = parts[1].split("-")
                start_line = int(range_parts[0])
                end_line = int(range_parts[1])
            except (ValueError, IndexError):
                path_str = path_spec  # not a valid range, treat whole thing as path
        else:
            path_str = path_spec

        full_path = os.path.abspath(os.path.join(self.working_dir, path_str.strip()))
        if not os.path.isfile(full_path):
            return f"Error: File '{path_str}' not found."

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            return f"Error reading file: {e}"

        total = len(lines)
        if start_line and end_line:
            start_line = max(1, start_line)
            end_line = min(total, end_line)
            selected = lines[start_line - 1:end_line]
            numbered = [f"{i}: {line.rstrip()}" for i, line in enumerate(selected, start=start_line)]
            return f"File: {path_str} (lines {start_line}-{end_line} of {total})\n" + "\n".join(numbered)
        else:
            # Cap at 200 lines to prevent context overflow
            if total > 200:
                selected = lines[:200]
                numbered = [f"{i}: {line.rstrip()}" for i, line in enumerate(selected, start=1)]
                return f"File: {path_str} ({total} lines, showing first 200)\n" + "\n".join(numbered)
            numbered = [f"{i}: {line.rstrip()}" for i, line in enumerate(lines, start=1)]
            return f"File: {path_str} ({total} lines)\n" + "\n".join(numbered)

    def _tool_search_code(self, pattern: str) -> str:
        pattern = pattern.strip()
        if not pattern:
            return "Error: Please provide a search pattern."

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return f"Error: Invalid regex pattern: {e}"

        matches = []
        code_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".php",
            ".c", ".cpp", ".h", ".rs", ".rb", ".sql", ".sh",
        }
        for root, dirs, filenames in os.walk(self.working_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in code_extensions:
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                rel = os.path.relpath(fpath, self.working_dir)
                                matches.append(f"  {rel}:{line_num}: {line.strip()}")
                                if len(matches) >= 50:
                                    break
                except Exception:
                    continue
                if len(matches) >= 50:
                    break

        if not matches:
            return f"No matches found for pattern: {pattern}"
        header = f"Found {len(matches)} matches for '{pattern}':"
        if len(matches) >= 50:
            header += " (capped at 50 results)"
        return header + "\n" + "\n".join(matches)

    def _tool_scan_code(self, file_path: str) -> str:
        full_path = os.path.abspath(os.path.join(self.working_dir, file_path.strip()))
        if not os.path.isfile(full_path):
            return f"Error: File '{file_path}' not found."

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file: {e}"

        # Import scanners here to avoid circular imports
        from smartagent.scanners import ALL_SCANNERS

        rel_path = os.path.relpath(full_path, self.working_dir)
        all_findings = []
        for scanner in ALL_SCANNERS:
            findings = scanner.scan_file(rel_path, content)
            all_findings.extend(findings)

        if not all_findings:
            return f"No vulnerabilities found in {file_path} by static scanners."

        lines = [f"Found {len(all_findings)} findings in {file_path}:"]
        for f in all_findings:
            lines.append(f"\n  [{f.severity}] {f.title}")
            lines.append(f"    CWE: {f.cwe} | CVSS: {f.cvss} | Line: {f.line_number}")
            lines.append(f"    Code: {f.snippet[:100]}")
            lines.append(f"    Fix: {(f.remediation or 'N/A')[:120]}")
        return "\n".join(lines)

    def _tool_get_cwe_info(self, cwe_id: str) -> str:
        cwe_id = cwe_id.strip().upper()
        if not cwe_id.startswith("CWE-"):
            cwe_id = f"CWE-{cwe_id}"

        info = CWE_DATABASE.get(cwe_id)
        if info is None:
            available = ", ".join(sorted(CWE_DATABASE.keys()))
            return f"CWE '{cwe_id}' not in local database. Available: {available}"

        return (
            f"{cwe_id}: {info['name']}\n"
            f"OWASP: {info['owasp']}\n"
            f"CVSS: {info['cvss']}\n"
            f"Description: {info['description']}\n"
            f"Remediation: {info['remediation']}"
        )

    def _tool_write_report(self, fmt: str) -> str:
        fmt = fmt.strip().lower()
        if fmt not in ("json", "markdown", "md"):
            return "Error: Format must be 'json' or 'markdown'."

        # Access findings from the agent's memory (injected at runtime)
        findings = getattr(self, "_agent_findings", [])
        if not findings:
            return "No findings to report. Run scan_code on files first."

        report_dir = os.path.join(self.working_dir, "reports")
        os.makedirs(report_dir, exist_ok=True)

        if fmt == "json":
            out_path = os.path.join(report_dir, "smartagent_report.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump({"findings": findings, "total": len(findings)}, f, indent=2)
            return f"JSON report written to: {os.path.relpath(out_path, self.working_dir)}"
        else:
            out_path = os.path.join(report_dir, "smartagent_report.md")
            lines = ["# SmartAGENT Security Report\n"]
            for i, finding in enumerate(findings, 1):
                lines.append(f"## {i}. [{finding.get('severity', '?')}] {finding.get('title', 'Untitled')}")
                lines.append(f"- **File:** `{finding.get('file_path', '?')}:{finding.get('line_number', '?')}`")
                lines.append(f"- **CWE:** `{finding.get('cwe', '?')}` | **CVSS:** {finding.get('cvss', '?')}")
                lines.append(f"- **Code:** `{finding.get('snippet', '')[:100]}`")
                lines.append(f"- **Fix:** {finding.get('remediation', 'N/A')[:200]}")
                lines.append("")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return f"Markdown report written to: {os.path.relpath(out_path, self.working_dir)}"

    def _tool_run_command(self, command: str) -> str:
        command = command.strip()
        if not command:
            return "Error: No command provided."

        # Sandbox check — only allow safe commands
        first_word = command.split()[0].lower()
        # Strip path prefixes for check
        base_cmd = os.path.basename(first_word).replace(".exe", "")
        if base_cmd not in ALLOWED_COMMANDS:
            return (
                f"Error: Command '{base_cmd}' is not in the allowed list. "
                f"Allowed: {', '.join(ALLOWED_COMMANDS)}"
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += "\n[stderr]\n" + result.stderr
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            return output.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error: {e}"

    def _tool_fix_code(self, input_str: str) -> str:
        """Generate a fix suggestion based on CWE and vulnerable code."""
        parts = input_str.split("|||", 1)
        if len(parts) != 2:
            return "Error: Use format: fix_code CWE-XX|||<code_snippet>"

        cwe_id = parts[0].strip().upper()
        code = parts[1].strip()

        if not cwe_id.startswith("CWE-"):
            cwe_id = f"CWE-{cwe_id}"

        info = CWE_DATABASE.get(cwe_id)
        if info is None:
            return f"No fix template for {cwe_id}. Provide a manual remediation."

        return (
            f"Vulnerability: {cwe_id} — {info['name']}\n\n"
            f"Vulnerable Code:\n```\n{code}\n```\n\n"
            f"Remediation Strategy: {info['remediation']}\n\n"
            f"Apply the remediation strategy to the vulnerable code above. "
            f"Key principle: {info['description']}"
        )
