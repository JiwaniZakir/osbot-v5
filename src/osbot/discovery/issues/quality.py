from __future__ import annotations

import re

from osbot.log import get_logger
from osbot.types import IssueQuality

logger = get_logger(__name__)

FILE_REF_PATTERN = re.compile(
    r"(?:[\w/\\]+\.(?:py|ts|js|tsx|jsx|rs|go|java|rb|c|cpp|h|yaml|yml|json|toml|cfg|ini|md))"
    r"|(?:`[^`]+\.(py|ts|js|tsx|jsx|rs|go)`)"
)

REPRODUCTION_PATTERN = re.compile(
    r"(?:steps?\s+to\s+reproduce|how\s+to\s+reproduce|reproduction\s+steps|repro\s+steps"
    r"|to\s+reproduce|reproduce\s+the\s+(?:bug|issue|error|problem))",
    re.IGNORECASE,
)

MRE_PATTERN = re.compile(
    r"(?:minimal\s+(?:reproducible\s+)?example|MRE|MCVE|minimal\s+repro"
    r"|minimal\s+reproduction|short\s+example|simple\s+example)",
    re.IGNORECASE,
)

REGRESSION_PATTERN = re.compile(
    r"(?:regression|worked\s+(?:before|previously|in\s+v?\d)|broke\s+(?:in|after|since)"
    r"|used\s+to\s+work|no\s+longer\s+works|stopped\s+working)",
    re.IGNORECASE,
)

VERSION_PATTERN = re.compile(
    r"(?:v?\d+\.\d+(?:\.\d+)?(?:-[\w.]+)?)"
    r"|(?:version\s*[:=]?\s*\d+)"
    r"|(?:python\s*\d+\.\d+)"
    r"|(?:node\s*(?:v|version)?\s*\d+)",
    re.IGNORECASE,
)

SINGLE_FILE_PATTERN = re.compile(
    r"(?:single\s+file|one\s+file|only\s+(?:one|1)\s+file|just\s+(?:change|modify|edit|update)\s+\w+\.(?:py|ts|js))"
    r"|(?:fix\s+in\s+\w+\.(?:py|ts|js|tsx|jsx))",
    re.IGNORECASE,
)

MAINTAINER_ASSOCIATIONS: set[str] = {"OWNER", "MEMBER", "COLLABORATOR"}


def assess_quality(body: str, author_association: str = "", labels: list[str] | None = None) -> IssueQuality:
    if not body:
        return IssueQuality()

    has_file_reference = bool(FILE_REF_PATTERN.search(body))
    has_reproduction_steps = bool(REPRODUCTION_PATTERN.search(body))
    has_mre = bool(MRE_PATTERN.search(body))
    filed_by_maintainer = author_association.upper() in MAINTAINER_ASSOCIATIONS
    likely_single_file = bool(SINGLE_FILE_PATTERN.search(body))
    is_regression = bool(REGRESSION_PATTERN.search(body))
    has_version_info = bool(VERSION_PATTERN.search(body))

    return IssueQuality(
        has_file_reference=has_file_reference,
        has_reproduction_steps=has_reproduction_steps,
        has_mre=has_mre,
        filed_by_maintainer=filed_by_maintainer,
        likely_single_file=likely_single_file,
        is_regression=is_regression,
        has_version_info=has_version_info,
    )
