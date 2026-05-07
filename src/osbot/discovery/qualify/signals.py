from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from osbot.log import get_logger
from osbot.types import RepoSignals

logger = get_logger(__name__)

KNOWN_BOT_NAMES: set[str] = {
    "dependabot",
    "renovate",
    "greenkeeper",
    "snyk-bot",
    "imgbot",
    "allcontributors",
    "codecov",
    "netlify",
    "vercel",
    "github-actions",
    "depfu",
    "whitesource-bolt",
    "mend-bolt-for-github",
    "pre-commit-ci",
    "release-drafter",
    "semantic-release-bot",
    "mergify",
    "kodiakhq",
    "stale",
    "copilot",
}


def compute_signals(profile: dict[str, Any]) -> RepoSignals:
    prs = profile.get("pullRequests", {}).get("nodes", [])
    topics_raw = profile.get("repositoryTopics", {}).get("nodes", [])
    topics = [t.get("topic", {}).get("name", "") for t in topics_raw]

    external_count = 0
    merged_external = 0
    has_ci = False
    has_merged_bots = False
    response_hours_sum = 0.0
    response_count = 0
    last_external_merge_days = 999

    now = datetime.now(UTC)

    for pr in prs:
        author_assoc = (pr.get("authorAssociation") or "").upper()
        author_login = (pr.get("author") or {}).get("login", "").lower()

        is_bot = author_login in KNOWN_BOT_NAMES or "[bot]" in author_login
        is_external = author_assoc not in {"OWNER", "MEMBER", "COLLABORATOR"}

        if is_bot:
            has_merged_bots = True
            continue

        if is_external:
            external_count += 1
            merged_at_str = pr.get("mergedAt")
            if merged_at_str:
                merged_external += 1
                try:
                    merged_dt = datetime.fromisoformat(merged_at_str.replace("Z", "+00:00"))
                    days_ago = (now - merged_dt).days
                    if days_ago < last_external_merge_days:
                        last_external_merge_days = days_ago
                except Exception:
                    pass

        commits = pr.get("commits", {}).get("nodes", [])
        for commit_node in commits:
            rollup = commit_node.get("commit", {}).get("statusCheckRollup")
            if rollup and rollup.get("state"):
                has_ci = True

    external_merge_rate = merged_external / max(external_count, 1)

    gfi_count = profile.get("gfiIssues", {}).get("totalCount", 0)
    hw_count = profile.get("helpWantedIssues", {}).get("totalCount", 0)
    bug_count = profile.get("bugIssues", {}).get("totalCount", 0)

    closed_total = profile.get("closedIssues", {}).get("totalCount", 0)
    open_total = profile.get("openIssues", {}).get("totalCount", 0)
    total_issues = closed_total + open_total
    completion_rate = closed_total / max(total_issues, 1)

    funding_links = profile.get("fundingLinks") or []
    has_funding = len(funding_links) > 0

    coc = profile.get("codeOfConduct")
    has_code_of_conduct = coc is not None and coc.get("name") is not None

    license_info = profile.get("licenseInfo") or {}
    license_key = license_info.get("spdxId", "")

    default_branch_ref = profile.get("defaultBranchRef") or {}
    default_branch = default_branch_ref.get("name", "main")

    has_contributing = profile.get("hasContributing") is not None
    has_pr_template = profile.get("hasPrTemplate") is not None

    return RepoSignals(
        external_merge_rate=round(external_merge_rate, 3),
        avg_response_hours=round(response_hours_sum / max(response_count, 1), 1),
        close_completion_rate=round(completion_rate, 3),
        has_ci=has_ci,
        last_external_merge_days=last_external_merge_days,
        has_merged_bots=has_merged_bots,
        ext_pr_count=external_count,
        gfi_issue_count=gfi_count,
        help_wanted_count=hw_count,
        bug_issue_count=bug_count,
        has_funding=has_funding,
        has_code_of_conduct=has_code_of_conduct,
        community_health_pct=0,
        license_key=license_key,
        default_branch=default_branch,
        topics=topics,
        has_contributing=has_contributing,
        has_pr_template=has_pr_template,
    )
