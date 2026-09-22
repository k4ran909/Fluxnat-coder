"""
AI Judge Module for SmartAGENT.
Leverages Fluxnat Coder 3B to verify static findings, eliminate false positives,
and generate contextual, secure code remediations.
"""

import os
import re
from typing import List, Optional
from smartagent.scanners.base import Finding
from smartagent.ai.model import ModelManager
from smartagent.ai.prompts import FLUXNAT_SYSTEM_PROMPT, VERIFY_FINDING_PROMPT


class AIJudge:
    def __init__(self, model_id: str = "fluxnat/Fluxnat-Coder-3B"):
        self.model_manager = ModelManager.get_instance(model_id=model_id)

    def verify_findings(self, findings: List[Finding], max_ai_verifications: int = 20) -> List[Finding]:
        """Review findings with Fluxnat Coder 3B to eliminate false positives and enrich fixes."""
        if not findings:
            return findings

        verified_count = 0
        for finding in findings:
            # Only run AI on findings that have source code context
            if verified_count >= max_ai_verifications:
                break

            context = self._get_code_context(finding.file_path, finding.line_number)
            if not context:
                continue

            user_prompt = VERIFY_FINDING_PROMPT.format(
                file_path=finding.file_path,
                line_number=finding.line_number,
                title=finding.title,
                cwe=finding.cwe,
                code_context=context,
            )

            messages = [
                {"role": "system", "content": FLUXNAT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]

            try:
                ai_response = self.model_manager.generate(messages, max_tokens=600, temperature=0.1)
                self._apply_ai_judgment(finding, ai_response)
                verified_count += 1
            except Exception as e:
                # If model inference fails (e.g. no GPU or model not yet downloaded), leave finding as-is
                finding.ai_verified = False

        return findings

    def _get_code_context(self, file_path: str, line_num: int, window: int = 10) -> Optional[str]:
        """Extract lines of code around the flagged location."""
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            start = max(0, line_num - window - 1)
            end = min(len(lines), line_num + window)

            snippet_lines = []
            for i in range(start, end):
                prefix = ">> " if i + 1 == line_num else "   "
                snippet_lines.append(f"{prefix}{i+1}: {lines[i].rstrip()}")

            return "\n".join(snippet_lines)
        except Exception:
            return None

    def _apply_ai_judgment(self, finding: Finding, ai_output: str):
        """Parse AI output and update finding attributes."""
        finding.ai_verified = True

        out_lower = ai_output.lower()
        if "status: false positive" in out_lower or "is a false positive" in out_lower:
            finding.is_false_positive = True
            finding.severity = "INFO"

        # Check for refined severity
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            if f"refined severity: {sev.lower()}" in out_lower:
                finding.severity = sev
                break

        # Extract fix block if present
        fix_match = re.search(r"Fix:\s*```[a-zA-Z0-9_-]*\n(.*?)```", ai_output, re.DOTALL)
        if fix_match:
            finding.remediation = fix_match.group(1).strip()
        else:
            finding.remediation = (finding.remediation or "") + f"\n\n[Fluxnat Coder 3B Analysis]:\n{ai_output}"
