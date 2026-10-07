"""
Unit tests for SmartAGENT Red Team and Penetration Testing tools.
Tests: recon, exploit_db, generate_payload, web_attack, post_exploit.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smartagent.agent.tools import ToolRegistry


def test_tool_registry_has_13_tools():
    registry = ToolRegistry(working_dir=".")
    tools = registry.list_tools()
    assert len(tools) == 13, f"Expected 13 tools, found {len(tools)}"
    names = {t.name for t in tools}
    expected = {
        "list_files", "read_file", "search_code", "scan_code",
        "get_cwe_info", "write_report", "run_command", "fix_code",
        "recon", "exploit_db", "generate_payload", "web_attack", "post_exploit"
    }
    assert expected.issubset(names), f"Missing tools: {expected - names}"


def test_recon_tool():
    registry = ToolRegistry(working_dir=".")
    # Test error handling on empty target
    err_res = registry.execute("recon", "")
    assert "Error:" in err_res

    # Test loopback scan on specific port
    res = registry.execute("recon", "127.0.0.1 80")
    assert "Reconnaissance Report" in res
    assert "127.0.0.1" in res


def test_exploit_db_direct_cve():
    registry = ToolRegistry(working_dir=".")
    res = registry.execute("exploit_db", "CVE-2021-44228")
    assert "Log4Shell" in res
    assert "10.0" in res
    assert "remediation" in res.lower()


def test_exploit_db_keyword_search():
    registry = ToolRegistry(working_dir=".")
    res = registry.execute("exploit_db", "apache")
    assert "Apache" in res
    assert "CVE-" in res


def test_generate_payload_sqli():
    registry = ToolRegistry(working_dir=".")
    res = registry.execute("generate_payload", "sqli auth_bypass")
    assert "SQL Injection" in res
    assert "' OR '1'='1' --" in res
    assert "Remediation:" in res


def test_generate_payload_xss():
    registry = ToolRegistry(working_dir=".")
    res = registry.execute("generate_payload", "xss dom")
    assert "Cross-Site Scripting" in res
    assert "<script>" in res or "<img" in res
    assert "Remediation:" in res


def test_generate_payload_revshell():
    registry = ToolRegistry(working_dir=".")
    res = registry.execute("generate_payload", "revshell 192.168.1.50:9001 bash")
    assert "192.168.1.50" in res
    assert "9001" in res
    assert "bash -i" in res


def test_web_attack_headers():
    registry = ToolRegistry(working_dir=".")
    # Test error handling on empty URL
    err_res = registry.execute("web_attack", "")
    assert "Error:" in err_res

    # Test headers mode against invalid/closed port without crashing
    res = registry.execute("web_attack", "http://127.0.0.1:59999 headers")
    assert "Web Attack Surface" in res or "Connection failed" in res


def test_post_exploit_linux():
    registry = ToolRegistry(working_dir=".")
    res = registry.execute("post_exploit", "linux privesc")
    assert "Linux Privilege Escalation" in res
    assert "SUID" in res
    assert "sudo" in res


def test_post_exploit_windows():
    registry = ToolRegistry(working_dir=".")
    res = registry.execute("post_exploit", "windows persistence")
    assert "Windows Persistence" in res
    assert "Registry" in res or "Run" in res


def test_post_exploit_ad():
    registry = ToolRegistry(working_dir=".")
    res = registry.execute("post_exploit", "ad")
    assert "Active Directory" in res
    assert "Kerberoasting" in res


if __name__ == "__main__":
    print("Running SmartAGENT Red Team Tool tests...")
    test_tool_registry_has_13_tools()
    print("  [OK] test_tool_registry_has_13_tools passed")
    test_recon_tool()
    print("  [OK] test_recon_tool passed")
    test_exploit_db_direct_cve()
    print("  [OK] test_exploit_db_direct_cve passed")
    test_exploit_db_keyword_search()
    print("  [OK] test_exploit_db_keyword_search passed")
    test_generate_payload_sqli()
    print("  [OK] test_generate_payload_sqli passed")
    test_generate_payload_xss()
    print("  [OK] test_generate_payload_xss passed")
    test_generate_payload_revshell()
    print("  [OK] test_generate_payload_revshell passed")
    test_web_attack_headers()
    print("  [OK] test_web_attack_headers passed")
    test_post_exploit_linux()
    print("  [OK] test_post_exploit_linux passed")
    test_post_exploit_windows()
    print("  [OK] test_post_exploit_windows passed")
    test_post_exploit_ad()
    print("  [OK] test_post_exploit_ad passed")
    print("\n[ALL RED TEAM TOOL TESTS PASSED SUCCESSFULLY!]")
