from __future__ import annotations

from typing import Any

from osbot.config import settings
from osbot.log import get_logger
from osbot.types import MemoryDBProtocol, RepoTier

logger = get_logger(__name__)


async def update_repo_tier(db: MemoryDBProtocol, full_name: str, score: float, signals: dict[str, Any]) -> RepoTier:
    repo = await db.fetchone("SELECT * FROM repo_registry WHERE full_name = ?", (full_name,))
    if repo is None:
        return RepoTier.PROSPECT

    current = RepoTier(repo["tier"])

    if score < 0:
        await _set_tier(db, full_name, RepoTier.EXCLUDED, "ai_policy")
        return RepoTier.EXCLUDED

    consecutive_rejections = repo.get("consecutive_rejections", 0)
    if consecutive_rejections >= 3:
        await _set_tier(db, full_name, RepoTier.EXCLUDED, "consecutive_rejections")
        return RepoTier.EXCLUDED

    if current == RepoTier.EXCLUDED:
        return RepoTier.EXCLUDED

    merge_days = signals.get("last_external_merge_days", 999)
    if merge_days > 180 and current not in {RepoTier.PROSPECT, RepoTier.EXCLUDED}:
        await _set_tier(db, full_name, RepoTier.DORMANT, "no_recent_merges")
        return RepoTier.DORMANT

    total_merged = repo.get("total_prs_merged", 0)
    total_submitted = repo.get("total_prs_submitted", 0)

    if current == RepoTier.PROSPECT:
        if score >= settings.repo_score_threshold:
            await _set_tier(db, full_name, RepoTier.QUALIFIED)
            return RepoTier.QUALIFIED
        return RepoTier.PROSPECT

    if current == RepoTier.QUALIFIED:
        if total_merged >= 1:
            await _set_tier(db, full_name, RepoTier.ACTIVE)
            return RepoTier.ACTIVE
        return RepoTier.QUALIFIED

    if current == RepoTier.ACTIVE:
        if total_merged >= 3 and total_submitted >= 4:
            await _set_tier(db, full_name, RepoTier.TRUSTED)
            return RepoTier.TRUSTED
        return RepoTier.ACTIVE

    if current == RepoTier.TRUSTED:
        return RepoTier.TRUSTED

    if current == RepoTier.DORMANT:
        if merge_days <= 30 and score >= settings.repo_score_threshold:
            await _set_tier(db, full_name, RepoTier.QUALIFIED)
            return RepoTier.QUALIFIED
        return RepoTier.DORMANT

    return current


async def _set_tier(db: MemoryDBProtocol, full_name: str, tier: RepoTier, reason: str = "") -> None:
    if tier == RepoTier.EXCLUDED:
        await db.execute(
            "UPDATE repo_registry SET tier = ?, exclusion_reason = ?, excluded_at = datetime('now') WHERE full_name = ?",
            (tier.value, reason, full_name),
        )
    else:
        await db.execute(
            "UPDATE repo_registry SET tier = ? WHERE full_name = ?",
            (tier.value, full_name),
        )
    logger.info("tier_updated", repo=full_name, tier=tier.value, reason=reason)


async def get_issue_search_pool(db: MemoryDBProtocol) -> list[dict[str, Any]]:
    return await db.fetchall(
        "SELECT * FROM repo_registry WHERE tier IN (?, ?, ?) ORDER BY score DESC",
        (RepoTier.QUALIFIED.value, RepoTier.ACTIVE.value, RepoTier.TRUSTED.value),
    )


async def repos_needing_refresh(db: MemoryDBProtocol, stale_days: int = 7) -> list[dict[str, Any]]:
    return await db.fetchall(
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
