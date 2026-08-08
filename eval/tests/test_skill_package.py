from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "miniproject"
REFERENCES = {
    "work-types.md",
    "bundling-criteria.md",
    "decision-points.md",
    "estimation-policy.md",
}


def test_skill_contains_the_four_planned_reference_documents():
    actual = {path.name for path in (SKILL / "references").glob("*.md")}
    assert actual == REFERENCES


def test_skill_routes_to_every_reference_and_validator():
    text = (SKILL / "SKILL.md").read_text()

    for name in REFERENCES:
        assert f"references/{name}" in text
    assert "scripts/validate_bundle.py" in text


def test_trigger_description_covers_board_work_and_small_fixes():
    frontmatter = (SKILL / "SKILL.md").read_text().split("---", 2)[1].lower()

    for trigger in ("what kind of work", "board", "bug", "typo"):
        assert trigger in frontmatter


def test_discovery_reference_carries_the_approved_contract():
    text = (SKILL / "references" / "work-types.md").read_text().lower()

    for required in (
        "question",
        "owner",
        "time box",
        "decision artifact",
        "ready to shape",
        "more discovery",
        "stop",
    ):
        assert required in text


def test_chore_bypass_is_an_explicit_skill_rule():
    text = (SKILL / "SKILL.md").read_text().lower()
    assert "chore fast lane" in text
    assert "do not run bundle validation" in text


def test_validator_is_executable():
    validator = SKILL / "scripts" / "validate_bundle.py"
    assert validator.stat().st_mode & 0o111
