---
name: review-ardent
description: Adaptive code review that scales from single-pass to full parallel swarm based on change size. One command for all review needs. Triggers on "review", "review my code", "check my changes". Use "/review-ardent fix" to auto-fix findings.
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

Store the **file paths** as `CLAUDE_MD_PATHS` — agents will read these files themselves (do NOT paste CLAUDE.md contents into agent prompts).

- **Small strategy**: Read every CLAUDE.md file for your own understanding — you'll need them for single-pass review.
- **Medium/Large strategy**: Do NOT read CLAUDE.md files yourself — only collect the paths. Agents will read them. Keep your context lightweight for synthesis.

#### 1b. Check Past Solutions

Scan for learnings from previous reviews and debugging sessions that may be relevant to this change:

```bash
ls .untracked/solutions/ .untracked/.shared/ 2>/dev/null || true
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

Store the **base diff command** as `DIFF_COMMAND` (e.g., `git diff main...HEAD`). Agents will use this with per-file scoping — NOT read a monolithic diff.

**Context management for the orchestrator:**
- **Small strategy**: Run the full diff yourself — you'll need it for single-pass review.
- **Medium/Large strategy**: Only run `{DIFF_COMMAND} --stat` and `git log --oneline main..HEAD` for scope measurement and the change summary. Do NOT read the full diff — agents will get per-file diffs themselves. Keep the orchestrator context lightweight so it can hold all 9 agent outputs during synthesis.

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

**ONLY use this if you announced "large" in Phase 1d.** You MUST spawn agents for all 9 agent types — do NOT do a single pass.

The 9 agent types: Convention, Design, Simplicity, TypeScript, Security, Architecture, Test, Performance, Frontend.

**After building the coverage matrix**, skip agent types with 0 files and split any type exceeding 20 files into multiple instances (see coverage matrix step 3). The total agent count is dynamic — it scales with the size of the change.

Then proceed to **Spawning Agents** below.

---

#### Building the File Coverage Matrix

<critical>
Do NOT manually compute chunk assignments, domain filtering, or agent counts in your thinking. Run the script below — it handles classification, bin-packing, domain filtering, merge of tiny trailing chunks, and threshold checks in milliseconds. Parse the output mechanically and spawn agents from it.
</critical>

**Run the coverage script** (replace `{DIFF_COMMAND}` with the actual diff command):

```bash
bash ~/.claude/skills/review-ardent/chunk-files.sh '{DIFF_COMMAND}'
```

The output contains pre-chunked file lists organized by agent category:

| Output section | Agent types to spawn | How many instances |
|---|---|---|
| `=== CROSS ===` | Convention, Design, Simplicity | One instance of **each** type per `CHUNK` |
| `=== TEST ===` | Test | One instance per `CHUNK` |
| `=== ARCHITECTURE ===` | Architecture | One instance per `CHUNK` |
| `=== FRONTEND ===` | Frontend | One instance per `CHUNK` |
| `=== SECURITY ===` | Security | One instance per `CHUNK` |
| `=== TYPESCRIPT ===` | TypeScript | One instance per `CHUNK` |
| `=== PERFORMANCE ===` | Performance | One instance per `CHUNK` |

- Sections marked `(skip)` or `(N lines, skip)` — skip that agent type entirely.
- Each `CHUNK N/M` header shows its pre-saved diff file path in brackets: `[/tmp/review-cross-1.diff]`. Pass this path as `{DIFF_FILE}` in the agent prompt.
- The file list under each chunk shows files with line counts — copy directly into the agent's file manifest.
- For cross-cutting agents (Convention, Design, Simplicity) sharing the same CROSS chunk, all three agents use the **same** diff file.
- Name instances: `Convention 1/6`, `Convention 2/6`, etc. Report skipped types as "No files in scope" in Coverage.

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

Each agent receives: its **diff file path** (from coverage matrix `[...]` brackets), the **change summary**, and **focus instructions** (from table below). Convention agents also get **CLAUDE.md paths**. All agents read `verification-rules.md` themselves (it has the output format, verification rules, and hard exclusions). Use `run_in_background: true`.

<parallel_tasks>
Spawn all agents in ONE message. For each agent:
- `description`: "Review: {agent-name}"
- `subagent_type`: The exact type (e.g., "Convention Reviewer", "Design Reviewer")
- `run_in_background`: true
- `prompt`: Use this template — replace `{PLACEHOLDERS}`. Keep it SHORT — do not add text beyond what's here:

```
{AGENT_NAME}. Read ~/.claude/skills/review-ardent/verification-rules.md then {DIFF_FILE}.
{If Convention: Also read CLAUDE.md: {CLAUDE_MD_PATHS}}
Change: {CHANGE_SUMMARY}
Focus: {FOCUS_INSTRUCTIONS}
Max 3 findings, max 3 verification reads. No Write/Edit.
```
</parallel_tasks>

**Agent-specific focus instructions to include in prompts:**

| Agent | Focus instructions |
|-------|---|
| Convention Reviewer | Check CLAUDE.md compliance: naming, patterns, imports, component usage. Run the **Type Quality Scan**: look for indexed access types (`SomeType['prop']`), utility-type extraction (`ReturnType<typeof fn>`), `typeof` in type positions, `unknown` + cast, inline anonymous types in signatures, weakened discriminated unions. Also run **AI Debt Scan**: restating comments, docstring bloat, generic naming, boilerplate error handling, nosy debug logging, bare TODOs. |
| TypeScript Reviewer | Type safety, modern patterns, naming quality. Run the **Type Quality Scan** (same patterns as Convention). |
| Design Reviewer | Right approach? Clean data flow? Proper separation of concerns? Run the **Silent Failure Scan**: empty catch blocks, swallowed errors, broad exception catching, silent fallbacks, missing error context, fire-and-forget without catch. |
| Security Reviewer | Actual vulnerabilities given the threat model. Run the **Silent Failure Scan**. {Include project threat model if non-default.} |
| Architecture Reviewer | Package boundary violations, cross-package coupling, proper separation of concerns. {Include package structure description.} |
| Test Reviewer | Are the right things tested? Testing philosophy compliance? {Note which files are test files vs the code they test.} |
| Performance Reviewer | N+1 queries, memory leaks, IPC overhead, unnecessary re-renders. {Note which files have DB queries, IPC calls, React components.} |
| Frontend Reviewer | Stale closures, race conditions, missing cleanup, incorrect deps, event listener leaks. {Note which files are .tsx, hooks, effects.} |
| Simplicity Reviewer | Over-engineering? YAGNI violations? Unnecessary complexity? |

**WAIT** for all background agents to complete before proceeding to Phase 3.

---

### Phase 3: Synthesize and Validate

After all agents report:

1. **Collect** all agent outputs — parse the structured FINDING blocks from each
   - If an agent returned without a `FINDINGS_COUNT` line, treat it as 0 findings and mark it as "No structured output" in the Coverage table. Do NOT retry or re-read its output looking for findings — move on.
2. **Merge** into a single list
3. **Deduplicate** — same issue from multiple agents = report once with higher confidence
4. **Cross-validate** — issues flagged by 2+ agents are especially credible
5. **Challenge findings efficiently** — do NOT read code for every finding:
   - **Confidence >= 93 with clear VERIFIED evidence**: Accept without re-reading code. The agent already verified.
   - **Confidence 85-92 or weak/missing verification**: Read the actual code to verify. Max 5 verification reads total — prioritize the most uncertain findings.
   - For all findings, apply these mental checks (no file read needed):
     - "Is this actually wrong, or intentional?"
     - For "duplication": at different boundaries? Drop it
     - For "could diverge/break": concrete triggering input? If no, drop it
     - For security: realistic attacker and vector? If no, drop it
     - For "missing X": does code actually need X, or is this over-engineering?
6. **Surface gaps** — using the Phase 1.5 analysis, identify anything obviously missing (unhandled cases, absent related changes, untested paths). Add these as Missing findings.
7. **Organize** into Design, Missing, and Details sections
8. **Number findings** sequentially starting at #1 across all sections (e.g., Design #1-#3, Missing #4, Details #5+)
9. **Clean up diff files**: `rm -f /tmp/review-*.diff`

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
| Agent | Files Assigned | Status | Findings |
|-------|---------------|--------|----------|
| Convention 1/N | {count} | Done | {count} |
| Convention 2/N | {count} | Done | {count} |
| Design 1/N | {count} | Done | {count} |
| ... | ... | ... | ... |
| {domain agent} | {count} | Done / No files in scope | {count} |
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
