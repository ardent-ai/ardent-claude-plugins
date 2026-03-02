---
name: plan
description: Transform feature descriptions into well-structured plans
argument-hint: "[feature description or problem]"
---

# Create a Plan

## Feature Description

<feature_description> #$ARGUMENTS </feature_description>

**If empty:** Ask "What would you like to plan?"

Do not proceed until you have a clear feature description.

### Phase 0: Check for Prior Brainstorm

Search for recent brainstorm docs in the agent workspace that match this feature:

```bash
# Search for brainstorm files across all topic folders
find .untracked -name "brainstorm.md" -maxdepth 3 2>/dev/null | head -10
```

**If a relevant brainstorm exists** (matching topic, created within 14 days):
1. Read it and announce: "Found brainstorm from [date]: [topic]. Using as context."
2. Extract key decisions and chosen approach
3. Skip idea refinement — the brainstorm already answered WHAT to build

**If no brainstorm found**, run idea refinement:
- Ask questions one at a time using **AskUserQuestion tool**
- Prefer multiple choice when natural options exist
- Focus on: purpose, constraints, success criteria
- Note user's familiarity level and topic risk
- Continue until clear OR user says "proceed"

### Phase 1: Local Research (Parallel)

Launch in parallel:

1. **Codebase exploration** — Spawn a Task with `subagent_type: "Explore"` and `model: "haiku"`: "Find existing patterns, conventions, and similar implementations related to: {feature_description}. Check CLAUDE.md files for relevant guidance."

2. **Workspace learnings** — Search the agent workspace solutions directory for relevant past learnings:
   ```
   Grep .untracked/solutions/ for keywords matching the feature domain
   ```

Consolidate findings: relevant file paths, conventions, institutional learnings.

### Phase 1.5: Research Decision

Based on signals from Phase 0 and findings from Phase 1:

- **High-risk topics** (security, payments, external APIs) → always research externally
- **Strong local context** (codebase has good patterns, user knows what they want) → skip external research
- **Uncertainty or unfamiliar territory** → research

Announce the decision briefly and proceed.

### Phase 1.5b: External Research (Conditional)

Only run if Phase 1.5 indicates external research is valuable.

Launch in parallel:

- Spawn a Task with `subagent_type: "Explore"` and `model: "haiku"`: "Research best practices and real-world patterns for: {feature_description}"
- WebSearch for recent (2024-2026) documentation and approaches

### Phase 2: High-Level Design

Before detailing code changes, produce a lightweight design and validate it. This catches wrong-layer decisions, missed unification opportunities, and overly complex approaches before investing in file-level planning.

**Skip this phase for Minimal plans** (simple bugs, small improvements with obvious implementation).

Run `/design-review` with the feature description and research context from Phase 1 as input. Design-review will explore multiple structurally different approaches, synthesize the best design, and present a clear recommendation.

**Loop on design iteration until the user approves.** Only then proceed to Phase 3.

### Phase 3: Plan Structure

**Title & Categorization:**
- Draft a clear, searchable title (e.g., `feat: Add user authentication`, `fix: Cart total calculation`)
- Determine type: enhancement, bug, refactor
- Derive `{topic}` slug from the title or branch name (e.g., `user-auth`, `cart-total-fix`)

**Choose detail level based on complexity:**

#### Minimal — Simple bugs, small improvements, clear features

```markdown
# [Title]

[Brief problem/feature description]

## Acceptance Criteria

- [ ] Core requirement 1
- [ ] Core requirement 2

## Context

[Critical information]

## References

- Related: [links]
```

#### Standard — Most features, complex bugs

Everything from Minimal plus: overview, problem statement, proposed solution, technical considerations, success metrics, dependencies & risks.

Include a **System-Wide Impact** section:

```markdown
## System-Wide Impact

- **Interaction graph**: What IPC handlers, event emitters, store subscriptions, or React effects fire when this runs?
- **Error propagation**: How do errors flow across main/renderer/IPC layers? Do retry strategies align?
- **State lifecycle risks**: Can partial failure leave orphaned DB rows, stale store state, or inconsistent cache?
- **API surface parity**: What other interfaces expose similar functionality and need the same change?
- **Integration test scenarios**: Cross-layer scenarios that unit tests won't catch
```

#### Comprehensive — Major features, architectural changes

Everything from Standard plus: implementation phases with tasks and success criteria, alternative approaches considered, risk analysis, future considerations.

Expand the **System-Wide Impact** section into subsections with guidance prose:

```markdown
## System-Wide Impact

### Interaction Graph
What IPC handlers, event emitters, store subscriptions, or React effects fire when this runs? Trace at least two levels out from the primary change. Identify any implicit coupling — stores that subscribe to changes, effects that re-trigger, IPC round-trips that cascade.

### Error Propagation
How do errors flow across main/renderer/IPC layers? Map the error types at each boundary. Verify that retry logic, error boundaries, and IPC error handling don't conflict. If one layer retries and another layer also retries, you get exponential attempts.

### State Lifecycle Risks
Can partial failure leave orphaned DB rows, stale store state, or inconsistent cache? If code persists state before calling an async operation, what happens on failure? Identify whether cleanup is needed and whether operations are idempotent.

### API Surface Parity
What other interfaces expose similar functionality and need the same change? Check main process APIs, renderer IPC handlers, and direct function calls. If multiple entry points exist, they all need consistent behavior.

### Integration Test Scenarios
Cross-layer scenarios that unit tests won't catch. Identify the critical paths through the full stack — IPC → main process → DB → response → renderer state update. These are the scenarios that need integration coverage.
```

