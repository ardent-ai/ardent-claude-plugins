---
name: security-scan
description: STRIDE-based security analysis of code changes. Scans diffs for vulnerabilities, validates findings for exploitability, filters false positives, and reports confirmed issues. Triggers on "security scan", "security review", "check for vulnerabilities", or /security-scan.
argument-hint: "[PR number, branch, 'staged', or commit range]"
context: fork
---

# Security Scan

STRIDE-based security analysis adapted for Electron + React + TypeScript + Cloudflare Workers. Scans code changes for vulnerabilities, validates each finding for exploitability, and filters aggressively to avoid false positives.

## Input

<scan_target> $ARGUMENTS </scan_target>

## Instructions

### Step 1: Determine Scan Scope

Parse `$ARGUMENTS` to determine what to scan:

| Target | Diff command |
|--------|-------------|
| *(empty)* | `git diff main...HEAD` |
| PR number | `gh pr diff {N}` |
| Branch name | `git diff main...{branch}` |
| `staged` | `git diff --cached` |
| `unstaged` | `git diff` |
| Commit range | `git diff {range}` |
| `last N commits` | `git diff HEAD~N...HEAD` |

Get the diff and list of changed files. Read the full content of each changed file for context.

### Step 2: STRIDE Analysis

Analyze every changed file against all six STRIDE categories, using the patterns in the companion `stride-reference.md` file. Focus on patterns relevant to what actually changed.

For each potential finding:

1. **Trace data flow** — Where does the input originate? Does it pass through validation? Where does it end up?
2. **Check existing mitigations** — Is there validation in middleware, framework protection, or sanitization elsewhere?
3. **Assess exploitability** — Can an attacker actually reach and control this code path?

### Step 3: Validate Findings

For each candidate finding, run this validation checklist:

1. **Reachability**: Is the vulnerable code reachable from external input?
   - `EXTERNAL` — reachable from unauthenticated input
   - `AUTHENTICATED` — requires valid session
   - `INTERNAL` — only reachable from internal/trusted code
   - `UNREACHABLE` — dead code or blocked by conditions

2. **Control**: Can an attacker control the input that reaches the vulnerability?

3. **Mitigations**: Are there existing controls that prevent exploitation?

4. **Exploitability**: Rate as EASY / MEDIUM / HARD / NOT_EXPLOITABLE

**Confidence threshold**: Only report findings with confidence >= 0.8. Below that, too speculative.

### Step 4: Filter False Positives

Apply the hard exclusion rules. **Automatically exclude:**

1. Findings only in test files
2. Denial of Service without significant business impact
3. Secrets stored on disk if properly secured (e.g., Electron safeStorage)
4. Rate limiting concerns (informational only)
5. Memory/CPU exhaustion without clear attack path
6. Missing input validation without proven impact
7. Theoretical race conditions without practical exploit
8. Log injection/spoofing concerns
9. Findings in documentation files
10. Missing audit logs (informational only)
11. SSRF that only controls path (not host/protocol)
12. Environment variables and CLI flags (treated as trusted)
13. UUIDs (treated as unguessable)
14. React/Radix components (XSS-safe unless using `dangerouslySetInnerHTML`)
15. Client-side code that doesn't need auth checks (server responsibility)
16. IPC messages between main and renderer when contextIsolation is enabled and preload is properly scoped
17. Type-level weaknesses that have no runtime impact

If a finding matches any exclusion, drop it silently.

### Step 5: Generate Report

For each confirmed finding, document:

```markdown
### VULN-{N}: {Title} ({SEVERITY})

**STRIDE:** {category}
**CWE:** {CWE-ID}
**File:** `{path}:{line}`
**Confidence:** {0.0-1.0}
**Exploitability:** {EASY|MEDIUM|HARD}

**Issue:** {What's wrong — concrete, not theoretical}

**Exploitation path:**
1. {step-by-step how an attacker reaches this}

**Proof of concept:**
```
{minimal payload or request demonstrating the vulnerability}
```

**Fix:**
```diff
- {vulnerable code}
+ {fixed code}
```
```

### Step 6: Output

Write the report:

```markdown
## Security Scan

**Target:** {branch/PR/commit range}
**Files analyzed:** {count}
**Scan date:** {ISO date}

### Summary

| Severity | Count |
|----------|-------|
| Critical | {N} |
| High | {N} |
| Medium | {N} |
| Low | {N} |

| STRIDE Category | Findings |
|-----------------|----------|
| Spoofing | {N} |
| Tampering | {N} |
| Repudiation | {N} |
| Info Disclosure | {N} |
| Denial of Service | {N} |
| Elevation of Privilege | {N} |

### Findings

{findings from Step 5, ordered by severity}

### False Positives Filtered

{count} candidates excluded by hard exclusion rules.

### Excluded from Scope

- Test files
- Documentation
- {any other exclusions applied}
```

Write the report to the agent workspace:

```
.untracked/{topic}/security-scan.md
```

Derive `{topic}` from the branch name. Overwrite if exists.

If no findings: report "No confirmed vulnerabilities found" with the scan metadata. A clean scan is a valid result.

## Severity Definitions

| Severity | Criteria | Examples |
|----------|----------|----------|
| Critical | Immediately exploitable, high impact, no auth required | RCE, auth bypass, hardcoded production secrets |
| High | Exploitable with some conditions, significant impact | SQL injection, stored XSS, IDOR, privilege escalation |
| Medium | Requires specific conditions, moderate impact | Reflected XSS, CSRF, info disclosure |
| Low | Difficult to exploit, low impact | Verbose errors, missing security headers |
