---
name: review-custom
description: Adaptive code review that scales from single-pass to full parallel swarm based on change size. One command for all review needs. Triggers on "review", "review my code", "check my changes". Use "/review-custom fix" to auto-fix findings.
---

# Review

Adaptive code review that automatically scales based on change size:

| Change Size | Strategy |
|-------------|----------|
| **Small** (1-3 files, <150 lines) | Single focused pass — no subagents |
| **Medium** (4-10 files, 150-500 lines) | 3-5 targeted agents based on what changed |
| **Large** (10+ files or 500+ lines) | Full 9-agent parallel swarm |

## Context

**Branch**: !`git branch --show-current`
**Arguments**: $ARGUMENTS

## Modes

- **`/review-custom`** — Review only. Outputs the report.
- **`/review-custom fix`** — Review + auto-fix. Fixes Detail findings and amends the appropriate commits.
- **`/review-custom triage`** — Review, then present findings for interactive triage before fixing.

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

Read every CLAUDE.md file completely for your own understanding. Store the **file paths** as `CLAUDE_MD_PATHS` — agents will read these files themselves (do NOT paste CLAUDE.md contents into agent prompts).

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

Store the **diff command** as `DIFF_COMMAND` — agents will run it themselves to get the diff. Do NOT pass the full diff inline in agent prompts.

**Context management for the orchestrator:**
- **Small strategy**: Run the full diff yourself — you'll need it for single-pass review.
- **Medium/Large strategy**: Only run `{DIFF_COMMAND} --stat` and `git log --oneline main..HEAD` for scope measurement and the change summary. Do NOT read the full diff — agents will do that. Keep the orchestrator context lightweight so it can hold all 9 agent outputs during synthesis.

#### 1d. Measure Scope and Choose Strategy

Use the diff stats (add `--stat` if needed).

| Metric | Small | Medium | Large |
|--------|-------|--------|-------|
| Files | 1-3 | 4-10 | 10+ |
| Lines | <150 | 150-500 | 500+ |

Use the **larger** category if metrics disagree (e.g., 2 files but 300 lines = Medium).

**The strategy is binding.** Once you measure and announce a strategy, you MUST follow it:
- **Small** → single pass, no agents
- **Medium** → spawn 3-5 targeted agents (never single pass)
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

Review all changes yourself in one pass. Read `~/.claude/skills/review/verification-rules.md` and `~/.claude/skills/review/scan-patterns.md` for the rules and patterns. Start by understanding the goal (Phase 1.5), then cover all perspectives:

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

Select 3-4 agents based on what changed. Always include `Convention Reviewer` + one domain expert.

**Selection logic:**

- Always: **Convention Reviewer**
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
CRITICAL: You MUST use the **Agent** tool (also known as "Task" tool) to spawn subagent processes. This is the tool with parameters `prompt`, `description`, `subagent_type`, `run_in_background`, and `model`.

Do NOT use any of these alternatives:
- TaskCreate, TaskUpdate, or TaskList — those are task-tracking tools that create checklist items, NOT agents
- Any MCP tool for running analysis — use ONLY the Agent tool

Do NOT skip agent spawning and do a single-pass review yourself. The whole point of medium/large strategy is parallel agents.
</critical>

**Spawn ALL selected agents in a SINGLE assistant message.** This is how you achieve parallelism — multiple Task tool calls in one response run concurrently.

Each agent MUST:
- Be told the diff command to run (e.g., `git diff main...HEAD`) — NOT receive the diff inline
- Be told the CLAUDE.md file paths to read — NOT receive the contents inline
- Be told to read `~/.claude/skills/review/verification-rules.md` for process, verification rules, and hard exclusions
- Be told to read `~/.claude/skills/review/scan-patterns.md` for scan patterns (when relevant to their focus)
- Receive the change summary
- Be told to **return text findings only — do NOT use Write, Edit, or modify any files**
- **Receive the output format inline** (see template below) — do NOT rely on them reading it from a file
- Use `model: sonnet` for speed
- Use `run_in_background: true` so they execute in parallel

<parallel_tasks>
Here is the exact pattern — spawn all agents in ONE message using multiple Task tool calls:

For each selected agent, make a Task tool call with these parameters:
- `description`: "Review: {agent-name}"
- `subagent_type`: Use the exact agent type name (e.g., "Convention Reviewer", "TypeScript Reviewer", "Design Reviewer", "Security Reviewer", "Architecture Reviewer", "Simplicity Reviewer", "Test Reviewer", "Performance Reviewer", "Frontend Reviewer")
- `model`: "sonnet"
- `max_turns`: 20
- `run_in_background`: true
- `prompt`: Use this template, filling in the agent-specific sections:

**IMPORTANT:** Replace `{AGENT_NAME}` below with the actual agent type (e.g., "Design Reviewer", "Security Reviewer") before sending.

