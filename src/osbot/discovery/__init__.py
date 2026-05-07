from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from osbot.config import settings
from osbot.discovery.feedback import record_discovery
from osbot.discovery.issues.finder import find_issues
from osbot.discovery.qualify.scorer import score_repo
from osbot.discovery.qualify.signals import compute_signals
from osbot.discovery.qualify.tiers import update_repo_tier
from osbot.discovery.search.dependency_search import dependency_search
from osbot.discovery.search.description_search import description_search
from osbot.discovery.search.readme_search import readme_search
from osbot.discovery.search.topic_search import topic_search
from osbot.intel.graphql import GraphQLClient
from osbot.log import get_logger
from osbot.safety.domain import is_in_domain
from osbot.types import GitHubCLIProtocol, MemoryDBProtocol, RepoMeta, RepoTier, ScoredIssue

logger = get_logger(__name__)


async def discover(
    gh: GitHubCLIProtocol,
    db: MemoryDBProtocol,
) -> list[ScoredIssue]:
    gql = GraphQLClient(gh)

    logger.info("discovery_start")

    topic_repos = await topic_search(gh)
    desc_repos = await description_search(gh)
    readme_repos = await readme_search(gh)
    dep_repos = await dependency_search(gh)

    all_repos: list[dict[str, Any]] = []
    seen: set[str] = set()
    for batch in [topic_repos, desc_repos, readme_repos, dep_repos]:
        for repo in batch:
            fn = repo["full_name"]
            if fn not in seen:
                seen.add(fn)
                all_repos.append(repo)

    logger.info("discovery_raw_repos", total=len(all_repos))

    qualified: list[dict[str, Any]] = []
    for repo_data in all_repos:
        full_name = repo_data["full_name"]
        language = repo_data.get("language", "")
        stars = repo_data.get("stars", 0)

        if stars < settings.repo_min_stars or stars > settings.repo_max_stars:
            continue

        if not is_in_domain(language, []):
            continue

        existing = await db.fetchone("SELECT * FROM repo_registry WHERE full_name = ?", (full_name,))
        if existing and existing["tier"] == RepoTier.EXCLUDED.value:
            continue

        parts = full_name.split("/")
        if len(parts) != 2:
            continue
        owner, name = parts

        profile = await gql.repo_profile(owner, name)
        if not profile:
            continue

        signals = compute_signals(profile)

        meta = RepoMeta(
            owner=owner,
            name=name,
            language=language,
            stars=stars,
            description=repo_data.get("description", ""),
            topics=signals.topics,
            license_key=signals.license_key,
            has_contributing=signals.has_contributing,
            has_pr_template=signals.has_pr_template,
            has_code_of_conduct=signals.has_code_of_conduct,
            has_ai_policy=signals.has_ai_policy,
            ci_enabled=signals.has_ci,
            external_merge_rate=signals.external_merge_rate,
            avg_response_hours=signals.avg_response_hours,
            close_completion_rate=signals.close_completion_rate,
            last_external_merge_days=signals.last_external_merge_days,
            has_merged_bots=signals.has_merged_bots,
            gfi_issue_count=signals.gfi_issue_count,
            help_wanted_count=signals.help_wanted_count,
            bug_issue_count=signals.bug_issue_count,
            has_funding=signals.has_funding,
            default_branch=signals.default_branch,
        )

        repo_score = score_repo(meta, signals)

        now = datetime.now(UTC).isoformat()
        await db.execute(
            """
            INSERT INTO repo_registry (
                full_name, owner, name, language, stars, description, topics,
                license_key, tier, score, has_contributing, has_pr_template,
                has_code_of_conduct, has_ai_policy, requires_assignment, ci_enabled,
                external_merge_rate, avg_response_hours, close_completion_rate,
                last_external_merge_days, has_merged_bots, gfi_issue_count,
                help_wanted_count, bug_issue_count, has_funding, default_branch,
                signals_updated_at, discovered_at, discovery_source
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(full_name) DO UPDATE SET
                score = excluded.score,
                signals_updated_at = excluded.signals_updated_at,
                external_merge_rate = excluded.external_merge_rate,
                avg_response_hours = excluded.avg_response_hours,
                close_completion_rate = excluded.close_completion_rate,
                last_external_merge_days = excluded.last_external_merge_days,
                has_merged_bots = excluded.has_merged_bots,
                ci_enabled = excluded.ci_enabled
            """,
            (
                full_name,
                owner,
                name,
                language,
                stars,
                repo_data.get("description", ""),
                str(signals.topics),
                signals.license_key,
                RepoTier.PROSPECT.value,
                repo_score,
                int(signals.has_contributing),
                int(signals.has_pr_template),
                int(signals.has_code_of_conduct),
                int(signals.has_ai_policy),
                int(signals.requires_assignment),
                int(signals.has_ci),
                signals.external_merge_rate,
                signals.avg_response_hours,
                signals.close_completion_rate,
                signals.last_external_merge_days,
                int(signals.has_merged_bots),
                signals.gfi_issue_count,
                signals.help_wanted_count,
                signals.bug_issue_count,
                int(signals.has_funding),
                signals.default_branch,
                now,
                now,
                repo_data.get("discovery_source", ""),
            ),
        )

        signals_dict = {
            "last_external_merge_days": signals.last_external_merge_days,
            "external_merge_rate": signals.external_merge_rate,
        }
        new_tier = await update_repo_tier(db, full_name, repo_score, signals_dict)

        if new_tier in {RepoTier.QUALIFIED, RepoTier.ACTIVE, RepoTier.TRUSTED}:
            qualified.append(
                {
                    "full_name": full_name,
                    "owner": owner,
                    "name": name,
                    "stars": stars,
                    "tier": new_tier.value,
                    "score": repo_score,
                }
            )

    logger.info("discovery_qualified", count=len(qualified))

    await record_discovery(
        db,
        strategy="full_cycle",
        repos_found=len(all_repos),
        repos_qualified=len(qualified),
    )

    pool = await db.fetchall(
        "SELECT * FROM repo_registry WHERE tier IN (?, ?, ?) ORDER BY score DESC LIMIT ?",
        (RepoTier.QUALIFIED.value, RepoTier.ACTIVE.value, RepoTier.TRUSTED.value, settings.active_pool_max),
    )

    issues = await find_issues(gh, gql, db, pool)

    await record_discovery(
        db,
        strategy="full_cycle",
        repos_found=len(all_repos),
        repos_qualified=len(qualified),
        issues_found=len(issues),
    )

    logger.info("discovery_complete", issues=len(issues), qualified_repos=len(qualified))
    return issues[: settings.max_queue_size]
