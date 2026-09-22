"""
SmartAGENT Scanner Registry.
"""

from smartagent.scanners.base import BaseScanner, Finding
from smartagent.scanners.secret_scanner import SecretScanner
from smartagent.scanners.pattern_scanner import PatternScanner
from smartagent.scanners.dependency_scanner import DependencyScanner
from smartagent.scanners.config_scanner import ConfigScanner

ALL_SCANNERS = [
    SecretScanner(),
    PatternScanner(),
    DependencyScanner(),
    ConfigScanner(),
]

__all__ = [
    "BaseScanner",
    "Finding",
    "SecretScanner",
    "PatternScanner",
    "DependencyScanner",
    "ConfigScanner",
    "ALL_SCANNERS",
]
