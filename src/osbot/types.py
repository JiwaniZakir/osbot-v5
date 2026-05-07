from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class RepoTier(enum.Enum):
    PROSPECT = "prospect"
    QUALIFIED = "qualified"
    ACTIVE = "active"
    TRUSTED = "trusted"
    DORMANT = "dormant"
    EXCLUDED = "excluded"


class Outcome(enum.Enum):
    MERGED = "merged"
    REJECTED = "rejected"
    IGNORED = "ignored"
    ITERATED_MERGED = "iterated_merged"
    STUCK = "stuck"
    SUBMITTED = "submitted"


class IssueStatus(enum.Enum):
    QUEUED = "queued"
    AWAITING_ASSIGNMENT = "awaiting_assignment"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    DONE = "done"
    REJECTED = "rejected"
    EXPIRED = "expired"


class FeedbackType(enum.Enum):
    REQUEST_CHANGES = "request_changes"
    STYLE_FEEDBACK = "style_feedback"
    QUESTION = "question"
    APPROVAL_PENDING_MINOR = "approval_pending_minor"
    REJECTION_WITH_REASON = "rejection_with_reason"
    CI_FAILURE = "ci_failure"


class Phase(enum.Enum):
    HEALTH_CHECK = "health_check"
    DISCOVER = "discover"
    CONTRIBUTE = "contribute"
    ITERATE = "iterate"
    REVIEW = "review"
    ENGAGE = "engage"
    MONITOR = "monitor"
    FAST_DIAG = "fast_diag"
    LEARN = "learn"
    NOTIFY = "notify"


class Priority(enum.IntEnum):
    FEEDBACK_RESPONSE = 0
    IMPLEMENTER = 1
    PATCH_APPLIER = 2
    PR_WRITER = 3
    CLAIM_COMMENT = 4
    DIAGNOSTIC = 5


@dataclass(frozen=True, slots=True)
class RepoMeta:
    owner: str
    name: str
    language: str
    stars: int
    description: str = ""
    topics: list[str] = field(default_factory=list)
    license_key: str = ""
    has_contributing: bool = False
    has_pr_template: bool = False
    has_code_of_conduct: bool = False
    requires_assignment: bool = False
    has_ai_policy: bool = False
    ci_enabled: bool = False
    external_merge_rate: float = 0.0
    avg_response_hours: float = 0.0
    close_completion_rate: float = 0.0
    last_external_merge_days: int = 999
    has_merged_bots: bool = False
    gfi_issue_count: int = 0
    help_wanted_count: int = 0
    bug_issue_count: int = 0
    community_health_pct: int = 0
    has_funding: bool = False
    score: float = 0.0
    tier: RepoTier = RepoTier.PROSPECT
    default_branch: str = "main"
    last_push_at: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


@dataclass(frozen=True, slots=True)
class IssueQuality:
    has_file_reference: bool = False
    has_reproduction_steps: bool = False
    has_mre: bool = False
    filed_by_maintainer: bool = False
    likely_single_file: bool = False
    is_regression: bool = False
    has_version_info: bool = False


@dataclass(frozen=True, slots=True)
class ScoredIssue:
    repo: str
    number: int
    title: str
    body: str = ""
    labels: list[str] = field(default_factory=list)
    url: str = ""
    score: float = 0.0
    maintainer_confirmed: bool = False
    has_error_trace: bool = False
    has_code_block: bool = False
    requires_assignment: bool = False
    created_at: str = ""
    updated_at: str = ""
    comment_count: int = 0
    reaction_count: int = 0
    quality: IssueQuality = field(default_factory=IssueQuality)


@dataclass(frozen=True, slots=True)
class CLIResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True, slots=True)
class AgentResult:
    success: bool
    text: str
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    tokens_used: int = 0
    model: str = ""


@dataclass(frozen=True, slots=True)
class RepoSignals:
    external_merge_rate: float = 0.0
    avg_response_hours: float = 0.0
    close_completion_rate: float = 0.0
    has_ci: bool = False
    last_external_merge_days: int = 999
    has_merged_bots: bool = False
    ext_pr_count: int = 0
    gfi_issue_count: int = 0
    help_wanted_count: int = 0
    bug_issue_count: int = 0
    has_funding: bool = False
    has_code_of_conduct: bool = False
    community_health_pct: int = 0
    license_key: str = ""
    default_branch: str = "main"
    topics: list[str] = field(default_factory=list)
    has_contributing: bool = False
    has_pr_template: bool = False
    has_ai_policy: bool = False
    requires_assignment: bool = False
    commit_format: str | None = None
    contributing_text: str = ""
    pr_template_text: str = ""


@runtime_checkable
class GitHubCLIProtocol(Protocol):
    async def run_gh(self, args: list[str], cwd: str | None = None) -> CLIResult: ...
    async def run_git(self, args: list[str], cwd: str | None = None) -> CLIResult: ...
    async def run_cmd(self, cmd: list[str], cwd: str | None = None, timeout: float = 60.0) -> CLIResult: ...
    async def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]: ...


@runtime_checkable
class MemoryDBProtocol(Protocol):
    async def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int: ...
    async def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None: ...
    async def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]: ...
    async def fetchval(self, sql: str, params: tuple[Any, ...] = ()) -> Any: ...
    async def get_outcome(self, repo: str, issue_number: int) -> dict[str, Any] | None: ...
    async def is_repo_banned(self, repo: str) -> bool: ...
    async def close(self) -> None: ...