### Phase 3.5: Verification Checkpoint

Before writing the plan, produce a structured fact sheet of every claim you will include:
- Every file path, function name, type name, and module name you will reference — cite the source (`file:line` where you read it)
- Every behavioral description of current code — verify it matches what the code actually does
- Every quantitative figure (line counts, file counts, test counts) — cite the command or file that produced it
- If something cannot be verified against the codebase, mark it as **uncertain** rather than stating it as fact

This fact sheet is your source of truth during plan writing — do not deviate from it. Plans that reference functions that don't exist or describe behavior that doesn't match the code cause implementation failures downstream.

### Phase 4: Write the Plan

Detail the specific code changes **based on the approved design from Phase 2**. Describe changes concisely, with minimal surrounding prose. Design changes so they can be implemented incrementally — generally two or three phases that logically go together and stack on each other.

Any new or changed interfaces should be well-typed, self-documenting, and self-consistent with surrounding code. Follow existing naming conventions.

In each phase, describe specific unit tests for complex logic, grouped with the relevant phase.

Add a section at the top of each phase listing affected files and a concise summary of changes per file.

Add a task checklist at the top organized by phase with checkboxes (`- [ ]`) that can be marked complete during implementation.

**Prioritize tasks strategically:**
- Cluster related changes that share context (same file, same concept) so they can be implemented in one pass
- Front-load tasks that unblock the most downstream work
- Defer low-value tasks (cosmetic, nice-to-have) to the end where they can be cut if scope tightens

Flag open questions clearly at the TOP of the plan.

**Derive `{area}`** from the feature domain (see CLAUDE.md for area mapping).

**Output path:**

```
.untracked/{topic}/plan.md
```

Create the directory if it doesn't exist. Before creating a new topic folder, check for existing folders with matching prefixes and reuse them. If a `plan.md` already exists, overwrite it.

### Phase 5: Post-Generation

Use **AskUserQuestion tool**:

**Question:** "Plan ready at `{path}`. What next?"

**Options:**
1. **Run /design-review** — Validate the high-level design with rethink check before building
2. **Review the plan** — Critique the technical approach (code-level review)
3. **Run document review** — Structured quality check via rubric (lighter than parallel review). Auto-runs fact-check for plans.
4. **Visual plan review** — Generate an HTML page showing current vs. planned architecture, change-by-change breakdown, ripple analysis, and risk assessment. Best for standard/comprehensive plans.
5. **Run /deepen-plan** — Enhance with parallel research agents
6. **Start /work** — Begin implementing this plan
7. **Create Linear issue** — Create from plan content
8. **Simplify** — Reduce detail level

#### Run document review

Invoke the `/document-review` skill on the plan document. This runs a structured rubric (Clarity, Completeness, Specificity, YAGNI) and automatically fact-checks the plan against the codebase (verifying function names, file paths, and behavioral descriptions). Auto-fixes minor issues and flags substantive improvements for approval.

After the review completes, loop back to the options menu.

#### Visual plan review

Invoke the `/plan-review` prompt from the visual-explainer skill, passing the plan file path. This generates a self-contained HTML page with current vs. planned architecture diagrams (Mermaid), change-by-change breakdown with side-by-side panels, dependency/ripple analysis, risk assessment, and Good/Bad/Ugly review. Opens in browser.

Best for standard and comprehensive plans where visualizing the architectural delta and blast radius is worth the extra time. Skip for minimal plans (simple bugs, small fixes).

After the page opens, loop back to the options menu.

#### Review the plan

Spawn 3 agents in parallel via Task tool in a SINGLE message — each with `subagent_type: "general-purpose"`, `model: "sonnet"`, and `run_in_background: true`. Pass each the full plan content and the project's AGENTS.md.

| Agent | Focus | Key questions |
|-------|-------|---------------|
| Simplicity | Over-engineering, YAGNI | Is there a simpler approach? Are any phases unnecessary? Could two phases collapse into one? |
| Architecture | Boundaries, coupling, patterns | Does this fit the existing architecture? Any new coupling or boundary violations? Are the right packages touched? |
| Design | Data flow, API shape, naming | Are the proposed interfaces clean? Does the data flow make sense? Any naming inconsistencies with existing code? |

After all 3 report back, synthesize into a short critique:

```markdown
## Plan Review

**Verdict:** {SOLID | MINOR CONCERNS | RETHINK NEEDED}

### Findings
- {finding with rationale}

### Suggestions
- {concrete improvement}
```

Present the critique, then loop back to the options menu so the user can revise, deepen, or proceed to /work.

Loop back to options after Simplify or Review until user selects work or another exit.

NEVER CODE! Just research and write the plan.
