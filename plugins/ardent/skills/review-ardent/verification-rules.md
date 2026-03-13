# Review Verification Rules

## CRITICAL: Turn Budget and Output Format

**Aim for ~10 turns. You have up to 20, but don't waste them investigating dead ends.** Typical budget:
- Turns 1-2: Read this file, scan-patterns.md (if told to), and the diff
- Turns 3-6: Read files for verification (only lines around candidates, not whole files)
- Turns 7-10: Output your findings in the REQUIRED format below

**Your FINAL message MUST contain the output block below.** If you run out of things to investigate, output immediately. Do NOT keep reading files looking for more issues.

### Required Output Format

Your final message must contain EXACTLY this structure. Put it at the END of your last message:

```
AGENT: {your agent type}
FINDINGS_COUNT: {number}

FINDING: {sequential number}
SEVERITY: design | detail
CONFIDENCE: {0-100}
FILE: {file path}
LINE: {line number or range}
TITLE: {brief title}
ISSUE: {what's wrong}
VERIFIED: {how you confirmed this — concrete evidence, not speculation}
SUGGESTION: {what would be better}
RULE: {specific CLAUDE.md rule or rationale}
---
```

If you have zero findings, output:
```
AGENT: {your agent type}
FINDINGS_COUNT: 0
```

---

## Process

Phase 1 — QUICK SCAN (1 turn): Read the diff. Identify concrete candidates that clearly violate your focus area. If nothing jumps out, output FINDINGS_COUNT: 0 immediately.

Phase 2 — VERIFY (1-2 turns max): For each strong candidate, read the actual file context around the flagged line. If it doesn't survive verification, drop it.

Phase 3 — OUTPUT: Format and return findings. This is mandatory — you must always reach this phase.

**EARLY EXIT**: If Phase 1 yields no candidates, skip Phase 2 and go directly to output.

## Verification Rules

1. Read the actual file for context around the flagged line — not the entire file.
2. Verify with a concrete example. If you can't prove it's wrong, drop it.
3. Write a brief counterargument. If the counterargument is stronger, drop it. BUT: "it's minor", "it's only N lines", or "it's small" are NOT valid counterarguments — they address severity, not correctness. A valid counterargument explains why the code is *actually right* (e.g., "the alias exists because consumers shouldn't depend on the internal name" or "the pre-check produces a better error message that's used in the UI"). If you can't argue the code is correct, report it.
4. Respect boundary duplication. Similar code in different packages often serves different boundaries.
5. Consider the threat model. For security: who provides the input? If trusted, drop it.
6. No hypotheticals. Only flag things that ARE problems given actual code and usage.
7. **Accumulate related smells.** If you find 2+ individually-minor issues pointing at the same root cause (e.g., redundant type aliases + dead public methods + stale exports all pointing to "unnecessary API surface"), report them as a single finding with the aggregate evidence. The confidence of the cluster is higher than any individual smell — a pattern of unnecessary indirection is a real design problem even if each instance is small. List each instance as evidence in the VERIFIED field.

## Hard Exclusions — Automatically drop these

1. Security findings only in test files
2. DoS concerns without significant business impact
3. Rate limiting suggestions
4. Missing input validation without proven downstream impact
5. Theoretical race conditions without a practical exploit path
6. Log injection or log spoofing concerns
7. Environment variables and CLI flags treated as untrusted (they're trusted)
8. React/Radix components flagged for XSS (auto-escaped unless dangerouslySetInnerHTML)
9. Client-side auth checks (server responsibility)
10. "Could diverge" warnings about separate code across package boundaries
11. Missing error handling on internal calls with upstream error boundaries
12. Suggesting abstractions for code that appears 2-3 times (threshold is 4+)
13. Flagging missing tests for trivial getters/setters or type-guaranteed behavior
14. Nitpicking import order when Biome already enforces it

## Confidence Threshold

Only report findings with confidence >= 85.
