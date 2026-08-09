from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "miniproject"
REFERENCES = {
    "work-types.md",
    "bundling-criteria.md",
    "decision-points.md",
    "estimation-policy.md",
    "workflows.md",
}

SCRIPTS = {
    "validate_bundle.py",
    "validate_split.py",
    "validate_board.py",
    "validate_discovery_plan.py",
    "route_request.py",
}


def test_skill_contains_the_four_planned_reference_documents():
    actual = {path.name for path in (SKILL / "references").glob("*.md")}
    assert actual == REFERENCES


def test_skill_routes_to_every_reference_and_validator():
    text = (SKILL / "SKILL.md").read_text()

    for name in REFERENCES:
        assert f"references/{name}" in text
    for name in SCRIPTS:
        assert f"scripts/{name}" in text


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
    for name in SCRIPTS:
        assert (SKILL / "scripts" / name).stat().st_mode & 0o111


def test_skill_routes_each_user_persona_to_executable_workflow():
    text = " ".join((SKILL / "SKILL.md").read_text().lower().split())
    for required in (
        "validate a proposed bundle",
        "validate a proposed split",
        "close tech refinement",
        "check tech estimation",
        "shape a broad project",
        "route a work request",
    ):
        assert required in text


def test_discovery_rule_forbids_points_even_beside_a_time_box():
    text = (SKILL / "references" / "estimation-policy.md").read_text().lower()
    assert "story points" in text
    assert "alongside a time box" in text


def test_discovery_uses_only_the_canonical_terminal_labels():
    text = " ".join((SKILL / "SKILL.md").read_text().lower().split())
    assert "use exactly one terminal label" in text
    assert "ready to shape, more discovery, or stop" in text
    assert "do not invent a synonym such as inconclusive" in text


def test_contributors_do_not_own_technical_slices_inside_one_miniproject():
    text = " ".join(
        (SKILL / "references" / "bundling-criteria.md").read_text().lower().split()
    )
    assert "contributors" in text
    assert "do not own technical-layer slices" in text


def test_skill_uses_contributor_labels_under_parallel_staffing():
    text = " ".join((SKILL / "SKILL.md").read_text().lower().split())
    assert "label every other participant as a contributor" in text
    assert "never assign contributors ownership" in text


def test_skill_reserves_accountability_for_the_end_to_end_owner():
    text = " ".join((SKILL / "SKILL.md").read_text().lower().split())
    assert "use accountable only for the one end-to-end owner" in text
    assert "do not call a specialist accountable for a technical slice" in text


def test_skill_requires_human_readable_validator_reports():
    text = " ".join((SKILL / "SKILL.md").read_text().lower().split())
    assert "--format human" in text
    assert "do not paste raw json as the user-facing result" in text
