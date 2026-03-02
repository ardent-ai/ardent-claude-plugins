---
name: fixup
description: Fold working tree fixes into the correct earlier commits on the current branch. Uses git blame and commit context to map each change hunk to its target commit, handles multiple fixes spanning different commits in one pass. Triggers on "fixup", "amend the right commit", "fold into the right commit", or requests to amend changes into specific earlier commits.
---

# Fixup

Fold working tree changes into the correct earlier branch commits. Analyzes each
change hunk using `git blame` and commit context (message, scope, files changed)
to determine which commit it belongs to, then creates fixup commits and
autosquash rebases — all non-interactively.

## When to Use

- After making targeted fixes that should amend earlier commits (not just HEAD)
- When multiple fixes target different commits on the branch
- When the user says "fixup", "amend the right commit", "fold this in"

## Critical Constraints

### No Interactive Git Commands

**NEVER use git commands that require user input or open an editor.**

- No `git rebase -i` without `GIT_SEQUENCE_EDITOR`
- No `git add -i` or `git add -p`
- No `git commit` without `-m`
- Use `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash` for non-interactive autosquash

### Safety

- Skip backup branches for straightforward fixups (single target, clean blame). Only create a backup ref (`fixup-backup-*`) when the rebase is risky — e.g., multiple target commits, ambiguous mappings, or hunks that needed manual splitting.
- Abort rebase on any conflict — report to user, don't try to resolve automatically
- Never push or force-push (user decides when to ship)

---

## Workflow

### Phase 1: Gather Branch Context

Understand the branch's commit structure before analyzing changes.

1. **Identify base and branch commits**

   ```bash
   BASE=$(git merge-base HEAD main)
   BRANCH=$(git branch --show-current)
   ```

2. **Collect commit context for every branch commit**

   ```bash
   # List commits oldest-first
   git log --reverse --format="%H %s" "$BASE"..HEAD

   # For each commit, get its scope
   git show --stat --format="%H%n%s%n%b" <sha>
   ```

   For each commit, record:
   - **SHA** (short is fine for display, full for commands)
   - **Title** (commit message first line)
   - **Body** (rest of commit message, if any)
   - **Files changed** (from `--stat`)
   - **Scope summary**: What this commit was "about" — infer from title + files

   Build a mental model:
   ```
   abc1234 "feat(schema): add skill versioning types"
     → Scope: data model / schema layer
     → Files: packages/schema/src/SkillVersion.ts, packages/schema/src/index.ts

   def5678 "feat(backend): add version resolution service"
     → Scope: backend service logic
     → Files: packages/app/backend/services/VersionService.ts, ...
   ```

   This context is essential for Phase 2 when blame is ambiguous.

### Phase 2: Capture and Analyze Changes

1. **Capture the full diff**

   ```bash
   # All changes (staged + unstaged) relative to HEAD
   git diff HEAD
   ```

   If there are only staged changes: `git diff --cached`
   If there are only unstaged changes: `git diff`

   Save the output mentally — you need to parse it into hunks.