```
YOUR #1 JOB: Output the findings block below before you run out of turns. Everything else is secondary.

You are the {AGENT_NAME}. Your output MUST start with:

AGENT: {AGENT_NAME}
FINDINGS_COUNT: {number, or 0 if none}

FINDING: 1
SEVERITY: design | detail
CONFIDENCE: {0-100}
FILE: {file path}
LINE: {line number}
TITLE: {brief title}
ISSUE: {what's wrong}
VERIFIED: {evidence}
SUGGESTION: {fix}
RULE: {rationale}
---

If zero findings, just output: AGENT: {AGENT_NAME} / FINDINGS_COUNT: 0

## What to review

**Change summary:** {CHANGE_SUMMARY}
**Changed files:** {file list}
{If PAST_SOLUTIONS is non-empty: **Past learnings:** {PAST_SOLUTIONS}}
{Agent-specific focus instructions}

## How to review (max 3 verification reads)

1. Read `~/.claude/skills/review/verification-rules.md` for rules and hard exclusions
2. {If relevant: Read `~/.claude/skills/review/scan-patterns.md`}
3. {If Convention: Read CLAUDE.md files: {CLAUDE_MD_PATHS}}
4. Read the diff: `{DIFF_COMMAND or Read /tmp/review-{scope}.diff}`
5. Identify up to 3 strong candidates from your focus area
6. Verify each by reading ONLY the specific lines in the actual file (not the whole file)
7. OUTPUT the findings block above — this is mandatory

RULES: Max 3 findings. Max 3 file reads for verification. Do NOT use Write/Edit. Text output only.
```
</parallel_tasks>

**Agent-specific context to include in prompts:**

| Agent | Extra context |
|-------|--------------|
| Convention Reviewer | CLAUDE.md file paths to read, scan-patterns.md |
| TypeScript Reviewer | scan-patterns.md |
| Design Reviewer | scan-patterns.md (silent failure scan) |
| Security Reviewer | scan-patterns.md (silent failure scan), project threat model if non-default |
| Architecture Reviewer | Package structure description |
| Test Reviewer | Note which files are test files vs code they test |
| Performance Reviewer | Note which files have DB queries, IPC calls, React components |
| Frontend Reviewer | Note which files are .tsx, hooks, effects |
| Simplicity Reviewer | (standard prompt is sufficient) |

#### Pre-scoping Diffs for Large Reviews

For **medium and large** reviews, the full diff is too large for agents to read in one turn. Pre-scope diffs before spawning.

Use the `--stat` output to classify changed files into these categories, then save scoped diffs:

```bash
# Backend services, models, stores (non-test, non-frontend)
git diff main...HEAD -- 'packages/*/backend/**' 'packages/*/services/**' 'packages/db/**' 'packages/llm-core/**' 'packages/mcp-remote/**' 'packages/deno-runner/**' 'packages/code-runner/**' > /tmp/review-backend.diff

# Frontend components, hooks, screens
git diff main...HEAD -- 'packages/*/frontend/**' 'packages/*/renderer/**' '*.tsx' '*.css' > /tmp/review-frontend.diff

# Shared types, schemas, config, infra
git diff main...HEAD -- 'packages/schema/**' 'packages/skill-manifest/**' 'packages/sdk/**' 'packages/prompts/**' 'packages/object-graph/**' 'packages/markdown/**' 'packages/search/**' '*.json' > /tmp/review-infra.diff

# Test files only
git diff main...HEAD -- '**/__tests__/**' '**/*.test.ts' '**/*.test.tsx' > /tmp/review-tests.diff

# Auth/IPC/MCP security surface
git diff main...HEAD -- '**/oauth/**' '**/auth/**' '**/mcp/**' '**/ipc/**' 'packages/mcp-remote/**' > /tmp/review-security.diff
```

Adapt the glob patterns to what actually changed — if a category has 0 lines, skip it.

Map agents to diff files:
- **Design, Simplicity**: `/tmp/review-backend.diff`
- **Convention**: `/tmp/review-backend.diff` + `/tmp/review-infra.diff`
- **TypeScript**: `/tmp/review-infra.diff` + `/tmp/review-backend.diff` (type-heavy files)
- **Security**: `/tmp/review-security.diff`
- **Architecture**: `/tmp/review-backend.diff` + `/tmp/review-infra.diff`
- **Test**: `/tmp/review-tests.diff`
- **Performance**: `/tmp/review-backend.diff` (IPC/DB paths) + `/tmp/review-frontend.diff` (React renders)
- **Frontend**: `/tmp/review-frontend.diff`

Tell each agent: `Read /tmp/review-{scope}.diff to get the diff` instead of running the git command. This saves them a turn.

**WAIT** for all background agents to complete before proceeding to Phase 3.

---

### Phase 3: Synthesize and Validate

After all agents report:

1. **Collect** all agent outputs — parse the structured FINDING blocks from each
   - If an agent returned without a `FINDINGS_COUNT` line, treat it as 0 findings and mark it as "No structured output" in the Coverage table. Do NOT retry or re-read its output looking for findings — move on.
2. **Merge** into a single list
3. **Deduplicate** — same issue from multiple agents = report once with higher confidence
4. **Cross-validate** — issues flagged by 2+ agents are especially credible
5. **Challenge every finding**:
   - Read the actual code referenced (not just the diff)
   - Ask: "Is this actually wrong, or intentional?"
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

- NEVER hardcode CLAUDE.md rules in prompts. Read files fresh every time.
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
