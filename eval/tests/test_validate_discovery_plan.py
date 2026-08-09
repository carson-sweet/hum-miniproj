import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True

from skills.miniproject.scripts.validate_discovery_plan import (
    format_discovery_plan_result,
    validate_discovery_plan,
)


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "miniproject" / "scripts" / "validate_discovery_plan.py"


def valid_plan():
    return {
        "project": "Onsite optimization v1",
        "scope": {
            "in": ["Sales-blog widget placement", "Widget performance reporting"],
            "out": ["Site-wide redesign", "Automated content generation"],
        },
        "discovery_cards": [
            {
                "id": "D-1",
                "rank": 1,
                "question": "Which sales-blog templates support widget placement?",
                "owner": "Chelsea",
                "useful_output": "Supported-template inventory",
            },
            {
                "id": "D-2",
                "rank": 2,
                "question": "Which reporting events define a useful widget view?",
                "owner": "Jake",
                "useful_output": "Approved event definition",
            },
        ],
        "engineering_review": {"status": "accepted", "returned_cards": []},
    }


def test_us_val_001_accepts_ranked_owned_discovery_cards_with_useful_outputs():
    result = validate_discovery_plan(valid_plan())

    assert result["status"] == "valid"
    assert result["ranked_cards"] == ["D-1", "D-2"]
    assert result["returned_cards"] == []
    assert result["findings"] == []


def test_us_val_001_rejects_direction_only_scope():
    plan = valid_plan()
    plan["scope"] = "Improve onsite optimization"

    result = validate_discovery_plan(plan)

    assert result["status"] == "invalid"
    assert ("scope", "scope-not-in-out") in {
        (finding["item"], finding["code"]) for finding in result["findings"]
    }
    assert format_discovery_plan_result(result).startswith(
        "INVALID — The deterministic Discovery-plan validator reported 1 finding.\n"
        "- scope / scope:"
    )


def test_us_val_001_rejects_cards_returned_for_rescoping():
    plan = valid_plan()
    plan["engineering_review"] = {
        "status": "changes_requested",
        "returned_cards": ["D-2"],
    }

    result = validate_discovery_plan(plan)

    assert result["status"] == "invalid"
    assert result["returned_cards"] == ["D-2"]
    assert ("engineering_review", "cards-returned") in {
        (finding["item"], finding["code"]) for finding in result["findings"]
    }


def test_us_val_001_requires_one_owner_per_discovery_card():
    plan = valid_plan()
    plan["discovery_cards"][0]["owner"] = "Chelsea and Jake"

    result = validate_discovery_plan(plan)

    assert result["status"] == "invalid"
    assert ("D-1", "one-owner-required") in {
        (finding["item"], finding["code"]) for finding in result["findings"]
    }


def test_human_result_explains_a_valid_discovery_plan():
    result = validate_discovery_plan(valid_plan())

    assert format_discovery_plan_result(result) == (
        "VALID — The Project has explicit in/out scope, 2 ranked Discovery cards, "
        "and Engineering acceptance with no returned cards. "
        "The deterministic validator reported no findings."
    )


def test_human_result_uses_singular_card_for_one_discovery_card():
    plan = valid_plan()
    plan["discovery_cards"] = [plan["discovery_cards"][0]]
    result = validate_discovery_plan(plan)

    assert format_discovery_plan_result(result) == (
        "VALID — The Project has explicit in/out scope, 1 ranked Discovery card, "
        "and Engineering acceptance with no returned cards. "
        "The deterministic validator reported no findings."
    )


def test_discovery_plan_cli_can_emit_a_human_readable_deterministic_result(tmp_path):
    source = tmp_path / "plan.json"
    source.write_text(json.dumps(valid_plan()))

    completed = subprocess.run(
        ["python3", str(SCRIPT), "--format", "human", str(source)],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    assert completed.stdout.strip() == (
        "VALID — The Project has explicit in/out scope, 2 ranked Discovery cards, "
        "and Engineering acceptance with no returned cards. "
        "The deterministic validator reported no findings."
    )
