import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True

from skills.miniproject.scripts.validate_split import format_split_result, validate_split


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "miniproject" / "scripts" / "validate_split.py"


def bundle(bundle_id, name, complete, dependencies):
    return {
        "id": bundle_id,
        "work_type": "miniproject",
        "name": name,
        "dependencies": dependencies,
        "criteria": {
            "complete": complete,
            "demoable": f"Demonstrate {name} end to end.",
            "owned": f"One owner carries {name} through release.",
            "launch_ready": f"{name} has verification and rollback coverage.",
        },
    }


def test_us_own_003_accepts_complete_improvement_split_with_an_independent_piece():
    result = validate_split(
        {
            "source": "Account recovery improvements",
            "bundles": [
                bundle(
                    "self-service",
                    "Self-service password recovery",
                    "A locked-out customer can reset a password and sign in.",
                    [],
                ),
                bundle(
                    "admin-help",
                    "Admin-assisted account recovery",
                    "An administrator can restore access for a blocked customer.",
                    ["self-service"],
                ),
            ],
        }
    )

    assert result["status"] == "valid"
    assert result["independently_launchable"] == ["self-service"]
    assert result["findings"] == []


def test_human_result_explains_a_valid_split_and_names_the_independent_piece():
    result = validate_split(
        {
            "source": "Account recovery improvements",
            "bundles": [
                bundle(
                    "self-service",
                    "Self-service password recovery",
                    "A locked-out customer can reset a password and sign in.",
                    [],
                ),
                bundle(
                    "admin-help",
                    "Admin-assisted account recovery",
                    "An administrator can restore access for a blocked customer.",
                    ["self-service"],
                ),
            ],
        }
    )

    assert format_split_result(result) == (
        "VALID — 2 resulting MiniProjects passed validation. "
        "Independently launchable: self-service. The deterministic validator reported no findings."
    )


def test_split_cli_can_emit_a_human_readable_deterministic_result(tmp_path):
    source = tmp_path / "split.json"
    source.write_text(
        json.dumps(
            {
                "source": "Account recovery improvements",
                "bundles": [
                    bundle(
                        "self-service",
                        "Self-service password recovery",
                        "A locked-out customer can reset a password and sign in.",
                        [],
                    ),
                    bundle(
                        "admin-help",
                        "Admin-assisted account recovery",
                        "An administrator can restore access for a blocked customer.",
                        ["self-service"],
                    ),
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
        "VALID — 2 resulting MiniProjects passed validation. "
        "Independently launchable: self-service. The deterministic validator reported no findings."
    )


def test_us_own_003_rejects_a_frontend_backend_split():
    result = validate_split(
        {
            "source": "Widget reporting",
            "bundles": [
                bundle(
                    "frontend",
                    "Frontend work for widget reporting",
                    "Frontend components are implemented.",
                    [],
                ),
                bundle(
                    "backend",
                    "Backend work for widget reporting",
                    "Backend API endpoints are implemented.",
                    [],
                ),
            ],
        }
    )

    assert result["status"] == "invalid"
    assert {
        (finding["bundle"], finding["code"])
        for finding in result["findings"]
    } == {
        ("frontend", "technical-layer-only"),
        ("backend", "technical-layer-only"),
    }

    report = format_split_result(result)
    assert report.startswith("INVALID — The deterministic split validator reported 2 findings.")
    assert "- frontend / complete:" in report
    assert "- backend / complete:" in report
