---
name: lfg
description: Full autonomous engineering pipeline — plan, deepen, build, review, fix. Use --swarm for parallel build + review on bigger features.
argument-hint: "[--swarm] [feature description]"
---

# LFG

End-to-end autonomous pipeline. Takes a feature description through planning, research, implementation, review, and fix — stopping only for clarification or approval gates built into each phase.

Use `--swarm` for bigger features: always deepens the plan and uses parallel execution for build and review.

## Input

<feature_description> $ARGUMENTS </feature_description>

**If empty:** Ask "What are we building?" and wait.

## Setup

Before starting the pipeline, handle all decisions upfront so the rest runs uninterrupted.

**Parse flags:** extract `--swarm` and any `--branch <name>` from the feature description. Strip them from the description passed to subsequent steps.

**Branch:** Use **AskUserQuestion tool**:

- **Question:** "Branch name for this feature?"
- **Options:**
  1. **Auto-derive** — derive from the feature description (e.g., `feat/add-user-auth`)
  2. **Current branch** — continue on `{current_branch}` (only if already on a feature branch)

If the user provides a custom name via "Other", use that.

Create the branch immediately:
```bash
git pull origin main && git checkout -b {branch_name}
```

If already on the chosen branch, skip creation.

## Pipeline

Run each step in order. Each step is a slash command — invoke it via the Skill tool, passing context forward.

### 1. Plan

```
/plan-ardent <feature_description>
```

Wait for the plan to be written. The plan includes a **Design Review** checkpoint (Phase 2) — let the user iterate on the high-level design there before detailing code changes. Don't rush past this phase.

**Skip Phase 5 options menu.** When plan-custom finishes writing the plan and would normally present the "What next?" AskUserQuestion, do NOT present it. Capture the plan file path and proceed directly to the next step.

### 1.5. Deepen (conditional)

- **If `--swarm` mode:** Always run `/deepen-plan` on the plan.
- **Otherwise:** Only run `/deepen-plan` if the feature is complex (multi-phase, architectural, or unfamiliar territory). For simple features (clear scope, known patterns, <3 files), skip deepening entirely.

### 2. Build

```
/work <plan_file_path>
```

The branch was already created in Setup. When `/work` asks about the branch, choose **continue on the current branch**. `/work` handles task breakdown, implementation, incremental commits, and quality gates (`npm run lint`, `npm run typecheck`).

### 3. Simplify

```
/cleanup
```

Clean up all changed files — dead code, nesting, trivial helpers, redundant logic. Re-run lint + typecheck after.

### 4. Review + Fix

**Always spawn review as an agent** to avoid context exhaustion from the accumulated pipeline work:

**If `--swarm` mode:** Launch TWO agents in parallel (SINGLE message, both with `run_in_background: true`):

- **Agent A — Review:** Task with `subagent_type: "general-purpose"`, `model: "sonnet"`: Run `/review-ardent fix` — reviews the branch and auto-fixes Detail findings. Return the report and any Design findings.
- **Agent B — Quality gates:** Task with `subagent_type: "general-purpose"`, `model: "haiku"`: Run `npm run typecheck && npm test -- --run`.

Wait for both to complete. If review found Design findings or tests/typecheck failed, fix them sequentially, then re-run `npm run lint && npm run typecheck && npm test -- --run`.

**Otherwise (default):**

Spawn a general-purpose agent:
```
Agent tool:
  subagent_type: "general-purpose"
  model: "sonnet"
  prompt: "Run `/review-ardent fix` on the current branch. Reviews the branch and auto-fixes Detail findings by amending them into the correct commits. Design findings are reported but not auto-fixed. Return the review report and any Design findings that need judgment."
```

Wait for the agent to complete. If it reports Design findings, address them. Then re-run `npm run lint && npm run typecheck`.

### 5. Done

Summarize what was built:
- Branch name and commit count
- What the feature does (one sentence)
- Any Design findings from review that weren't auto-fixed
- Any open questions or follow-up work

**Stop here.** Do NOT push, create a PR, or do any remote git operations. The user will decide when to ship.

## When to Bail Out

If any step fails or gets stuck:
- **Plan unclear** — Ask for clarification, don't guess
- **Build blocked** — Report what's blocking and suggest options
- **Tests won't pass** — Fix up to 3 attempts, then report with details
- **Review finds P1 issues** — Fix them. If the fix is non-trivial, explain the approach before applying
- **Swarm coordination issues** — Fall back to sequential execution and report the issue

Don't silently cut corners. If something is harder than expected, say so.
