---
name: compound
description: Document a recently solved problem to compound your knowledge
argument-hint: "[optional: brief context about the fix]"
---

# Compound

Capture a recently solved problem as a searchable solution document. Each documented solution compounds your knowledge — the first time you solve a problem takes research, the next time takes minutes.

## Context

<context_hint> #$ARGUMENTS </context_hint>

## When to Use

- After solving a non-trivial problem (multiple investigation attempts, tricky debugging)
- After phrases like "that worked", "it's fixed", "problem solved"
- When the solution would help future sessions

**Skip for:** simple typos, obvious syntax errors, trivial fixes.

## Process

### 1. Extract from Conversation

From the current conversation, identify:

- **Problem symptom**: exact error messages, observable behavior
- **Investigation steps**: what was tried, what didn't work and why
- **Root cause**: technical explanation of the underlying issue
- **Working solution**: the actual fix with code examples
- **Prevention**: how to avoid this in the future

If the conversation doesn't contain enough context, ask: "What was the problem you just solved? What was the root cause?"

### 2. Classify and Route

**First, determine scope:** Is this solution specific to the current project, or is it general knowledge useful across any project?

- **Project-specific**: a bug in your codebase, a workaround for your architecture, a fix tied to specific files/commits
- **Cross-project**: a language/framework gotcha, a tool configuration pattern, a general technique

**Then determine the category:**

| Category | When |
|----------|------|
| `performance` | Slow queries, memory issues, scaling |
| `debugging` | Hard-to-find bugs, misleading errors |
| `configuration` | Environment, tooling, build issues |
| `integration` | External APIs, services, protocols |
| `architecture` | Design decisions, patterns, boundaries |
| `testing` | Test flakiness, mocking, test design |
| `electron` | Electron-specific (IPC, security, packaging) |
| `typescript` | Type system, compiler, patterns |
| `general` | Anything else |

### 3. Write the Document

**Derive `{slug}`** from the problem context — a short slug describing the solution (e.g. `n-plus-one-briefs`, `ipc-deadlock`).
**Derive `{area}`** from the domain of work (see CLAUDE.md for area mapping) — used in frontmatter only, not in the path.

**Output path depends on scope:**

- **Project-specific:** `.untracked/solutions/YYYY-MM-DD-{slug}.md`
- **Cross-project:** `.untracked/.shared/{category}/YYYY-MM-DD-{slug}.md`

Create directories if they don't exist.

**Project-specific template:**

```markdown
---
type: solution
project: {project}
area: {area}
topic: {slug}
date: YYYY-MM-DD
category: {category}
tags: [relevant, tech, keywords]
branch: {current branch if applicable}
status: complete
---

# {Descriptive title of the problem}

## Symptom

{What you observed — error messages, behavior, metrics}

## Root Cause

{Technical explanation of why this happened}

## Solution

{Step-by-step fix with code examples}

## What Didn't Work

{Investigation steps that were dead ends and why — saves future time}

## Prevention

{How to avoid this in the future — patterns, checks, tests}
```

**Cross-project template:**

```markdown
---
type: resource
topic: {category}
date: YYYY-MM-DD
tags: [relevant, tech, keywords]
status: active
---

# {Descriptive title}

## Summary

{One-paragraph explanation of the gotcha/pattern/technique}

## Details

{Full explanation with code examples}

## References

{Links, docs, related solutions}
```

### 4. Confirm

Output:

```
Solution documented at {path}

Key insight: {one-line summary of root cause and fix}
```
