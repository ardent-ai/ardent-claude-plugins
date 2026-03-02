---
name: rethink
description: Redesign a system area as if a proposed change had been a foundational assumption from the start. Use when adding a feature, fixing a pattern, or refactoring — to find the elegant solution rather than bolting on. Triggers on "rethink", "redesign this", "what would this look like if we'd designed for it".
context: fork
---

# Rethink

For each proposed change, examine the existing system and redesign it into the most elegant solution that would have emerged if the change had been a foundational assumption from the start.

## Context

**Branch**: !`git branch --show-current`
**Arguments**: $ARGUMENTS

## Instructions

### Step 1: Understand the Change

Read `$ARGUMENTS` to understand what the user wants to add, fix, or change. If unclear, ask.

Then gather context:
- Read the files involved and their surrounding code
- Understand the current architecture of the affected area
- Map the data flow and dependencies

### Step 2: Identify the Bolt-On

Ask: "If I just implemented this change directly, what would it look like?"

This is the naive approach — the patch, the extra parameter, the new flag, the added special case. Write it down mentally. This is what you're trying to avoid.

### Step 3: Rethink from First Principles

Now forget the current code exists. Ask:

> "If this requirement had been known from day one, how would this area of the system have been designed?"

Work through:
1. **What abstractions would exist?** — Would the current types/interfaces look different? Would there be a different boundary between modules?
2. **What would the data flow look like?** — Would information travel the same path? Would the same things be grouped together?
3. **What wouldn't exist?** — What current code is only there because the original design didn't account for this? What becomes unnecessary?
4. **What's the simplest version?** — The redesign should reduce complexity, not add it. If the rethought version is more complex than the bolt-on, the bolt-on might actually be right.

### Step 4: Find the Practical Path

The goal isn't a full rewrite. It's finding the minimal transformation that gets from here to there:

- What can stay as-is?
- What needs to change shape?
- What should be removed?
- What's the migration path that keeps things working at each step?

Bias toward fewer moving parts. The best rethink often removes code rather than adding it.

### Step 5: Present the Redesign

Output:

```
## Rethink: {brief description}

### The Bolt-On
{What the naive implementation would look like and why it's suboptimal}

### The Redesign
{What the system would look like if this requirement had been foundational}

### Key Insight
{The one sentence that captures why the redesign is better}

### Changes
{Concrete list of what to add, modify, and remove — with file paths}

### Migration
{Step-by-step path from current state to redesigned state}
```

Keep it concrete. File paths, function names, before/after shapes. No hand-waving.

## Guidelines

- Read all relevant code before proposing anything. No rethinking in the abstract.
- The redesign must be simpler or equal in complexity to the current system + bolt-on. If it's more complex, say so and recommend the simpler path.
- Don't rethink beyond the affected area. A change to one service doesn't mean redesigning the whole app.
- Respect existing patterns in CLAUDE.md / AGENTS.md. The redesign should feel native to the codebase.
- This is a thinking tool, not an implementation tool. Present the redesign and let the user decide whether to proceed.
