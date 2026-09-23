#!/usr/bin/env python3
"""
Generate comprehensive, multi-language, balanced Chain-of-Thought (CoT)
cybersecurity training samples for Fluxnat Coder 3B.
Fixes CWE classification bias and ensures accurate multi-class discrimination.
"""

import json
from pathlib import Path

SYSTEM_PROMPT = (
    "You are Fluxnat Coder 3B, an elite AI cybersecurity and secure coding intelligence model created by Fluxnat. "
    "Your mission is to perform rigorous source code vulnerability auditing, identify CWE and OWASP Top 10 security flaws, "
    "explain attack surfaces and root causes using detailed step-by-step reasoning, and provide production-ready secure remediations."
)

DATASET = [
    # =========================================================================
    # CWE-502: Insecure Deserialization
    # =========================================================================
    {
        "prompt": """Audit this Java method for security vulnerabilities:

public Object processSerializedData(byte[] incomingBytes) throws Exception {
    ByteArrayInputStream bais = new ByteArrayInputStream(incomingBytes);
    ObjectInputStream ois = new ObjectInputStream(bais);
    return ois.readObject();
}""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** Critical (CVSS 9.8)
**Vulnerability:** Deserialization of Untrusted Data
**CWE:** CWE-502 (Deserialization of Untrusted Data)
**OWASP:** A08:2021 - Software and Data Integrity Failures

#### Root Cause & Step-by-Step Reasoning:
1. **Untrusted Input:** The method takes raw `incomingBytes` from an external source without validation.
2. **Unrestricted Object Instantiation:** `ObjectInputStream.readObject()` automatically deserializes serialized Java objects. If vulnerable gadget classes (e.g. Apache Commons Collections, Spring) exist on the application classpath, deserialization triggers arbitrary method invocations during object reconstruction.
3. **Impact:** Remote Code Execution (RCE) with the full privileges of the JVM process.

#### Secure Remediation:
Do not use Java native serialization for untrusted data. Use safe, structured formats such as JSON (Jackson with safe default typing), Protocol Buffers, or enforce strict object lookahead filtering via `ValidatingObjectInputStream` or Java 9+ serialization filters (`ObjectInputFilter`).

```java
import java.io.ObjectInputFilter;

public Object processFilteredData(byte[] incomingBytes) throws Exception {
    ByteArrayInputStream bais = new ByteArrayInputStream(incomingBytes);
    ObjectInputStream ois = new ObjectInputStream(bais);
    // Allowlist only safe classes
    ObjectInputFilter filter = ObjectInputFilter.Config.createFilter("com.example.model.SafeData;!*");
    ois.setObjectInputFilter(filter);
    return ois.readObject();
}
```"""
    },
    {
        "prompt": """Review this Python endpoint for deserialization risks:

import pickle
import base64
from flask import request

@app.route('/api/load_state', methods=['POST'])
def load_state():
    token = request.headers.get('X-State-Token')
    data = base64.b64decode(token)
    user_state = pickle.loads(data)
    return f"Loaded state for {user_state.user}"
""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** Critical (CVSS 9.8)
**Vulnerability:** Insecure Deserialization
**CWE:** CWE-502 (Deserialization of Untrusted Data)
**OWASP:** A08:2021 - Software and Data Integrity Failures

#### Root Cause & Step-by-Step Reasoning:
1. **Source:** `X-State-Token` header supplies client-controlled base64 bytes directly to the application.
2. **Sink:** `pickle.loads(data)` reconstructs arbitrary Python objects. Python's pickle protocol supports the `__reduce__` method, which allows an object to specify a callable and arguments to execute during unpacking (e.g., `os.system`).
3. **Impact:** Immediate unauthenticated Remote Code Execution (RCE) on the host server.

#### Secure Remediation:
Never pass untrusted data to `pickle`. Use JSON parsing with strict schema validation or cryptographically signed tokens (e.g. `itsdangerous.URLSafeSerializer` with HMAC).

```python
import json
from flask import request, abort

@app.route('/api/load_state', methods=['POST'])
def load_state():
    data = request.get_json(silent=True)
    if not data or 'user' not in data:
        abort(400, description="Invalid payload")
    return f"Loaded state for {data['user']}"
```"""
    },
    {
        "prompt": """Check this Python YAML configuration loader for vulnerabilities:

import yaml

def parse_user_config(yaml_string: str):
    return yaml.load(yaml_string)
""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** Critical (CVSS 9.8)
**Vulnerability:** Deserialization of Untrusted Data via PyYAML
**CWE:** CWE-502 (Deserialization of Untrusted Data)
**OWASP:** A08:2021 - Software and Data Integrity Failures

#### Root Cause & Step-by-Step Reasoning:
1. **Unsafe Loader:** Calling `yaml.load()` without specifying a safe loader allows custom YAML tags (such as `!!python/object/apply:subprocess.Popen`) to instantiate arbitrary Python objects.
2. **Sink:** PyYAML executes the specified constructors dynamically when parsing the YAML structure.
3. **Impact:** Arbitrary command execution and system compromise via untrusted YAML input.

#### Secure Remediation:
Always use `yaml.safe_load()` or explicitly pass `Loader=yaml.SafeLoader` to restrict parsing exclusively to standard YAML data types.

```python
import yaml

def parse_user_config(yaml_string: str):
    return yaml.safe_load(yaml_string)
```"""
    },
    {
        "prompt": """Audit this Node.js endpoint for security flaws:

const serialize = require('node-serialize');

app.post('/profile', (req, res) => {
    if (req.cookies.profile) {
        const obj = serialize.unserialize(req.cookies.profile);
        res.send(`Hello ${obj.name}`);
    }
});""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** Critical (CVSS 9.8)
**Vulnerability:** Insecure Deserialization in Node.js
**CWE:** CWE-502 (Deserialization of Untrusted Data)
**OWASP:** A08:2021 - Software and Data Integrity Failures

#### Root Cause & Step-by-Step Reasoning:
1. **Taint Source:** `req.cookies.profile` is received directly from the client request.
2. **Sink:** `node-serialize.unserialize()` supports Immediate Function Invocation (IIFE) via `_$$ND_FUNC$$_` markers within serialized strings.
3. **Impact:** Arbitrary JavaScript code execution inside the Node.js event loop, allowing reverse shells and host compromise.

#### Secure Remediation:
Use standard `JSON.parse()` instead of dynamic object serialization libraries.

```javascript
app.post('/profile', (req, res) => {
    try {
        const obj = JSON.parse(req.cookies.profile || '{}');
        res.send(`Hello ${encodeURIComponent(obj.name || 'Guest')}`);
    } catch (e) {
        res.status(400).send('Invalid profile cookie');
    }
});
```"""
    },

    # =========================================================================
    # CWE-79: Cross-Site Scripting (XSS)
    # =========================================================================
    {
        "prompt": """Audit this PHP code for web security vulnerabilities:

<?php
$search = $_GET['q'];
echo "<h1>Search results for: " . $search . "</h1>";
?>""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 7.1)
**Vulnerability:** Reflected Cross-Site Scripting (XSS)
**CWE:** CWE-79 (Improper Neutralization of Input During Web Page Generation)
**OWASP:** A03:2021 - Injection

#### Root Cause & Step-by-Step Reasoning:
1. **Source:** `$_GET['q']` reads untrusted query parameters directly from the client.
2. **Sink:** Direct string concatenation and echoing into the HTML response stream without context-aware output encoding.
3. **Impact:** Attackers can inject arbitrary HTML/JavaScript tags (e.g., `<script>alert(document.cookie)</script>`). When a victim clicks the malicious link, the script executes within their browser context, leading to session hijacking, credential theft, or page defacement.

#### Secure Remediation:
Apply HTML entity encoding using `htmlspecialchars()` with `ENT_QUOTES` and specify UTF-8 encoding.

```php
<?php
$search = isset($_GET['q']) ? $_GET['q'] : '';
echo "<h1>Search results for: " . htmlspecialchars($search, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8') . "</h1>";
?>
```"""
    },
    {
        "prompt": """Review this React component for XSS risks:

function UserComment({ commentText }) {
    return (
        <div className="comment-box">
            <span dangerouslySetInnerHTML={{ __html: commentText }} />
        </div>
    );
}""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 7.2)
**Vulnerability:** Stored / Cross-Site Scripting (XSS) via React dangerouslySetInnerHTML
**CWE:** CWE-79 (Improper Neutralization of Input During Web Page Generation)
**OWASP:** A03:2021 - Injection

#### Root Cause & Step-by-Step Reasoning:
1. **Bypass of Built-in Escaping:** React automatically escapes variables rendered inside JSX. However, `dangerouslySetInnerHTML` explicitly disables this protection.
2. **Sink:** Direct injection of unescaped HTML/JavaScript strings into the DOM tree.
3. **Impact:** If `commentText` originates from user submissions without server-side purification, persistent XSS is executed against all viewers.

#### Secure Remediation:
Render standard JSX elements directly so React safely escapes strings, or sanitize using DOMPurify before assigning to innerHTML.

```jsx
import DOMPurify from 'dompurify';

function UserComment({ commentText }) {
    // If rich HTML is strictly required:
    const cleanHtml = DOMPurify.sanitize(commentText);
    return (
        <div className="comment-box">
            <span dangerouslySetInnerHTML={{ __html: cleanHtml }} />
        </div>
    );
    // Otherwise render plain text: <span>{commentText}</span>
}
```"""
    },
    {
        "prompt": """Check this client-side JavaScript snippet for security issues:

const hash = decodeURIComponent(window.location.hash.substring(1));
document.getElementById("output").innerHTML = "Welcome " + hash;""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 7.3)
**Vulnerability:** DOM-Based Cross-Site Scripting (DOM XSS)
**CWE:** CWE-79 (Improper Neutralization of Input During Web Page Generation)
**OWASP:** A03:2021 - Injection

#### Root Cause & Step-by-Step Reasoning:
1. **DOM Source:** `window.location.hash` is fully controllable by external actors via URL manipulation.
2. **DOM Sink:** Assigning to `.innerHTML` parses and executes any HTML and script fragments contained in the string.
3. **Execution Context:** The payload executes immediately in the victim's browser session without requiring server round-trips.

#### Secure Remediation:
Use safe DOM text manipulation properties like `textContent` or `innerText`, which treat inputs strictly as plain text.

```javascript
const hash = decodeURIComponent(window.location.hash.substring(1));
document.getElementById("output").textContent = "Welcome " + hash;
```"""
    },

    # =========================================================================
    # CWE-918: Server-Side Request Forgery (SSRF)
    # =========================================================================
    {
        "prompt": """Audit this Python Flask endpoint for security vulnerabilities:

import requests
from flask import request

@app.route('/fetch-avatar')
def fetch_avatar():
    image_url = request.args.get('url')
    response = requests.get(image_url, timeout=5)
    return response.content""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 8.6)
**Vulnerability:** Server-Side Request Forgery (SSRF)
**CWE:** CWE-918 (Server-Side Request Forgery)
**OWASP:** A10:2021 - Server-Side Request Forgery

#### Root Cause & Step-by-Step Reasoning:
1. **Source:** `image_url` is fetched directly from client query parameters without domain validation or scheme restriction.
2. **Sink:** `requests.get()` initiates an outbound HTTP request from the server's internal network environment.
3. **Impact:** Attackers can supply internal IP addresses (e.g. `http://127.0.0.1:8000/admin`, `http://192.168.1.10`) or cloud metadata endpoints (`http://169.254.169.254/latest/meta-data/`) to extract IAM credentials, tokens, and internal network architecture details.

#### Secure Remediation:
Enforce protocol restrictions (HTTPS only), parse and resolve hostnames to IP addresses, verify that target IPs do not fall into private, loopback, or cloud link-local CIDRs (RFC 1918 / RFC 3927), and restrict requests to an approved domain allowlist.

```python
import ipaddress
import urllib.parse
import socket
import requests
from flask import request, abort

ALLOWED_DOMAINS = {"cdn.example.com", "avatars.example.com"}

@app.route('/fetch-avatar')
def fetch_avatar():
    url = request.args.get('url', '')
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_DOMAINS:
        abort(400, description="Invalid image source")
    
    # Resolve and verify IP is not internal
    ip = socket.gethostbyname(parsed.hostname)
    ip_obj = ipaddress.ip_address(ip)
    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
        abort(403, description="Access to private IP rejected")
        
    res = requests.get(url, timeout=3, allow_redirects=False)
    return res.content
```"""
    },
    {
        "prompt": """What security risk exists in this Go HTTP handler?

func serveDoc(w http.ResponseWriter, r *http.Request) {
    targetUrl := r.URL.Query().Get("url")
    resp, err := http.Get(targetUrl)
    if err != nil {
        http.Error(w, err.Error(), 500)
        return
    }
    defer resp.Body.Close()
    io.Copy(w, resp.Body)
}""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 8.6)
**Vulnerability:** Server-Side Request Forgery (SSRF)
**CWE:** CWE-918 (Server-Side Request Forgery)
**OWASP:** A10:2021 - Server-Side Request Forgery

#### Root Cause & Step-by-Step Reasoning:
1. **Taint Source:** `r.URL.Query().Get("url")` captures unverified URLs directly from the caller.
2. **Sink:** `http.Get()` issues an HTTP request from inside the server's network perimeter.
3. **Perimeter Bypass:** Attackers can pivot through the server to scan internal network ports, reach unauthenticated microservices, or read cloud metadata at `169.254.169.254`.

#### Secure Remediation:
Validate URL scheme, perform DNS resolution prior to connection, and ensure IP addresses do not belong to private or reserved subnets (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16)."""
    },
    {
        "prompt": """Review this Node.js proxy handler for security vulnerabilities:

const express = require('express');
const axios = require('axios');
const app = express();

app.get('/proxy', async (req, res) => {
    const target = req.query.target;
    const response = await axios.get(target);
    res.send(response.data);
});""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 8.6)
**Vulnerability:** Server-Side Request Forgery (SSRF)
**CWE:** CWE-918 (Server-Side Request Forgery)
**OWASP:** A10:2021 - Server-Side Request Forgery

#### Root Cause & Step-by-Step Reasoning:
1. **Unrestricted Ingestion:** `req.query.target` accepts arbitrary URLs without validation.
2. **Network Pivot:** `axios.get(target)` issues requests with server identity, allowing attackers to access internal endpoints like `http://169.254.169.254` (cloud metadata) or internal Redis/Elasticsearch ports.

#### Secure Remediation:
Implement domain allowlisting and IP resolution checks before sending requests."""
    },

    # =========================================================================
    # CWE-120: Buffer Overflow / Memory Safety
    # =========================================================================
    {
        "prompt": """Review this C function for memory safety flaws:

void copy_user_token(const char *token) {
    char local_buffer[64];
    strcpy(local_buffer, token);
}""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** Critical (CVSS 9.8)
**Vulnerability:** Buffer Copy without Checking Size of Input (Classic Buffer Overflow)
**CWE:** CWE-120 (Buffer Copy without Checking Size of Input)
**OWASP:** A03:2021 - Injection

#### Root Cause & Step-by-Step Reasoning:
1. **Unbounded Copy:** `strcpy` copies characters from source pointer `token` into `local_buffer` until finding a null terminator (`\\0`), without checking the size of `local_buffer` (64 bytes).
2. **Stack Smashing:** An input string longer than 63 characters overwrites the stack frame, including the saved frame pointer (EBP/RBP) and the function return address (EIP/RIP).
3. **Impact:** Arbitrary code execution or process crashes (Denial of Service).

#### Secure Remediation:
Replace `strcpy` with bounded copy functions such as `snprintf` or `strncpy` with explicit null termination, or validate length before copying.

```c
#include <string.h>
#include <stdio.h>

void copy_user_token(const char *token) {
    char local_buffer[64];
    if (token == NULL) return;
    snprintf(local_buffer, sizeof(local_buffer), "%s", token);
}
```"""
    },
    {
        "prompt": """Audit this C program for buffer vulnerabilities:

#include <stdio.h>

void get_input() {
    char name[128];
    printf("Enter name: ");
    gets(name);
}""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** Critical (CVSS 9.8)
**Vulnerability:** Use of Inherently Dangerous Function (Buffer Overflow)
**CWE:** CWE-120 (Buffer Copy without Checking Size of Input)
**OWASP:** A03:2021 - Injection

#### Root Cause & Step-by-Step Reasoning:
1. **Inherently Unsafe Function:** `gets()` does not accept a buffer size parameter and will read input indefinitely from standard input until encountering a newline or EOF.
2. **Stack Overflow:** Input exceeding 127 bytes will overwrite adjacent stack variables and the return pointer.
3. **Standard Status:** `gets()` is deprecated in C99 and removed in C11 due to its fundamental inability to prevent buffer overflows.

#### Secure Remediation:
Use `fgets()` specifying the buffer size and the input stream (`stdin`).

```c
#include <stdio.h>

void get_input() {
    char name[128];
    printf("Enter name: ");
    if (fgets(name, sizeof(name), stdin) != NULL) {
        // Input safely bounded
    }
}
```"""
    },
    {
        "prompt": """Review this C string formatting function:

void format_log(const char *msg) {
    char buffer[256];
    sprintf(buffer, "LOG: %s", msg);
}""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 7.8)
**Vulnerability:** Unbounded String Formatting (Buffer Overflow)
**CWE:** CWE-120 (Buffer Copy without Checking Size of Input)
**OWASP:** A03:2021 - Injection

#### Root Cause & Step-by-Step Reasoning:
1. **Missing Bounds Limit:** `sprintf()` formats and writes arbitrary length strings into `buffer[256]` without length restriction.
2. **Overflow:** If `msg` exceeds 250 characters, `buffer` overflows on the stack.

#### Secure Remediation:
Use `snprintf()` specifying the maximum destination buffer size.

```c
void format_log(const char *msg) {
    char buffer[256];
    snprintf(buffer, sizeof(buffer), "LOG: %s", msg ? msg : "");
}
```"""
    },

    # =========================================================================
    # CWE-798: Hardcoded Credentials
    # =========================================================================
    {
        "prompt": """Audit this Python script for hardcoded secrets:

AWS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def connect_s3():
    return boto3.client('s3', aws_access_key_id=AWS_KEY_ID, aws_secret_access_key=AWS_SECRET)""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 7.5)
**Vulnerability:** Use of Hard-coded Credentials
**CWE:** CWE-798 (Use of Hard-coded Credentials)
**OWASP:** A07:2021 - Identification and Authentication Failures

#### Root Cause & Step-by-Step Reasoning:
1. **Plaintext Embedding:** AWS access key and secret credentials are embedded directly as plaintext string literals in source code.
2. **Exposure Vector:** Code committed to repositories or build artifacts exposes long-lived infrastructure credentials to unauthorized developers, CI logs, or public leaks.
3. **Impact:** Complete administrative compromise of associated AWS resources and data.

#### Secure Remediation:
Remove hardcoded credentials from source code. Retrieve credentials dynamically from environment variables, AWS IAM roles, or secret management vaults.

```python
import os
import boto3

def connect_s3():
    # Automatically resolves credentials from environment variables or IAM instance profiles
    return boto3.client('s3')
```"""
    },
    {
        "prompt": """Check this Node.js JWT verification code for credentials issues:

const jwt = require('jsonwebtoken');
const JWT_SECRET = "MySuperSecretKey123!@#";

function verifyToken(token) {
    return jwt.verify(token, JWT_SECRET);
}""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 7.5)
**Vulnerability:** Hardcoded Cryptographic Key / Secret
**CWE:** CWE-798 (Use of Hard-coded Credentials)
**OWASP:** A07:2021 - Identification and Authentication Failures

#### Root Cause & Step-by-Step Reasoning:
1. **Embedded Signing Key:** The secret key `MySuperSecretKey123!@#` used to sign and verify JSON Web Tokens is hardcoded into the source code.
2. **Impact:** Anyone with read access to the codebase can forge valid JWT tokens for any user or administrator, bypassing authentication completely.

#### Secure Remediation:
Load cryptographic secrets from environment variables or a dedicated secrets manager.

```javascript
const jwt = require('jsonwebtoken');
const JWT_SECRET = process.env.JWT_SECRET;

if (!JWT_SECRET) {
    throw new Error("JWT_SECRET environment variable is missing");
}

function verifyToken(token) {
    return jwt.verify(token, JWT_SECRET);
}
```"""
    },
    {
        "prompt": """Audit this database connection setup in Python:

import psycopg2

def get_connection():
    return psycopg2.connect(
        host="db.internal.company.com",
        user="postgres",
        password="ProductionPassword2024!",
        dbname="customer_data"
    )""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 7.5)
**Vulnerability:** Hardcoded Database Password
**CWE:** CWE-798 (Use of Hard-coded Credentials)
**OWASP:** A07:2021 - Identification and Authentication Failures

#### Root Cause & Step-by-Step Reasoning:
1. **Hardcoded Secret:** Production database password is stored in plaintext in the Python source file.
2. **Exposure:** Any repository access or leak grants full database access to unauthorized parties.

#### Secure Remediation:
Retrieve credentials from environment variables or secret stores."""
    },

    # =========================================================================
    # CWE-89: SQL Injection
    # =========================================================================
    {
        "prompt": """Audit this database query helper in Python:

def fetch_user_record(db, username):
    cursor = db.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** Critical (CVSS 9.8)
**Vulnerability:** SQL Injection
**CWE:** CWE-89 (Improper Neutralization of Special Elements used in an SQL Command)
**OWASP:** A03:2021 - Injection

#### Root Cause & Step-by-Step Reasoning:
1. **Taint Source:** `username` is received from external caller without sanitization.
2. **String Interpolation:** Formatted directly into the SQL string via `f"SELECT ... WHERE username = '{username}'"`.
3. **Execution:** Evaluated by `cursor.execute()`, allowing attackers to break out of data context with `' OR 1=1 --` to extract records or modify data.

#### Secure Remediation:
Use parameterized queries:

```python
def fetch_user_record(db, username):
    cursor = db.cursor()
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    return cursor.fetchone()
```"""
    },

    # =========================================================================
    # CWE-78: OS Command Injection
    # =========================================================================
    {
        "prompt": """Review this Node.js script for command injection:

const { exec } = require('child_process');
app.get('/ping', (req, res) => {
    const host = req.query.host;
    exec(`ping -c 4 ${host}`, (err, stdout) => {
        res.send(stdout);
    });
});""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** Critical (CVSS 9.8)
**Vulnerability:** OS Command Injection
**CWE:** CWE-78 (Improper Neutralization of Special Elements used in an OS Command)
**OWASP:** A03:2021 - Injection

#### Root Cause & Step-by-Step Reasoning:
1. **Untrusted Query Parameter:** `req.query.host` is ingested directly from HTTP query parameters.
2. **Shell Execution:** `child_process.exec()` evaluates the string within a system shell (`sh` or `cmd.exe`).
3. **Payload Injection:** Metacharacters like `;`, `&`, `|` allow attackers to execute arbitrary shell commands with the privileges of the web application.

#### Secure Remediation:
Use `child_process.execFile` with argument arrays and strict IP/hostname regex validation.

```javascript
const { execFile } = require('child_process');
const net = require('net');

app.get('/ping', (req, res) => {
    const host = req.query.host;
    if (!host || !net.isIP(host)) {
        return res.status(400).send("Invalid IP address");
    }
    execFile('ping', ['-c', '4', host], (err, stdout) => {
        if (err) return res.status(500).send("Ping error");
        res.send(stdout);
    });
});
```"""
    },

    # =========================================================================
    # CWE-22: Path Traversal
    # =========================================================================
    {
        "prompt": """Audit this Go file download handler:

func serveDoc(w http.ResponseWriter, r *http.Request) {
    fileName := r.URL.Query().Get("doc")
    data, err := ioutil.ReadFile("/var/www/docs/" + fileName)
    if err != nil {
        http.Error(w, "File not found", 404)
        return
    }
    w.Write(data)
}""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** High (CVSS 7.5)
**Vulnerability:** Path Traversal / Arbitrary File Read
**CWE:** CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)
**OWASP:** A01:2021 - Broken Access Control

#### Root Cause & Step-by-Step Reasoning:
1. **Unsanitized Input:** `fileName` accepts relative traversal sequences (`../`).
2. **Path Resolution:** Concatenating `/var/www/docs/` with `../../../../etc/passwd` escapes the root directory.
3. **Arbitrary Disclosure:** Attackers can read sensitive files across the filesystem.

#### Secure Remediation:
Sanitize with `filepath.Base()` and verify containment using `filepath.Clean()` and `strings.HasPrefix()`."""
    },

    # =========================================================================
    # CWE-95: Eval Injection / Dynamic Code Execution
    # =========================================================================
    {
        "prompt": """Audit this Python calculation helper:

def calculate_expression(user_input: str):
    return eval(user_input)""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Severity:** Critical (CVSS 9.8)
**Vulnerability:** Improper Neutralization of Directives in Dynamically Evaluated Code (Eval Injection)
**CWE:** CWE-95 (Improper Neutralization of Directives in Dynamically Evaluated Code)
**OWASP:** A03:2021 - Injection

#### Root Cause & Step-by-Step Reasoning:
1. **Dynamic Execution:** Python's built-in `eval()` parses and executes arbitrary Python expressions.
2. **Full Scope Access:** An attacker can provide `__import__('os').system('id')` to achieve immediate Remote Code Execution.

#### Secure Remediation:
Replace `eval()` with `ast.literal_eval()` for safe literal parsing, or a dedicated mathematical expression parser.

```python
import ast

def calculate_expression(user_input: str):
    try:
        return ast.literal_eval(user_input)
    except (ValueError, SyntaxError):
        return None
```"""
    },

    # =========================================================================
    # BENIGN / SAFE SAMPLES (Controls for False Positive Prevention)
    # =========================================================================
    {
        "prompt": """Analyze this Python database query function for security issues:

import psycopg2

def get_user_profile(conn, account_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, created_at FROM accounts WHERE id = %s AND active = %s;",
            (account_id, True)
        )
        return cur.fetchone()""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Status:** SECURE / BENIGN
**Severity:** None (CVSS 0.0)
**Vulnerabilities Detected:** None

#### Analysis & Reasoning:
1. **Parameterized Query:** The SQL statement uses parameter placeholders (`%s`) and passes data as a separate tuple `(account_id, True)`.
2. **Separation of Code & Data:** Untrusted inputs cannot break out of data literals to modify query syntax (CWE-89 protected).
3. **Type Safety:** Function enforces `account_id: int`.

#### Conclusion:
Code adheres to secure SQL coding standards. No vulnerabilities detected."""
    },
    {
        "prompt": """Review this Python git helper for command injection risks:

import subprocess

def get_status(repo: str):
    return subprocess.run(['git', '-C', repo, 'status', '--porcelain'], capture_output=True, text=True, shell=False).stdout""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Status:** SECURE / BENIGN
**Severity:** None (CVSS 0.0)
**Vulnerabilities Detected:** None

#### Analysis & Reasoning:
1. **No Shell Interpreter:** `subprocess.run` is called with `shell=False`.
2. **Vector Execution:** Command and flags are passed as an argument list, so metacharacters (`;`, `|`, `&`) are treated as literal strings rather than commands (CWE-78 protected).

#### Conclusion:
Secure subprocess execution."""
    },
    {
        "prompt": """Audit this Go static file serving handler for path traversal flaws:

func serveDoc(w http.ResponseWriter, r *http.Request) {
    base := "/var/www/docs"
    clean := filepath.Clean(filepath.Join(base, filepath.Base(r.URL.Query().Get("file"))))
    if !strings.HasPrefix(clean, base) { http.Error(w, "Denied", 403); return }
    http.ServeFile(w, r, clean)
}""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Status:** SECURE / BENIGN
**Severity:** None (CVSS 0.0)
**Vulnerabilities Detected:** None

#### Analysis & Reasoning:
1. **Basename Sanitization:** `filepath.Base` strips all directory components and traversal sequences.
2. **Canonicalization:** `filepath.Clean` resolves path redundancies.
3. **Containment Check:** `strings.HasPrefix` guarantees the resolved target resides within the `base` root (CWE-22 protected).

#### Conclusion:
Robust boundary validation."""
    },
    {
        "prompt": """Inspect this client-side JavaScript rendering code for XSS vulnerabilities:

function displayUser(input) {
    const el = document.getElementById('username');
    el.textContent = input;
}""",
        "response": """### Security Assessment by Fluxnat Coder 3B

**Status:** SECURE / BENIGN
**Severity:** None (CVSS 0.0)
**Vulnerabilities Detected:** None

#### Analysis & Reasoning:
1. **Text Node Assignment:** Uses `textContent` instead of `innerHTML`.
2. **No HTML Parsing:** The browser renders the input strictly as textual content, neutralizing scripts or tags (CWE-79 protected).

#### Conclusion:
Safe DOM rendering."""
    }
]


def main():
    output_path = Path("data/custom_cot/security_cot.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    records = []
    for item in DATASET:
        record = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": item["prompt"].strip()},
                {"role": "assistant", "content": item["response"].strip()}
            ]
        }
        records.append(record)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[+] Successfully wrote {len(records)} balanced CoT samples to {output_path}")


if __name__ == "__main__":
    main()
