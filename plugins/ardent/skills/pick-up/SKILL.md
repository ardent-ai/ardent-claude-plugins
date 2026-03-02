---
name: pick-up
description: Morning briefing from the most recent in-flight doc. Reads the last wrap-up, diffs it against current repo state, flags what changed overnight, and presents a prioritized list of what to work on. Triggers on "pick up", "what's next", "morning briefing", "where did I leave off".
---

# Pick Up

Read the most recent in-flight summary and produce a morning briefing by diffing it against current repo state.

## Phase 1: Find the Latest In-Flight Doc

Search the agent workspace for the most recent in-flight file:

```bash
find .untracked -name "in-flight.md" -maxdepth 2 | head -1
```

If no in-flight doc is found, tell the user and suggest running `/wrap-up` first.

Read the file and parse its sections: merged PRs, open PRs, unpushed branches, uncommitted work, and Monday priorities.

## Phase 2: Check What Changed

For each repo referenced in the in-flight doc, gather fresh state and compare.

### PRs

```bash
gh pr list --state merged --limit 20 --json number,title,mergedAt
gh pr list --state open --json number,title,headRefName,url
```

Compare against the in-flight doc:
- **Newly merged** — PRs that were "open" in the doc but are now merged
- **Newly opened** — PRs that didn't exist in the doc
- **Still open** — unchanged, carry forward

### Branches

For each branch mentioned in the doc:

```bash
git log --oneline $(git merge-base <branch> main)..<branch>
```

Compare commit counts and SHAs:
- **New commits** — branch has commits not in the doc
- **Rebased / force-pushed** — SHAs changed
- **Deleted** — branch no longer exists (probably merged)
- **Unchanged** — same state

### Uncommitted Work

```bash
git status --short
git diff --stat
git stash list
```

Compare against what the doc reported:
- **New uncommitted changes** — work done outside of commits
- **Changes committed** — previously uncommitted work is now in commits
- **Still dirty** — same uncommitted changes persist

### CI / Checks (if applicable)

```bash
gh pr checks <number> --json name,state 2>/dev/null
```

Note any failed checks on open PRs.

## Phase 3: Present the Briefing

Output a concise, scannable morning briefing directly in the conversation. Don't write a new file — this is ephemeral.

Format:

```markdown
## Morning Briefing — YYYY-MM-DD

### Since Last Wrap-Up
- ✓ PR #297 (prompt caching) was merged
- ⚠ PR #299 (gen UI v3) has failing checks
- New: 2 commits added to `feat/autonomous-skill-building`

### Priority List

1. **[action]** Brief description — context from in-flight doc
   - Status: what changed, what's needed
2. ...

### At Risk
- `feat/autonomous-skill-building` has ~476 lines of uncommitted work (unchanged since Thursday)
```

### Formatting Rules

- **Lead with changes** — what's different from the in-flight doc. If nothing changed, say so.
- **Priority list** — carry forward from the in-flight doc but reorder based on new information (e.g., if a PR was merged, remove it; if checks failed, bump it up).
- **At risk** — call out uncommitted work, stale branches, or anything that might lose context. This is the most important section for Monday mornings.
- **Keep it short** — this is a 30-second scan, not a document. No tables unless there are 4+ items in a category.
- **Action verbs** — each priority starts with what to DO: "Merge", "PR", "Review", "Continue", "Fix", "Clean up".

## Phase 4: Offer Next Steps

After the briefing, use **AskUserQuestion** to ask what to tackle:

**Question:** "What do you want to start with?"

**Options:** Generate 2-3 options from the top priorities, plus "Something else". Each option should be a concrete action (e.g., "Create PR for message queue branch", "Continue autonomous skill building").

## Key Principles

- **Fast** — this should take seconds, not minutes. Read one file, run a few git commands, compare, output.
- **Diff-oriented** — the value is in what CHANGED since the wrap-up, not restating what the wrap-up already said.
- **Actionable** — every line should either inform a decision or suggest an action.
- **Don't rewrite the in-flight doc** — this is a read-only briefing. If the user wants an updated doc, they should run `/wrap-up` again.
