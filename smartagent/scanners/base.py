"""
Base Scanner Interfaces and Data Models for SmartAGENT.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Finding(BaseModel):
    id: str = Field(..., description="Unique finding ID")
    title: str = Field(..., description="Short finding summary")
    cwe: str = Field(default="CWE-Unknown", description="MITRE CWE identifier")
    owasp: str = Field(default="Unknown", description="OWASP category")
    severity: str = Field(default="MEDIUM", description="CRITICAL, HIGH, MEDIUM, LOW, INFO")
    cvss: float = Field(default=5.0, description="Estimated CVSS score (0.0 - 10.0)")
    file_path: str = Field(..., description="Path to file containing finding")
    line_number: int = Field(default=1, description="Line number of code match")
    snippet: str = Field(..., description="Code snippet flagged")
    description: str = Field(..., description="Detailed description of vulnerability")
    remediation: Optional[str] = Field(default=None, description="Suggested secure fix")
    scanner_name: str = Field(..., description="Name of scanner that generated finding")
    ai_verified: bool = Field(default=False, description="Whether reviewed by Fluxnat Coder 3B")
    is_false_positive: bool = Field(default=False, description="Flagged as false positive by AI")


class BaseScanner(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def scan_file(self, file_path: str, content: str) -> List[Finding]:
        """Scan a single file content and return findings."""
        pass
