---
name: split-commits
description: This skill should be used when splitting a branch's commits into small, atomic commits. It creates a backup branch, squashes all commits, analyzes changes to identify logical groupings, then recreates the branch with clean atomic commits that each pass lint/typecheck/tests. Triggers on "split commits", "atomic commits", "clean up commit history", "reorganize commits", or requests to break down large commits.
---

# Split Commits

## Overview

Transform a messy commit history into clean, atomic commits. This skill creates a safe working branch, squashes all changes, analyzes them to identify logical groupings, and recreates the commit history with small, focused commits that each pass all validation checks.

## Critical Constraints

### No Interactive Git Commands

**NEVER use git commands that require user input or open an editor.** These will hang indefinitely in an automated context.

**Forbidden commands:**
- `git rebase -i` (interactive rebase)
- `git add -i` or `git add -p` (interactive staging)
- `git commit` without `-m` flag (opens editor)
- `git merge` without `--no-edit` when it might prompt
- `git rebase` without `--no-edit` for conflict resolution
- `git cherry-pick` without handling conflicts non-interactively

**Safe alternatives:**
- Instead of `git add -p`: Use the Edit tool to modify files directly, then `git add <file>`
- Instead of `git rebase -i`: Use `git reset --soft` + selective commits
- Instead of interactive conflict resolution: Use `git checkout --ours/--theirs` or edit files directly
- Always use `git commit -m "message"` with the message inline

**If a conflict occurs:**
1. Check conflict status with `git status`
2. Read the conflicted files to understand the conflict
3. Edit files directly to resolve (using Edit tool)
4. Stage resolved files with `git add <file>`
5. Continue with `git rebase --continue` or `git commit`

Never rely on git opening an editor or prompting for input.

## Workflow

### Phase 1: Setup and Safety

**Important: The original branch is NEVER modified.** All work happens on a new working branch. The original branch remains as a backup/reference.

1. **Capture current state**
   ```bash
   # Get current branch name and base branch
   CURRENT_BRANCH=$(git branch --show-current)
   BASE_BRANCH=$(git merge-base HEAD main || git merge-base HEAD master)
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   WORK_BRANCH="${CURRENT_BRANCH}_split_commits_${TIMESTAMP}"
   ```

2. **Create working branch**
   ```bash
   # Create the new working branch from current state (original branch untouched)
   git checkout -b "$WORK_BRANCH"
   ```

3. **Squash all commits into one**
   ```bash
   # Reset to base while keeping all changes staged
   git reset --soft "$BASE_BRANCH"
   git commit -m "WIP: Squashed commits for atomic splitting"
   ```

4. **Create documentation directory**
   - Create a temp directory: `.untracked/split-commits-${TIMESTAMP}/`
   - This will store the commit plan and analysis

### Phase 2: Change Analysis

1. **Generate comprehensive diff**
   ```bash
   git diff "$BASE_BRANCH"...HEAD > .untracked/split-commits-${TIMESTAMP}/full_diff.patch
   git diff --stat "$BASE_BRANCH"...HEAD > .untracked/split-commits-${TIMESTAMP}/diff_stat.txt
   ```

2. **Identify PR-worthy units of work**

   Using the big picture understanding from Part 0 of your dependency analysis, think about what would make sense as standalone PRs:
   - What are the major logical units? (a feature, a layer, a complete refactor)
   - Each unit should tell a coherent story a reviewer could understand
   - How would you split the overall branch description into 2-5 smaller PR descriptions?
   - Small changes (lint fixes, exports, config tweaks) are NOT units - absorb them into related commits

3. **Analyze changes by category**

   Examine the diff to identify logical groupings. Look for:
   - **Schema/type changes**: New types, interfaces, schemas
   - **Infrastructure changes**: Build config, dependencies, tooling
   - **Core feature logic**: Main business logic implementation
   - **API layer**: Routes, controllers, handlers
   - **UI components**: New or modified components
   - **Tests**: Test files and fixtures

   **Choose the right grouping strategy:**

   | Strategy | When to use | Example |
   |----------|-------------|---------|
   | **By feature (vertical)** | Multiple independent features | "Add auth" then "Add billing" |
   | **By layer (horizontal)** | Single feature, clear layers | "Add schemas" then "Add services" then "Add UI" |
   | **Hybrid** | Large feature with some independent parts | "Add core data model" then "Add feature A" then "Add feature B" |

   **Prefer vertical (by feature) when:**
   - The branch has multiple distinct features
   - Layer-based splitting would create many cross-dependencies
   - Each feature can stand alone

   **Do NOT create separate commits for:**
   - Minor lint fixes (absorb into related commit)
   - Small config changes (absorb into the feature they enable)
   - Documentation updates (absorb into the feature they document)
   - Tiny refactors (< 20 lines, absorb into related commit)

