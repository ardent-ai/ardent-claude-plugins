---
name: shaping
description: Shape Up methodology for features with unclear UX/product decisions. Explores requirements and shapes through fit checks, breadboarding, and spike-driven investigation before planning. Heavier-weight alternative to /brainstorm for ambiguous features. Triggers on "shape", "shaping", "shape up", or /shaping.
---

# Shaping

Shape Up methodology for features where UX and product decisions are unclear. Produces requirements (R), mutually exclusive shapes (S), fit checks (R x S), and slices ready for implementation.

## Input

<shaping_input> $ARGUMENTS </shaping_input>

**If empty:** Ask "What feature would you like to shape?"

Two entry points:
- **Start from R** (requirements) — you have a problem but no solutions yet
- **Start from S** (shapes) — you have solution ideas but haven't validated them against requirements

If the input describes a problem or goal, start from R. If it describes solution ideas or approaches, start from S. If ambiguous, ask.

## Phase 1: Requirements (R)

### 1.1 Gather Requirements

Use **AskUserQuestion tool** to explore the problem space one question at a time. Build the requirements list incrementally.

Each requirement gets:
- **ID**: R0, R1, R2...
- **Description**: What must be true
- **Status**: One of:
  - `Core` — the fundamental goal; without this, nothing else matters
  - `Must` — non-negotiable for shipping
  - `Nice` — valuable but deferrable
  - `Undecided` — not yet categorized (resolve before Phase 3)
  - `Out` — explicitly excluded from scope

```markdown
### Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| R0 | [core goal] | Core |
| R1 | [must-have] | Must |
| R2 | [nice-to-have] | Nice |
```

### 1.2 Flag Unknowns

Any requirement where the mechanism is described but not concretely understood is a **flagged unknown**. Mark these with a `?` suffix (e.g., `R3?`). Unknowns must be resolved via spikes before shaping is complete.

**Exit condition:** At least R0 (Core) is defined and the user confirms the requirements list.

## Phase 2: Shapes (S)

### 2.1 Explore Shapes

Generate **2-3 mutually exclusive shapes** — genuinely different approaches to satisfying the requirements. Each shape is a complete, self-contained approach.

Each shape gets:
- **ID**: A, B, C...
- **Core idea**: One sentence distinguishing this shape
- **Components**: Named parts of the shape (C1, C2, C3...)
- **Alternatives within components**: When a component has multiple valid implementations, note them (C3-A, C3-B...)

```markdown
### Shape A: [name]

**Core idea:** [one sentence]

| Component | Description |
|-----------|-------------|
| C1 | [what it does] |
| C2 | [what it does] |
| C3-A | [alternative implementation] |
| C3-B | [alternative implementation] |
```

### 2.2 Codebase Context

Spawn a Task with `subagent_type: "Explore"` and `model: "haiku"`: "Find existing patterns, abstractions, and implementations related to: {shapes summary}. Focus on what already exists that shapes could reuse or must work with."

## Phase 3: Fit Check (R x S)

Render a binary pass/fail matrix of every requirement against every shape. No hand-waving — if a shape can't concretely satisfy a requirement, it fails.

```markdown
### Fit Check

| Req | Requirement | Status | A | B | C |
|-----|-------------|--------|---|---|---|
| R0 | [core goal] | Core | pass | pass | pass |
| R1 | [must-have] | Must | pass | fail | pass |
| R2 | [nice-to-have] | Nice | fail | pass | pass |

Notes:
- A fails R2: [concrete reason]
- B fails R1: [concrete reason]
```

Rules:
- If all shapes pass all requirements, there's a missing requirement — articulate what makes one shape feel better than another as a new R
- Any `Undecided` requirements must be resolved before proceeding
- Flagged unknowns (`R3?`) that affect the fit check must be investigated via spikes

Present the matrix to the user and use **AskUserQuestion tool** to select a shape or request modifications.

## Phase 4: Spikes (if needed)

For each flagged unknown that affects the chosen shape:

1. Define the spike: what specific question needs answering?
2. Time-box: what's the minimum investigation to answer it?
3. Execute: research, prototype, or explore
4. Report: concrete answer that resolves the unknown

Remove the `?` suffix from resolved requirements. If a spike reveals that a requirement is impossible, update the fit check and potentially re-select shapes.

## Phase 5: Slicing

Break the chosen shape into vertical slices — demo-able increments that each deliver user-visible value.

For each slice:
- What the user can do after this slice ships
- Which components (C1, C2...) are involved
- Dependencies on other slices

Order slices by dependency, then by value. The first slice should be the smallest thing that proves the core idea works.

If the shape is complex enough to warrant detailed wiring, invoke `/breadboarding` on the chosen shape before slicing.

## Phase 6: Capture

**Derive `{topic}`** from the feature being shaped — a short slug.

**Output path:**

```
.untracked/{topic}/shaping.md
```

Create the directory if it doesn't exist. Before creating a new topic folder, check for existing folders with matching prefixes and reuse them. If a `shaping.md` already exists, overwrite it.

**Document structure:**
- Requirements (full R table)
- Shapes Considered (brief summary of each)
- Fit Check (the matrix)
- Chosen Shape (detailed components)
- Spikes & Findings (if any)
- Slices (ordered list)
- Open Questions (if any remain)

## Phase 7: Handoff

Use **AskUserQuestion tool**:

**Question:** "Shaping captured. What next?"

**Options:**
1. **Proceed to /plan-ardent** — will auto-detect this shaping doc
2. **Run /breadboarding** — map the chosen shape into affordances and wiring
3. **Run document review** — structured quality check
4. **Refine further** — continue shaping
5. **Done for now** — return later

## Guidelines

- Shapes must be mutually exclusive — not variations of the same idea
- Fit checks are binary: pass or fail. No "partial" or "maybe"
- Flagged unknowns block completion — resolve them or descope the requirement
- Stay focused on WHAT and WHY, not HOW — implementation details belong in the plan
- Apply YAGNI — the simplest shape that passes all Must requirements wins
- This is heavier than `/brainstorm` — use it when UX/product decisions are genuinely unclear

NEVER CODE! Shape the problem space, then hand off to planning.
