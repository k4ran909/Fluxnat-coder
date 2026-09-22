"""
Secret Scanner for SmartAGENT.
Detects hardcoded API keys, passwords, bearer tokens, private keys, and cloud credentials.
"""

import re
import math
import uuid
from typing import List
from smartagent.scanners.base import BaseScanner, Finding

SECRET_PATTERNS = [
    {
        "name": "AWS Access Key ID",
        "pattern": r"\b(AKIA[0-9A-Z]{16})\b",
        "cwe": "CWE-798",
        "owasp": "A07:2021 - Identification and Authentication Failures",
        "severity": "CRITICAL",
        "cvss": 9.1,
    },
    {
        "name": "AWS Secret Access Key",
        "pattern": r"(?i)aws_?(?:secret)?_?(?:access)?_?key\s*[:=]\s*['\"]([a-zA-Z0-9/+=]{40})['\"]",
        "cwe": "CWE-798",
        "owasp": "A07:2021 - Identification and Authentication Failures",
        "severity": "CRITICAL",
        "cvss": 9.5,
    },
    {
        "name": "GitHub Personal Access Token",
        "pattern": r"\b(gh[pousr]_[A-Za-z0-9_]{36,255})\b",
        "cwe": "CWE-798",
        "owasp": "A07:2021 - Identification and Authentication Failures",
        "severity": "CRITICAL",
        "cvss": 9.1,
    },
    {
        "name": "Generic Private Key",
        "pattern": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
        "cwe": "CWE-312",
        "owasp": "A02:2021 - Cryptographic Failures",
        "severity": "CRITICAL",
        "cvss": 9.8,
    },
    {
        "name": "Database Connection URL with Credentials",
        "pattern": r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?):\/\/[a-zA-Z0-9_]+:[a-zA-Z0-9_!@#$%^&*()\-+=\[\]{}|:;\"'<>,.?/~`]+@[a-zA-Z0-9.-]+",
        "cwe": "CWE-798",
        "owasp": "A07:2021 - Identification and Authentication Failures",
        "severity": "HIGH",
        "cvss": 8.5,
    },
    {
        "name": "Hardcoded Password Variable",
        "pattern": r"(?i)(?:password|passwd|pwd|secret|api_?key|auth_?token)\s*=\s*['\"][^'\"]{6,}['\"]",
        "cwe": "CWE-798",
        "owasp": "A07:2021 - Identification and Authentication Failures",
        "severity": "HIGH",
        "cvss": 7.8,
    },
    {
        "name": "JSON Web Token (JWT)",
        "pattern": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9._-]{10,}\.[A-Za-z0-9._-]{10,}\b",
        "cwe": "CWE-798",
        "owasp": "A07:2021 - Identification and Authentication Failures",
        "severity": "MEDIUM",
        "cvss": 6.5,
    }
]


class SecretScanner(BaseScanner):
    def __init__(self):
        super().__init__(name="SecretScanner")

    def scan_file(self, file_path: str, content: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            for rule in SECRET_PATTERNS:
                matches = re.finditer(rule["pattern"], line)
                for match in matches:
                    matched_text = match.group(0)
                    # Mask sensitive secret in reported snippet
                    masked = matched_text[:4] + "*" * (max(4, len(matched_text) - 8)) + matched_text[-4:] if len(matched_text) > 8 else "***"
                    snippet = line.replace(matched_text, masked).strip()

                    findings.append(Finding(
                        id=f"SEC-{uuid.uuid4().hex[:6].upper()}",
                        title=f"Hardcoded Secret Detected: {rule['name']}",
                        cwe=rule["cwe"],
                        owasp=rule["owasp"],
                        severity=rule["severity"],
                        cvss=rule["cvss"],
                        file_path=file_path,
                        line_number=idx,
                        snippet=snippet,
                        description=(
                            f"Identified hardcoded credential ({rule['name']}) on line {idx}. "
                            "Hardcoded secrets in source control can lead to complete account compromise."
                        ),
                        remediation="Move secrets to environment variables (.env) or a secret manager (HashiCorp Vault, AWS Secrets Manager).",
                        scanner_name=self.name,
                    ))

        return findings
