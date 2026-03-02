# Ardent Claude Plugins

Claude Code skills for the Ardent team.

## Install

```bash
claude /plugin marketplace add ardent-ai/ardent-claude-plugins
claude /plugin install ardent@ardent
```

Or add to your project's `.claude/settings.json` for automatic setup:

```json
{
  "extraKnownMarketplaces": {
    "ardent": {
      "source": { "source": "github", "repo": "ardent-ai/ardent-claude-plugins" }
    }
  },
  "enabledPlugins": {
    "ardent@ardent": true
  }
}
```

## Skills

All skills are invoked as `/ardent:<skill-name>`.

### Planning

| Skill | Command | Description |
|---|---|---|
| brainstorm | `/ardent:brainstorm` | Explore requirements and approaches through collaborative dialogue |
| shaping | `/ardent:shaping` | Shape Up methodology for ambiguous features |
| plan | `/ardent:plan` | Transform feature descriptions into structured plans |
| deepen-plan | `/ardent:deepen-plan` | Enhance plans with parallel research agents |
| design-review | `/ardent:design-review` | Validate high-level design before building |
| document-review | `/ardent:document-review` | Structured review rubric for plans and docs |

### Building

| Skill | Command | Description |
|---|---|---|
| work | `/ardent:work` | Execute work plans with quality gates |
| lfg | `/ardent:lfg` | Full autonomous pipeline: plan, deepen, build, review, fix |
| tdd | `/ardent:tdd` | Test-driven development with red-green-refactor |
| rethink | `/ardent:rethink` | Redesign a system area from first principles |

### Review

| Skill | Command | Description |
|---|---|---|
| review | `/ardent:review` | Adaptive code review, scales from single-pass to 9-agent swarm |
| security-scan | `/ardent:security-scan` | STRIDE-based security analysis |
| simplify | `/ardent:simplify` | Simplify code for clarity and maintainability |
| address_pr_feedback | `/ardent:address_pr_feedback` | Analyze and implement PR review feedback |

### Git

| Skill | Command | Description |
|---|---|---|
| fixup | `/ardent:fixup` | Fold fixes into the correct earlier commits |
| split-commits | `/ardent:split-commits` | Clean up commit history into atomic commits |
| pr | `/ardent:pr` | Create a PR end-to-end: description, humanize, link Linear issues |

### Knowledge

| Skill | Command | Description |
|---|---|---|
| compound | `/ardent:compound` | Document a solved problem as a searchable solution |
| pick-up | `/ardent:pick-up` | Morning briefing from the most recent wrap-up |
| wrap-up | `/ardent:wrap-up` | End-of-day summary of all in-flight work |

### Writing

| Skill | Command | Description |
|---|---|---|
| humanizer | `/ardent:humanizer` | Remove AI writing patterns from text |
| visual-explainer | `/ardent:visual-explainer` | Generate self-contained HTML technical diagrams |

### Other

| Skill | Command | Description |
|---|---|---|
| archive | `/ardent:archive` | Upload HTML docs to the team's GitHub Pages archive |
| webcomic | `/ardent:webcomic` | Generate a webcomic page from a feature or diff |

## Workspace convention

Several skills (planning, review, compound, wrap-up) write documents to `.untracked/` in the project root. Make sure `.untracked/` is in your `.gitignore`.
