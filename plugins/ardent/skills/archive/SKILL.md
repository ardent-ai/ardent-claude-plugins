---
name: archive
description: Upload HTML docs to the team's GitHub Pages archive for permanent browsing and sharing. Use when the user says "archive this", "upload to archive", or /archive.
argument-hint: "[optional: path to HTML file]"
---

# Archive

Upload an HTML document to the `ardent-ai/docs-archive` GitHub Pages site. Produces a permanent, shareable URL.

## Context

<context_hint> #$ARGUMENTS </context_hint>

## Workflow

### 1. Identify the file

If the user provided a path as an argument, use that file.

Otherwise, find the most recently modified `.html` file in `~/.agent/diagrams/`:

```bash
ls -t ~/.agent/diagrams/*.html 2>/dev/null | head -1
```

If no HTML files exist, ask the user for a path.

Show the user which file you'll archive and confirm before proceeding.

### 2. Gather metadata

Ask the user for the following (infer defaults from the filename or HTML `<title>`):

- **Title** (required) — a short, descriptive name
- **Description** (optional) — one-liner summary
- **Author** (optional, default: infer from `git config user.name` or `whoami`)
- **PR URL** (optional) — link to a related pull request
- **Linear issue URL** (optional) — link to a related Linear issue

Keep this lightweight — one question with sensible defaults, not a form interrogation.

### 3. Sync local checkout

The archive repo lives at `~/.claude/docs-archive/`. Sync it:

```bash
if [ -d ~/.claude/docs-archive/.git ]; then
  cd ~/.claude/docs-archive && git pull --ff-only
else
  gh repo clone ardent-ai/docs-archive ~/.claude/docs-archive
fi
```

### 4. Copy file and update manifest

Derive the filename:
- Date: today's date as `YYYY-MM-DD`
- Slug: lowercase, hyphenated version of the title (strip special chars, max 50 chars)
- Result: `docs/{date}-{slug}.html`

Copy the HTML file:

```bash
cp /path/to/source.html ~/.claude/docs-archive/docs/{date}-{slug}.html
```

Read `manifest.json`, append the new entry, write it back. The entry shape:

```json
{
  "id": "{date}-{slug}",
  "title": "...",
  "description": "...",
  "author": "...",
  "date": "YYYY-MM-DD",
  "filename": "docs/{date}-{slug}.html",
  "links": {
    "pr": "https://... or omit",
    "linear": "https://... or omit"
  }
}
```

Omit `links` (or individual keys within it) if no URLs were provided. Omit `description` if empty.

### 5. Commit and push

```bash
cd ~/.claude/docs-archive
git add docs/{date}-{slug}.html manifest.json
git commit -m "archive: {title}"
git push
```

### 6. Return the URL

Output the GitHub Pages URL:

```
Archived: https://ardent-ai.github.io/docs-archive/docs/{date}-{slug}.html
Browse all: https://ardent-ai.github.io/docs-archive/
```
