---
name: security-review
description: Review code files for security vulnerabilities. Covers OWASP Top 10, injection flaws, auth issues, secrets, XSS, SSRF, and more. Used by the tester agent after implementation is complete, or on explicit request.
license: MIT
compatibility: Python 3.10+, Node 18+
allowed-tools: read_file glob grep
---

# Security Review Skill

Use this skill when asked to perform a security review, or after implementation is complete and the tester agent is verifying work.

## When to Apply

- After the tester agent finishes verifying functional tests
- When explicitly asked: "security review", "check for vulnerabilities", "audit this"
- Before any endpoint that handles user authentication, file uploads, or external data is merged

## Confidence Threshold

**Only report a finding if you are >80% confident it is a real vulnerability in this specific codebase.**
Do not report theoretical issues. Do not flag well-known framework protections as vulnerabilities.
If a framework (FastAPI, SQLAlchemy ORM, React) already handles the protection by default, do not flag it.

## Review Process

1. **Identify scope** — list the files to review (routers, models, services, components with user input)
2. **Read each file** using `read_file` — never guess at content
3. **Check each category below** systematically
4. **Rate confidence** per finding before including it
5. **Write the report** in the format below

## Vulnerability Categories

### Injection (SQL, Command, Template, LDAP)
- Raw SQL strings with f-strings or `.format()` — always flag
- `subprocess`, `os.system`, `eval()`, `exec()` with user input
- Template rendering (`render_template_string`) with user-controlled content
- SQLAlchemy: raw `text()` queries that concatenate user input
- Safe patterns: ORM queries (`db.query(Model).filter(Model.field == value)`), parameterized `text("SELECT ... WHERE x = :val")`

### Authentication and Authorization
- Missing authentication on sensitive endpoints (check for `Depends(get_current_user)` or equivalent)
- JWT: verify signature algorithm is RS256 or HS256 with strong secret; flag `alg: none`
- Password storage: flag any use of MD5/SHA1 for passwords; bcrypt/argon2/scrypt are correct
- Broken access control: endpoint fetches a resource by ID without checking `resource.owner == current_user`
- Session fixation, insecure direct object references

### Cryptography
- Hardcoded secrets, API keys, passwords in source code
- Weak algorithms: MD5, SHA1, DES, RC4 for security purposes
- Predictable random: `random.random()` for tokens/IDs — should use `secrets.token_hex()`
- Missing TLS verification: `verify=False` in `requests` calls

### Sensitive Data Exposure
- Passwords, tokens, or PII logged to console or written to log files
- Error responses that expose stack traces, file paths, or internal state to clients
- Sensitive fields returned in API responses that clients don't need

### Cross-Site Scripting (XSS) — Frontend
- `dangerouslySetInnerHTML` with user-controlled content
- `innerHTML =` assignments with unsanitized data
- URL construction: `href={userInput}` without protocol validation (allows `javascript:`)

### Server-Side Request Forgery (SSRF)
- User-supplied URLs fetched by the server without allowlist validation
- Internal metadata endpoints reachable via crafted URLs

### Insecure Dependencies
- Note any `requirements.txt` or `package.json` entries with known CVEs if you have knowledge of them
- Flag packages pinned to versions with known security issues

### File Handling
- Path traversal: user-controlled filenames not sanitized with `os.path.basename()` or equivalent
- Unrestricted file upload: no MIME type or extension validation
- Files written to predictable paths

### Error Handling
- Bare `except:` clauses that swallow all errors silently
- Generic 500 responses that leak internal details to the client

## Report Format

Write findings using this structure:

```
## Security Review — [files reviewed]

### Findings

#### [SEVERITY] [Category] — [File:Line]
**Finding:** [One sentence describing the vulnerability]
**Risk:** [What an attacker could do]
**Fix:** [Specific code change or pattern to use]

---

### Summary
- HIGH: [count]
- MEDIUM: [count]
- LOW: [count]
- Files reviewed: [list]
- Files with no issues: [list]
```

Severity levels:
- **HIGH** — Directly exploitable; confidentiality/integrity/availability impact
- **MEDIUM** — Exploitable with effort or under specific conditions
- **LOW** — Defense-in-depth; unlikely to be exploited alone

If no issues are found:
```
## Security Review — [files reviewed]
No security issues found. All [N] files reviewed follow secure patterns.
```

## Hard Exclusions (Never Flag)

Do not flag these — they are safe by design:

- SQLAlchemy ORM filter calls (`Model.field == value`)
- FastAPI's built-in request parsing and validation
- React's JSX rendering (auto-escapes by default)
- bcrypt / argon2 password hashing
- HTTPS-only cookie flags set by the framework
- Development-only `DEBUG=True` settings clearly labeled as dev-only
- Test files with hardcoded test credentials (clearly scoped to tests)
