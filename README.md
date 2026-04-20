# AI Code Review Bot

A GitHub Action that automatically reviews pull requests using Claude AI. Built with LangGraph for agent orchestration, it runs as an ephemeral Docker container — starts, reviews, posts a comment, and exits.

## How it works

```
PR opened / updated
        │
        ▼
  GitHub Actions pulls pre-built image from GHCR
        │
        ▼
  Container starts → fetches PR diff via GitHub API
        │
        ▼
  LangGraph agent pipeline
  ├── parse_diff  — extracts changed files (16 languages supported)
  ├── review      — Claude reviews each changed file chunk
  └── post_comment — posts a structured markdown comment on the PR
        │
        ▼
  Container exits
```

## Usage

Add this to your repo at `.github/workflows/code-review.yml`:

```yaml
name: Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: AI Code Review
        uses: evjohns005/code-review-bot@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Required secrets

| Secret | How to get it |
|--------|---------------|
| `GITHUB_TOKEN` | Built-in — no configuration needed |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `github-token` | Yes | — | GitHub token with `pull-requests: write` |
| `anthropic-api-key` | Yes | — | Anthropic API key |
| `model` | No | `claude-sonnet-4-5` | Claude model ID |
| `max-tokens` | No | `2000` | Max tokens per LLM response |
| `pr-number` | No | auto-detected | Override the PR number to review |
| `langsmith-api-key` | No | — | Enable LangSmith tracing (optional) |
| `langsmith-project` | No | `code-review-bot` | LangSmith project name |

## Architecture

```
code-review-bot/
├── action.yml                  # GitHub Action definition
├── Dockerfile                  # Ephemeral container image
├── main.py                     # Entrypoint — reads GHA context, runs agent
├── src/
│   ├── agent/
│   │   ├── review.py           # LangGraph state machine (3 nodes)
│   │   └── prompts/
│   │       └── system.md       # Code review instructions for Claude
│   ├── config/
│   │   └── settings.py         # Environment-based configuration
│   ├── data/schemas/
│   │   └── graph.py            # ReviewState Pydantic model
│   ├── github/
│   │   └── client.py           # Fetch PR diff via GitHub API
│   ├── services/
│   │   └── llm_provider.py     # Anthropic client with retry + model fallback
│   ├── system/
│   │   └── logs.py             # Structured logging (structlog)
│   └── utils/
│       └── diff_parser.py      # Parse unified diffs into reviewable chunks
└── .github/workflows/
    ├── build-push.yml          # Build & push image to GHCR on merge to main
    └── self-review.yml         # Uses the action on this repo's own PRs
```

### Agent nodes

| Node | Input | Output |
|------|-------|--------|
| `parse_diff` | Raw unified diff string | List of per-file chunks with added lines + context |
| `review` | File chunks | LLM review text per chunk |
| `post_comment` | Reviews + PR metadata | GitHub comment posted; routes to END |

### LLM fallback chain

If the primary model fails, the service automatically retries with fallbacks:

```
claude-sonnet-4-5 → claude-opus-4-6 → claude-haiku-4-5
```

Each model gets up to 3 attempts before the chain advances.

## Publishing the image

Pushing to `main` triggers `build-push.yml`, which builds and pushes to:

```
ghcr.io/evjohns005/code-review-bot:latest
ghcr.io/evjohns005/code-review-bot:main
ghcr.io/evjohns005/code-review-bot:sha-<short-sha>
```

Semantic version tags (`v1.2.3`) are also published when you push a tag.

After the first push, set the GHCR package visibility to **Public** in your GitHub package settings so consumer repos can pull the image without authentication.

## Local development

```bash
# Install dependencies
uv sync

# Copy and fill in credentials
cp .env.example .env

# Run against a local diff file
uv run python main.py   # reads diff.patch if GITHUB_REPOSITORY / GITHUB_EVENT_PATH are unset
```

## Observability

Structured JSON logs are emitted to stdout in the container (`LOG_FORMAT=json`). Set `LOG_FORMAT=text` locally for readable output.

Optional [LangSmith](https://smith.langchain.com) tracing is enabled by passing a `langsmith-api-key` input — LangGraph emits full traces automatically when `LANGCHAIN_TRACING_V2=true`.
