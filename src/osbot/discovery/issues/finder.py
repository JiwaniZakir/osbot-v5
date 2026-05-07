from __future__ import annotations

import asyncio
import json
import random
from typing import TYPE_CHECKING, Any

from osbot.config import settings
from osbot.discovery.issues.quality import assess_quality
from osbot.discovery.issues.scorer import score_issue
from osbot.log import get_logger
from osbot.types import GitHubCLIProtocol, IssueQuality, MemoryDBProtocol, ScoredIssue

if TYPE_CHECKING:
    from osbot.intel.graphql import GraphQLClient

logger = get_logger(__name__)


async def find_issues(
    gh: GitHubCLIProtocol,
    gql: GraphQLClient,
    db: MemoryDBProtocol,
    repos: list[dict[str, Any]],
) -> list[ScoredIssue]:
    semaphore = asyncio.Semaphore(5)
    tasks = [_fetch_repo_issues(gh, gql, db, repo, semaphore) for repo in repos]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_issues: list[ScoredIssue] = []
    for result in results:
        if isinstance(result, BaseException):
            logger.warning("issue_fetch_error", error=str(result))
            continue
        all_issues.extend(result)

    all_issues.sort(key=lambda i: i.score, reverse=True)
    logger.info("find_issues_complete", total=len(all_issues))
    return all_issues


async def _fetch_repo_issues(
    gh: GitHubCLIProtocol,
    gql: GraphQLClient,
    db: MemoryDBProtocol,
    repo: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> list[ScoredIssue]:
    async with semaphore:
        full_name = repo["full_name"]

        if await db.is_repo_banned(full_name):
            return []

        parts = full_name.split("/")
        if len(parts) != 2:
            return []
        owner, name = parts

        label_queries = ["good first issue", "help wanted", "bug"]
        issues_raw: list[dict[str, Any]] = []

        for label in label_queries:
            args = [
                "issue",
                "list",
                "-R",
                full_name,
                "--label",
                label,
                "--state",
                "open",
                "--limit",
                str(settings.issues_per_repo),
                "--json",
                "number,title,body,labels,url,createdAt,updatedAt,comments,reactionGroups",
            ]
            result = await gh.run_gh(args)
            if result.success:
                try:
                    items = json.loads(result.stdout)
                    issues_raw.extend(items)
                except Exception:
                    pass

        seen_numbers: set[int] = set()
        scored: list[ScoredIssue] = []

        for issue_data in issues_raw:
            number = issue_data.get("number", 0)
            if number in seen_numbers or number == 0:
                continue
            seen_numbers.add(number)

            existing_outcome = await db.get_outcome(full_name, number)
            if existing_outcome is not None:
                continue

            body = issue_data.get("body", "") or ""
            labels = [lb.get("name", "") for lb in (issue_data.get("labels") or [])]
            comment_count = len(issue_data.get("comments", []))

            quality = assess_quality(body)
            prescore = _prescore(quality, labels)
            if prescore < 2.0:
                continue

            jitter = random.uniform(0.3, 1.2)
            await asyncio.sleep(jitter)

            detail = await gql.issue_detail(owner, name, number)
            author_assoc = detail.get("authorAssociation", "")
            if detail:
                body = detail.get("body", body) or body
                labels = [lb.get("name", "") for lb in (detail.get("labels", {}).get("nodes") or [])]
                comment_count = detail.get("comments", {}).get("totalCount", comment_count)

            quality = assess_quality(body, author_assoc, labels)

            reaction_count = 0
            reaction_groups = issue_data.get("reactionGroups") or []
            for rg in reaction_groups:
                reaction_count += rg.get("users", {}).get("totalCount", 0)
            if detail:
                reaction_count = max(reaction_count, detail.get("reactions", {}).get("totalCount", 0))

            issue_score = score_issue(
                labels=labels,
                quality=quality,
                stars=repo.get("stars", 0),
                comment_count=comment_count,
                reaction_count=reaction_count,
                tier=repo.get("tier", "prospect"),
            )

            scored.append(
                ScoredIssue(
                    repo=full_name,
                    number=number,
                    title=issue_data.get("title", ""),
                    body=body[:2000],
                    labels=labels,
                    url=issue_data.get("url", ""),
                    score=issue_score,
                    quality=quality,
                    created_at=issue_data.get("createdAt", ""),
                    updated_at=issue_data.get("updatedAt", ""),
                    comment_count=comment_count,
                    reaction_count=reaction_count,
                )
            )

        return scored


def _prescore(quality: IssueQuality, labels: list[str]) -> float:
    score = 3.0
    if quality.has_file_reference:
        score += 1.0
    if quality.has_reproduction_steps:
        score += 0.5
    if any(lb in {"good first issue", "help wanted"} for lb in labels):
        score += 1.0
    return score
