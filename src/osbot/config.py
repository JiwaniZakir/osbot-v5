from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "OSBOT_", "frozen": True}

    @model_validator(mode="after")
    def _validate(self) -> Settings:
        if self.max_workers < 1:
            msg = f"max_workers={self.max_workers} must be >= 1"
            raise ValueError(msg)
        return self

    state_dir: Path = Path("state")
    workspaces_dir: Path = Path("workspaces")
    claude_binary: str = "claude"

    @property
    def db_path(self) -> Path:
        return self.state_dir / "memory.db"

    cycle_interval_sec: int = 600
    discover_interval_sec: int = 1800
    engage_interval_sec: int = 7200
    review_interval_sec: int = 14400
    learn_interval_sec: int = 43200

    max_workers: int = 5

    five_hour_ceiling: float = 0.60
    seven_day_ceiling: float = 0.50
    timezone: str = "US/Eastern"

    allowed_languages: list[str] = Field(default=["Python", "TypeScript"])
    interest_areas: list[dict] = Field(
        default=[
            {
                "name": "ai-agents",
                "topics": ["ai", "agent", "llm", "langchain", "autogen", "crewai"],
                "description_queries": ["ai agent", "llm framework", "autonomous agent"],
                "readme_keywords": ["agent", "llm"],
                "packages": ["langchain", "autogen", "crewai", "openai"],
                "weight": 1.0,
            },
            {
                "name": "ml-infra",
                "topics": ["ml", "machine-learning", "deep-learning", "transformer"],
                "description_queries": ["machine learning", "ml pipeline", "model serving"],
                "readme_keywords": ["transformer", "pytorch"],
                "packages": ["torch", "transformers", "scikit-learn"],
                "weight": 0.8,
            },
            {
                "name": "rag-embeddings",
                "topics": ["rag", "embeddings", "vector", "vector-database"],
                "description_queries": ["vector database", "retrieval augmented"],
                "readme_keywords": ["rag", "embedding"],
                "packages": ["chromadb", "pinecone", "qdrant"],
                "weight": 0.7,
            },
            {
                "name": "nlp-tools",
                "topics": ["nlp", "gpt", "openai", "anthropic"],
                "description_queries": ["natural language", "text processing"],
                "readme_keywords": ["nlp", "tokenizer"],
                "packages": ["spacy", "nltk", "tiktoken"],
                "weight": 0.6,
            },
        ]
    )

    search_budget_topic: int = 8
    search_budget_description: int = 4
    search_budget_readme: int = 3
    search_budget_dependency: int = 3

    repo_min_stars: int = 200
    repo_max_stars: int = 30000
    repo_max_push_age_days: int = 30
    active_pool_max: int = 100
    repo_score_threshold: float = 4.0
    issues_per_repo: int = 5
    max_queue_size: int = 30

    signal_cache_ttl_days: int = 7
    benchmark_staleness_days: int = 30

    maintainer_confirmed_bonus: float = 1.50
    issue_base_score: float = 5.0

    implementation_timeout_sec: float = 600.0
    pr_writer_timeout_sec: float = 60.0
    feedback_reader_timeout_sec: float = 60.0
    patch_applier_timeout_sec: float = 120.0

    max_diff_lines: int = 80
    max_files_changed: int = 3
    max_commit_message_len: int = 100
    min_commit_message_len: int = 10

    max_iteration_rounds: int = 3
    assignment_timeout_hours: int = 72

    implementation_model: str = "sonnet"
    pr_writer_model: str = "sonnet"
    feedback_reader_model: str = "sonnet"
    patch_applier_model: str = "sonnet"

    github_username: str = ""
    webhook_url: str = ""

    max_daily_prs: int = 5
    max_daily_engagements: int = 6
    max_daily_reviews: int = 3
    quiet_hours_start: int = 2
    quiet_hours_end: int = 6
    weekend_activity_ratio: float = 0.5
    cycle_jitter_sec: int = 120


settings = Settings()
