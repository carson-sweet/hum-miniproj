import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
from skills.miniproject.scripts.validate_bundle import validate_bundle


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "miniproject" / "scripts" / "validate_bundle.py"


def complete_bundle(**overrides):
    criteria = {
        "complete": "Delivers the customer-visible account recovery flow.",
        "demoable": "Demo recovery from request through successful sign-in.",
        "owned": "One owner carries behavior, tests, and rollout.",
        "launch_ready": "Includes monitoring, rollback, and release checks.",
    }
    criteria.update(overrides)
    return {
        "work_type": "miniproject",
        "name": "Recover a locked account",
        "criteria": criteria,
    }


def test_rejects_partial_technical_layer_with_missing_answers():
    result = validate_bundle(
        {
            "work_type": "miniproject",
            "name": "Build recovery API endpoints",
            "criteria": {"complete": "Backend endpoints are implemented."},
        }
    )

    assert result["status"] == "invalid"
    assert result["checked"] == [
        "complete",
        "demoable",
        "owned",
        "launch_ready",
    ]
    assert {finding["criterion"] for finding in result["findings"]} == {
        "demoable",
        "owned",
        "launch_ready",
    }
    assert {finding["code"] for finding in result["findings"]} == {"missing-answer"}


def test_accepts_complete_improvement_with_all_four_answers():
    result = validate_bundle(complete_bundle())

    assert result["status"] == "valid"
    assert result["findings"] == []


def test_checks_presence_without_grading_the_answer():
    result = validate_bundle(
        complete_bundle(
            complete="no",
            demoable="not yet",
            owned="unknown",
            launch_ready="blocked",
        )
    )

    assert result["status"] == "valid"
    assert result["findings"] == []


def test_blank_answer_is_missing():
    result = validate_bundle(complete_bundle(demoable="   "))

    assert result["status"] == "invalid"
    assert result["findings"] == [
        {
            "criterion": "demoable",
            "code": "missing-answer",
            "message": "State how the improvement will be demonstrated.",
        }
    ]


def test_chore_bypasses_bundle_validation():
    result = validate_bundle(
        {"work_type": "chore", "name": "Correct a label typo"}
    )

    assert result == {
        "schema_version": 1,
        "work_type": "chore",
        "status": "bypass",
        "checked": [],
        "findings": [],
        "message": "Chore fast lane: bundle validation not required.",
    }


def test_unknown_work_type_is_an_input_error():
    result = validate_bundle({"work_type": "project", "name": "Account security"})

    assert result["status"] == "error"
    assert result["findings"][0]["code"] == "unsupported-work-type"


def test_cli_emits_json_and_fails_for_invalid_bundle(tmp_path):
    source = tmp_path / "bundle.json"
    source.write_text(
        json.dumps(
            {
                "work_type": "miniproject",
                "criteria": {"complete": "Only the database migration."},
            }
        )
    )

    completed = subprocess.run(
        ["python3", str(SCRIPT), str(source)],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 1
    assert json.loads(completed.stdout)["status"] == "invalid"