4. **Identify file-level splits**

   For files with changes that belong to multiple commits:
   - Note specific line ranges for each logical change
   - Plan the order to apply them (dependencies first)

5. **Build the dependency graph document (REQUIRED)**

   **Before proposing ANY commits, create `DEPENDENCY_ANALYSIS.md` in the temp folder.**

   This is NOT optional. The structured analysis forces thorough understanding.

   ```markdown
   # Dependency Analysis for [branch-name]

   ## Part 0: Big Picture Understanding

   Before analyzing individual files, understand what this branch accomplishes AS A WHOLE.

   **What does this branch do?** (2-3 sentences, as you'd explain to a colleague)
   > Example: "This branch adds skill versioning support. Users can now install specific versions of skills and switch between them. The backend tracks version history and the UI shows a version selector."

   **What are the major components being added/changed?**
   - [Component 1]: [brief description]
   - [Component 2]: [brief description]
   - [Component 3]: [brief description]

   **What's the architectural change?** (if any)
   > Example: "Skills change from single-instance to multi-version. New tables track versions and installations. Frontend stores need to manage version state."

   **What would the PR title/description be for the ENTIRE branch?**
   > This helps frame the scope and guides how to split it into smaller PRs (commits).

   ---

   ## Part 1: File-Level Analysis

   For EACH changed file, document:
   - **Code dependencies**: What it imports from other changed files
   - **Feature/behavior**: What this file DOES (what feature it enables)

   | File | Imports From | Exports Used By | Feature/Behavior |
   |------|--------------|-----------------|------------------|
   | SkillRecord.ts | (none) | SkillService, SkillStore, SkillCard | Defines skill data shape |
   | SkillVersionRecord.ts | (none) | SkillService, SkillStore | Defines version data shape |
   | SkillService.ts | SkillRecord, SkillVersion | LibraryService, CatalogService | Core skill version management logic |
   | getSkill.ts | SkillRecord | - | API: fetch single skill |
   | LibraryService.ts | SkillService | - | Integrates versioning into library |
   | CatalogService.ts | SkillService | - | Integrates versioning into catalog |
   | SkillStore.ts | SkillService (types) | SkillCard | Frontend state for skill versions |
   | SkillCard.tsx | SkillStore, SkillRecord | - | UI: displays skill with version selector |

   ## Part 2: Feature/Behavior Groupings

   Group files by WHAT THEY DO, not just what they import:

   | Feature | Files | Description |
   |---------|-------|-------------|
   | Data model | SkillRecord.ts, SkillVersionRecord.ts | Define the shape of data |
   | Core versioning logic | SkillService.ts | The main business logic |
   | API access | getSkill.ts | External access to skills |
   | Library integration | LibraryService.ts | Makes library version-aware |
   | Catalog integration | CatalogService.ts | Makes catalog version-aware |
   | Frontend | SkillStore.ts, SkillCard.tsx | User-facing version selection |

   This helps identify which files are part of the same "story" even if they don't directly import each other.

   ## Part 3: Code Dependency Matrix

   Does FILE IN ROW depend on FILE IN COLUMN? (Only showing files with dependencies)

   | File | SkillRecord | SkillVersion | SkillService | getSkill | LibraryService | SkillStore |
   |------|-------------|--------------|--------------|----------|----------------|------------|
   | SkillService | YES | YES | - | no | no | no |
   | getSkill | YES | no | no | - | no | no |
   | LibraryService | YES | no | YES | YES* | - | no |
   | CatalogService | YES | no | YES | YES* | no | no |
   | SkillStore | YES | YES | YES | YES* | no | - |
   | SkillCard | YES | no | no | no | no | YES |

   *Calls API endpoint

   ## Part 4: Deriving Commit Groups

   Looking at the matrix, identify clusters of files that:
   - Have no external dependencies (can be first)
   - Depend only on each other (can be grouped)
   - Have clear dependency chains

   Analysis:
   - SkillRecord, SkillVersionRecord: No deps → Foundation, commit together
   - SkillService: Depends only on schemas → Can be next
   - getSkill: Depends only on schemas → Can be parallel with SkillService
   - LibraryService, CatalogService: Depend on SkillService AND getSkill → Must come after both
   - SkillStore: Depends on SkillService AND getSkill → Must come after both
   - SkillCard: Depends on SkillStore → Must come last

   ## Part 5: Proposed Commit Groups

   Combining code dependencies (Part 3) with feature groupings (Part 2):

   | Commit | Files | Why grouped | Feature story |
   |--------|-------|-------------|---------------|
   | 1. schemas | SkillRecord.ts, SkillVersionRecord.ts | No dependencies | "Here's the data model" |
   | 2. core-service | SkillService.ts | Depends only on schemas | "Here's the core logic" |
   | 3. api | getSkill.ts | Depends only on schemas | "Here's how to fetch a skill" |
   | 4. integration | LibraryService.ts, CatalogService.ts | Both need service + api | "Now existing features are version-aware" |
   | 5. frontend | SkillStore.ts, SkillCard.tsx | UI layer | "Here's the user-facing UI" |

   ## Part 6: Validate Order

   Checking each commit can compile given previous commits:
   - After commit 1: SkillRecord, SkillVersionRecord available ✓
   - After commit 2: SkillService can import schemas ✓
   - After commit 3: getSkill can import schemas ✓
   - After commit 4: LibraryService can import SkillService ✓, can call getSkill ✓
   - After commit 5: SkillStore can import all ✓, SkillCard can import SkillStore ✓

   Final order: 1 → 2 → 3 → 4 → 5 ✓
   ```

   **DO NOT proceed to step 6 until this document exists and is complete.**

   **The file-level matrix is the foundation. Commit groups are DERIVED from it, not invented first.**

