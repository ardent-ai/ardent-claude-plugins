---
name: document-review
description: Structured document review rubric for plans, brainstorms, and design docs
argument-hint: "[fact-check] [path to document]"
context: fork
---

# Document Review

Structured quality check for plans, brainstorms, and design documents. Evaluates against a rubric, auto-fixes minor issues, and flags substantive improvements for approval.

## Modes

- **`/document-review path/to/doc.md`** — Standard rubric review (default)
- **`/document-review fact-check path/to/doc.md`** — Verify factual claims against the codebase

**Argument parsing:** If `$ARGUMENTS` starts with `fact-check`, extract it as the mode and use the rest as the document path. Otherwise, default to standard review mode.

## Input

<document_path> $ARGUMENTS </document_path>

**If empty:** Check for recent documents in the agent workspace:
```bash
find .untracked -name "*.md" -maxdepth 3 2>/dev/null | head -10
```

If no document found, ask the user which document to review.

---

**If fact-check mode**, skip to the Fact-Check section below.

---

## Phase 1: Read and Understand

Read the document completely. Identify:
- Document type (plan, brainstorm, review, solution)
- Current status (draft, active, complete)
- Scope and intent

**Auto fact-check for plans:** If the document type is **plan** (has `type: plan` in frontmatter, or contains implementation phases with file paths and function names), automatically run the Fact-Check phases after the standard rubric review completes. Plans with wrong function names or incorrect behavioral descriptions cause implementation failures — catching these during review is far cheaper than discovering them during `/work`.

Skip auto fact-check for brainstorms, reviews, and solutions — factual precision matters less in exploratory or retrospective documents.

## Phase 2: Rubric Evaluation

Score each dimension **1-5** with specific evidence:

### Clarity (1-5)
- Are decisions stated unambiguously?
- Can a developer act on each section without asking clarifying questions?
- Are technical terms used consistently?
- Red flags: "maybe", "probably", "we could", "TBD", vague references to "the system"

### Completeness (1-5)
- Are all acceptance criteria testable?
- Are edge cases and error scenarios addressed?
- Are dependencies and risks identified?
- For plans: are affected files listed? Are phases incremental?
- Red flags: missing error handling strategy, no mention of existing patterns, gaps in the happy path

### Specificity (1-5)
- Are file paths, function names, and interfaces concrete?
- Are code changes described precisely enough to implement?
- Are alternatives evaluated with real trade-offs (not just "simpler" vs "more complex")?
- Red flags: hand-waving ("update the relevant components"), abstract architecture without grounding in actual code

### YAGNI (1-5, inverted — 5 = lean, 1 = bloated)
- Is every section necessary for the stated goal?
- Are there phases or features that could be deferred?
- Is the scope minimal for the desired outcome?
- Red flags: "future-proofing", config options nobody asked for, abstraction layers for single implementations

## Phase 3: Identify Critical Improvements

From the rubric scores, identify:

1. **Critical** — Issues that would cause implementation to fail or go off-track (score 1-2 on any dimension)
2. **Substantive** — Improvements that meaningfully strengthen the document (score 3 on any dimension)
3. **Minor** — Polish items: typos, formatting, unclear phrasing that doesn't affect meaning

## Phase 4: Apply Fixes

**Minor issues:** Auto-fix directly in the document. No approval needed. Report what was changed.

**Substantive and critical issues:** Present each with:
- The rubric dimension and current score
- The specific problem (quote the relevant section)
- A concrete proposed fix

Use **AskUserQuestion tool** for each substantive/critical issue:
- **Apply fix** — Make the change
- **Skip** — Leave as-is
- **Modify** — Let me adjust the proposed fix

## Phase 5: Summary

```markdown
## Document Review Summary

| Dimension | Score | Notes |
|-----------|-------|-------|
| Clarity | X/5 | ... |
| Completeness | X/5 | ... |
| Specificity | X/5 | ... |
| YAGNI | X/5 | ... |

**Overall:** {SOLID | NEEDS WORK | MAJOR GAPS}

### Changes Applied
- [list of auto-fixed minor issues]
- [list of approved substantive fixes]

### Remaining Issues
- [any skipped substantive/critical issues]
```

## Iteration Guidance

- **First pass:** Full rubric evaluation + fixes
- **Second pass:** Re-score only dimensions that were below 4. Focus on whether fixes landed well.
- **After 2 passes:** Recommend completion unless critical issues remain. Diminishing returns beyond 2 rounds — ship it.

## Guidelines

- Be specific in feedback — quote the problematic text, propose the replacement
- Don't inflate scores. A 3 is fine — it means "adequate but could be better"
- Don't add content the author didn't intend. Improvements should sharpen existing intent, not expand scope.
- Respect the document type: brainstorms should be exploratory (don't penalize open questions), plans should be precise (do penalize vagueness)

---

## Fact-Check Mode

Verify the factual accuracy of a document against the actual codebase. This is not a re-review — it does not second-guess analysis, opinions, or design judgments. It verifies that data presented matches reality, corrects what doesn't, and leaves everything else alone.

### Fact-Check Phase 1: Extract Claims

Read the document. Extract every verifiable factual claim:
- **Quantitative**: line counts, file counts, function counts, module counts, test counts, any numeric metrics
- **Naming**: function names, type names, module names, file paths referenced in the document
- **Behavioral**: descriptions of what code does, how things work, before/after comparisons
- **Structural**: architecture claims, dependency relationships, import chains, module boundaries
- **Temporal**: git history claims, commit attributions, timeline entries

Skip subjective analysis (opinions, design judgments, readability assessments) — these aren't verifiable facts.

### Fact-Check Phase 2: Verify Against Source

For each extracted claim, go to the source:
- Re-read every file referenced in the document — check function signatures, type definitions, behavior descriptions against the actual code
- For claims about git history: re-run git commands (`git diff --stat`, `git log`, `git diff --name-status`, etc.) and compare output against the document's numbers
- For plan docs: verify that files, functions, and types the plan references actually exist and behave as described

Classify each claim:
- **Confirmed**: claim matches the code/output exactly
- **Corrected**: claim was inaccurate — note what was wrong and what the correct value is
- **Unverifiable**: claim can't be checked (e.g., references a file that doesn't exist, or a behavior that requires runtime testing)

### Fact-Check Phase 3: Correct In Place

Edit the document directly using surgical text replacements:
- Fix incorrect numbers, function names, file paths, behavior descriptions
- If a section is fundamentally wrong (not just a detail error), rewrite that section's content while preserving the surrounding structure
- Preserve heading structure, formatting, and document organization

### Fact-Check Phase 4: Summary

Append a `## Verification Summary` section at the end of the document:

```markdown
## Verification Summary

**Verified on:** YYYY-MM-DD
**Claims checked:** {total}
**Confirmed:** {count}
**Corrected:** {count}
**Unverifiable:** {count}

### Corrections Made
- {what was fixed and why, with file:line citations}
```

### Fact-Check Phase 5: Report

Tell the user what was checked, what was corrected, and the document path. If nothing needed correction, say so — the verification still has value as confirmation.
