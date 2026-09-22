import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pytest
except ImportError:
    pytest = None
from smartagent.scanners.secret_scanner import SecretScanner
from smartagent.scanners.pattern_scanner import PatternScanner
from smartagent.scanners.dependency_scanner import DependencyScanner
from smartagent.scanners.config_scanner import ConfigScanner
from smartagent.reporting.scorer import SecurityScorer


def test_secret_scanner_detects_aws_key():
    scanner = SecretScanner()
    code = 'aws_key = "AKIAIOSFODNN7EXAMPLE"'
    findings = scanner.scan_file("test.py", code)
    assert len(findings) == 1
    assert "AWS Access Key ID" in findings[0].title
    assert findings[0].severity == "CRITICAL"


def test_pattern_scanner_detects_sqli():
    scanner = PatternScanner()
    code = 'cursor.execute(f"SELECT * FROM users WHERE id = {uid}")'
    findings = scanner.scan_file("test.py", code)
    assert len(findings) == 1
    assert "SQL Injection" in findings[0].title
    assert findings[0].cwe == "CWE-89"


def test_pattern_scanner_detects_command_injection():
    scanner = PatternScanner()
    code = 'os.system(f"rm -rf {path}")'
    findings = scanner.scan_file("test.py", code)
    assert len(findings) >= 1
    assert "Command Injection" in findings[0].title
    assert findings[0].cwe == "CWE-78"


def test_pattern_scanner_clean_code_no_findings():
    scanner = PatternScanner()
    code = '''
def add(a: int, b: int) -> int:
    return a + b
'''
    findings = scanner.scan_file("test.py", code)
    assert len(findings) == 0


def test_config_scanner_dockerfile_root():
    scanner = ConfigScanner()
    content = """
FROM python:3.11-slim
COPY . /app
CMD ["python", "app.py"]
"""
    findings = scanner.scan_file("Dockerfile", content)
    assert any("Default Root User" in f.title for f in findings)


def test_security_scorer():
    scanner = PatternScanner()
    code = 'cursor.execute(f"SELECT * FROM users WHERE id = {uid}")'
    findings = scanner.scan_file("test.py", code)
    score_data = SecurityScorer.calculate_score(findings)

    assert score_data["score"] < 100.0
    assert score_data["breakdown"]["CRITICAL"] == 1


if __name__ == "__main__":
    print("Running SmartAGENT unit tests...")
    test_secret_scanner_detects_aws_key()
    print("  [OK] test_secret_scanner_detects_aws_key passed")
    test_pattern_scanner_detects_sqli()
    print("  [OK] test_pattern_scanner_detects_sqli passed")
    test_pattern_scanner_detects_command_injection()
    print("  [OK] test_pattern_scanner_detects_command_injection passed")
    test_pattern_scanner_clean_code_no_findings()
    print("  [OK] test_pattern_scanner_clean_code_no_findings passed")
    test_config_scanner_dockerfile_root()
    print("  [OK] test_config_scanner_dockerfile_root passed")
    test_security_scorer()
    print("  [OK] test_security_scorer passed")
    print("\n[ALL TESTS PASSED SUCCESSFULLY!]")

