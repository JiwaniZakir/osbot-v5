from __future__ import annotations

from typing import TYPE_CHECKING

from osbot.log import get_logger

if TYPE_CHECKING:
    from osbot.types import RepoMeta, RepoSignals

logger = get_logger(__name__)


def score_repo(meta: RepoMeta, signals: RepoSignals) -> float:
    if signals.has_ai_policy:
        logger.info("repo_excluded_ai_policy", repo=meta.full_name)
        return -1.0

    score = 5.0

    mr = signals.external_merge_rate
    if mr >= 0.6:
        score += 3.0
    elif mr >= 0.4:
        score += 2.0
    elif mr >= 0.2:
        score += 1.0
    elif mr < 0.05:
        score -= 3.0
    elif mr < 0.1:
        score -= 1.5

    if signals.last_external_merge_days <= 14:
        score += 1.5
    elif signals.last_external_merge_days <= 30:
        score += 1.0
    elif signals.last_external_merge_days <= 60:
        score += 0.5

    if signals.has_merged_bots:
        score += 1.0

    if signals.avg_response_hours > 0:
        if signals.avg_response_hours <= 24:
            score += 1.0
        elif signals.avg_response_hours <= 72:
            score += 0.5
        elif signals.avg_response_hours > 168:
            score -= 1.0

    if signals.has_ci:
        score += 0.5

    if meta.stars >= 1000:
        score += 0.5
    elif meta.stars >= 500:
        score += 0.25

    cr = signals.close_completion_rate
    if cr >= 0.7:
        score += 0.5
    elif cr >= 0.4:
        score += 0.25
    elif cr < 0.2:
        score -= 0.5

    return round(max(0.0, min(10.0, score)), 2)
