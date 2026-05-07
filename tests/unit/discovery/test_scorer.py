from __future__ import annotations

from osbot.discovery.issues.scorer import score_issue
from osbot.discovery.qualify.scorer import score_repo
from osbot.types import IssueQuality, RepoMeta, RepoSignals


class TestRepoScorer:
    def test_high_merge_rate_high_score(self) -> None:
        meta = RepoMeta(owner="org", name="repo", language="Python", stars=5000)
        signals = RepoSignals(
            external_merge_rate=0.7,
            last_external_merge_days=10,
            has_merged_bots=True,
            has_ci=True,
            avg_response_hours=12.0,
            close_completion_rate=0.8,
        )
        score = score_repo(meta, signals)
        assert score >= 8.0
        assert score <= 10.0

    def test_low_merge_rate_low_score(self) -> None:
        meta = RepoMeta(owner="org", name="repo", language="Python", stars=300)
        signals = RepoSignals(
            external_merge_rate=0.02,
            last_external_merge_days=200,
            avg_response_hours=200.0,
            close_completion_rate=0.1,
        )
        score = score_repo(meta, signals)
        assert score <= 3.0

    def test_ai_policy_returns_negative(self) -> None:
        meta = RepoMeta(owner="org", name="repo", language="Python", stars=1000)
        signals = RepoSignals(has_ai_policy=True)
        score = score_repo(meta, signals)
        assert score == -1.0

    def test_medium_merge_rate(self) -> None:
        meta = RepoMeta(owner="org", name="repo", language="Python", stars=800)
        signals = RepoSignals(
            external_merge_rate=0.45,
            last_external_merge_days=25,
            has_ci=True,
            close_completion_rate=0.5,
        )
        score = score_repo(meta, signals)
        assert 5.0 <= score <= 9.0

    def test_score_bounded(self) -> None:
        meta = RepoMeta(owner="org", name="repo", language="Python", stars=10000)
        signals = RepoSignals(
            external_merge_rate=0.9,
            last_external_merge_days=1,
            has_merged_bots=True,
            has_ci=True,
            avg_response_hours=6.0,
            close_completion_rate=0.95,
        )
        score = score_repo(meta, signals)
        assert score <= 10.0

    def test_zero_merge_rate(self) -> None:
        meta = RepoMeta(owner="org", name="repo", language="Python", stars=500)
        signals = RepoSignals(external_merge_rate=0.0)
        score = score_repo(meta, signals)
        assert score < 5.0


class TestIssueScorer:
    def test_base_score(self) -> None:
        quality = IssueQuality()
        score = score_issue(labels=[], quality=quality)
        assert score == 5.0

    def test_maintainer_filed_bonus(self) -> None:
        quality = IssueQuality(filed_by_maintainer=True)
        score = score_issue(labels=[], quality=quality)
        assert score == 6.0

    def test_file_reference_bonus(self) -> None:
        quality = IssueQuality(has_file_reference=True)
        score = score_issue(labels=[], quality=quality)
        assert score == 5.75

    def test_single_file_bonus(self) -> None:
        quality = IssueQuality(likely_single_file=True)
        score = score_issue(labels=[], quality=quality)
        assert score == 5.6

    def test_reproduction_bonus(self) -> None:
        quality = IssueQuality(has_reproduction_steps=True)
        score = score_issue(labels=[], quality=quality)
        assert score == 5.5

    def test_regression_bonus(self) -> None:
        quality = IssueQuality(is_regression=True)
        score = score_issue(labels=[], quality=quality)
        assert score == 5.5

    def test_mre_bonus(self) -> None:
        quality = IssueQuality(has_mre=True)
        score = score_issue(labels=[], quality=quality)
        assert score == 5.4

    def test_gfi_label_bonus(self) -> None:
        quality = IssueQuality()
        score = score_issue(labels=["good first issue"], quality=quality)
        assert score == 5.75

    def test_help_wanted_bonus(self) -> None:
        quality = IssueQuality()
        score = score_issue(labels=["help wanted"], quality=quality)
        assert score == 5.5

    def test_bug_label_bonus(self) -> None:
        quality = IssueQuality()
        score = score_issue(labels=["bug"], quality=quality)
        assert score == 5.25

    def test_all_quality_signals(self) -> None:
        quality = IssueQuality(
            has_file_reference=True,
            has_reproduction_steps=True,
            has_mre=True,
            filed_by_maintainer=True,
            likely_single_file=True,
            is_regression=True,
            has_version_info=True,
        )
        score = score_issue(
            labels=["good first issue", "help wanted", "bug"],
            quality=quality,
            stars=10000,
            reaction_count=10,
            tier="trusted",
        )
        assert score >= 8.0
        assert score <= 10.0

    def test_high_comment_penalty(self) -> None:
        quality = IssueQuality()
        score = score_issue(labels=[], quality=quality, comment_count=15)
        assert score < 5.0

    def test_trusted_tier_bonus(self) -> None:
        quality = IssueQuality()
        score = score_issue(labels=[], quality=quality, tier="trusted")
        assert score == 5.5

    def test_reactions_bonus(self) -> None:
        quality = IssueQuality()
        score = score_issue(labels=[], quality=quality, reaction_count=6)
        assert score == 5.5

    def test_score_bounded(self) -> None:
        quality = IssueQuality(
            has_file_reference=True,
            has_reproduction_steps=True,
            has_mre=True,
            filed_by_maintainer=True,
            likely_single_file=True,
            is_regression=True,
            has_version_info=True,
        )
        score = score_issue(
            labels=["good first issue", "help wanted", "bug"],
            quality=quality,
            stars=20000,
            reaction_count=100,
            tier="trusted",
        )
        assert score <= 10.0
        assert score >= 0.0
