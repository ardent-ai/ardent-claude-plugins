---
name: brainstorm
description: Explore requirements and approaches through collaborative dialogue before planning
argument-hint: "[feature idea or problem to explore]"
---

# Brainstorm

Brainstorming answers **WHAT** to build through collaborative dialogue. It precedes `/plan-ardent`, which answers **HOW** to build it.

## Feature Description

<feature_description> #$ARGUMENTS </feature_description>

**If empty:** Ask "What would you like to explore?"

Do not proceed until you have a feature description.

### Phase 0: Assess Requirements Clarity

**If requirements are already detailed** (specific acceptance criteria, exact expected behavior, constrained scope):
Use **AskUserQuestion tool**: "Your requirements seem detailed enough to proceed directly to `/plan-ardent`. Should I plan instead, or explore the idea further?"

### Phase 1: Understand the Idea

#### 1.1 Quick Codebase Scan

Spawn a Task with `subagent_type: "Explore"` and `model: "haiku"`: "Find existing patterns, similar features, and CLAUDE.md guidance related to: {feature_description}"

#### 1.2 Collaborative Dialogue

Use **AskUserQuestion tool** to ask questions **one at a time**:

- Prefer multiple choice when natural options exist
- Start broad (purpose, users) then narrow (constraints, edge cases)
- Validate assumptions explicitly
- Ask about success criteria

**Exit condition:** Idea is clear OR user says "proceed"

### Phase 2: Explore Approaches

Propose **2-3 concrete approaches** based on research and conversation.

For each:
- Brief description (2-3 sentences)
- Pros and cons
- When it's best suited

Lead with your recommendation. Apply YAGNI — prefer simpler solutions.

#### 2.1 Fit Check

When requirements have been gathered during Phase 1 dialogue, render a fit check matrix before asking for a preference. Binary pass/fail only — no hand-waving. If an approach can't concretely satisfy a requirement, it's a fail.

```markdown
### Fit Check

| Req | Requirement | Status | A | B | C |
|-----|-------------|--------|---|---|---|
| R0 | Core goal | Core | ... | ... | ... |
| R1 | Must-have X | Must | ... | ... | ... |
| R2 | Nice-to-have Y | Nice | ... | ... | ... |

Notes:
- A fails R2: [concrete reason]
- B fails R1: [concrete reason]
```

Guidance:
- Status values: Core goal, Must-have, Nice-to-have
- If all approaches pass all requirements, there's a missing requirement — articulate what makes one feel better than another as a new R
- Pros/cons stay as supplementary color, but the matrix is the decision tool

Use **AskUserQuestion tool** to ask which approach the user prefers.

### Phase 3: Capture

**Derive `{topic}`** from the feature being explored — a short slug (e.g. `skill-preloading`, `web-search`).

**Output path:**

```
.untracked/{topic}/brainstorm.md
```

Create the directory if it doesn't exist. Before creating a new topic folder, check for existing folders with matching prefixes and reuse them. If a `brainstorm.md` already exists, overwrite it.

**Document structure:**
- What We're Building
- Why This Approach
- Key Decisions (with rationale)
- Open Questions (if any remain)

### Phase 4: Handoff

Use **AskUserQuestion tool**:

**Question:** "Brainstorm captured. What next?"

**Options:**
1. **Proceed to /plan-ardent** — will auto-detect this brainstorm
2. **Run document review** — structured quality check before proceeding
3. **Refine further** — continue exploring
4. **Done for now** — return later

#### Run document review

Invoke the `/document-review` skill on the brainstorm document. This runs a structured rubric (Clarity, Completeness, Specificity, YAGNI) and auto-fixes minor issues while flagging substantive improvements for approval. Recommended before handing off to planning — catches gaps in requirements and vague decisions early.

## Guidelines

- Stay focused on WHAT, not HOW — implementation details belong in the plan
- Ask one question at a time
- Apply YAGNI — prefer simpler approaches
- Keep sections to 200-300 words max

NEVER CODE! Just explore and document decisions.
