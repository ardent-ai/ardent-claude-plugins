---
name: work
description: Execute work plans efficiently while maintaining quality and finishing features
argument-hint: "[plan file path]"
---

# Work

Execute a work plan efficiently while maintaining quality and finishing features.

## Input Document

<input_document> #$ARGUMENTS </input_document>

**If empty:** Check for plans in the agent workspace:
```bash
find .untracked -name "plan.md" -maxdepth 3 2>/dev/null | head -10
```
Ask the user which plan to execute.

## Phase 1: Quick Start

1. **Read Plan and Clarify**
   - Read the work document completely
   - Review any references or links provided
   - If anything is unclear or ambiguous, ask clarifying questions now
   - Get user approval to proceed

2. **Setup Environment**

   Check the current branch:
   ```bash
   current_branch=$(git branch --show-current)
   default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
   if [ -z "$default_branch" ]; then
     default_branch=$(git rev-parse --verify origin/main >/dev/null 2>&1 && echo "main" || echo "master")
   fi
   ```

   **If already on a feature branch** (not default):
   Ask: "Continue on `[current_branch]`, or create a new branch?"

   **If on the default branch:**
   Use **AskUserQuestion tool**:
   - **New branch** — `git pull origin [default] && git checkout -b feat/branch-name`
   - **Worktree** — Use git-worktree skill for isolated parallel work
   - **Stay on default** — Requires explicit confirmation

3. **Create Task List**
   - Use TaskCreate to break plan into actionable tasks
   - Include dependencies between tasks
   - Prioritize based on what needs to be done first

## Phase 2: Execute

1. **Task Execution Loop**

   For each task in priority order:
   - Mark task as in_progress
   - Read any referenced files from the plan
   - Look for similar patterns in codebase
   - Implement following existing conventions
   - Write tests for new functionality
   - **System-Wide Test Check** — Before running tests, walk through these 5 questions. Skip for leaf-node changes with no callbacks, no state persistence, no parallel interfaces.

     | Question | What to do |
     |----------|------------|
     | **What fires when this runs?** IPC handlers, event emitters, Zustand subscriptions, React effects — trace two levels out. | Read actual code for event listeners on models/stores you touch, IPC handlers in the chain, `useEffect` dependencies. |
     | **Do my tests exercise the real chain?** If every dependency is mocked, the test proves logic in isolation only. | Write at least one integration test that uses real objects through the full IPC/store/component chain. No mocks for layers that interact. |
     | **Can failure leave orphaned state?** If code persists state (DB row, store update, file) before calling an async operation, what happens on failure? | Trace the failure path. If state is created before the risky call, test that failure cleans up or retry is idempotent. |
     | **What other interfaces expose this?** Multiple entry points — main process API, renderer IPC, direct function calls. | Grep for the method/behavior in related modules. If parity is needed, add it now. |
     | **Do error strategies align across layers?** Retry logic + error boundaries + IPC error handling — do they conflict? | List error types at each layer. Verify catch blocks match what lower layers actually throw. |

   - Run tests after changes
   - Mark task as completed — in the TaskUpdate, include a one-line attestation: what changed and what was verified (e.g., "Added retry logic to McpServerService.connect(), tested with mock timeout")
   - Check off the corresponding item in the plan file (`- [ ]` → `- [x]`)
   - Evaluate for incremental commit (see below)

2. **Incremental Commits**

   | Commit when... | Don't commit when... |
   |----------------|---------------------|
   | Logical unit complete | Small part of a larger unit |
   | Tests pass + meaningful progress | Tests failing |
   | About to switch contexts | Purely scaffolding with no behavior |
   | About to attempt risky changes | Would need a "WIP" message |

   Commit workflow:
   ```bash
   git add <files related to this logical unit>
   git commit -m "feat(scope): description of this unit"
   ```

3. **Follow Existing Patterns**
   - Read referenced similar code first
   - Match naming conventions exactly
   - Reuse existing components
   - Follow CLAUDE.md standards

4. **Test Continuously**
   - Run relevant tests after each significant change
   - Fix failures immediately
   - Add tests for new functionality

## Phase 3: Quality Check

1. **Run Core Quality Checks**

   ```bash
   npm run lint
   npm run typecheck
   npm test -- --run
   ```

   Fix all errors before proceeding.

2. **Self-Audit**

   Before simplifying, scan your own changes for these patterns:
   - Did you dismiss any plan items as unnecessary? List them — they're deferred debt, not completed work.
   - Did you take shortcuts anywhere ("this is simpler" without verifying it's equivalent)? Flag them.
   - Are there any TODO/FIXME comments you introduced? They should be tracked tasks, not inline hopes.

   If any deferred items exist, note them in the task list so they're visible.

3. **Simplify**

   Run `/simplify` on all changed files. This cleans up dead code, flattens nesting, inlines trivial helpers, and collapses redundant logic — without changing behavior. (`/simplify` uses `context: fork` so it runs in a fresh context.)

   After simplify, re-run lint + typecheck to confirm nothing broke.

   **IMPORTANT: After simplify completes, you are still in the /work pipeline. Continue to step 4 below. Do not stop.**

4. **Review + Auto-Fix**

   Spawn a general-purpose agent to run the review — this keeps the review in its own context window instead of piling onto the already-full work context:

   ```
   Agent tool:
     subagent_type: "general-purpose"
     model: "sonnet"
     prompt: "Run `/review-custom fix` on the current branch. This reviews the branch and auto-fixes Detail findings by amending them into the correct commits. Design findings are reported but not auto-fixed. Return the review report and list of any Design findings that need human judgment."
   ```

   Wait for the agent to complete. If it reports Design findings or unresolved issues, address them before moving on.

   **IMPORTANT: After review completes, you are still in the /work pipeline. Continue to step 5 below. Do not stop.**

5. **Final Validation**
   - All tasks marked completed
   - All tests pass
   - Lint and typecheck pass
   - Code follows existing patterns

## Key Principles

- **Start fast, execute faster** — Get clarification once, then execute
- **The plan is your guide** — Load references, follow existing patterns
- **Test as you go** — Don't wait until the end
- **Ship complete features** — Don't leave things 80% done
- **Minimal commits, clean history** — Each commit should be a complete, valuable change
