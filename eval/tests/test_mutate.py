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


# --- verdict aggregation across repeated runs (pure, no model calls) ---

from eval.run_contracts import classify  # noqa: E402


def test_negative_control_needs_the_floor_to_count_as_detecting():
    assert classify(["DETECTED"] * 4 + ["BROKEN"], negative=True) == ("DETECTED", "4/5")


def test_negative_control_below_floor_is_broken():
    assert classify(["DETECTED"] * 3 + ["BROKEN"] * 2, negative=True) == ("BROKEN", "3/5")


def test_mp_c01_actual_result_scores_broken():
    """The real MP-C01 sequence from the P0.2 spike: 2 of 5."""
    v = ["DETECTED", "BROKEN", "BROKEN", "BROKEN", "DETECTED"]
    assert classify(v, negative=True) == ("BROKEN", "2/5")


def test_normal_mode_requires_every_run_to_pass():
    assert classify(["PASS", "PASS"], negative=False) == ("PASS", "2/2")
    assert classify(["PASS", "FAIL"], negative=False) == ("FAIL", "1/2")


def test_any_inert_mutation_poisons_the_whole_result():
    assert classify(["DETECTED", "MUTATION-INERT"], negative=True)[0] == "MUTATION-INERT"


def test_no_runs_is_not_a_silent_pass():
    assert classify([], negative=True)[0] == "NO-RUNS"
