---
name: review-ardent
description: Adaptive code review that scales from single-pass to full parallel swarm based on change size. One command for all review needs. Triggers on "review", "review my code", "check my changes". Use "/review-ardent fix" to auto-fix findings.
---

# Review

Adaptive code review that automatically scales based on change size:

| Change Size | Strategy |
|-------------|----------|
| **Small** (1-3 files, <150 lines) | Single focused pass — no subagents |
| **Medium** (4-10 files, 150-500 lines) | 2-3 targeted agents based on what changed |
| **Large** (10+ files or 500+ lines) | Full 9-agent parallel swarm |

## Context

**Branch**: !`git branch --show-current`
**Arguments**: $ARGUMENTS

## Modes

- **`/review-ardent`** — Review only. Outputs the report.
- **`/review-ardent fix`** — Review + auto-fix. Fixes Detail findings and amends the appropriate commits.
- **`/review-ardent triage`** — Review, then present findings for interactive triage before fixing.

**Argument parsing:** `$ARGUMENTS` is the full text after `/review`. Extract the mode keyword if one appears first:

- `fix` → fix mode
- `triage` → triage mode

Everything after the mode keyword (or all of `$ARGUMENTS` if no mode keyword) is the **review target**. This is free-form text — it could be a PR number, branch name, or a natural-language description like "just the unstaged changes" or "only the last commit".

If no target is specified, default to the current branch vs main.

## Instructions

### Phase 1: Gather Context

#### 1a. Find and Read ALL CLAUDE.md Files

```
Glob("**/CLAUDE.md") in the repo root
Read("~/.claude/CLAUDE.md") for global user instructions
```

Read every CLAUDE.md file completely. Store the **full contents** as `CLAUDE_MD_CONTENT` — you will inline relevant sections into agent prompts so agents don't waste turns reading them.

#### 1b. Check Past Solutions

Scan for learnings from previous reviews and debugging sessions that may be relevant to this change:

```bash
ls .untracked/solutions/ 2>/dev/null
ls .untracked/.shared/*/ 2>/dev/null
```

Skim the filenames. If any look relevant to the changed files/domains (based on the branch name or what you already know about the change), read those solution files. Store relevant excerpts as `PAST_SOLUTIONS` — a few bullet points summarizing patterns to watch for.

If nothing is relevant, set `PAST_SOLUTIONS` to empty and move on. Don't spend more than 1 turn on this.

#### 1c. Resolve the Review Target

**CRITICAL: Do this BEFORE running any git diff commands.** Look at the **Arguments** field in the Context section above. If arguments were provided, they define the review target — do NOT default to branch-vs-main.

Parse the arguments to determine the review target, then run ONLY the matching diff command:

| Target | Diff command |
|--------|-------------|
| *(empty — no arguments)* | `git diff main...HEAD` |
| **Unstaged changes** (e.g., "unstaged", "working tree", "my changes") | `git diff` |
| **Staged changes** (e.g., "staged", "what I'm about to commit") | `git diff --cached` |
| **Unstaged + staged** (e.g., "all local changes") | `git diff HEAD` |
| **Last N commits** (e.g., "last commit", "last 3 commits") | `git diff HEAD~N...HEAD` |
| **Specific file(s)** (e.g., "apiclient.ts in last commit") | `git diff HEAD~1...HEAD -- {file}` |
| **PR number** (e.g., `123`) | `gh pr diff 123` |
| **Branch name** | `git diff main...{branch}` |

If the arguments mention specific files, add `-- {files}` to scope the diff. Combine with the target type (e.g., "unstaged changes in foo.ts" → `git diff -- foo.ts`).

Store the **diff command** as `DIFF_COMMAND`.

**Context management for the orchestrator:**
- **Small strategy**: Run the full diff yourself — you'll need it for single-pass review.
- **Medium/Large strategy**: Run `{DIFF_COMMAND} --stat` and `git log --oneline main..HEAD` for scope measurement and the change summary. Then prepare per-agent scoped diffs (see Phase 2) — you will inline diff content directly into agent prompts so they don't waste turns on discovery.

