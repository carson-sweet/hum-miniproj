from pathlib import Path

import pytest

from scripts.lint_portable import lint_skill


REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def portable_skill(tmp_path):
    skill = tmp_path / "miniproject"
    (skill / "references").mkdir(parents=True)
    (skill / "scripts").mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: miniproject\n"
        "description: Portable test skill.\n"
        "---\n\n"
        "Run `python3 scripts/check.py`.\n"
    )
    (skill / "references" / "policy.md").write_text("# Policy\n")
    (skill / "scripts" / "check.py").write_text("print('ok')\n")
    return skill


def codes(violations):
    return {violation.code for violation in violations}


def test_portable_subset_passes(portable_skill):
    assert lint_skill(portable_skill) == []


def test_repository_scaffold_passes():
    assert lint_skill(REPO / "skills" / "miniproject") == []


@pytest.mark.parametrize(
    ("relative_path", "text", "expected_code"),
    [
        ("agents/openai.yaml", "interface: {}\n", "nonportable-path"),
        ("SKILL.md", "! echo bootstrap\n", "bang-preamble"),
        ("SKILL.md", "Run ${CLAUDE_PLUGIN_ROOT}/check.py\n", "plugin-root"),
        ("SKILL.md", "Call AskUserQuestion now.\n", "interactive-tool"),
        ("SKILL.md", "Invoke sweetclaude:status.\n", "cross-skill"),
        ("SKILL.md", "Use $other-skill now.\n", "cross-skill"),
        (
            "references/source.md",
            "SPDX-License-Identifier: GPL-3.0-only\n",
            "incompatible-license",
        ),
        (
            "references/source.md",
            "SPDX-License-Identifier: Apache-2.0 AND GPL-3.0-only\n",
            "incompatible-license",
        ),
        (
            "references/source.md",
            "Copied verbatim from an external source.\n",
            "verbatim-import",
        ),
    ],
)
def test_rejects_nonportable_constructs(
    portable_skill, relative_path, text, expected_code,
):
    target = portable_skill / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if target.exists() else "w"
    with target.open(mode) as handle:
        handle.write(text)

    violations = lint_skill(portable_skill)

    assert expected_code in codes(violations)
    assert any(
        violation.path == relative_path and violation.line >= 1
        for violation in violations
        if violation.code == expected_code
    )


def test_allows_compatible_spdx_identifier(portable_skill):
    (portable_skill / "references" / "source.md").write_text(
        "SPDX-License-Identifier: Apache-2.0\n"
    )
    assert lint_skill(portable_skill) == []


def test_missing_skill_file_is_named(tmp_path):
    violations = lint_skill(tmp_path)
    assert codes(violations) == {"missing-skill-file"}
    assert violations[0].path == "SKILL.md"


def test_symlink_escape_is_rejected(portable_skill, tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text("not part of the skill\n")
    (portable_skill / "references" / "escape.md").symlink_to(outside)

    assert "symlink" in codes(lint_skill(portable_skill))


def test_pull_request_ci_runs_lint_and_deterministic_tests():
    workflow = REPO / ".github" / "workflows" / "ci.yml"
    text = workflow.read_text()

    assert "pull_request:" in text
    assert "python scripts/lint_portable.py" in text
    assert "python -m pytest -m \"not integration\"" in text
