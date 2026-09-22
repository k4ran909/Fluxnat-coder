"""
Pattern Scanner for SmartAGENT.
Performs deterministic static analysis for common OWASP Top 10 and CWE vulnerabilities across languages.
"""

import re
import uuid
from typing import List
from smartagent.scanners.base import BaseScanner, Finding

CODE_VULN_PATTERNS = [
    {
        "name": "SQL Injection (String Formatting)",
        "pattern": r"(?:execute|raw|query)\s*\(\s*(?:f['\"][^'\"]*\{|['\"][^'\"]*%s[^'\"]*['\"]\s*%)",
        "cwe": "CWE-89",
        "owasp": "A03:2021 - Injection",
        "severity": "CRITICAL",
        "cvss": 9.8,
        "description": "SQL query built via string formatting or f-strings allows user-supplied parameters to alter SQL structure.",
        "remediation": "Use parameterized queries / prepared statements with placeholders (e.g. cursor.execute(query, (params,)))."
    },
    {
        "name": "OS Command Injection (Shell Execution)",
        "pattern": r"(?:os\.system|subprocess\.(?:call|Popen|run)\s*\([^)]*shell\s*=\s*True|child_process\.exec\s*\()",
        "cwe": "CWE-78",
        "owasp": "A03:2021 - Injection",
        "severity": "CRITICAL",
        "cvss": 9.8,
        "description": "Executing system commands through a shell interpreter allows command chaining via metacharacters (; & | `).",
        "remediation": "Avoid shell=True. Pass arguments as a list to subprocess.run or use execFile without shell evaluation."
    },
    {
        "name": "Arbitrary Code Evaluation (eval/exec)",
        "pattern": r"\b(?:eval|exec)\s*\([^)]+\)",
        "cwe": "CWE-95",
        "owasp": "A03:2021 - Injection",
        "severity": "CRITICAL",
        "cvss": 9.8,
        "description": "Dynamic code execution via eval/exec allows arbitrary code execution if input is attacker-influenced.",
        "remediation": "Refactor logic to use safe parsers (e.g., ast.literal_eval or json.loads) instead of executing code."
    },
    {
        "name": "Insecure Deserialization (Pickle/Unsafe YAML)",
        "pattern": r"(?:pickle\.loads?|yaml\.load\s*\([^)]*(?:Loader\s*=\s*yaml\.(?:UnsafeLoader|Loader)|Loader\s*=\s*None)\)|yaml\.unsafe_load\s*\()",
        "cwe": "CWE-502",
        "owasp": "A08:2021 - Software and Data Integrity Failures",
        "severity": "CRITICAL",
        "cvss": 9.8,
        "description": "Deserializing untrusted data with pickle or unsafe YAML loaders can trigger remote code execution via object instantiation.",
        "remediation": "Use safe serialization formats like JSON, or yaml.safe_load(). Never unpickle untrusted data."
    },
    {
        "name": "Weak Cryptographic Hash (MD5 / SHA1)",
        "pattern": r"(?:hashlib\.(?:md5|sha1)|crypto\.createHash\s*\(\s*['\"](?:md5|sha1)['\"]\))",
        "cwe": "CWE-328",
        "owasp": "A02:2021 - Cryptographic Failures",
        "severity": "MEDIUM",
        "cvss": 5.3,
        "description": "MD5 and SHA-1 are cryptographically broken and vulnerable to collision and preimage attacks.",
        "remediation": "Upgrade to secure hashing algorithms such as SHA-256, SHA-3, or password-hashing schemes (bcrypt, argon2id)."
    },
    {
        "name": "Potential Cross-Site Scripting (DOM XSS / Unsafe HTML)",
        "pattern": r"(?:dangerouslySetInnerHTML\s*=|innerHTML\s*=\s*[^;\n]+|document\.write\s*\()",
        "cwe": "CWE-79",
        "owasp": "A03:2021 - Injection",
        "severity": "HIGH",
        "cvss": 7.2,
        "description": "Injecting unsanitized input directly into DOM elements can lead to Cross-Site Scripting (XSS).",
        "remediation": "Use textContent or innerText, or sanitize HTML using DOMPurify before inserting into the DOM."
    }
]


class PatternScanner(BaseScanner):
    def __init__(self):
        super().__init__(name="PatternScanner")

    def scan_file(self, file_path: str, content: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            # Skip pure comment lines
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
                continue

            for rule in CODE_VULN_PATTERNS:
                if re.search(rule["pattern"], line):
                    findings.append(Finding(
                        id=f"PAT-{uuid.uuid4().hex[:6].upper()}",
                        title=f"{rule['name']}",
                        cwe=rule["cwe"],
                        owasp=rule["owasp"],
                        severity=rule["severity"],
                        cvss=rule["cvss"],
                        file_path=file_path,
                        line_number=idx,
                        snippet=line.strip(),
                        description=f"{rule['description']} (Found on line {idx})",
                        remediation=rule["remediation"],
                        scanner_name=self.name,
                    ))

        return findings