#### 1d. Measure Scope and Choose Strategy

Use the diff stats (add `--stat` if needed).

| Metric | Small | Medium | Large |
|--------|-------|--------|-------|
| Files | 1-3 | 4-10 | 10+ |
| Lines | <150 | 150-500 | 500+ |

Use the **larger** category if metrics disagree (e.g., 2 files but 300 lines = Medium).

**The strategy is binding.** Once you measure and announce a strategy, you MUST follow it:
- **Small** → single pass, no agents
- **Medium** → spawn 2-3 targeted agents (never single pass)
- **Large** → spawn all 9 agents (never single pass)

Do NOT downgrade a medium/large review to single pass. The whole point of agents is parallel, specialized analysis. A single pass cannot replicate 9 focused perspectives.

Announce the strategy: "Reviewing {N} files, {M} lines changed — using {small/medium/large} review."

### Phase 1.5: Understand the Change

Before reviewing, analyze the diff holistically to build a mental model of the change:

1. **Goal**: What is this change trying to accomplish? What's the underlying intent — not just "adds function X" but *why* X is needed?
2. **Approach**: How does it achieve that goal? What are the clear benefits and improvements?
3. **Gaps**: Is there something obviously missing? A case not handled, a boundary not checked, a related change that should have been included?

Write a 2-4 sentence **change summary** capturing the goal, approach, and any obvious gaps. Store it as `CHANGE_SUMMARY`.

For small reviews (single pass), keep this analysis in your head. For medium/large reviews, include it in every agent's prompt.

---

### Phase 2: Review

<critical>
ROUTING — Read the strategy you announced in Phase 1d, then jump to EXACTLY that section:
- If you announced **small** → go to "Strategy: Small" below
- If you announced **medium** → go to "Strategy: Medium" below
- If you announced **large** → go to "Strategy: Large" below

Do NOT read the Small strategy section if you announced medium or large. Skip directly to the correct section.
</critical>

#### Strategy: Small (Single Pass)

**ONLY use this if you announced "small" in Phase 1d.** If you announced medium or large, skip to the matching section.

Review all changes yourself in one pass. Start by understanding the goal (Phase 1.5), then cover all perspectives. Apply the verification rules and hard exclusions from the agent template below, and use the scan patterns (type quality, AI debt, silent failure) listed in the agent-specific context table:

- **Design**: Right approach? Clean data flow? Proper separation of concerns? Could the high-level approach be simpler?
- **Gaps**: Anything obviously missing — unhandled cases, absent related changes, untested paths?
- **Conventions**: CLAUDE.md compliance — naming, patterns, imports, component usage
- **TypeScript**: Type safety, modern patterns, naming quality, **type quality scan**
- **Simplicity**: Over-engineering? YAGNI violations? Unnecessary complexity?
- **Security**: Actual vulnerabilities given the threat model
- **Error handling**: Silent failures, swallowed errors, missing context — **silent failure scan**
- **Tests**: Are the right things tested? Testing philosophy compliance?
- **Performance**: N+1 queries, memory leaks, IPC overhead, unnecessary re-renders?
- **Frontend**: Stale closures, race conditions, missing cleanup, incorrect deps?

Apply the verification rules to every finding. Skip anything caught by automated tools.

After completing the single pass, skip directly to **Phase 3: Synthesize and Validate**.

---

#### Strategy: Medium (Targeted Agents)

**ONLY use this if you announced "medium" in Phase 1d.** You MUST spawn agents — do NOT do a single pass.

Select 2-3 agents based on what changed. Pick the 2-3 most relevant perspectives — fewer focused agents with full context outperform many starved ones.

**Selection logic** (pick 2-3, not all):

