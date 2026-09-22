"""
Conversation Memory for SmartAGENT.
Manages chat history with a sliding window to stay within 3B model context limits.
"""

from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field


@dataclass
class AgentMemory:
    """Sliding-window conversation memory for the agentic loop."""

    messages: List[Dict[str, str]] = field(default_factory=list)
    scanned_files: Set[str] = field(default_factory=set)
    findings: List[Dict] = field(default_factory=list)
    max_messages: int = 20  # sliding window size

    def add_message(self, role: str, content: str):
        """Add a message and trim if over the window size."""
        self.messages.append({"role": role, "content": content})
        self._trim()

    def add_finding(self, finding: Dict):
        """Track a finding discovered during the agent loop."""
        self.findings.append(finding)

    def mark_scanned(self, file_path: str):
        """Record that a file has been scanned."""
        self.scanned_files.add(file_path)

    def get_messages(self) -> List[Dict[str, str]]:
        """Return the current message window."""
        return list(self.messages)

    def get_findings_summary(self) -> str:
        """Return a brief summary of accumulated findings."""
        if not self.findings:
            return "No findings yet."
        lines = []
        for i, f in enumerate(self.findings, 1):
            sev = f.get("severity", "UNKNOWN")
            title = f.get("title", "Untitled")
            path = f.get("file_path", "unknown")
            lines.append(f"  {i}. [{sev}] {title} — {path}")
        return "\n".join(lines)

    def clear(self):
        """Reset all memory."""
        self.messages.clear()
        self.scanned_files.clear()
        self.findings.clear()

    def _trim(self):
        """Keep only the system message + last N messages."""
        if len(self.messages) <= self.max_messages:
            return
        # Always preserve the first message (system prompt)
        system = [self.messages[0]] if self.messages[0]["role"] == "system" else []
        rest = self.messages[len(system):]
        # Keep the most recent messages
        keep = self.max_messages - len(system)
        self.messages = system + rest[-keep:]