6. **Create commit plan document**

   Write to `.untracked/split-commits-${TIMESTAMP}/COMMIT_PLAN.md`:

   ```markdown
   # Commit Plan for ${CURRENT_BRANCH}

   Created: ${TIMESTAMP}
   Original branch: ${CURRENT_BRANCH}
   Working branch: ${WORK_BRANCH}
   Base commit: ${BASE_BRANCH}

   **Dependency analysis**: See DEPENDENCY_ANALYSIS.md (created in step 5)

   ## Commit Order Rationale

   Based on the dependency matrix in DEPENDENCY_ANALYSIS.md:
   - Commit 1 has no dependencies → can be first
   - Commit 2 depends on 1 → must come after 1
   - Commit 3 depends on 1 → can be parallel with 2 or after
   - [etc.]

   Chosen order: 1 → 2 → 3 → ...

   ## Planned Commits (in order)

   ### Commit 1: [Short description]
   **Purpose**: [Why this change exists - what PR story does this tell?]
   **Files**:
   - path/to/file1.ts
   - path/to/file2.ts
   **Provides**: [What types/functions/APIs this commit makes available]
   **Requires**: None (or list what this commit imports from earlier commits)
   **Absorbed**: [minor changes included: lint fixes, exports, etc.]
   **Validation**: [ ] lint [ ] typecheck [ ] tests

   ### Commit 2: [Short description]
   ...
   ```

7. **Sanity check the plan**

   Before proceeding, verify:
   - Each commit could reasonably be its own PR to review
   - No commits exist just for tiny fixes or single-line changes
   - Small changes are absorbed into the commits they relate to
   - Related changes are grouped (all schemas together, all frontend together, etc.)

   **CRITICAL: Validate the order by mentally executing each commit:**
   ```
   For commit 1: What files exist after this commit? What can be imported?
   For commit 2: Given commit 1 exists, can commit 2's code compile?
                 Does it import anything not yet committed?
   For commit 3: Given commits 1-2 exist, can commit 3's code compile?
   ... and so on
   ```

   **If ANY commit would fail because it imports/uses something from a LATER commit, the order is wrong. Fix it before presenting to user.**

