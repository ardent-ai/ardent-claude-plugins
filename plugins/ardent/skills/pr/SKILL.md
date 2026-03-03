---
name: pr
version: 1.1.0
description: |
  Create a pull request end-to-end: generate description, humanize the copy,
  find and link related Linear issues, optionally generate a visual reviewer guide,
  and open the PR via gh CLI.
---

# PR — Create Pull Request

End-to-end PR creation pipeline. Analyzes the branch, generates a description, humanizes the copy, links Linear issues, optionally produces a visual reviewer guide, and creates the PR.

## Pipeline

### 1. Analyze the branch

Run these in parallel:
- `git log --oneline origin/main..HEAD` — commit history
- `git diff origin/main...HEAD --stat` — file overview
- `git diff origin/main...HEAD` — full diff (read key files if too large)

Check if the branch is pushed:
```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null
```
If no upstream, push with `-u`:
```bash
git push -u origin HEAD
```

### 2. Generate PR title and description

Determine the PR type from the branch changes (ask if unclear):
- `issue` — bugs, fixes, regressions, performance problems, technical corrections
- `feature` — normal features, improvements, small UX additions, non-architectural changes
- `big-feature` — new systems, architectural changes, major UX flows, large refactors

Generate the title and body using the matching template below.

**PR title rules:**
- Concise and descriptive
- Captures the high-level **what and why**, not mechanics
- Prefer conventional style: `fix(auth): prevent session reset on refresh`, `feat(payments): add MercadoPago checkout support`

#### Template — Issue

```md
## Problem

<What was happening? When did it occur?>

## Root Cause

<Technical cause, if known.>

## Solution

<What changed and why it fixes the problem.>

## Outcome

<Impact. Demo links, videos, screenshots if available.>
```

#### Template — Feature

```md
## Problem

<The need, limitation, or missing capability.>

## Root Cause

<Optional. Only if there was a technical limitation to solve.>

## Outcome

<What the feature enables and its impact.>
```

- No **Solution** section for features.
- Root Cause is optional — omit if not relevant.

#### Template — Big Feature

```md
<High level explanation of what this PR introduces and why it matters. Start directly — no "Summary" header.>

### Key Changes

- <Main change>
- <Main change>
- <Main change>

---

### Architecture Overview

#### Concept / Strategy

<Main architectural idea>

#### Implementation

<Folders, routing, state, patterns, infra>

#### Components / Systems

<Main modules or domains involved>

#### Data / State Flow

<How data moves through the system>

#### Navigation / UX Flow

<If applicable — omit if not>

#### Migration / Breaking Changes

<If applicable — omit if not>

---

### Notes

<Tradeoffs, future improvements, known limitations>
```

- Omit any architecture subsection that isn't relevant.

### 3. Humanize the copy

Invoke `/humanizer` via the Skill tool. Pass it the generated title and body text. It removes AI writing patterns (bold-header lists, em dashes, rule of three, sycophantic tone, promotional language, etc.).

Update the title and body with the humanized versions.

### 4. Search Linear for related issues

Search for related issues using `mcp__plugin_linear_linear__list_issues` with:
- `query` derived from PR title keywords and branch name keywords
- Filter to open states if the tool supports it

**Linking logic:**
- **Obvious match** (issue title/description clearly matches the PR scope) → auto-append `Closes ENG-XXX` to the body
- **Multiple plausible matches or uncertain** → present candidates to the user via AskUserQuestion, let them pick which to link (or none)
- **No matches** → skip, mention that no related issues were found

Append any linked issues at the bottom of the body, each on its own line:
```
Closes ENG-123
```

### 5. Reviewer guide (conditional)

Assess whether the PR warrants a visual reviewer guide. The decision:

- **`big-feature`** → always generate one
- **`feature`** → generate when the diff touches 4+ files across 2+ packages/directories, introduces new data flows, or adds a new system/module that a reviewer would need context to understand
- **`issue`** → skip

If the PR doesn't qualify, move to step 6.

**If generating:**

1. Invoke `/visual-explainer` via the Skill tool. Frame the prompt around what a reviewer needs to understand — the before/after, the data flow, the architecture change, or the new UX flow. Use the branch diff and PR description as source material.
2. Invoke `/archive` via the Skill tool to publish the HTML to the docs archive. Use the PR title as the archive title.
3. Add the archive URL to the PR body. Insert it right after the opening paragraph or Key Changes section, as a standalone line:
   ```md
   [Reviewer guide](https://ardent-ai.github.io/docs-archive/docs/{date}-{slug}.html)
   ```

### 6. Create the PR

Present the final title and body to the user for review before creating. Then:

```bash
gh pr create --title "the title" --body "$(cat <<'EOF'
body content here
EOF
)"
```

Use `gh api repos/{owner}/{repo}/pulls/{n} -X PATCH -f body="..."` for any subsequent body edits — never `gh pr edit --body`.

Return the PR URL when done.

## Rules

- No "Summary" header at the top of the body — start directly with content.
- No "Test plan" section.
- No AI attribution lines ("Generated by", "Co-Authored-By").
- First person voice ("I added...", "I tested...") not "we".
- Keep it conversational and concise — a human engineer would write this.
- Focus on **why + impact**, not only what changed.
- No function signatures, format specs, or implementation minutiae in the description.
