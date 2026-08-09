import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True

from skills.miniproject.scripts.validate_board import format_board_result, validate_board


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "miniproject" / "scripts" / "validate_board.py"


def test_us_fac_001_resolves_every_discovery_card_and_keeps_owner_plans_off_board():
    result = validate_board(
        {
            "stage": "tech_refinement",
            "project": "Account access",
            "cards": [
                {
                    "id": "D-1",
                    "resolution": {
                        "work_type": "miniproject",
                        "name": "Self-service password recovery",
                        "owner": "Alice",
                    },
                },
                {
                    "id": "D-2",
                    "resolution": {
                        "work_type": "miniproject",
                        "name": "Admin-assisted recovery",
                        "owner": "Ben",
                    },
                },
                {
                    "id": "D-3",
                    "resolution": {
                        "work_type": "chore",
                        "name": "Correct the recovery email label",
                    },
                },
                {
                    "id": "D-4",
                    "resolution": {
                        "work_type": "discovery",
                        "terminal_outcome": "More Discovery",
                        "owner": "Chen",
                        "next_question": "Which tenants require delegated recovery?",
                    },
                },
                {
                    "id": "D-5",
                    "resolution": {
                        "work_type": "chore",
                        "name": "Add recovery instructions to support notes",
                    },
                },
            ],
        }
    )

    assert result["status"] == "valid"
    assert result["resolved"] == 5
    assert result["unclassified"] == []
    assert result["findings"] == []


def test_us_fac_001_rejects_unclassified_cards_multiple_owners_and_pr_sequences():
    result = validate_board(
        {
            "stage": "tech_refinement",
            "cards": [
                {"id": "D-1"},
                {
                    "id": "D-2",
                    "resolution": {
                        "work_type": "miniproject",
                        "name": "Recovery",
                        "owners": ["Alice", "Ben"],
                        "pr_sequence": ["API", "UI"],
                    },
                },
            ],
        }
    )

    assert result["status"] == "invalid"
    assert result["unclassified"] == ["D-1"]
    assert {
        (finding["item"], finding["code"])
        for finding in result["findings"]
    } == {
        ("D-1", "unclassified"),
        ("D-2", "one-owner-required"),
        ("D-2", "implementation-detail-on-board"),
    }


def test_us_fac_001_rejects_multiple_owners_hidden_in_one_string():
    result = validate_board(
        {
            "stage": "tech_refinement",
            "cards": [
                {
                    "id": "D-1",
                    "resolution": {
                        "work_type": "miniproject",
                        "name": "Account recovery",
                        "owner": "Alice and Ben",
                    },
                }
            ],
        }
    )

    assert result["status"] == "invalid"
    assert result["findings"][0]["code"] == "one-owner-required"
    assert format_board_result(result) == (
        "INVALID — Tech Refinement reported 1 finding.\n"
        "- D-1 / owner: A MiniProject must name exactly one end-to-end owner."
    )


def test_us_fac_002_accepts_estimates_for_delivery_and_time_box_for_discovery():
    result = validate_board(
        {
            "stage": "tech_estimation",
            "items": [
                {"id": "C-1", "work_type": "chore", "effort_estimate": "1"},
                {
                    "id": "MP-1",
                    "work_type": "miniproject",
                    "effort_estimate": "5",
                },
                {
                    "id": "D-1",
                    "work_type": "discovery",
                    "time_box": "2 days",
                    "target_output": "Tenant mapping decision",
                },
            ],
        }
    )

    assert result["status"] == "valid"
    assert result["findings"] == []


def test_us_fac_002_names_discovery_that_was_given_story_points():
    result = validate_board(
        {
            "stage": "tech_estimation",
            "items": [
                {
                    "id": "D-SSO",
                    "work_type": "discovery",
                    "time_box": "2 days",
                    "target_output": "Tenant mapping decision",
                    "story_points": 3,
                }
            ],
        }
    )

    assert result["status"] == "invalid"
    assert result["findings"] == [
        {
            "item": "D-SSO",
            "criterion": "measure",
            "code": "discovery-estimated",
            "message": "Discovery uses a time box and target output, never an effort estimate.",
        }
    ]


def test_human_result_explains_successful_tech_refinement():
    result = validate_board(
        {
            "stage": "tech_refinement",
            "cards": [
                {
                    "id": "D-1",
                    "resolution": {
                        "work_type": "miniproject",
                        "name": "Self-service password recovery",
                        "owner": "Alice",
                    },
                }
            ],
        }
    )

    assert format_board_result(result) == (
        "VALID — Tech Refinement resolved 1 card. "
        "The deterministic validator reported no findings."
    )


def test_board_cli_can_emit_a_human_readable_deterministic_result(tmp_path):
    source = tmp_path / "board.json"
    source.write_text(
        json.dumps(
            {
                "stage": "tech_estimation",
                "items": [
                    {"id": "C-1", "work_type": "chore", "effort_estimate": "1"},
                    {
                        "id": "D-1",
                        "work_type": "discovery",
                        "time_box": "2 days",
                        "target_output": "Tenant mapping decision",
                    },
                ],
            }
        )
    )

    completed = subprocess.run(
        ["python3", str(SCRIPT), "--format", "human", str(source)],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    assert completed.stdout.strip() == (
        "VALID — Tech Estimation satisfies the measurement rules for every item. "
        "The deterministic validator reported no findings."
    )