- If conventions/naming/patterns matter: **Convention Reviewer**
- If new types/interfaces: **TypeScript Reviewer**
- If security-adjacent (auth, IPC, network, permissions): **Security Reviewer**
- If architectural changes (new packages, cross-package imports, new services): **Architecture Reviewer**
- If complex logic or algorithms: **Simplicity Reviewer**
- If test files changed or new features without tests: **Test Reviewer**
- If database queries, D1 operations, IPC calls, or potential hot paths: **Performance Reviewer**
- If React components, hooks, effects, or renderer-side async code: **Frontend Reviewer**
- Default if nothing special: **Design Reviewer** + **Simplicity Reviewer**

Then proceed to **Spawning Agents** below.

---

#### Strategy: Large (Full Swarm)

**ONLY use this if you announced "large" in Phase 1d.** You MUST spawn ALL 9 agents — do NOT do a single pass.

Use ALL 9 agents:

1. Design Reviewer
2. Convention Reviewer
3. TypeScript Reviewer
4. Simplicity Reviewer
5. Security Reviewer
6. Architecture Reviewer
7. Test Reviewer
8. Performance Reviewer
9. Frontend Reviewer

Then proceed to **Spawning Agents** below.

---

#### Spawning Agents

<critical>
CRITICAL: You MUST use the **Agent** tool (also known as "Task" tool) to spawn subagent processes. This is the tool with parameters `prompt`, `description`, `subagent_type`, and `run_in_background`.

Do NOT use any of these alternatives:
- TaskCreate, TaskUpdate, or TaskList — those are task-tracking tools that create checklist items, NOT agents
- Any MCP tool for running analysis — use ONLY the Agent tool

Do NOT skip agent spawning and do a single-pass review yourself. The whole point of medium/large strategy is parallel agents.
</critical>

#### Preparing Agent Context (Orchestrator Does This BEFORE Spawning)

Agents have limited turns. Every turn an agent spends on discovery (reading diffs, reading CLAUDE.md) is a turn it can't spend on analysis. The orchestrator must front-load all context.

**Step 1: Prepare per-agent diffs.** Use the `--stat` output to identify which files are relevant to each agent, then generate targeted diffs:

```bash
# Build per-agent diffs using file paths from --stat.
# Only include files relevant to each agent's specialty.
# Example patterns (adapt to what actually changed):

# Security: auth, IPC, permissions, MCP files
git diff main...HEAD -- '**/oauth/**' '**/auth/**' '**/mcp/**' '**/ipc/**' '**/permission*' > /tmp/review-security.diff

# Frontend: .tsx, hooks, effects, CSS
git diff main...HEAD -- '*.tsx' '*.css' '**/frontend/**' '**/renderer/**' > /tmp/review-frontend.diff

# Tests: test files only
git diff main...HEAD -- '**/*.test.ts' '**/*.test.tsx' '**/__tests__/**' > /tmp/review-tests.diff

# Backend: everything else (services, models, stores)
git diff main...HEAD -- '*.ts' ':!*.test.ts' ':!*.test.tsx' ':!*.tsx' ':!*.css' > /tmp/review-backend.diff
```

Adapt patterns to what actually changed. If an agent's scoped diff is empty (0 lines), **do not spawn that agent** — skip it entirely.

**Step 2: Read the scoped diff files** into memory. You will paste the relevant diff content directly into each agent's prompt.

**Step 3: Extract relevant CLAUDE.md rules.** From `CLAUDE_MD_CONTENT`, extract the sections relevant to each agent type (e.g., Convention Reviewer needs the Code Style, TypeScript Patterns, and UI Components sections; Security Reviewer needs the architecture overview). Prepare a condensed excerpt for each.

**Agent-to-diff mapping:**

