---
name: cleanup
description: Simplify and refine recently modified code for clarity and maintainability while preserving behavior. Use for requests like "simplify this", "clean this up", "reduce complexity", or readability-focused refactors.
context: fork
---

# Simplify

Simplify code for clarity, consistency, and maintainability while preserving behavior.
Default focus is recently modified code unless the user specifies a different scope.

## Context

**Branch**: !`git branch --show-current`
**Arguments**: $ARGUMENTS

## Step 1: Resolve Scope and Choose Strategy

Determine target files in this order:

1. If the user specifies files or scope, use that exactly.
2. Otherwise gather local changes:
   - `git diff --name-only`
   - `git diff --cached --name-only`
3. If no local changes exist, use recent branch changes:
   - `git diff --name-only origin/main...HEAD`
4. If still empty, ask the user what to simplify.

Exclude test files unless the user explicitly asks to simplify tests.

**Choose strategy based on file count:**

| Files | Strategy |
|-------|----------|
| 1-8 | **Single pass** — handle all files yourself, sequentially |
| 9+ | **Parallel** — chunk files and spawn cleanup agents |

Announce: "Simplifying {N} files — using {single pass / parallel} strategy."

---

## Single-Pass Strategy (1-8 files)

### Step 2: Understand Before Editing

Read each target file and surrounding context before making changes.

### Step 3: Simplify (Behavior-Preserving Only)

Allowed transformations:

- Remove dead code, unused locals, and unreachable branches
- Flatten unnecessary nesting (prefer early returns)
- Inline trivial one-use variables/helpers that obscure intent
- Collapse redundant conditional and branching logic
- Remove one-off abstractions or wrappers that add indirection without value

### Step 4: Guardrails

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

### Step 5: Validate

Run from repo root after edits:

- `npm run lint:fix`
- `npm run typecheck`

Fix any issues introduced by simplification.

### Output

Provide:

- Files simplified
- Key simplifications made
- Validation results

---

## Parallel Strategy (9+ files)

<critical>
Do NOT manually sort, group, or deliberate about file assignments. Pipe the file list through the chunking command below and use the output directly.
</critical>

### Step 2: Chunk Files

Run this command, replacing `{FILE_LIST_CMD}` with the command that produces your file list (e.g., `git diff --name-only origin/main...HEAD`):

```bash
{FILE_LIST_CMD} | grep -v '\.test\.' | grep -v '__tests__' | awk -v max=8 '
  { bin = int((NR-1) / max) + 1; print "CHUNK_" bin "\t" $0 }
  END { for (i = 1; i <= bin; i++) printf "SUMMARY\tCHUNK_%d\t%d files\n", i, (i < bin ? max : NR - (bin-1)*max) }
'
```

This splits files into groups of 8 (round-robin by input order). Each `CHUNK_N` block becomes one agent.

### Step 3: Spawn Cleanup Agents

Spawn one agent per chunk in a **single message** (all `run_in_background: true`).

Each agent prompt:

```
You are a cleanup agent. Simplify the assigned files for clarity and maintainability while preserving behavior.

## Your assigned files

{CHUNK_FILES — one per line}

## Instructions

1. Read each file.
2. Apply ONLY these behavior-preserving transformations:
   - Remove dead code, unused locals, unreachable branches
   - Flatten unnecessary nesting (prefer early returns)
   - Inline trivial one-use variables/helpers that obscure intent
   - Collapse redundant conditional/branching logic
   - Remove one-off abstractions or wrappers that add indirection without value
3. Edit each file with your simplifications.
4. Skip files that are already clean — do not force changes.

## Guardrails

- Preserve exact behavior (including evaluation order and side effects)
- Do not add features, validation, fallback behavior, or broader refactors
- Do not change public APIs, exported contracts, or signatures
- Do not touch tests
- Respect CLAUDE.md / AGENTS.md constraints (read them first: {CLAUDE_MD_PATHS})
- Prefer clear control flow over compact clever expressions
- No nested ternaries, no over-clever one-liners
- Three clear lines > one dense line

## Output

End your response with:

AGENT: Cleanup {N}/{TOTAL}
FILES_CHANGED: {count}
CHANGES:
- {file}: {what you simplified}
- ...
```

### Step 4: Collect and Validate

Wait for all agents to complete. Then run from repo root:

```bash
npm run lint:fix
npm run typecheck
```

Fix any issues. Report total files simplified and key changes across all agents.
