from __future__ import annotations

from typing import TYPE_CHECKING, Any

from osbot.log import get_logger

if TYPE_CHECKING:
    from osbot.types import MemoryDBProtocol

logger = get_logger(__name__)


async def record_discovery(
    db: MemoryDBProtocol,
    strategy: str,
    query: str = "",
    repos_found: int = 0,
    repos_qualified: int = 0,
    issues_found: int = 0,
) -> None:
    await db.execute(
        """
        INSERT INTO discovery_sources (strategy, query, repos_found, repos_qualified, issues_found)
        VALUES (?, ?, ?, ?, ?)
        """,
        (strategy, query, repos_found, repos_qualified, issues_found),
    )
    logger.info(
        "discovery_recorded",
        strategy=strategy,
        repos_found=repos_found,
        repos_qualified=repos_qualified,
        issues_found=issues_found,
    )


async def get_strategy_effectiveness(db: MemoryDBProtocol, days: int = 30) -> list[dict[str, Any]]:
    return await db.fetchall(
        """
        SELECT
            strategy,
            SUM(repos_found) as total_repos,
            SUM(repos_qualified) as total_qualified,
            SUM(issues_found) as total_issues,
            COUNT(*) as runs,
            CASE WHEN SUM(repos_found) > 0
                THEN CAST(SUM(repos_qualified) AS REAL) / SUM(repos_found)
                ELSE 0
            END as qualification_rate
        FROM discovery_sources
        WHERE created_at > datetime('now', ?)
        GROUP BY strategy
        ORDER BY total_qualified DESC
        """,
        (f"-{days} days",),
    )


async def get_adjusted_budgets(
    db: MemoryDBProtocol,
    base_budgets: dict[str, int],
    total_budget: int = 18,
) -> dict[str, int]:
    effectiveness = await get_strategy_effectiveness(db)
    if not effectiveness:
        return base_budgets

    strategy_scores: dict[str, float] = {}
    for row in effectiveness:
        strategy = row["strategy"]
        base_strategy = strategy.split(":")[0] if ":" in strategy else strategy
        qualified = row["total_qualified"] or 0
        issues = row["total_issues"] or 0
        runs = row["runs"] or 1
        score = (qualified * 2 + issues) / runs
        if base_strategy in strategy_scores:
            strategy_scores[base_strategy] = max(strategy_scores[base_strategy], score)
        else:
            strategy_scores[base_strategy] = score

    if not strategy_scores:
        return base_budgets

    total_score = sum(strategy_scores.values()) or 1.0
    adjusted: dict[str, int] = {}
    remaining = total_budget

    for strategy_name in base_budgets:
        score = strategy_scores.get(strategy_name, 1.0)
        share = score / total_score
        budget = max(1, round(total_budget * share))
        adjusted[strategy_name] = budget
        remaining -= budget

    if remaining != 0:
        best = max(adjusted, key=lambda k: strategy_scores.get(k, 0))
        adjusted[best] = max(1, adjusted[best] + remaining)

    return adjusted