| Agent | Diff source | CLAUDE.md sections to inline |
|-------|-------------|------------------------------|
| Convention Reviewer | backend + frontend | Code Style, TypeScript Patterns, UI Components, File Naming |
| TypeScript Reviewer | backend + infra | TypeScript Patterns |
| Design Reviewer | backend | Architecture overview |
| Simplicity Reviewer | backend | (minimal — architecture overview) |
| Security Reviewer | security diff (skip if empty) | Architecture overview |
| Architecture Reviewer | backend + infra | Architecture, package structure |
| Test Reviewer | tests diff (skip if empty) | Testing section |
| Performance Reviewer | backend + frontend | Architecture overview |
| Frontend Reviewer | frontend diff (skip if empty) | UI Components, Code Style |

#### Spawning

**Spawn ALL selected agents in a SINGLE assistant message.** This is how you achieve parallelism — multiple Agent tool calls in one response run concurrently.

Each agent MUST:
- **Receive its scoped diff content inline in the prompt** — agents should NOT need to read files or run git commands to get the diff
- **Receive relevant CLAUDE.md rules inline** — agents should NOT need to read CLAUDE.md themselves
- Receive the change summary and past solutions
- Be told to **return text findings only — do NOT use Write, Edit, or modify any files**
- Receive the output format and hard exclusions inline
- Use `run_in_background: true` so they execute in parallel

<parallel_tasks>
Here is the exact pattern — spawn all agents in ONE message using multiple Agent tool calls:

For each selected agent, make an Agent tool call with these parameters:
- `description`: "{agent-name} review of {branch}"
- `subagent_type`: Use the exact agent type name (e.g., "Convention Reviewer", "TypeScript Reviewer", "Design Reviewer", "Security Reviewer", "Architecture Reviewer", "Simplicity Reviewer", "Test Reviewer", "Performance Reviewer", "Frontend Reviewer")
- `run_in_background`: true
- `prompt`: Use this template, filling in the agent-specific sections:

**IMPORTANT:** Replace `{AGENT_NAME}` below with the actual agent type (e.g., "Design Reviewer", "Security Reviewer") before sending.

```
You are the {AGENT_NAME}.

## Output format (MANDATORY)

AGENT: {AGENT_NAME}
FINDINGS_COUNT: {number, or 0 if none}

FINDING: 1
SEVERITY: design | detail
CONFIDENCE: {0-100}
FILE: {path} LINE: {number}
TITLE: {brief title}
ISSUE: {what's wrong}
SUGGESTION: {fix}
---

Zero findings: AGENT: {AGENT_NAME} / FINDINGS_COUNT: 0

## Context

**Change summary:** {CHANGE_SUMMARY}
{If PAST_SOLUTIONS is non-empty: **Past learnings:** {PAST_SOLUTIONS}}

### Project rules (from CLAUDE.md)

{Relevant CLAUDE.md excerpts for this agent — already extracted by orchestrator}

### Diff to review

{Paste the scoped diff content inline here}

## Focus

{Agent-specific focus — see agent-specific context table below}

## Rules

- Verify findings with concrete evidence. If you can't prove it's wrong, drop it. No hypotheticals.
- You may read source files to verify findings — use targeted line ranges, not whole files.
- Text output only — do NOT use Write/Edit.
- Quality over quantity — a few verified findings beat many speculative ones.

## Hard exclusions — drop these

Security in test files only, DoS without business impact, rate limiting, missing validation without downstream impact, theoretical races, log injection, env vars as untrusted, React/Radix XSS (auto-escaped), client-side auth, "could diverge" across boundaries, missing error handling with upstream boundaries, abstractions for <4 occurrences, tests for type-guaranteed behavior, import order (Biome handles it).
```
</parallel_tasks>

**Agent-specific focus to include in prompts:**

