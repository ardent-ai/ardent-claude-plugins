---
name: deepen-plan
description: Enhance a plan with parallel research agents for depth, best practices, and implementation details
argument-hint: "[path to plan file]"
---

# Deepen Plan

Takes an existing plan (from `/plan-custom`) and enhances each section with parallel research. Each major element gets a dedicated research agent to find best practices, performance considerations, edge cases, and real-world examples.

## Plan File

<plan_path> #$ARGUMENTS </plan_path>

**If empty:**
1. Check for recent plans:
   ```bash
   find .untracked -name "plan.md" -maxdepth 3 2>/dev/null | head -10
   ```
2. Ask the user which plan to deepen.

Do not proceed until you have a valid plan file path.

## Execution

### 1. Parse Plan Structure

Read the plan file and extract:
- Overview/Problem Statement
- Proposed Solution sections
- Technical Approach/Architecture
- Implementation phases/steps
- Technologies and frameworks mentioned
- Domain areas (data models, APIs, UI, security, performance)

Create a section manifest:
```
Section 1: [Title] - [What to research]
Section 2: [Title] - [What to research]
...
```

### 2. Check Institutional Knowledge

Search the agent workspace solutions directory for relevant past learnings:

```bash
# Search for keyword matches in solutions
Grep: pattern="relevant keywords" path=".untracked/solutions/"
```

Extract any applicable learnings, gotchas, or patterns that apply to this plan.

### 3. Launch Parallel Research

For each major section in the plan, spawn a dedicated research agent. Use the Task tool with `subagent_type: "Explore"`, `model: "haiku"`, and `run_in_background: true`.

Prompt each agent: "Research best practices, patterns, and real-world examples for: {section topic}. Find: industry standards, performance considerations, common pitfalls, documentation and tutorials. Return concrete, actionable recommendations."

Also spawn in the SAME message:
- **WebSearch agent** — Task with `subagent_type: "general-purpose"`, `model: "haiku"`, `run_in_background: true`: "Search the web for current (2024-2026) best practices on: {key topics}"
- **Codebase patterns agent** — Task with `subagent_type: "Explore"`, `model: "haiku"`, `run_in_background: true`: "Find existing implementations of similar patterns in this codebase"

Launch ALL research agents in a SINGLE message for true parallelism. Wait for all to complete before proceeding to Step 4.

### 4. Synthesize

Collect outputs from all agents. For each agent's findings, extract:
- Concrete recommendations (actionable items)
- Code patterns and examples
- Anti-patterns to avoid
- Performance considerations
- Edge cases discovered
- Documentation links

Deduplicate and prioritize by impact. Flag conflicting advice for human review.

### 4.5. Verification Checkpoint

Before writing enhancements into the plan, verify every factual claim from the research:
- Every file path, function name, type name, and module name referenced in research findings — confirm they exist in the codebase (`file:line`)
- Every behavioral description — verify it matches what the code actually does
- Every best-practice recommendation — confirm it's compatible with the existing codebase patterns and conventions
- If something cannot be verified, mark it as **uncertain** rather than presenting it as fact

This prevents research hallucinations from propagating into the plan. Drop findings that reference nonexistent code or describe behavior that doesn't match reality.

### 5. Enhance Plan Sections

For each section, add research insights below the original content:

```markdown
## [Original Section Title]

[Original content preserved]

### Research Insights

**Best Practices:**
- [Concrete recommendation]

**Performance Considerations:**
- [Optimization opportunity]

**Edge Cases:**
- [Edge case and how to handle it]

**References:**
- [Documentation URL]
```

### 6. Add Enhancement Summary

At the top of the plan, add:

```markdown
## Enhancement Summary

**Deepened on:** [Date]
**Sections enhanced:** [Count]

### Key Improvements
1. [Major improvement]
2. [Major improvement]

### New Considerations Discovered
- [Important finding]
```

### 7. Update Plan File

Write the enhanced plan in place. Update the `status` in frontmatter to `active`.

## Post-Enhancement

Use **AskUserQuestion tool**:

**Question:** "Plan deepened at `{path}`. What next?"

**Options:**
1. **Open in Obsidian** — View the enhanced plan
2. **Start /work** — Begin implementing
3. **Deepen further** — Run another round on specific sections
4. **Revert** — Restore original from git

NEVER CODE! Just research and enhance the plan.
