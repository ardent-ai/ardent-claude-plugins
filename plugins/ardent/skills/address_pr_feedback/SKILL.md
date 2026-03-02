---
name: address_pr_feedback
description: Analyze PR changes and comments, create a plan, and implement feedback
argument-hint: [pr-number-or-url]
allowed-tools: Task, Read, Write, Edit, Bash
---

# Address PR Feedback

Resolve unresolved PR review threads — fetch via GraphQL, fix in parallel, commit, and optionally push + resolve.

## Variables
PR_INPUT

## Phase 1: Setup

Determine PR_NUMBER:
- If `PR_INPUT` is just a number (e.g., "59"), use as-is
- If `PR_INPUT` is a path format (e.g., "/pull/59"), extract the number
- If `PR_INPUT` is a full URL (e.g., "https://github.com/owner/repo/pull/59"), extract the number
- If no `PR_INPUT` is provided, try to find the PR for the current branch:
  - Run `gh pr view --json number --jq '.number'`
  - If a PR is found, use that number
  - If no PR is found, STOP and ask the user to provide a PR number or URL

Get the repo owner and name:
```bash
gh repo view --json owner,name --jq '"\(.owner.login) \(.name)"'
```

Get PR branch name with `gh pr view PR_NUMBER --json headRefName --jq '.headRefName'`

Check current branch with `git branch --show-current`. If not on the PR's branch:
- Check for uncommitted changes with `git status --porcelain`
- If there are any changes, STOP immediately and tell the user
- If no changes: `git fetch origin && git checkout BRANCH_NAME && git pull origin BRANCH_NAME`
- Verify we're up to date with `git status`

## Phase 2: Fetch Unresolved Threads

Use GraphQL to fetch only unresolved, non-outdated review threads:

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 10) {
            nodes {
              body
              author { login }
              path
              position
            }
          }
        }
      }
    }
  }
}' -f owner="OWNER" -f repo="REPO" -F pr=PR_NUMBER
```

Filter to threads where `isResolved == false` and `isOutdated == false`.

If zero unresolved threads: report "No unresolved feedback — nothing to do." and stop.

### Categorize by Priority

Classify each thread as **high**, **medium**, or **low**:

| Priority | Signals |
|----------|---------|
| **high** | `h:` prefix, "blocker", "changes requested", security/correctness issues |
| **medium** | `m:` prefix, standard feedback with no priority marker (default) |
| **low** | `l:` prefix, "nit", "style", "suggestion", "optional", "minor", "consider" |

**Auto-address:** high + medium threads.

**Prompt user for low-priority threads** before proceeding to Phase 4. Present a numbered list:

```
Found N low-priority suggestions:
1. [nit] "Consider renaming this variable" — @reviewer in api.ts:42
2. [l] "Could extract this into a helper" — @reviewer in utils.ts:18

Which would you like to address? (e.g., "1,2" or "all" or "none")
```

Add selected low-priority threads to the auto-address set. Discard unselected ones — do not fix them.

## Phase 3: Analyze and Plan (Conditional)

**If 5 or more unresolved threads:** Create a plan document at `.untracked/pr-feedback/plan.md` with:
- Summary of all unresolved threads with file paths and line numbers
- Mapping of comments to specific code locations
- Prioritized list of changes to make
- Each change should show the comment it addresses

Present the plan to the user and ask: "Does this plan look good, or would you like any modifications?"

**If fewer than 5 threads:** Skip the plan — go straight to parallel resolution.

Create the `.untracked/` directory if it doesn't exist.

## Phase 4: Parallel Resolution

Spawn all sub-agents in a SINGLE message using the Task tool with `run_in_background: true`:

1. **Branch Analysis Agent** — Task with `subagent_type: "general-purpose"`, `model: "haiku"`: "Fetch PR title/description, run `git log --oneline origin/main..HEAD`, analyze all changes and author intent. Return: modified files, change summary, context."

2. **Resolution Agents** — For each unresolved thread (or group of small related threads targeting the same file), spawn a Task with `subagent_type: "general-purpose"`, `model: "sonnet"`, `run_in_background: true`:

   Each agent receives:
   - The thread's comments (body, author, file path, line numbers)
   - The branch analysis context
   - Instructions: Read the file, understand the feedback, implement the fix. If the feedback is unclear or requires a design decision, report it as "needs judgment" instead of guessing.

   Each agent returns:
   - What it changed (file:line references)
   - Which thread it addressed
   - Whether it was resolved or flagged as "needs judgment"

After all agents complete, synthesize results.

## Phase 5: Commit and Summarize

Commit all fixes (don't push yet):
```bash
git add <changed files>
git commit -m "fix: address PR review feedback"
```

Present a summary:

```markdown
## PR Feedback Resolution