| Agent | Focus to inline |
|-------|----------------|
| Convention Reviewer | **AI Debt Scan**: flag restating comments, docstring bloat, generic naming, boilerplate error handling, nosy debug logging, bare TODOs without issue reference. **Type Quality Scan**: flag indexed access types, utility-type extraction (`ReturnType<typeof fn>`), `typeof` in type positions, `unknown` + cast, inline anonymous object types in signatures/generic args, weakened discriminated unions. |
| TypeScript Reviewer | **Type Quality Scan**: flag indexed access types (`SomeType['prop']`), utility-type extraction (`ReturnType<typeof fn>`, `Parameters<typeof fn>[0]`, `Awaited<ReturnType<...>>`), `typeof` in type positions, `unknown` + cast, inline anonymous object types in signatures/generic args, weakened discriminated unions. |
| Design Reviewer | **Silent Failure Scan**: flag empty catch blocks, swallowed errors (log but continue when caller needs to know), broad exception catching, silent fallbacks (return default/null without logging), missing error context, fire-and-forget `.catch(() => {})` on operations whose failure should be visible. |
| Security Reviewer | **Silent Failure Scan** (same as Design). Project threat model if non-default. |
| Architecture Reviewer | Focus on package boundary violations and cross-package coupling. |
| Test Reviewer | Note which files are test files vs code they test. |
| Performance Reviewer | Focus on DB queries, IPC calls, N+1 patterns, unnecessary re-renders. |
| Frontend Reviewer | Focus on stale closures, race conditions, missing cleanup, incorrect effect deps. |
| Simplicity Reviewer | Focus on YAGNI violations, unnecessary abstractions, over-engineering. |

**Clean up temp files after all agents complete**: `rm -f /tmp/review-*.diff`

**WAIT** for all background agents to complete before proceeding to Phase 3.

---

### Phase 3: Synthesize and Validate

After all agents report:

1. **Collect** all agent outputs — parse the structured FINDING blocks from each
   - If an agent returned without a `FINDINGS_COUNT` line, treat it as 0 findings and mark it as "No structured output" in the Coverage table. Do NOT retry or re-read its output looking for findings — move on.
2. **Merge** into a single list
3. **Deduplicate** — same issue from multiple agents = report once with higher confidence
4. **Cross-validate** — issues flagged by 2+ agents are especially credible
5. **Challenge findings using your existing context** (diff stats, change summary, what you already know). Only read a source file if you genuinely can't determine whether a finding is valid without it. Ask:
   - "Is this actually wrong, or intentional?"
   - For "duplication": at different boundaries? Drop it
   - For "could diverge/break": concrete triggering input? If no, drop it
   - For security: realistic attacker and vector? If no, drop it
   - For "missing X": does code actually need X, or is this over-engineering?
6. **Surface gaps** — using the Phase 1.5 analysis, identify anything obviously missing (unhandled cases, absent related changes, untested paths). Add these as Missing findings.
7. **Organize** into Design, Missing, and Details sections
8. **Number findings** sequentially starting at #1 across all sections (e.g., Design #1-#3, Missing #4, Details #5+)
9. **Clean up temp files**: `rm -f /tmp/review-*.diff`

### Phase 4: Report

```markdown
## Review

**Target:** {branch/PR description}
**Commits:** {count} commits, {files} files changed
**Strategy:** {small/medium/large} ({N} agents)
**CLAUDE.md files loaded:** {list of paths}

### Verdict: {CLEAN | MINOR ISSUES | NEEDS CHANGES}{if deferred > 0: " ({N} deferred — acknowledged debt)"}

### What this change does
{2-4 sentence change summary from Phase 1.5 — goal, approach, key benefits}

### What's done well
- {clear benefits and improvements this change brings}

---

### Design ({count} findings)

- **#{N}. {brief title}** (confidence: {score}, found by: {agent names})
  Issue: {what's wrong}
  Verified: {how you confirmed this is actually a problem}
  Suggestion: {what would be better}

### Missing (if any)

- **#{N}. {brief title}** (confidence: {score})
  Gap: {what's absent — unhandled case, missing related change, untested path}
  Suggestion: {what should be added}

---

### Details ({count} findings)

#### {file path}

- **#{N}.** [:{line}] **{brief title}** (confidence: {score}, found by: {agent names})
  Rule: {specific CLAUDE.md rule or specialist rationale}
  Issue: {what's wrong}
  Fix: {concrete suggestion}

---

### Deferred (if any)

Findings reviewed and intentionally not fixed — acknowledged debt, not resolved.

- **#{N}. {brief title}** (confidence: {score})
  Reason deferred: {why this isn't being fixed now}

---

### Coverage
| Agent | Status | Findings |
|-------|--------|----------|
| ... | Done | {count} |
```

