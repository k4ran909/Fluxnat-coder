"""
Security Scorer for SmartAGENT.
Calculates project vulnerability index (0-100) and letter grades (A+ to F).
"""

from typing import List, Dict, Any
from smartagent.scanners.base import Finding


class SecurityScorer:
    # Deductions per verified finding severity
    SEVERITY_WEIGHTS = {
        "CRITICAL": 25.0,
        "HIGH": 12.0,
        "MEDIUM": 5.0,
        "LOW": 2.0,
        "INFO": 0.5,
    }

    @classmethod
    def calculate_score(cls, findings: List[Finding]) -> Dict[str, Any]:
        """Compute project security health grade and breakdown."""
        # Filter out false positives
        active_findings = [f for f in findings if not f.is_false_positive]

        total_deduction = 0.0
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

        for f in active_findings:
            sev = f.severity.upper()
            if sev in counts:
                counts[sev] += 1
                total_deduction += cls.SEVERITY_WEIGHTS.get(sev, 2.0)

        # Baseline score starts at 100
        score = max(0.0, 100.0 - total_deduction)

        # Determine letter grade
        if score >= 95:
            grade = "A+"
            status = "EXCELLENT"
        elif score >= 85:
            grade = "A"
            status = "SECURE"
        elif score >= 75:
            grade = "B"
            status = "ACCEPTABLE"
        elif score >= 60:
            grade = "C"
            status = "MODERATE RISK"
        elif score >= 40:
            grade = "D"
            status = "HIGH RISK"
        else:
            grade = "F"
            status = "CRITICAL HAZARD"

        return {
            "score": round(score, 1),
            "grade": grade,
            "status": status,
            "total_active_findings": len(active_findings),
            "false_positives_filtered": len(findings) - len(active_findings),
            "breakdown": counts,
        }
