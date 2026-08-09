import sys

sys.dont_write_bytecode = True

from skills.miniproject.scripts.validate_discovery_plan import validate_discovery_plan


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
