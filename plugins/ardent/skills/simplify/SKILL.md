---
name: simplify
description: Simplify and refine recently modified code for clarity and maintainability while preserving behavior. Use for requests like "simplify this", "clean this up", "reduce complexity", or readability-focused refactors.
context: fork
---

# Simplify

Simplify code for clarity, consistency, and maintainability while preserving behavior.
Default focus is recently modified code unless the user specifies a different scope.

## Context

**Branch**: !`git branch --show-current`
**Arguments**: $ARGUMENTS

## Step 1: Resolve Scope

Determine target files in this order:

1. If the user specifies files or scope, use that exactly.
2. Otherwise gather local changes:
   - `git diff --name-only`
   - `git diff --cached --name-only`
3. If no local changes exist, use recent branch changes:
   - `git diff --name-only origin/main...HEAD`
4. If still empty, ask the user what to simplify.

## Step 2: Understand Before Editing

Read each target file and surrounding context before making changes.

**Do NOT spawn subagents.** This is a single-pass skill — do all analysis and edits yourself, sequentially. Spawning "code reuse", "code quality", or "efficiency" agents is explicitly wrong — it produces unstructured output that can't be parsed downstream.

## Step 3: Simplify (Behavior-Preserving Only)

Allowed transformations:

- Remove dead code, unused locals, and unreachable branches
- Flatten unnecessary nesting (prefer early returns)
- Inline trivial one-use variables/helpers that obscure intent
- Collapse redundant conditional and branching logic
- Remove one-off abstractions or wrappers that add indirection without value

## Step 4: Guardrails

- Preserve exact behavior (including evaluation order and side effects)
- Do not add features, validation, fallback behavior, or broader refactors
- Do not change public APIs, exported contracts, or signatures unless requested
- Do not touch tests unless the user asks
- Keep changes tightly scoped to the target
- Respect project-level AGENTS.md / CLAUDE.md constraints
- Prefer clear control flow over compact clever expressions

**Avoid over-simplification.** Do not:

- Create overly clever solutions that sacrifice readability for fewer lines
- Use nested ternaries — prefer if/else or switch for multiple conditions
- Combine too many concerns into a single function or expression
- Remove abstractions that genuinely improve code organization
- Prioritize "fewer lines" over readability (three clear lines > one dense line)
- Make code harder to debug or extend in pursuit of elegance

## Step 5: Validate

Run from repo root after edits:

- `npm run lint`
- `npm run typecheck`

Fix any issues introduced by simplification.

## Output

Provide:

- Files simplified
- Key simplifications made
- Validation results
