from __future__ import annotations

from osbot.discovery.issues.quality import assess_quality


class TestIssueQuality:
    def test_file_reference_python(self) -> None:
        body = "The bug is in src/utils/parser.py where the regex fails"
        quality = assess_quality(body)
        assert quality.has_file_reference is True

    def test_file_reference_typescript(self) -> None:
        body = "Check `components/Modal.tsx` for the rendering issue"
        quality = assess_quality(body)
        assert quality.has_file_reference is True

    def test_file_reference_backtick(self) -> None:
        body = "The error originates from `lib/auth.ts`"
        quality = assess_quality(body)
        assert quality.has_file_reference is True

    def test_no_file_reference(self) -> None:
        body = "The application crashes when I click the button"
        quality = assess_quality(body)
        assert quality.has_file_reference is False

    def test_reproduction_steps(self) -> None:
        body = "Steps to reproduce:\n1. Open the app\n2. Click submit\n3. See error"
        quality = assess_quality(body)
        assert quality.has_reproduction_steps is True

    def test_reproduction_how_to(self) -> None:
        body = "How to reproduce: run `python main.py` with debug flag"
        quality = assess_quality(body)
        assert quality.has_reproduction_steps is True

    def test_no_reproduction(self) -> None:
        body = "It just doesn't work anymore"
        quality = assess_quality(body)
        assert quality.has_reproduction_steps is False

    def test_mre_detected(self) -> None:
        body = "Minimal reproducible example:\n```python\nimport foo\nfoo.bar()\n```"
        quality = assess_quality(body)
        assert quality.has_mre is True

    def test_mcve_detected(self) -> None:
        body = "Here is the MCVE showing the issue"
        quality = assess_quality(body)
        assert quality.has_mre is True

    def test_no_mre(self) -> None:
        body = "See the logs attached for details"
        quality = assess_quality(body)
        assert quality.has_mre is False

    def test_maintainer_filed(self) -> None:
        quality = assess_quality("Fix needed in the parser", author_association="MEMBER")
        assert quality.filed_by_maintainer is True

    def test_owner_filed(self) -> None:
        quality = assess_quality("This needs fixing", author_association="OWNER")
        assert quality.filed_by_maintainer is True

    def test_not_maintainer(self) -> None:
        quality = assess_quality("Found a bug", author_association="NONE")
        assert quality.filed_by_maintainer is False

    def test_regression_detected(self) -> None:
        body = "This is a regression from v2.3.0, it worked before the update"
        quality = assess_quality(body)
        assert quality.is_regression is True

    def test_regression_worked_previously(self) -> None:
        body = "This worked previously in version 1.0 but broke in 2.0"
        quality = assess_quality(body)
        assert quality.is_regression is True

    def test_regression_stopped_working(self) -> None:
        body = "The feature stopped working after the last release"
        quality = assess_quality(body)
        assert quality.is_regression is True

    def test_no_regression(self) -> None:
        body = "New feature request for the dashboard"
        quality = assess_quality(body)
        assert quality.is_regression is False

    def test_version_info(self) -> None:
        body = "I'm running version 3.2.1 on Python 3.12"
        quality = assess_quality(body)
        assert quality.has_version_info is True

    def test_version_with_v_prefix(self) -> None:
        body = "Using v4.0.0-beta.1 of the library"
        quality = assess_quality(body)
        assert quality.has_version_info is True

    def test_no_version_info(self) -> None:
        body = "The button doesn't work"
        quality = assess_quality(body)
        assert quality.has_version_info is False

    def test_single_file_fix(self) -> None:
        body = "This is a simple fix in utils.py, just change the return type"
        quality = assess_quality(body)
        assert quality.likely_single_file is True

    def test_not_single_file(self) -> None:
        body = "This requires changes across multiple modules"
        quality = assess_quality(body)
        assert quality.likely_single_file is False

    def test_empty_body(self) -> None:
        quality = assess_quality("")
        assert quality.has_file_reference is False
        assert quality.has_reproduction_steps is False
        assert quality.has_mre is False
        assert quality.filed_by_maintainer is False
        assert quality.likely_single_file is False
        assert quality.is_regression is False
        assert quality.has_version_info is False

    def test_complex_issue_body(self) -> None:
        body = """
        Bug Report

        Steps to reproduce:
        1. Install v2.1.0
        2. Run the CLI
        3. Check output

        The error is in src/cli/handler.py line 42.
        This is a regression - it worked before in v2.0.0.
        Minimal reproducible example:
        ```python
        from mylib import handler
        handler.run()
        ```
        """
        quality = assess_quality(body, author_association="OWNER")
        assert quality.has_file_reference is True
        assert quality.has_reproduction_steps is True
        assert quality.has_mre is True
        assert quality.filed_by_maintainer is True
        assert quality.is_regression is True
        assert quality.has_version_info is True
