from __future__ import annotations

SCHEMA_VERSION = 5

MIGRATIONS: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS repo_registry (
        full_name TEXT PRIMARY KEY,
        owner TEXT NOT NULL,
        name TEXT NOT NULL,
        language TEXT NOT NULL DEFAULT '',
        stars INTEGER NOT NULL DEFAULT 0,
        description TEXT NOT NULL DEFAULT '',
        topics TEXT NOT NULL DEFAULT '[]',
        license_key TEXT NOT NULL DEFAULT '',
        tier TEXT NOT NULL DEFAULT 'prospect',
        score REAL NOT NULL DEFAULT 0.0,
        has_contributing INTEGER NOT NULL DEFAULT 0,
        has_pr_template INTEGER NOT NULL DEFAULT 0,
        has_code_of_conduct INTEGER NOT NULL DEFAULT 0,
        has_ai_policy INTEGER NOT NULL DEFAULT 0,
        requires_assignment INTEGER NOT NULL DEFAULT 0,
        ci_enabled INTEGER NOT NULL DEFAULT 0,
        external_merge_rate REAL NOT NULL DEFAULT 0.0,
        avg_response_hours REAL NOT NULL DEFAULT 0.0,
        close_completion_rate REAL NOT NULL DEFAULT 0.0,
        last_external_merge_days INTEGER NOT NULL DEFAULT 999,
        has_merged_bots INTEGER NOT NULL DEFAULT 0,
        gfi_issue_count INTEGER NOT NULL DEFAULT 0,
        help_wanted_count INTEGER NOT NULL DEFAULT 0,
        bug_issue_count INTEGER NOT NULL DEFAULT 0,
        community_health_pct INTEGER NOT NULL DEFAULT 0,
        has_funding INTEGER NOT NULL DEFAULT 0,
        default_branch TEXT NOT NULL DEFAULT 'main',
        last_push_at TEXT NOT NULL DEFAULT '',
        signals_updated_at TEXT NOT NULL DEFAULT '',
        discovered_at TEXT NOT NULL DEFAULT '',
        discovery_source TEXT NOT NULL DEFAULT '',
        exclusion_reason TEXT NOT NULL DEFAULT '',
        excluded_at TEXT NOT NULL DEFAULT '',
        total_prs_submitted INTEGER NOT NULL DEFAULT 0,
        total_prs_merged INTEGER NOT NULL DEFAULT 0,
        total_prs_rejected INTEGER NOT NULL DEFAULT 0,
        last_pr_at TEXT NOT NULL DEFAULT '',
        consecutive_rejections INTEGER NOT NULL DEFAULT 0
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_repo_tier ON repo_registry(tier);
    CREATE INDEX IF NOT EXISTS idx_repo_language ON repo_registry(language);
    CREATE INDEX IF NOT EXISTS idx_repo_score ON repo_registry(score DESC);
    CREATE INDEX IF NOT EXISTS idx_repo_signals_updated ON repo_registry(signals_updated_at);
    """,
    """
    CREATE TABLE IF NOT EXISTS outcomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT NOT NULL,
        issue_number INTEGER NOT NULL,
        pr_number INTEGER,
        outcome TEXT NOT NULL,
        details TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(repo, issue_number)
    );
    CREATE INDEX IF NOT EXISTS idx_outcomes_repo ON outcomes(repo);
    CREATE INDEX IF NOT EXISTS idx_outcomes_outcome ON outcomes(outcome);
    """,
    """
    CREATE TABLE IF NOT EXISTS discovery_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy TEXT NOT NULL,
        query TEXT NOT NULL DEFAULT '',
        repos_found INTEGER NOT NULL DEFAULT 0,
        repos_qualified INTEGER NOT NULL DEFAULT 0,
        issues_found INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_discovery_strategy ON discovery_sources(strategy);
    """,
    """
    CREATE TABLE IF NOT EXISTS issue_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT NOT NULL,
        issue_number INTEGER NOT NULL,
        title TEXT NOT NULL DEFAULT '',
        score REAL NOT NULL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'queued',
        labels TEXT NOT NULL DEFAULT '[]',
        body TEXT NOT NULL DEFAULT '',
        url TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(repo, issue_number)
    );
    CREATE INDEX IF NOT EXISTS idx_issue_queue_status ON issue_queue(status);
    CREATE INDEX IF NOT EXISTS idx_issue_queue_score ON issue_queue(score DESC);
    CREATE INDEX IF NOT EXISTS idx_issue_queue_repo ON issue_queue(repo);
    """,
]