8. **Decide whether to confirm with the user**

   **Only ask for confirmation when the split is genuinely ambiguous** — i.e., there are multiple reasonable ways to group the changes and the right choice depends on user preference.

   Signs you should ask:
   - Multiple viable grouping strategies (by-feature vs by-layer vs hybrid)
   - Unclear boundaries between logical units
   - Trade-offs the user should weigh (e.g., bigger commits vs more granular history)

   Signs you should just proceed:
   - The grouping falls out naturally from the dependency analysis
   - There's only one sensible way to split
   - The commits are clearly distinct (e.g., separate packages, independent features)

   If you do ask, present concrete options:
   ```
   I see a few ways to split these commits:

   Option A (by layer):
   1. feat(schema): add all new types
   2. feat(backend): add all services
   3. feat(frontend): add all UI

   Option B (by feature):
   1. feat: add skill versioning core
   2. feat: add skill installation flow
   3. feat: add version selection UI

   Which approach do you prefer? [A / B / Other]
   ```

   If the split is obvious, just proceed to Phase 3.

### Phase 3: Atomic Commit Creation

1. **Reset to base for clean slate**
   ```bash
   git reset --hard "$BASE_BRANCH"
   ```

2. **For each planned commit:**

   a. **Apply the specific changes**
      - For full files: `git checkout <squashed-commit> -- path/to/file`
      - For partial files: Edit the file directly using the Edit tool to include only the needed changes

   b. **Stage the changes**
      ```bash
      git add <specific-files>
      ```

   c. **Check for multiple migrations (REQUIRED)**

      If this commit includes multiple migration files, **STOP and merge them first**:
      ```bash
      # Check staged migrations
      git diff --cached --name-only | grep -E "migrations/.*\.sql"
      ```

      If more than one migration file appears:
      1. Combine the SQL into a single migration file with a descriptive name
      2. Delete the extra migration files
      3. Update staged files accordingly

      **One commit = One migration (max).** This is not optional.

   d. **Run tests (REQUIRED before committing)**
      ```bash
      npm test
      ```

      Note: Lint and typecheck are enforced by the pre-commit hook, but tests are not.
      Running tests first ensures the commit will work and helps identify missing dependencies.

      **DO NOT proceed to step (f) until tests pass.**

   e. **If tests fail:**
      - Identify what's missing (likely a dependency from a later commit)
      - Either pull in the minimum required code, or reorder the commit plan
      - Update COMMIT_PLAN.md with the adjustment
      - **Re-run tests after any fix** - loop back to step (d)

   f. **Commit with descriptive message** (only after all checks pass)
      ```bash
      git commit -m "feat: [description of atomic change]"
      ```

   g. **Record success in plan**
      - Update COMMIT_PLAN.md validation checkboxes

3. **Handle complex file splits**

   When a single file has changes for multiple commits:

   a. **Read the full version from squashed commit**
      ```bash
      git show <squashed-sha>:path/to/file.ts
      ```

   b. **Read the base version**
      ```bash
      git show "$BASE_BRANCH":path/to/file.ts
      ```

   c. **Use the Edit tool to apply only the specific changes needed for this commit**
      - Compare the two versions
      - Identify which hunks belong to this commit
      - Apply only those changes to the current file

   d. **Stage and commit**
      ```bash
      git add path/to/file.ts
      git commit -m "feat: [description]"
      ```

### Phase 4: Verification

1. **Verify final state matches original**
   ```bash
   # Compare working tree to original branch
   git diff "$CURRENT_BRANCH" --stat
   git diff "$CURRENT_BRANCH"

   # Should show NO differences
   ```

2. **If differences exist:**
   - Identify missing changes
   - Create additional commit(s) to include them
   - Re-verify

3. **Review commit history**
   ```bash
   git log --oneline "$BASE_BRANCH"..HEAD
   ```

4. **Audit each commit**

   For each commit in the new history:
   ```bash
   git checkout <commit-sha>
   npm test
   git checkout "$WORK_BRANCH"
   ```

   Note: Lint/typecheck are enforced by the pre-commit hook, so if the commits exist, they passed. Tests verify runtime correctness.