2. **Parse into hunks**

   A "hunk" is one contiguous block of changes within a file, delimited by
   `@@ ... @@` headers. Each hunk is the unit of analysis.

   For each hunk, note:
   - **File path**
   - **Line range** (old lines being modified/removed)
   - **Content** (what's changing)

3. **Blame the original lines for each hunk**

   For each hunk that modifies or removes existing lines, blame those specific
   lines in the current HEAD to find which commit last touched them:

   ```bash
   git blame -L <start>,<end> HEAD -- <file>
   ```

   The blame output shows a SHA for each line. If that SHA is a branch commit
   (between BASE..HEAD), it's a strong signal for the target commit.

   **If blame points to a pre-branch commit** (before BASE), the hunk is
   modifying "inherited" code — fall through to context matching.

4. **Context matching for ambiguous hunks**

   When blame is inconclusive (new lines, pre-branch blame, mixed blame), use
   commit context to determine the target:

   **Signal priority (strongest first):**

   | Signal | How to check | Strength |
   |--------|-------------|----------|
   | Blame consensus | Most blamed lines point to one commit | Strong |
   | File exclusivity | Only one branch commit touched this file | Strong |
   | Commit scope match | Hunk is clearly about what a commit's title describes | Medium |
   | Surrounding blame | Lines above/below the hunk blame to one commit | Medium |
   | File overlap | Multiple commits touched this file, but hunk area matches one | Weak |

   **File exclusivity** is powerful: if `VersionService.ts` was only changed by
   commit `def5678`, any fix to that file almost certainly targets that commit.

   **Commit scope match**: If the hunk fixes a validation bug and commit
   `abc1234` is titled "add input validation", that's a strong contextual match
   even if blame points elsewhere (e.g., the line was reformatted by a later
   commit).

5. **Handle edge cases**

   - **Purely new lines** (additions with no modified/removed lines): Use file
     exclusivity first, then scope matching.
   - **Hunk touches lines from multiple commits**: If the lines clearly split
     between two commits, consider splitting the hunk. If interleaved, pick the
     commit with the strongest signal and note it for user confirmation.
   - **No clear match**: Flag for user decision in Phase 3.

### Phase 3: Present Mapping (ask only when ambiguous)

Print the mapping so the user can see it, then **proceed immediately** unless
there are ambiguous hunks that need a decision.

**Format:**

```
Fixup mapping for branch `feat/my-feature` (base: main)

  [abc1234] "feat(schema): add skill versioning types"
    ← packages/schema/src/SkillVersion.ts:15-20 (fix typo in type name)

  [def5678] "feat(backend): add version resolution service"
    ← packages/app/backend/services/VersionService.ts:42-45 (fix null check)
    ← packages/app/backend/services/VersionService.ts:78-80 (add missing return)
```

- Group hunks under their target commit
- Show file, line range, and a brief description of what the hunk does
- If there's only one commit target and the mapping is obvious, keep it brief

**When all mappings are clear: print the mapping and proceed to Phase 4 without
waiting for confirmation.** Do not ask "Proceed?" or "Look good?" — just do it.

**When any hunk is ambiguous** (flagged `[??? needs decision]`): stop and ask the
user only about the ambiguous hunks. Once resolved, proceed immediately.

### Phase 4: Execute Fixups

1. **Save changes and clean the working tree**

   ```bash
   # Save the full diff to a temp file
   git diff HEAD > /tmp/fixup-full.patch

   # Clean the working tree
   git checkout -- .
   # If there are untracked files in the diff (new files), also handle those
   ```

2. **Optionally create a backup ref** (only for risky rebases — multiple targets, ambiguous mappings, or split hunks)

   ```bash
   git branch fixup-backup-$(date +%Y%m%d_%H%M%S)
   ```

3. **For each target commit (order doesn't matter for fixup commits):**

   a. **Write a patch file containing only this commit's hunks**

      Construct a valid unified diff with:
      - The `diff --git` header for each file
      - The `---` and `+++` lines
      - Only the `@@ ... @@` hunks assigned to this commit

      Write it to `/tmp/fixup-<short-sha>.patch`

   b. **Apply the patch to the working tree**

      ```bash
      git apply /tmp/fixup-<short-sha>.patch
      ```

      If applying a partial patch for a file that has other hunks going to
      different commits, the patch must include correct line numbers. If patch
      application fails due to context mismatch, fall back to using the Edit
      tool to apply the changes manually.

   c. **Stage and create the fixup commit**

      ```bash
      git add <files touched by this patch>
      git commit --fixup=<full-sha>
      ```

   d. **Clean the working tree for the next iteration**

      ```bash
      git checkout -- .
      ```

4. **Autosquash rebase**

   ```bash
   GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash "$BASE"
   ```

   This reorders the fixup commits to sit right after their targets, then
   squashes them — all without opening an editor.

5. **If rebase fails (conflict):**

   ```bash
   git rebase --abort
   ```

   Report the conflict to the user. Do NOT attempt to resolve it automatically.
   The backup ref is still there. Common resolution paths:
   - User resolves manually and continues
   - Rethink which commit a hunk should target
   - Apply fixes to HEAD instead and deal with it differently

### Phase 5: Verify

1. **Check that no changes were lost**

   ```bash
   # Apply the original full patch to a temp branch to get expected state
   # Compare current HEAD to expected
   git diff HEAD
   git status
   ```

   There should be no remaining changes. If there are, something was missed —
   create an additional fixup or report to the user.

2. **Review the updated history**

   ```bash
   git log --oneline "$BASE"..HEAD
   ```

   The commit count should be the same as before (fixup commits are squashed).
   Commit messages should be unchanged (fixup preserves the original message).

3. **Clean up temp files and backup branch**

   ```bash
   rm -f /tmp/fixup-*.patch /tmp/fixup-full.patch
   ```

   If a backup branch was created and verification passed (no lost changes,
   correct commit count, clean working tree), delete it:

   ```bash
   git branch -D fixup-backup-<timestamp>
   ```

   If verification failed or anything looks off, keep the backup and tell the
   user about it.

---

## Handling Common Scenarios

### Single file, single target commit

Simplest case. Blame confirms the target, create one fixup commit. Show a
one-liner and proceed immediately:

```
Fixup: changes in VersionService.ts → [def5678] "feat(backend): add version resolution"
```

### Single file, multiple target commits

The file has hunks targeting different commits. Write separate patches for each
commit's hunks. Be careful with line numbers — apply patches in order from
top of file to bottom to avoid offset issues, or recalculate offsets.

### Multiple files, single target commit

All changes go to one commit. Stage everything, one fixup commit. Easy.

### Multiple files, multiple target commits

The full workflow. Group by target commit, create separate patches, multiple
fixup commits, single autosquash rebase at the end.

### Changes that should go to HEAD

If some hunks target the most recent commit, use `git commit --amend` for those
instead of the fixup+rebase flow. Or, if other hunks need fixup+rebase anyway,
just treat HEAD the same as any other commit (fixup works on HEAD too).

### New files

New files can't be blamed. Use commit context:
- Which commit added the directory or related files?
- Which commit's scope matches?
- Ask the user if unclear.

For the patch, new files need the special `/dev/null` diff header:
```
diff --git a/path/to/new-file.ts b/path/to/new-file.ts
new file mode 100644
--- /dev/null
+++ b/path/to/new-file.ts
@@ -0,0 +1,N @@
+line 1
+line 2
...
```

### Deleted files

Similar to new files — use commit context. The diff header uses `/dev/null` for
the destination.
