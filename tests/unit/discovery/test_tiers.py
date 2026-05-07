from __future__ import annotations

import pytest

from osbot.discovery.qualify.tiers import update_repo_tier
from osbot.state.memory import MemoryDB
from osbot.types import RepoTier


@pytest.fixture
async def db() -> MemoryDB:
    mem = MemoryDB(":memory:")
    await mem.open()
    yield mem
    await mem.close()


async def _insert_repo(
    db: MemoryDB,
    full_name: str = "org/repo",
    tier: str = "prospect",
    score: float = 5.0,
    total_prs_merged: int = 0,
    total_prs_submitted: int = 0,
    consecutive_rejections: int = 0,
) -> None:
    owner, name = full_name.split("/")
    await db.execute(
        """
        INSERT INTO repo_registry (
            full_name, owner, name, language, tier, score,
            total_prs_merged, total_prs_submitted, consecutive_rejections
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (full_name, owner, name, "Python", tier, score, total_prs_merged, total_prs_submitted, consecutive_rejections),
    )


class TestTierTransitions:
    async def test_prospect_to_qualified(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="prospect", score=5.0)
        result = await update_repo_tier(db, "org/repo", 5.0, {"last_external_merge_days": 10})
        assert result == RepoTier.QUALIFIED

    async def test_prospect_stays_if_low_score(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="prospect", score=2.0)
        result = await update_repo_tier(db, "org/repo", 2.0, {"last_external_merge_days": 10})
        assert result == RepoTier.PROSPECT

    async def test_qualified_to_active(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="qualified", score=6.0, total_prs_merged=1)
        result = await update_repo_tier(db, "org/repo", 6.0, {"last_external_merge_days": 10})
        assert result == RepoTier.ACTIVE

    async def test_qualified_stays_without_merges(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="qualified", score=6.0, total_prs_merged=0)
        result = await update_repo_tier(db, "org/repo", 6.0, {"last_external_merge_days": 10})
        assert result == RepoTier.QUALIFIED

    async def test_active_to_trusted(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="active", score=7.0, total_prs_merged=3, total_prs_submitted=4)
        result = await update_repo_tier(db, "org/repo", 7.0, {"last_external_merge_days": 5})
        assert result == RepoTier.TRUSTED

    async def test_active_stays_without_enough_merges(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="active", score=7.0, total_prs_merged=2, total_prs_submitted=3)
        result = await update_repo_tier(db, "org/repo", 7.0, {"last_external_merge_days": 5})
        assert result == RepoTier.ACTIVE

    async def test_trusted_stays_trusted(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="trusted", score=8.0, total_prs_merged=5, total_prs_submitted=6)
        result = await update_repo_tier(db, "org/repo", 8.0, {"last_external_merge_days": 5})
        assert result == RepoTier.TRUSTED

    async def test_dormant_on_no_recent_merges(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="qualified", score=6.0)
        result = await update_repo_tier(db, "org/repo", 6.0, {"last_external_merge_days": 200})
        assert result == RepoTier.DORMANT

    async def test_dormant_revival(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="dormant", score=5.0)
        result = await update_repo_tier(db, "org/repo", 5.0, {"last_external_merge_days": 20})
        assert result == RepoTier.QUALIFIED

    async def test_excluded_on_ai_policy(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="prospect", score=5.0)
        result = await update_repo_tier(db, "org/repo", -1.0, {"last_external_merge_days": 10})
        assert result == RepoTier.EXCLUDED

    async def test_excluded_on_consecutive_rejections(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="active", score=6.0, consecutive_rejections=3)
        result = await update_repo_tier(db, "org/repo", 6.0, {"last_external_merge_days": 10})
        assert result == RepoTier.EXCLUDED

    async def test_excluded_stays_excluded(self, db: MemoryDB) -> None:
        await _insert_repo(db, tier="excluded", score=8.0)
        result = await update_repo_tier(db, "org/repo", 8.0, {"last_external_merge_days": 5})
        assert result == RepoTier.EXCLUDED

    async def test_nonexistent_repo_returns_prospect(self, db: MemoryDB) -> None:
        result = await update_repo_tier(db, "nonexistent/repo", 5.0, {"last_external_merge_days": 10})
        assert result == RepoTier.PROSPECT