5. **Generate final report**

   Append to COMMIT_PLAN.md:
   ```markdown
   ## Final Report

   - Total commits: X
   - All validations passed: Yes/No
   - Final state matches original: Yes/No

   ### Commit Summary
   | # | SHA | Message | Lint | Types | Tests |
   |---|-----|---------|------|-------|-------|
   | 1 | abc123 | feat: add types | ✓ | ✓ | ✓ |
   | 2 | def456 | feat: add logic | ✓ | ✓ | ✓ |
   ...
   ```

### Phase 5: Cleanup

**By default, both branches are kept:**
- `$CURRENT_BRANCH` - Original branch (untouched, serves as backup)
- `$WORK_BRANCH` - New branch with clean atomic commits

1. **Replace the original branch**

   Delete the original and rename the working branch:
   ```bash
   git branch -D "$CURRENT_BRANCH"
   git branch -m "$WORK_BRANCH" "$CURRENT_BRANCH"
   ```

2. **Keep documentation**
   - The `.untracked/split-commits-${TIMESTAMP}/` folder remains for reference
   - Contains the full plan, original diff, and final report

## Commit Grouping Guidelines

### The Core Principle: PR-Worthy Commits

**Each commit should be something you'd be comfortable submitting as its own PR for review.**

Ask yourself: "Could this commit stand alone as a small, focused PR that a reviewer could easily understand and approve?"

- **YES** → It's a good commit boundary
- **NO, it's too small/trivial** → Absorb it into a related commit
- **NO, it's too intertwined with other changes** → Combine with dependent changes

### No Break-Then-Fix Commits

**Every commit must leave the codebase in a working state.** Never create commits like:

```
BAD:
1. feat: add user authentication (has a bug)
2. fix: fix authentication bug
```

Instead, the fix belongs in the original commit:

```
GOOD:
1. feat: add user authentication (complete and working)
```

If you discover a bug while splitting commits, absorb the fix into the commit that introduced the broken code. The commit history should read as if you got it right the first time.

### What Qualifies as a Commit

A commit should represent a **complete, meaningful unit of work**:

- A feature or significant part of a feature
- A complete layer (all schemas, all migrations, all services for a feature)
- A self-contained refactor that improves the codebase
- A bugfix with its test

### What Does NOT Qualify as Its Own Commit

**Absorb these into related commits:**

- Index file exports (goes with the code being exported)
- Lint/format fixes (goes with the code that triggered them)
- Single-line typo fixes (goes with related feature work)
- Minor refactors that support a feature (goes with that feature)
- Test file updates (goes with the code being tested)
- Config tweaks (goes with the feature they enable)

### Migrations: One Commit = One Migration (HARD RULE)

**NEVER commit multiple migration files in the same commit. Always merge them first.**

This is checked in Phase 3 step (c) before every commit. If you have:
```
migrations/
  001_create_skill_versions.sql
  002_create_skill_installs.sql
  003_add_skill_selections.sql
```

You MUST combine them into one:
```
migrations/
  001_add_skill_versioning.sql  (contains all three tables)
```

**Why this matters:**
- Migrations run in sequence - multiple files in one commit is confusing
- One commit should represent one logical change, including its migration
- Keeps the migration history clean and auditable

### Example: Thinking in PR-Worthy Units

**BAD - Over-split (each would be a trivial/confusing PR):**
```
1. feat: add SkillVersion schema
2. feat: add SkillInstall schema
3. chore: update index exports
4. feat: add skill_versions migration
5. feat: add skill_installs migration
6. refactor: minor button tweak
7. chore: fix lint error
```

**GOOD - PR-worthy units:**
```
1. feat(schema): add skill versioning data model
   - All related schemas together
   - Index exports included
   - "Here's the new data model for skill versioning"

2. feat(backend): add skill versioning services
   - Services + interfaces + tests
   - "Here's the backend implementation"

3. feat(frontend): add skill version selection UI
   - Components + stores + screens
   - Button tweak absorbed if related
   - "Here's the user-facing feature"
```

### Grouping Heuristics

