"""
Dependency Scanner for SmartAGENT.
Parses dependency manifests (requirements.txt, package.json)
and queries the free Open Source Vulnerabilities (OSV.dev) database for known CVEs.
"""

import re
import json
import uuid
from typing import List, Dict, Any
import requests

from smartagent.scanners.base import BaseScanner, Finding


class DependencyScanner(BaseScanner):
    def __init__(self):
        super().__init__(name="DependencyScanner")
        self.osv_api_url = "https://api.osv.dev/v1/query"

    def scan_file(self, file_path: str, content: str) -> List[Finding]:
        findings: List[Finding] = []

        if file_path.endswith("requirements.txt"):
            findings.extend(self._scan_python_requirements(file_path, content))
        elif file_path.endswith("package.json"):
            findings.extend(self._scan_npm_package_json(file_path, content))

        return findings

    def _query_osv(self, package_name: str, version: str, ecosystem: str) -> List[Dict[str, Any]]:
        """Query OSV API for known vulnerabilities."""
        payload = {
            "version": version,
            "package": {
                "name": package_name,
                "ecosystem": ecosystem
            }
        }
        try:
            resp = requests.post(self.osv_api_url, json=payload, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("vulns", [])
        except Exception:
            # Silent fallback if offline or request blocked
            pass
        return []

    def _scan_python_requirements(self, file_path: str, content: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            line_clean = line.strip()
            if not line_clean or line_clean.startswith("#"):
                continue

            match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*==\s*([a-zA-Z0-9_\-\.]+)$", line_clean)
            if match:
                pkg_name, version = match.groups()
                vulns = self._query_osv(pkg_name, version, "PyPI")
                for v in vulns:
                    vuln_id = v.get("id", "UNKNOWN-CVE")
                    summary = v.get("summary", f"Vulnerability detected in {pkg_name} {version}")
                    details = v.get("details", summary)

                    findings.append(Finding(
                        id=f"DEP-{uuid.uuid4().hex[:6].upper()}",
                        title=f"Vulnerable Dependency: {pkg_name}=={version} ({vuln_id})",
                        cwe="CWE-1104",
                        owasp="A06:2021 - Vulnerable and Outdated Components",
                        severity="HIGH",
                        cvss=7.5,
                        file_path=file_path,
                        line_number=idx,
                        snippet=line_clean,
                        description=f"Package '{pkg_name}' version {version} is affected by {vuln_id}: {summary}",
                        remediation=f"Upgrade '{pkg_name}' to a patched release version.",
                        scanner_name=self.name,
                    ))

        return findings

    def _scan_npm_package_json(self, file_path: str, content: str) -> List[Finding]:
        findings: List[Finding] = []
        try:
            data = json.loads(content)
        except Exception:
            return findings

        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        for pkg_name, raw_ver in deps.items():
            # Clean semantic version
            version = re.sub(r"^[\^~>=<]+", "", raw_ver).strip()
            if re.match(r"^\d+\.\d+\.\d+", version):
                vulns = self._query_osv(pkg_name, version, "npm")
                for v in vulns:
                    vuln_id = v.get("id", "UNKNOWN-CVE")
                    summary = v.get("summary", f"Vulnerability detected in {pkg_name} {version}")

                    findings.append(Finding(
                        id=f"DEP-{uuid.uuid4().hex[:6].upper()}",
                        title=f"Vulnerable NPM Dependency: {pkg_name}@{version} ({vuln_id})",
                        cwe="CWE-1104",
                        owasp="A06:2021 - Vulnerable and Outdated Components",
                        severity="HIGH",
                        cvss=7.5,
                        file_path=file_path,
                        line_number=1,
                        snippet=f'"{pkg_name}": "{raw_ver}"',
                        description=f"Package '{pkg_name}' version {version} is affected by {vuln_id}: {summary}",
                        remediation=f"Upgrade '{pkg_name}' using `npm update {pkg_name}` or `npm audit fix`.",
                        scanner_name=self.name,
                    ))

        return findings
