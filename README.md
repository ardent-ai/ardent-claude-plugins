# Ardent Claude Plugins

Claude Code skills for the Ardent team.

## Install

From inside Claude Code, run:

```
/plugin marketplace add ardent-ai/ardent-claude-plugins
/plugin install ardent@ardent
```

To update after changes:

```
/plugin marketplace update ardent
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

Skills show up as `/<skill-name>` with `(ardent)` label in the autocomplete.

### Planning

| Skill | Command | Description |
|---|---|---|
| brainstorm | `/brainstorm` | Explore requirements and approaches through collaborative dialogue |
| shaping | `/shaping` | Shape Up methodology for ambiguous features |
| plan-ardent | `/plan-ardent` | Transform feature descriptions into structured plans |
| deepen-plan | `/deepen-plan` | Enhance plans with parallel research agents |
| design-review | `/design-review` | Validate high-level design before building |
| document-review | `/document-review` | Structured review rubric for plans and docs |

### Building

| Skill | Command | Description |
|---|---|---|
| work | `/work` | Execute work plans with quality gates |
| lfg | `/lfg` | Full autonomous pipeline: plan, deepen, build, review, fix |
| tdd | `/tdd` | Test-driven development with red-green-refactor |
| rethink | `/rethink` | Redesign a system area from first principles |

### Review

| Skill | Command | Description |
|---|---|---|
| review-ardent | `/review-ardent` | Adaptive code review, scales from single-pass to 9-agent swarm |
| security-scan | `/security-scan` | STRIDE-based security analysis |
| cleanup | `/cleanup` | Simplify code for clarity and maintainability |
| address_pr_feedback | `/address_pr_feedback` | Analyze and implement PR review feedback |

### Git

| Skill | Command | Description |
|---|---|---|
| fixup | `/fixup` | Fold fixes into the correct earlier commits |
| split-commits | `/split-commits` | Clean up commit history into atomic commits |
| pr | `/pr` | Create a PR end-to-end: description, humanize, link Linear issues |

### Knowledge

| Skill | Command | Description |
|---|---|---|
| compound | `/compound` | Document a solved problem as a searchable solution |
| pick-up | `/pick-up` | Morning briefing from the most recent wrap-up |
| wrap-up | `/wrap-up` | End-of-day summary of all in-flight work |

### Writing

| Skill | Command | Description |
|---|---|---|
| humanizer | `/humanizer` | Remove AI writing patterns from text |
| visual-explainer | `/visual-explainer` | Generate self-contained HTML technical diagrams |

### Other

| Skill | Command | Description |
|---|---|---|
| archive | `/archive` | Upload HTML docs to the team's GitHub Pages archive |
| webcomic | `/webcomic` | Generate a webcomic page from a feature or diff |

## Workspace convention

Several skills (planning, review, compound, wrap-up) write documents to `.untracked/` in the project root. Make sure `.untracked/` is in your `.gitignore`.
