"""Mutations must be deterministic and must report when they changed nothing.

A mutation that matched nothing proves nothing. If the runner scored such a
contract it would report a green negative control for a rule it never removed —
the exact false confidence the negative-control mode exists to prevent.
"""
import pytest

from eval.mutate import apply_mutation

SKILL = """---
name: mp-rules
---

RULE-EST: Never estimate a Discovery item.

RULE-BUNDLE: A partial technical layer is not a MiniProject.
"""


@pytest.fixture
def skill_dir(tmp_path):
    (tmp_path / "SKILL.md").write_text(SKILL)
    return tmp_path


def test_delete_lines_matching_removes_the_rule(skill_dir):
    result = apply_mutation(
        skill_dir,
        {"file": "SKILL.md", "op": "delete_lines_matching", "pattern": r"^RULE-EST:"},
    )
    assert result.applied
    assert result.matched == 1
    body = (skill_dir / "SKILL.md").read_text()
    assert "RULE-EST" not in body
    assert "RULE-BUNDLE" in body, "must not remove unrelated rules"


def test_delete_lines_matching_reports_inert_when_nothing_matches(skill_dir):
    result = apply_mutation(
        skill_dir,
        {"file": "SKILL.md", "op": "delete_lines_matching", "pattern": r"^RULE-NOPE:"},
    )
    assert not result.applied
    assert result.matched == 0
    assert (skill_dir / "SKILL.md").read_text() == SKILL, "inert mutation must not edit"


def test_replace_substitutes_text(skill_dir):
    result = apply_mutation(
        skill_dir,
        {"file": "SKILL.md", "op": "replace", "pattern": "Never estimate", "value": "Always estimate"},
    )
    assert result.applied and result.matched == 1
    assert "Always estimate" in (skill_dir / "SKILL.md").read_text()


def test_replace_is_inert_when_pattern_absent(skill_dir):
    result = apply_mutation(
        skill_dir,
        {"file": "SKILL.md", "op": "replace", "pattern": "nonexistent", "value": "x"},
    )
    assert not result.applied
    assert (skill_dir / "SKILL.md").read_text() == SKILL


def test_delete_file_removes_it(skill_dir):
    (skill_dir / "scripts").mkdir()
    (skill_dir / "scripts" / "run.py").write_text("print()")
    result = apply_mutation(skill_dir, {"file": "scripts/run.py", "op": "delete_file"})
    assert result.applied
    assert not (skill_dir / "scripts" / "run.py").exists()


def test_delete_file_is_inert_when_already_absent(skill_dir):
    result = apply_mutation(skill_dir, {"file": "scripts/gone.py", "op": "delete_file"})
    assert not result.applied


def test_truncate_after_drops_the_tail(skill_dir):
    result = apply_mutation(
        skill_dir,
        {"file": "SKILL.md", "op": "truncate_after", "pattern": r"^RULE-EST:"},
    )
    assert result.applied
    body = (skill_dir / "SKILL.md").read_text()
    assert "RULE-EST" in body
    assert "RULE-BUNDLE" not in body


def test_unknown_op_raises(skill_dir):
    with pytest.raises(ValueError, match="unknown mutation op"):
        apply_mutation(skill_dir, {"file": "SKILL.md", "op": "vibes"})


def test_path_escape_is_rejected(skill_dir):
    with pytest.raises(ValueError, match="escapes skill dir"):
        apply_mutation(
            skill_dir,
            {"file": "../../etc/passwd", "op": "delete_lines_matching", "pattern": "x"},
        )


def test_missing_target_file_is_inert_not_crash(skill_dir):
    result = apply_mutation(
        skill_dir,
        {"file": "references/absent.md", "op": "delete_lines_matching", "pattern": "x"},
    )
    assert not result.applied
    assert "does not exist" in result.detail
