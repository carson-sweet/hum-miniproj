"""Step 3 gate: an artifact assertion must pass AND fail on a planted fixture.

No model calls. Artifact assertions are deterministic by design — that is the
whole reason they are preferred over judged assertions.
"""
import pytest

from eval.assertions import check_artifact


def plant(tmp_path, name, content):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def test_exists_passes_when_file_planted(tmp_path):
    plant(tmp_path, "bundle.md", "# Bundle\n")
    outcome = check_artifact(tmp_path, {"kind": "exists", "path": "bundle.md"})
    assert outcome.passed
    assert "bundle.md" in outcome.detail


def test_exists_fails_when_file_absent(tmp_path):
    outcome = check_artifact(tmp_path, {"kind": "exists", "path": "bundle.md"})
    assert not outcome.passed


def test_absent_passes_when_file_missing(tmp_path):
    outcome = check_artifact(tmp_path, {"kind": "absent", "path": "leaked.md"})
    assert outcome.passed


def test_absent_fails_when_file_planted(tmp_path):
    plant(tmp_path, "leaked.md", "oops")
    outcome = check_artifact(tmp_path, {"kind": "absent", "path": "leaked.md"})
    assert not outcome.passed


def test_contains_passes_on_match(tmp_path):
    plant(tmp_path, "bundle.md", "# Bundle\n## Owner\nLisa\n")
    outcome = check_artifact(
        tmp_path, {"kind": "contains", "path": "bundle.md", "pattern": r"^## Owner$"}
    )
    assert outcome.passed


def test_contains_fails_when_pattern_missing(tmp_path):
    plant(tmp_path, "bundle.md", "# Bundle\nno owner section\n")
    outcome = check_artifact(
        tmp_path, {"kind": "contains", "path": "bundle.md", "pattern": r"^## Owner$"}
    )
    assert not outcome.passed


def test_contains_fails_when_file_absent(tmp_path):
    outcome = check_artifact(
        tmp_path, {"kind": "contains", "path": "nope.md", "pattern": "anything"}
    )
    assert not outcome.passed
    assert "does not exist" in outcome.detail


def test_min_lines_passes_at_threshold(tmp_path):
    plant(tmp_path, "bundle.md", "a\nb\nc\n")
    outcome = check_artifact(
        tmp_path, {"kind": "min_lines", "path": "bundle.md", "count": 3}
    )
    assert outcome.passed


def test_min_lines_fails_below_threshold(tmp_path):
    plant(tmp_path, "bundle.md", "a\nb\n")
    outcome = check_artifact(
        tmp_path, {"kind": "min_lines", "path": "bundle.md", "count": 3}
    )
    assert not outcome.passed


def test_unknown_kind_raises_rather_than_passing(tmp_path):
    """A trust anchor must not silently green-light a spec it does not understand."""
    with pytest.raises(ValueError, match="unknown assertion kind"):
        check_artifact(tmp_path, {"kind": "vibes", "path": "bundle.md"})


def test_path_escaping_workdir_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="escapes workdir"):
        check_artifact(tmp_path, {"kind": "exists", "path": "../../etc/passwd"})


def test_absolute_path_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="escapes workdir"):
        check_artifact(tmp_path, {"kind": "exists", "path": "/etc/passwd"})
