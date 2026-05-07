from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import aiosqlite

from osbot.log import get_logger
from osbot.state.migrations import MIGRATIONS, SCHEMA_VERSION
from osbot.types import RepoTier

logger = get_logger(__name__)


class MemoryDB:
    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def open(self) -> None:
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._run_migrations()

    async def _run_migrations(self) -> None:
        db = self._get_db()
        current = 0
        try:
            rows = await db.execute_fetchall("SELECT version FROM schema_version LIMIT 1")
            row_list = list(rows)
            if row_list:
                current = int(row_list[0][0])
        except Exception:
            pass

        for i, sql in enumerate(MIGRATIONS):
            if i >= current:
                for statement in sql.strip().split(";"):
                    stmt = statement.strip()
                    if stmt:
                        await db.execute(stmt)

        await db.execute("DELETE FROM schema_version")
        await db.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        await db.commit()
        logger.info("migrations_complete", version=SCHEMA_VERSION)

    def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            msg = "database not opened"
            raise RuntimeError(msg)
        return self._db

    async def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        db = self._get_db()
        cursor = await db.execute(sql, params)
        await db.commit()
        return cursor.rowcount

    async def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        db = self._get_db()
        cursor = await db.execute(sql, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    async def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        db = self._get_db()
        cursor = await db.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def fetchval(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        db = self._get_db()
        cursor = await db.execute(sql, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        return row[0]

    async def upsert_repo(self, data: dict[str, Any]) -> None:
        full_name = data["full_name"]
        owner = data.get("owner", full_name.split("/")[0])
        name = data.get("name", full_name.split("/")[1])
        topics = json.dumps(data.get("topics", []))
        now = datetime.now(UTC).isoformat()

        await self.execute(
            """
            INSERT INTO repo_registry (
                full_name, owner, name, language, stars, description, topics,
                license_key, tier, score, has_contributing, has_pr_template,
                has_code_of_conduct, has_ai_policy, requires_assignment, ci_enabled,
                external_merge_rate, avg_response_hours, close_completion_rate,
                last_external_merge_days, has_merged_bots, gfi_issue_count,
                help_wanted_count, bug_issue_count, community_health_pct,
                has_funding, default_branch, last_push_at, discovered_at,
                discovery_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(full_name) DO UPDATE SET
                language = excluded.language,
                stars = excluded.stars,
                description = excluded.description,
                topics = excluded.topics,
                license_key = excluded.license_key,
                score = excluded.score,
                has_contributing = excluded.has_contributing,
                has_pr_template = excluded.has_pr_template,
                has_code_of_conduct = excluded.has_code_of_conduct,
                has_ai_policy = excluded.has_ai_policy,
                requires_assignment = excluded.requires_assignment,
                ci_enabled = excluded.ci_enabled,
                external_merge_rate = excluded.external_merge_rate,
                avg_response_hours = excluded.avg_response_hours,
                close_completion_rate = excluded.close_completion_rate,
                last_external_merge_days = excluded.last_external_merge_days,
                has_merged_bots = excluded.has_merged_bots,
                gfi_issue_count = excluded.gfi_issue_count,
                help_wanted_count = excluded.help_wanted_count,
                bug_issue_count = excluded.bug_issue_count,
                community_health_pct = excluded.community_health_pct,
                has_funding = excluded.has_funding,
                default_branch = excluded.default_branch,
                last_push_at = excluded.last_push_at
            """,
            (
                full_name,
                owner,
                name,
                data.get("language", ""),
                data.get("stars", 0),
                data.get("description", ""),
                topics,
                data.get("license_key", ""),
                data.get("tier", RepoTier.PROSPECT.value),
                data.get("score", 0.0),
                int(data.get("has_contributing", False)),
                int(data.get("has_pr_template", False)),
                int(data.get("has_code_of_conduct", False)),
                int(data.get("has_ai_policy", False)),
                int(data.get("requires_assignment", False)),
                int(data.get("ci_enabled", False)),
                data.get("external_merge_rate", 0.0),
                data.get("avg_response_hours", 0.0),
                data.get("close_completion_rate", 0.0),
                data.get("last_external_merge_days", 999),
                int(data.get("has_merged_bots", False)),
                data.get("gfi_issue_count", 0),
                data.get("help_wanted_count", 0),
                data.get("bug_issue_count", 0),
                data.get("community_health_pct", 0),
                int(data.get("has_funding", False)),
                data.get("default_branch", "main"),
                data.get("last_push_at", ""),
                now,
                data.get("discovery_source", ""),
            ),
        )

    async def get_repo(self, full_name: str) -> dict[str, Any] | None:
        return await self.fetchone("SELECT * FROM repo_registry WHERE full_name = ?", (full_name,))

    async def update_tier(self, full_name: str, tier: RepoTier, reason: str = "") -> None:
        now = datetime.now(UTC).isoformat()
        if tier == RepoTier.EXCLUDED:
            await self.execute(
                "UPDATE repo_registry SET tier = ?, exclusion_reason = ?, excluded_at = ? WHERE full_name = ?",
                (tier.value, reason, now, full_name),
            )
        else:
            await self.execute(
                "UPDATE repo_registry SET tier = ? WHERE full_name = ?",
                (tier.value, full_name),
            )

    async def get_repos_by_tier(self, tier: RepoTier) -> list[dict[str, Any]]:
        return await self.fetchall(
            "SELECT * FROM repo_registry WHERE tier = ? ORDER BY score DESC",
            (tier.value,),
        )

    async def get_issue_search_pool(self) -> list[dict[str, Any]]:
        return await self.fetchall(
            "SELECT * FROM repo_registry WHERE tier IN (?, ?, ?) ORDER BY score DESC",
            (RepoTier.QUALIFIED.value, RepoTier.ACTIVE.value, RepoTier.TRUSTED.value),
        )

    async def repos_needing_refresh(self, stale_days: int = 7) -> list[dict[str, Any]]:
        return await self.fetchall(
            """
            SELECT * FROM repo_registry
            WHERE tier IN (?, ?, ?)
              AND (signals_updated_at = '' OR signals_updated_at < datetime('now', ?))
            ORDER BY signals_updated_at ASC
            """,
            (
                RepoTier.QUALIFIED.value,
                RepoTier.ACTIVE.value,
                RepoTier.TRUSTED.value,
                f"-{stale_days} days",
            ),
        )

    async def record_outcome(
        self, repo: str, issue_number: int, outcome: str, pr_number: int | None = None, details: str = ""
    ) -> None:
        await self.execute(
            """
            INSERT INTO outcomes (repo, issue_number, pr_number, outcome, details)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(repo, issue_number) DO UPDATE SET
                outcome = excluded.outcome,
                pr_number = excluded.pr_number,
                details = excluded.details,
                created_at = datetime('now')
            """,
            (repo, issue_number, pr_number, outcome, details),
        )

    async def get_outcome(self, repo: str, issue_number: int) -> dict[str, Any] | None:
        return await self.fetchone(
            "SELECT * FROM outcomes WHERE repo = ? AND issue_number = ?",
            (repo, issue_number),
        )

    async def is_repo_banned(self, repo: str) -> bool:
        row = await self.fetchone(
            "SELECT tier FROM repo_registry WHERE full_name = ?",
            (repo,),
        )
        if row is None:
            return False
        return bool(row["tier"] == RepoTier.EXCLUDED.value)

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None
