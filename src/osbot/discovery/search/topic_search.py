from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING, Any

from osbot.config import settings
from osbot.log import get_logger

if TYPE_CHECKING:
    from osbot.types import CLIResult, GitHubCLIProtocol

logger = get_logger(__name__)


def _build_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for lang in settings.allowed_languages:
        for area in settings.interest_areas:
            for topic in area.get("topics", []):
                combos.append((lang, topic))
    return combos


async def topic_search(gh: GitHubCLIProtocol) -> list[dict[str, Any]]:
    combos = _build_combos()
    random.shuffle(combos)
    budget = settings.search_budget_topic
    combos = combos[:budget]

    repos: list[dict[str, Any]] = []
    sorts = ["stars", "updated", "best-match"]

    for i, (lang, topic) in enumerate(combos):
        query = f"topic:{topic} language:{lang} archived:false fork:false stars:>={settings.repo_min_stars}"
        sort_key = sorts[i % len(sorts)]
        limit = random.choice([20, 30, 40])

        args = [
            "search",
            "repos",
            query,
            "--sort",
            sort_key,
            "--limit",
            str(limit),
            "--json",
            "fullName,description,stargazersCount,primaryLanguage,updatedAt",
        ]
        result: CLIResult = await gh.run_gh(args)
        if result.success:
            try:
                import json

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
                                "discovery_source": f"topic:{topic}",
                            }
                        )
            except Exception:
                logger.warning("topic_search_parse_error", topic=topic, lang=lang)

        delay = random.uniform(2.0, 4.5)
        logger.debug("topic_search_delay", delay=round(delay, 1), topic=topic, lang=lang)
        await asyncio.sleep(delay)

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for r in repos:
        if r["full_name"] not in seen:
            seen.add(r["full_name"])
            deduped.append(r)
    logger.info("topic_search_complete", total=len(deduped))
    return deduped
