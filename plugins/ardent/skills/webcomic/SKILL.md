---
name: webcomic
description: >
  Generate a webcomic page from a feature description or the current git branch diff.
  Creates 4-6 illustrated panels with narrative flow, generates each via Gemini,
  and combines into a single comic page PNG. Triggers on "webcomic", "make a comic",
  "comic about", or /webcomic.
user_invocable: true
---

# Webcomic Generator

Generate a complete webcomic page: write the narrative, generate panel art with Gemini, and assemble into a single comic page image.

## Configuration

```
STYLE: funny
PANELS: 4
MODEL: pro
```

## Workflow

### Step 1: Determine Topic

Parse `$ARGUMENTS` for:
- **Style keyword** (optional): `funny` | `dramatic` | `technical` | `absurd` | `noir` — defaults to `funny`
- **Panel count** (optional): a number 4-6 — defaults to 4
- **Topic**: everything else in the arguments

Style and panel count can appear in any order before the topic. Examples:
- `/webcomic the login flow` → funny, 4 panels, topic = "the login flow"
- `/webcomic dramatic 6 our deploy pipeline` → dramatic, 6 panels, topic = "our deploy pipeline"
- `/webcomic noir the auth system` → noir, 4 panels, topic = "the auth system"

**If no arguments are provided**, auto-detect the topic from the current branch:
```bash
git diff main...HEAD --stat
git diff main...HEAD
```
Summarize what changed and use that as the comic topic. Use the branch name for additional context.

### Step 2: Design Panels

Create a narrative arc with setup → development → climax → resolution. Write a detailed image prompt for each panel.

**Critical prompt rules:**
- Every prompt MUST include: "No text, no speech bubbles, no words, no letters, no captions in the image."
- Describe the scene visually — characters, setting, action, mood, lighting
- Maintain visual consistency across panels (same characters, same art style)
- Include the style tone in prompts (e.g., "cartoon style, bright colors, exaggerated expressions" for funny)

**Style guidance:**

| Style | Art Direction |
|-------|--------------|
| funny | Bright cartoon style, exaggerated expressions, vibrant colors, comedic poses |
| dramatic | Cinematic lighting, dynamic angles, high contrast, intense expressions |
| technical | Clean line art, blueprint aesthetic, diagram-like precision, cool tones |
| absurd | Surreal imagery, impossible physics, clashing colors, dreamlike scenes |
| noir | High contrast B&W with deep shadows, rain-slicked surfaces, moody atmosphere |

Write a short caption (1 sentence) for each panel that tells the story. Captions are overlaid by `combine.py`, NOT baked into the image.

Present the panel plan to the user and ask for approval before generating.

### Step 3: Create Output Directory

```bash
mkdir -p ~/Desktop/webcomic-{slug}/
```

Where `{slug}` is a kebab-case version of the topic (e.g., `webcomic-login-flow`).

### Step 4: Generate Panel Images

Generate all panels using `image.py`. Run them in parallel (separate Bash calls) for speed.

For each panel:
```bash
uv run ~/.claude/skills/webcomic/scripts/image.py \
  --prompt "{panel_prompt}" \
  --output ~/Desktop/webcomic-{slug}/panel-{N}.png \
  --aspect landscape \
  --model pro \
  --size 1K
```

If a panel fails, retry it once. If it fails again, skip it and note the failure.

### Step 5: Combine into Comic Page

```bash
uv run ~/.claude/skills/webcomic/scripts/combine.py \
  --title "{comic_title}" \
  --panels ~/Desktop/webcomic-{slug}/panel-1.png ~/Desktop/webcomic-{slug}/panel-2.png ... \
  --captions "Caption 1" "Caption 2" ... \
  --output ~/Desktop/webcomic-{slug}/comic-page.png \
  --style {style}
```

### Step 6: Show Result

```bash
open ~/Desktop/webcomic-{slug}/comic-page.png
```

Report the output path and a summary of what was created.
