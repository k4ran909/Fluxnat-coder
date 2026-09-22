"""
Configuration and Infrastructure Scanner for SmartAGENT.
Scans Dockerfiles, .env files, and deployment configurations for security misconfigurations.
"""

import re
import uuid
from typing import List
from smartagent.scanners.base import BaseScanner, Finding


class ConfigScanner(BaseScanner):
    def __init__(self):
        super().__init__(name="ConfigScanner")

    def scan_file(self, file_path: str, content: str) -> List[Finding]:
        findings: List[Finding] = []
        filename = file_path.replace("\\", "/").split("/")[-1].lower()

        if "dockerfile" in filename:
            findings.extend(self._scan_dockerfile(file_path, content))
        elif filename == ".env" or filename.endswith(".env"):
            findings.extend(self._scan_env_file(file_path, content))

        return findings

    def _scan_dockerfile(self, file_path: str, content: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = content.splitlines()

        has_user_directive = False
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            if stripped.upper().startswith("USER "):
                has_user_directive = True

            # Check for latest tag
            if stripped.upper().startswith("FROM ") and (":latest" in stripped or ":" not in stripped.split()[1]):
                findings.append(Finding(
                    id=f"CFG-{uuid.uuid4().hex[:6].upper()}",
                    title="Dockerfile Uses Mutable/Unpinned Base Image Tag",
                    cwe="CWE-1104",
                    owasp="A05:2021 - Security Misconfiguration",
                    severity="LOW",
                    cvss=3.7,
                    file_path=file_path,
                    line_number=idx,
                    snippet=stripped,
                    description="Using ':latest' or unpinned base images can lead to non-reproducible builds and unexpected breaking vulnerabilities.",
                    remediation="Pin base images to specific version tags or digests (e.g. `FROM python:3.11-slim@sha256:...`).",
                    scanner_name=self.name,
                ))

            # Check for exposed SSH
            if stripped.upper().startswith("EXPOSE ") and "22" in stripped:
                findings.append(Finding(
                    id=f"CFG-{uuid.uuid4().hex[:6].upper()}",
                    title="Container Exposes SSH Port 22",
                    cwe="CWE-284",
                    owasp="A05:2021 - Security Misconfiguration",
                    severity="HIGH",
                    cvss=7.5,
                    file_path=file_path,
                    line_number=idx,
                    snippet=stripped,
                    description="Running SSH inside standard application containers increases attack surface unnecessarily.",
                    remediation="Remove SSH server from container; use orchestrator exec mechanisms (e.g. `kubectl exec`, `docker exec`).",
                    scanner_name=self.name,
                ))

        if not has_user_directive and len(lines) > 2:
            findings.append(Finding(
                id=f"CFG-{uuid.uuid4().hex[:6].upper()}",
                title="Container Runs as Default Root User",
                cwe="CWE-250",
                owasp="A05:2021 - Security Misconfiguration",
                severity="MEDIUM",
                cvss=6.5,
                file_path=file_path,
                line_number=1,
                snippet="FROM ... (No USER instruction specified)",
                description="The container does not define a non-root USER. If an attacker breaches the app, they gain root privileges inside the container.",
                remediation="Add a non-root user (e.g. `RUN useradd -u 1000 appuser && USER appuser`).",
                scanner_name=self.name,
            ))

        return findings

    def _scan_env_file(self, file_path: str, content: str) -> List[Finding]:
        findings: List[Finding] = []
        if not file_path.endswith(".example") and not file_path.endswith(".template"):
            findings.append(Finding(
                id=f"CFG-{uuid.uuid4().hex[:6].upper()}",
                title="Committed .env File Detected in Repository",
                cwe="CWE-540",
                owasp="A05:2021 - Security Misconfiguration",
                severity="HIGH",
                cvss=7.5,
                file_path=file_path,
                line_number=1,
                snippet=".env file committed to source tree",
                description="Live .env files contain environment-specific secrets. Committing them risks exposing database credentials and API keys.",
                remediation="Add `.env` to `.gitignore` and maintain a safe `.env.example` file instead.",
                scanner_name=self.name,
            ))

        return findings
