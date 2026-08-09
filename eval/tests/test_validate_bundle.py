import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
from skills.miniproject.scripts.validate_bundle import (
    format_bundle_result,
    validate_bundle,
)


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "miniproject" / "scripts" / "validate_bundle.py"


def complete_bundle(*, name="Recover a locked account", **overrides):
    criteria = {
        "complete": "Delivers the customer-visible account recovery flow.",
        "demoable": "Demo recovery from request through successful sign-in.",
        "owned": "One owner carries behavior, tests, and rollout.",
        "launch_ready": "Includes monitoring, rollback, and release checks.",
    }
    criteria.update(overrides)
    return {
        "work_type": "miniproject",
        "name": name,
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
        "complete",
        "demoable",
        "owned",
        "launch_ready",
    }
    assert {finding["code"] for finding in result["findings"]} == {
        "missing-answer",
        "technical-layer-only",
    }


def test_us_own_002_rejects_backend_only_even_when_every_answer_is_present():
    result = validate_bundle(
        complete_bundle(
            name="Backend API changes for widget reporting",
            complete="Backend endpoints are implemented.",
            demoable="The API responses can be inspected.",
            owned="Ben owns the API work.",
            launch_ready="The endpoints have tests.",
        )
    )

    assert result["status"] == "invalid"
    assert {
        (finding["criterion"], finding["code"])
        for finding in result["findings"]
    } == {("complete", "technical-layer-only")}


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


def test_human_result_explains_a_valid_presence_only_result():
    result = validate_bundle(
        complete_bundle(
            complete="no",
            demoable="not yet",
            owned="unknown",
            launch_ready="blocked",
        )
    )

    assert format_bundle_result(result) == (
        "VALID — All four required MiniProject criteria have stated answers. "
        "The deterministic validator reported no findings. Answer quality was not assessed."
    )


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


def test_cli_can_emit_a_human_readable_deterministic_result(tmp_path):
    source = tmp_path / "bundle.json"
    source.write_text(
        json.dumps(
            complete_bundle(
                complete="no",
                demoable="not yet",
                owned="unknown",
                launch_ready="blocked",
            )
        )
    )

    completed = subprocess.run(
        ["python3", str(SCRIPT), "--format", "human", str(source)],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    assert completed.stdout.strip() == (
        "VALID — All four required MiniProject criteria have stated answers. "
        "The deterministic validator reported no findings. Answer quality was not assessed."
    )
