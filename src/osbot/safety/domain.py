from __future__ import annotations

import re

from osbot.config import settings
from osbot.log import get_logger

logger = get_logger(__name__)

AI_POLICY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"no\s+(?:ai|llm|bot|automated)\s+(?:contributions?|pull\s+requests?|prs?|submissions?)", re.IGNORECASE),
    re.compile(
        r"(?:ai|llm|bot|automated)\s+(?:contributions?\s+)?(?:are\s+)?not\s+(?:accepted|welcome|allowed)", re.IGNORECASE
    ),
    re.compile(r"do\s+not\s+(?:submit|send|open)\s+(?:ai|llm|bot|automated)", re.IGNORECASE),
    re.compile(
        r"(?:ban|prohibit|forbid|reject)\w*\s+(?:ai|llm|bot|automated)\s+(?:generated|created|written)", re.IGNORECASE
    ),
    re.compile(r"human[\s-]+only\s+contributions?", re.IGNORECASE),
    re.compile(
        r"(?:ai|llm|copilot|chatgpt)[\s-]+generated\s+(?:code\s+)?(?:will\s+be\s+)?(?:rejected|closed|ignored)",
        re.IGNORECASE,
    ),
]


def is_in_domain(language: str, topics: list[str]) -> bool:
    if not language:
        return False

    lang_match = language.lower() in [lang.lower() for lang in settings.allowed_languages]
    if not lang_match:
        return False

    all_topics: set[str] = set()
    for area in settings.interest_areas:
        for topic in area.get("topics", []):
            all_topics.add(topic.lower())

    if not topics:
        return lang_match

    topic_match = any(t.lower() in all_topics for t in topics)
    return lang_match and topic_match


def has_ai_policy(text: str) -> bool:
    if not text:
        return False
    for pattern in AI_POLICY_PATTERNS:
        if pattern.search(text):
            logger.info("ai_policy_detected", pattern=pattern.pattern[:60])
            return True
    return False
