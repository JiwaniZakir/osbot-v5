# osbot-v5

Autonomous open-source contribution bot with tiered discovery, smart search, and production CI/CD.

## Architecture

```
discovery/
├── search/              4 search strategies (topic, description, readme, dependency)
│   ├── topic_search     GitHub topic: qualifiers, shuffled, budget-limited
│   ├── description      "phrase" queries for repo name/description
│   ├── readme           in:readme deep content matching
│   └── dependency       in:file filename:requirements.txt package detection
├── qualify/             Repo qualification pipeline
│   ├── signals          GraphQL superquery (1 call per repo for everything)
│   ├── scorer           0-10 scoring with merge rate, recency, bot acceptance
│   └── tiers            5-tier lifecycle (PROSPECT->QUALIFIED->ACTIVE->TRUSTED->EXCLUDED)
├── issues/              Issue discovery and scoring
│   ├── quality          Regex-based quality assessment (file refs, repro steps, MRE)
│   ├── finder           Concurrent fetching with semaphore, GraphQL enrichment
│   └── scorer           12-signal scoring formula
└── feedback             Strategy effectiveness tracking and budget adjustment
```

## Key Design Decisions

- **Zero ML dependencies** - No embeddings, no vector DB, no torch. Pure heuristics + smart GitHub API usage.
- **GraphQL superquery** - 1 call per repo replaces 7-13 REST calls. Fetches topics, license, PR history, issue counts, CI, funding, CoC.
- **5-tier repo lifecycle** - TRUSTED repos (proven merges) get priority. EXCLUDED repos cost zero API calls.
- **4 search strategies** - Topic, description, README, and dependency searches. Budget-limited to 18 calls/cycle (was 30).
- **Self-improving** - Tracks merge rate per search strategy, auto-shifts budget toward what works.

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check src/ tests/
ruff format src/ tests/
mypy src/osbot/
```

## CI/CD

- **CI** - Lint (ruff), type check (mypy), test (pytest) on every push and PR
- **PR Review Gate** - Diff size check, full test suite, lint, type check
- **Deploy** - Docker image built and pushed to GHCR on main branch changes

## Docker

```bash
docker build -f deploy/Dockerfile -t osbot-v5 .
docker run -v osbot-state:/app/state -e GH_TOKEN=... osbot-v5
```

## License

MIT
