from __future__ import annotations

from typing import TYPE_CHECKING

from osbot.config import settings
from osbot.log import get_logger

if TYPE_CHECKING:
    from osbot.types import IssueQuality

logger = get_logger(__name__)


def score_issue(
    labels: list[str],
    quality: IssueQuality,
    stars: int = 0,
    comment_count: int = 0,
    reaction_count: int = 0,
    tier: str = "prospect",
) -> float:
    score = settings.issue_base_score

    if quality.filed_by_maintainer:
        score += 1.0
    if quality.has_file_reference:
        score += 0.75
    if quality.likely_single_file:
        score += 0.60
    if quality.has_reproduction_steps:
        score += 0.50
    if quality.is_regression:
        score += 0.50
    if quality.has_mre:
        score += 0.40

    lower_labels = [lb.lower() for lb in labels]
    if "good first issue" in lower_labels:
        score += 0.75
    if "help wanted" in lower_labels:
        score += 0.50
    if "bug" in lower_labels:
        score += 0.25

    if quality.has_version_info:
        score += 0.20

    if reaction_count >= 5:
        score += 0.50
    elif reaction_count >= 2:
        score += 0.25

    if comment_count > 10:
        score -= 0.50
    elif comment_count > 5:
        score -= 0.25

    if tier == "trusted":
        score += 0.50
    elif tier == "active":
        score += 0.25

    if stars >= 5000:
        score += 0.25

    return round(max(0.0, min(10.0, score)), 2)
