---
name: wrap-up
description: End-of-day summary of all in-flight work across repos. Gathers branches, commits, PRs, uncommitted changes, and vault docs to create a clear "pick up Monday" document. Triggers on "wrap up", "end of day", "eod summary".
---

# Wrap Up Day

Generate a comprehensive end-of-day summary of all in-flight work across all repos in the working directory tree, then save it to the agent workspace.

## Phase 1: Discover Repos

Find all git repos the user is working with:

1. Check the primary working directory and any additional directories from settings
2. For each directory that looks like a project root (has `.git/`), gather state
3. Also check sibling directories of the primary working directory (e.g., if working in `~/projects/frontend`, also check `~/projects/backend`, `~/projects/api`, etc.)

```bash
# Find repos in the project parent directory
for dir in <parent>/*; do
  if [ -d "$dir/.git" ]; then
    echo "$dir"
  fi
done
```

## Phase 2: Gather State Per Repo

For each discovered repo, collect:

### Branches
```bash
git branch --sort=-committerdate --format='%(refname:short) (%(committerdate:relative))'
```

Only include branches with commits in the last 7 days (skip stale ones).

### For each active branch (diverged from main)
```bash
git log --oneline $(git merge-base <branch> main)..<branch>
```

### Uncommitted work
```bash
git status --short
git diff --stat  # summarize scope of unstaged changes
git stash list
```

### Open PRs
```bash
gh pr list --state open --json number,title,headRefName,url --jq '.[] | "#\(.number) \(.title) [\(.headRefName)]"'
```

### Recently merged PRs (today only)
```bash
gh pr list --state merged --limit 10 --json number,title,mergedAt --jq '.[] | select(.mergedAt | startswith("YYYY-MM-DD")) | "#\(.number) \(.title)"'
```

Replace `YYYY-MM-DD` with today's date.

## Phase 3: Gather Workspace Activity

Search for workspace docs modified today:

```bash
find .untracked -name "*.md" -newer .untracked/in-flight.md -maxdepth 3 2>/dev/null
```

Run this from the project root where `.untracked/` lives.

## Phase 4: Write the Summary

Create a markdown file with this structure:

```markdown
# In-Flight Work — YYYY-MM-DD (Day of Week)

## Merged Today
Table of PRs merged today with PR number, title, and repo.

## Open PRs (need review / merge)
For each open PR:
- Branch name and repo
- Status and commit count
- What it does (one sentence from PR title + commit messages)
- Next steps

## Branches Not Yet PR'd
For each branch with divergent commits:
- Branch name and repo
- Commit list (short hash + message)
- Summary of what the work is
- State: clean working tree vs uncommitted changes (with diff --stat summary)
- Link to vault plan if one exists
- Next steps as checkboxes

## Uncommitted Work
For repos with dirty working trees, summarize:
- Which files changed and rough scope
- What the changes are about (infer from file paths and diff context)

## Plans & Docs Active Today
Table with paths to workspace docs modified today.

## Monday Priority Order
Numbered list of what to tackle first, ordered by:
1. Things closest to shipping (ready to PR, ready to merge)
2. Things with significant uncommitted work at risk of context loss
3. Everything else by recency
```

## Phase 5: Save

**Output path:**
```
.untracked/in-flight.md
```

Overwrite the existing `in-flight.md` if one exists.

## Phase 5.5: Archive Stale Topics

After writing the summary, clean up the workspace:

1. List all topic folders in `.untracked/`
2. For each topic folder, check if its associated branch still exists:
   ```bash
   git branch --list "{topic}" "feat/{topic}" "*/{topic}" 2>/dev/null
   ```
3. If the branch has been merged or deleted (no matching branch exists), move the folder to `.untracked/.archive/{topic}/`
4. Report what was archived: "Archived N stale topic folders: {list}"

Skip folders named `solutions/` — those are permanent.

## Key Principles

- **Be thorough** — check every repo, every branch, every stash. The whole point is to not miss anything.
- **Be concise** — each item should be scannable in seconds. No paragraphs, use tables and bullet points.
- **Prioritize actionability** — the Monday priority list is the most important section. Order it well.
- **Link everything** — workspace docs get file paths, PRs get PR numbers, branches get names.
- **Infer context** — use commit messages, file paths, and vault docs to summarize what work is about. Don't just list files.
- **Flag risk** — if there's significant uncommitted work, call it out. That's the stuff most likely to lose context over a weekend.