| Priority | Thread | File | Fix Applied | Status |
|----------|--------|------|-------------|--------|
| high | @reviewer: "comment excerpt..." | path/to/file.ts:42 | Description of fix | Resolved |
| medium | @reviewer: "comment excerpt..." | path/to/file.ts:88 | Needs judgment — reason | Skipped |
| low (skipped) | @reviewer: "nit: ..." | path/to/file.ts:22 | — | User declined |

**Changes:** X files modified, Y threads resolved, Z need manual review
```

Run `npm run lint` and `npm run typecheck` to verify fixes don't break anything.

## Phase 6: User Review Gate

Use **AskUserQuestion tool**:

**Question:** "Fixes committed locally. What would you like to do?"

**Options:**
1. **Push, reply, and resolve threads** — Push to remote, post replies, then resolve threads via GraphQL
2. **Review first** — Let me look at the changes before pushing
3. **Don't push** — Keep changes local only

#### Push, reply, and resolve threads

Push to remote:
```bash
git push origin $(git branch --show-current)
```

##### Draft Thread Replies

Before resolving threads, draft a short reply for each resolved thread. The reply should:
- Briefly acknowledge the feedback
- State what was done to address it (e.g., "Renamed to `X`", "Extracted into a named type", "Added the missing null check")
- Be 1-2 sentences max — concise and direct

**Run each draft reply through the `/humanizer` skill** before presenting it. This ensures the replies sound natural and don't read as AI-generated.

Present all draft replies to the user in a single table:

```markdown
## Draft Thread Replies

| Thread | Reviewer | Reply |
|--------|----------|-------|
| path/to/file.ts:42 | @reviewer | "Good catch — renamed to `processItems` for clarity." |
| path/to/file.ts:88 | @reviewer | "Extracted `WidgetConfig` as a named type." |
```

Ask: "These replies will be posted before resolving each thread. Edit any you'd like to change, or approve to proceed."

Wait for user approval. The user may:
- Approve all as-is
- Edit specific replies (apply their edits exactly)
- Skip replies for certain threads (resolve without replying)

##### Post Replies and Resolve

For each approved reply, post the comment on the thread, then resolve:

```bash
# Reply to the thread (use the first comment's GraphQL node ID as the reply target)
gh api graphql -f query='
mutation($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $threadId, body: $body}) {
    comment { id }
  }
}' -f threadId="THREAD_ID" -f body="REPLY_TEXT"

