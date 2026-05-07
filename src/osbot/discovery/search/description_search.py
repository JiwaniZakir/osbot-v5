from __future__ import annotations

import asyncio
import json
import random
from typing import TYPE_CHECKING, Any

from osbot.config import settings
from osbot.log import get_logger

if TYPE_CHECKING:
    from osbot.types import CLIResult, GitHubCLIProtocol

logger = get_logger(__name__)


def _build_queries() -> list[tuple[str, str]]:
    queries: list[tuple[str, str]] = []
    for lang in settings.allowed_languages:
        for area in settings.interest_areas:
            for phrase in area.get("description_queries", []):
                queries.append((lang, phrase))
    return queries


async def description_search(gh: GitHubCLIProtocol) -> list[dict[str, Any]]:
    queries = _build_queries()
    random.shuffle(queries)
    budget = settings.search_budget_description
    queries = queries[:budget]

    repos: list[dict[str, Any]] = []

    for lang, phrase in queries:
        query = f'"{phrase}" language:{lang} archived:false fork:false stars:>={settings.repo_min_stars}'
        args = [
            "search",
            "repos",
            query,
            "--sort",
            "stars",
            "--limit",
            "20",
            "--json",
            "fullName,description,stargazersCount,primaryLanguage,updatedAt",
        ]
        result: CLIResult = await gh.run_gh(args)
        if result.success:
            try:
                items = json.loads(result.stdout)
                for item in items:
                    full_name = item.get("fullName", "")
                    if full_name and "/" in full_name:
                        repos.append(
                            {
                                "full_name": full_name,
                                "description": item.get("description", ""),
                                "stars": item.get("stargazersCount", 0),
                                "language": (item.get("primaryLanguage") or {}).get("name", ""),
                                "discovery_source": f"description:{phrase}",
                            }
                        )
            except Exception:
                logger.warning("description_search_parse_error", phrase=phrase)

        delay = random.uniform(2.0, 4.5)
        await asyncio.sleep(delay)

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for r in repos:
        if r["full_name"] not in seen:
            seen.add(r["full_name"])
            deduped.append(r)
    logger.info("description_search_complete", total=len(deduped))
    return deduped