Quality over quantity. A review with 3 verified findings beats one with 25 unverified ones.

### Phase 5: Triage (only in `triage` mode)

Skip if not triage mode. After the report is written, present findings interactively so the user can decide what to fix.

#### 5a. Present Findings

For each finding (Design first, then Details), use AskUserQuestion:

```
Finding #{N}: {brief title} (confidence: {score})
{Issue description}
Suggestion: {fix suggestion}
```

Options:
- **Fix** — Apply this fix
- **Skip** — Ignore this finding
- **Customize** — User provides alternative fix approach

Present findings in batches of up to 3 at a time using AskUserQuestion's multi-question support to reduce back-and-forth. Group related findings when possible.

#### 5b. Collect Approved Fixes

Build a list of approved findings with their fix approach (original or customized). Report the triage summary:

```
Triage: {approved} to fix, {skipped} skipped out of {total} findings
```

#### 5c. Apply Approved Fixes

Proceed to Phase 6 (Auto-Fix) but only for the approved findings. If no findings were approved, stop here.

---

### Phase 6: Auto-Fix (only in `fix` or `triage` mode)

Skip if no findings or neither fix nor triage mode enabled. In fix mode, fix all Detail findings. In triage mode, fix only approved findings. Skip Design findings in fix mode — those need human judgment.

#### 6a. Map Findings to Commits

```bash
git blame -l -L {line},{line} main..HEAD -- {file_path}
```

Build a map: `commit_hash → [findings]`

#### 6b. Create Backup

```bash
git branch backup/{current_branch_name} HEAD
```

#### 6c. Apply Fixes by Commit

For each commit group:
1. Apply fixes (bottom to top by line number to avoid shifts)
2. Read each file after editing to verify
3. Stage: `git add {files}`
4. Fixup with attestation: `git commit --fixup={commit_hash} -m "fix: #{finding_number} — {what was changed and why}"`

#### 6d. Verify

```bash
npm run lint:fix
npm run typecheck
```

If lint:fix made changes, stage and commit as fixup. Repeat until both pass.

#### 6e. Squash into History

```bash
GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash main
```

If rebase fails: abort, report failure, backup branch is available at `backup/{branch}`.

#### 6f. Final Verification + Cleanup

```bash
npm run lint
npm run typecheck
git branch -D backup/{current_branch_name}
```

Output a fix summary with findings fixed, commits amended, and verification status.

## Guidelines

- Read CLAUDE.md files fresh every time — then inline relevant sections into agent prompts so agents don't waste turns on discovery.
- Every convention finding must cite a specific CLAUDE.md rule.
- Skip anything caught by automated tools.
- Focus on the diff. Don't review unchanged code unless the diff breaks patterns.
- Fix mode: always create backup before modifying history. Never force-push. Only fix Detail findings.
- Triage mode: present findings for user approval before fixing. Includes Design findings in triage (user can approve them for fixing). Batch findings in groups of up to 3 to reduce back-and-forth.

## Report Output

Write the report to the agent workspace:

```
.untracked/{topic}/review.md
```

**Derive `{topic}`** from the branch name (e.g. `feat/gen-ui-v3` → `gen-ui`). Before creating a new topic folder, check for existing folders with matching prefixes and reuse them.

If a `review.md` already exists in the topic folder, overwrite it — this is the latest review.