# Then resolve
gh api graphql -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { isResolved }
  }
}' -f threadId="THREAD_ID"
```

For threads the user skipped replies on, resolve without posting a comment.

Report which threads were replied to and resolved.

#### Review first

Run `git diff HEAD~1` and present the changes. Then loop back to the options.

## Phase 7: Prevent Recurrence

After the user gates on push/review, close the feedback loop. The goal is to prevent the same *class* of issue from reaching a human reviewer again.

### 7a. Classify the Addressed Issues

For each thread that was actually resolved (not skipped, not flagged "needs judgment"), identify what *class* of problem it was:

| Class | Examples |
|-------|---------|
| **TypeScript anti-pattern** | Indexed access annotations, utility-type extraction, `typeof` in type positions, inline anonymous object types, weakened discriminated unions |
| **Style / naming** | Wrong naming convention, import style, file organization |
| **Architecture** | Cross-package import, wrong layer, missing abstraction |
| **React / frontend** | Stale closure, missing cleanup, incorrect deps, async race |
| **Runtime logic** | Missing error case, edge case, incorrect behavior |
| **Process gap** | Something that should have been caught during implementation |

### 7b. Match Each Class to a Prevention Mechanism

Work through this priority order and find the best available option for each class of issue:

**1. Biome lint rule** — deterministic, zero-friction, catches it at commit time

Read the project Biome config:
```bash
cat biome.json 2>/dev/null || cat biome.jsonc 2>/dev/null
```

Check if a relevant rule exists but is disabled or set to `warn` instead of `error`. Full rule reference: https://biomejs.dev/linter/rules/

If a Biome rule can catch the pattern: propose enabling or tightening it. Note that Biome doesn't support custom plugins, so if no rule covers the pattern, move to the next option.

**2. TypeScript compiler flag** — for type-safety issues

Check `tsconfig.json` for flags that could have caught it: `noImplicitReturns`, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`, `noPropertyAccessFromIndexSignature`, etc.

**3. AGENTS.md** — for patterns the AI agent routinely introduces

Read `AGENTS.md` first to avoid duplicates. If this is a pattern the agent keeps producing (not a one-off logic error), add a precise, actionable rule:
- "Don't do X, use Y instead" — not vague
- Placed under an existing relevant section if one fits

**4. Review skill** — for quality patterns the automated reviewer should catch but currently doesn't

If it's a code quality issue that should be flagged in review, add it to the Type Quality Scan table or as a check in `~/.claude/skills/review/SKILL.md`.

**5. Work skill** — for process gaps during implementation

If it's something that should be verified while building the feature, add a question to the System-Wide Test Check in `~/.claude/skills/work/SKILL.md`.

### 7c. Present the Prevention Plan

Show the user a table before making any changes:

```markdown
## Recurrence Prevention

| Issue | Class | Mechanism | Proposed Change |
|-------|-------|-----------|----------------|
| Indexed access used as annotation | TypeScript | Review skill | Already covered in Type Quality Scan |
| `noConsole` violation | Style | Biome rule | Already enforced (`"noConsole": "error"`) |
| Inline anonymous object in function sig | TypeScript | AGENTS.md | Add rule under TypeScript Patterns |
| Missing error case in handler | Runtime logic | Work skill | Add question to System-Wide Test Check |
```

For each item where the pattern is already covered (existing Biome rule, existing AGENTS.md rule, existing review check): say so — don't add duplicates.

Ask: "Which of these would you like to apply?"

Wait for user selection before touching any files.

### 7d. Apply Approved Changes

For each approved prevention:

- **Biome rule**: Edit `biome.json`/`biome.jsonc`. Run `npm run lint:fix` to verify no unexpected new errors. Commit to repo: `chore: enforce lint rule to prevent {pattern}`
- **TypeScript flag**: Edit `tsconfig.json`. Run `npm run typecheck`. Commit: `chore: tighten tsconfig to prevent {pattern}`
- **AGENTS.md**: Edit the file with a precise rule. Commit: `docs: add rule to prevent {pattern}`
- **Review skill**: Edit `~/.claude/skills/review/SKILL.md` — not committed to the repo
- **Work skill**: Edit `~/.claude/skills/work/SKILL.md` — not committed to the repo

If the Biome or tsconfig change introduces new errors beyond the expected ones, revert it and report to the user.

## Report

### Post-Resolution Report
- Total unresolved threads found
- Threads resolved vs. threads needing judgment
- Files modified with `git diff --stat`
- Lint and typecheck status
- Any threads that couldn't be addressed and why
- Prevention mechanisms applied (or why each class had no viable prevention)