- **Same layer, same feature** → Same commit (all schemas together, all migrations together)
- **Tightly coupled code** → Same commit (if A can't work without B, they go together)
- **Tests** → Always with the code they test
- **Small fixes** → Absorb into the most related commit

### When in Doubt, Combine

A slightly larger commit that tells a coherent story is better than multiple tiny commits that are confusing to review separately.

## Troubleshooting

### Finding Coupling Does NOT Mean "Combine Everything"

**This is the most common mistake.** When you discover that schemas and services are coupled, the WRONG response is:

❌ "Schema and services are coupled → combine ALL backend changes into one commit"

The RIGHT response is to be SURGICAL:

✅ "Schema field X is used by Service Y → those specific pieces go together"

**Example of bad reasoning:**
```
"The schema changes break existing code because the tools field was removed.
The schema and service changes are tightly coupled - they can't be split.
Let me combine all backend changes into one commit."
```

**Example of good reasoning:**
```
"The tools field removal in SkillRecord breaks SkillService.getTools().
ONLY those two changes are coupled:
- SkillRecord.tools removal
- SkillService.getTools() removal/update

The OTHER schema changes (SkillVersion, SkillInstall) and OTHER service
methods are NOT coupled to this. They can still be separate commits."
```

**Ask these questions:**
1. What SPECIFIC change is breaking what SPECIFIC code?
2. Is that the ONLY coupling, or are there others?
3. Can I combine JUST those coupled pieces and keep the rest separate?

**The goal is the MINIMUM viable grouping, not the MAXIMUM convenient grouping.**

### Validation Fails Mid-Process

**DO NOT immediately bundle everything together.** Take time to understand the dependency and find the minimal fix.

When a commit fails validation:

1. **Identify exactly what's missing**
   ```
   Error: Cannot find name 'SkillVersion'
   ```
   → The type `SkillVersion` is defined in a later commit

2. **Understand the dependency relationship**
   - Is it a type/interface that this code needs?
   - Is it a function being called?
   - Is it an import that's missing?

3. **Choose the RIGHT fix (in order of preference):**

   **Option A: Reorder commits** (best if possible)
   - If Commit 3 depends on something from Commit 5, maybe Commit 5 should come first
   - Ask: "Does the new order still make logical sense?"
   - If yes, reorder and continue

   **Option B: Pull in ONLY the missing piece** (surgical fix)
   - If Commit 2 needs a type from Commit 4, pull JUST that type into Commit 2
   - Don't pull the entire file or all the types - just what's needed
   - Example: Add only the `SkillVersion` interface, not the entire schema file

   **Option C: Move the dependent code to a later commit**
   - If a small piece of Commit 2 depends on Commit 4, move that piece to Commit 4
   - Keep the rest of Commit 2 intact

   **Option D: Merge two specific commits** (targeted merge)
   - If Commits 2 and 4 are tightly coupled, merge JUST those two
   - Don't merge everything - keep other commits separate

   **Option E: Rethink the split** (not a last resort - often the RIGHT answer)
   - **Dependency issues are a signal, not just a problem to hack around**
   - If you're constantly pulling pieces from other commits, the boundaries are wrong
   - Step back and ask: "What grouping would have NO cross-dependencies?"
   - Often the answer is grouping by feature slice (vertical) instead of by layer (horizontal)

   Example of bad vs good grouping:
   ```
   BAD (causes dependency issues):
   1. All types/schemas
   2. All services
   3. All UI components
   → Services need types, UI needs services = constant dependency problems

   GOOD (self-contained):
   1. Feature A: types + service + UI for feature A
   2. Feature B: types + service + UI for feature B
   → Each commit is complete and independent
   ```

4. **NEVER do this:**
   - ❌ "This is too hard, let me just put everything in one commit"
   - ❌ Merge 5 commits into 2 because one had a dependency issue
   - ❌ Give up on the split entirely

### Dependency Analysis Checklist

Before panicking, ask:

1. **What exactly is missing?** (specific type, function, constant)
2. **Where is it defined?** (which planned commit)
3. **Can that definition move earlier?** (reorder)
4. **Can just that definition be pulled in?** (surgical)
5. **Does this reveal a better grouping?** (rethink)

### File Has Interleaved Changes

When a file has changes that logically belong to different commits but are interleaved:
1. Determine if they can be separated
2. If not, assign entire file to the commit with the primary change
3. Document in COMMIT_PLAN.md why separation wasn't possible

### Final State Doesn't Match

If the final state differs from the original:
1. Run `git diff "$CURRENT_BRANCH"` to see what's different
2. Create a "fixup" commit with the missing changes
3. Consider if the original had unintended changes that should be excluded
