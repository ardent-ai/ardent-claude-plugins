---
name: design-review
description: Validate the high-level design of an existing plan or in-progress feature before building
argument-hint: "[plan file path, topic, or feature description]"
---

# Design Review

Explore multiple structurally different approaches for a feature, synthesize the best design, and present a clear recommendation. Use standalone on existing plans or as the design phase during `/plan-custom`.

## Input

<design_input> $ARGUMENTS </design_input>

### Resolve the input

- **If a file path** — read the plan directly
- **If a topic/keyword** — search `.untracked/` for matching plan files, pick the best match and confirm with the user
- **If a feature description** (called from `/plan-custom`) — use the feature description and research context already gathered
- **If empty** — list plans from the agent workspace and ask the user to pick one

## Step 1: Gather Context

**If reviewing an existing plan** (standalone invocation):

Launch in parallel (SINGLE message, both with `run_in_background: true`):
1. **Codebase exploration** — Task with `subagent_type: "Explore"`, `model: "haiku"`: "Find existing patterns, conventions, and current implementations related to: {plan summary}. Focus on the packages and files the plan touches. Map the current data flow and abstractions in the affected area."
2. **Workspace learnings** — Grep `.untracked/solutions/` for keywords matching the plan's domain.

Consolidate: relevant file paths, existing abstractions, current data flow, institutional learnings.

**If called from `/plan-custom`** — use the research context already gathered in Phase 1. Don't re-run research.

## Step 2: Understand Current State

**If reviewing an existing plan**, extract the implicit design from the proposed changes:

1. **Core idea** — What's the plan's fundamental approach in one sentence?
2. **Key Abstractions** — What types/interfaces/concepts does it introduce, change, or remove?
3. **Data Flow** — Trace the path with package/file names.
4. **Layer Responsibilities** — Which package owns what concern? Right layer?
5. **What Gets Simpler** — What existing code becomes unnecessary? If nothing, flag it.

**If called from `/plan-custom`** — there's no plan yet. Use the feature description and codebase context to understand the problem space. The first approach you generate in Step 3 can be the "obvious" solution.

## Step 3: Explore Approaches

Generate **2-3 structurally different approaches** — not variations of the same idea, but genuinely different ways to solve the problem. Each should differ in at least one of: where data lives, what abstractions exist, how components communicate, or what gets eliminated.

If reviewing an existing plan, one approach is the plan's current design. Generate 1-2 alternatives that differ structurally.

For each approach, sketch internally (a few bullets each):
1. **Core idea** — The one-sentence insight that distinguishes this approach
2. **Key Abstractions** — What new types/interfaces/concepts? What existing ones change shape or get removed?
3. **Data Flow** — Where does data originate → how does it transform → where is it consumed? Use package/file names.
4. **Trade-offs** — What's better about this approach? What's worse or harder?

Tactics for finding genuinely different approaches:
- **Invert the direction**: if approach A pushes data from producer to consumer, consider one where the consumer pulls/resolves on demand
- **Change what's stored vs computed**: if approach A persists something, consider one that derives it at read time from existing data
- **Move the boundary**: if approach A adds logic to layer X, consider one where a different layer owns the concern
- **Eliminate the problem**: consider whether a simpler version of the feature avoids the design problem entirely

## Step 4: Synthesize and Decide

This is where you do the hard thinking. Don't just pick from the list — actively look for a better option:

1. **Compare** the approaches: complexity, what gets simpler, layer fit, fragility/coupling
2. **Cross-pollinate** — can the data flow from one approach + the abstraction boundaries from another yield something better than any individual option?
3. **Synthesize** — if a hybrid or new approach emerges that's stronger, develop that as the recommendation. The final design doesn't have to be one of the original approaches.

Apply the rethink check to your chosen design:
- "If this requirement had existed from day one, would we structure it this way?"
- "Are there parallel systems that could be unified instead of adding another?"
- "Is anything being stored or computed in the wrong layer?"
- "Does data travel through unnecessary hops or intermediaries?"
- "Could a simpler approach achieve the same goal?"

For each question, give a concrete answer referencing specifics — not a generic "looks fine." If the rethink check reveals a weakness, iterate on the design until it's solid. Don't present a design you have doubts about.

#### Naming Test

For every new abstraction, function, or component in the recommended design, apply this test:

1. **Who is the caller?**
2. **What is the step-level effect?** (not the downstream chain — just what this step does)
3. **Can you name it with one idiomatic verb?**

Signals:
- One verb covers all code paths — boundary is correct
- Need "or" to connect two verbs — likely two things bundled, should split
- Name matches a downstream effect, not this step — naming the chain, not the step

If naming resistance is found, flag it in the recommendation as a design smell: the abstraction boundary is likely wrong and should be revisited before implementation.

## Step 5: Present Recommendation

Lead with the answer, not a menu. Output:

```markdown
## Recommended Design

### Core Idea
{One sentence — the key insight driving this design}

### Design
- **Abstractions**: {what's introduced, changed, removed}
- **Data Flow**: {origin → transformation → consumption, with file/package names}
- **Layer Responsibilities**: {which package owns what}
- **What Gets Simpler**: {what existing code is eliminated or simplified}

### Why This Over the Alternatives

**Approach X (rejected):** {core idea} — {why it's worse: e.g., "stores frontend concern in data layer", "adds a parallel system instead of unifying"}

**Approach Y (rejected):** {core idea} — {why it's worse}

{If the recommendation is a hybrid, note which elements came from where}

### Rethink Check
{Concrete answers to each question}
```

## Step 6: Iterate

Present the recommendation to the user with **AskUserQuestion**:

**Question:** "Here's my recommended design. Good to proceed?"

**Options:**
1. **Looks good, proceed** — Accept the design
2. **I have concerns** — Discuss specific aspects of the recommendation
3. **Run /rethink** — Full rethink analysis for a deeper redesign
4. **Explore more** — Alternatives feel too similar, look harder for different options

### If reviewing an existing plan and the recommendation differs

1. Read the current plan file
2. Restructure the plan around the recommended design — update data flow, affected files, and task list
3. Re-run Steps 2-5 on the revised plan to confirm improvements
4. Loop back to Step 6

NEVER CODE. This is a design thinking tool — explore, synthesize, recommend, iterate. Implementation happens in /work.
