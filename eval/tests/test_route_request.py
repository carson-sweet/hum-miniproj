import subprocess
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from skills.miniproject.scripts.route_request import (
    format_route_result,
    route_request,
    validate_request_route,
)


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "miniproject" / "scripts" / "route_request.py"


def test_us_req_001_routes_specific_widget_request_to_chore_fast_lane():
    route = route_request(
        "Add the onsite optimization widget to the sales blog",
        shaping_owner="Chelsea",
    )

    assert route["status"] == "routed"
    assert route["classification"] == "chore"
    assert route["lane"] == "fast"
    assert route["discovery_required"] is False
    assert validate_request_route(route)["status"] == "valid"


def test_us_req_001_returns_broad_request_with_named_shaping_step_and_owner():
    route = route_request("Improve onsite optimization", shaping_owner="Chelsea")

    assert route["status"] == "routed"
    assert route["classification"] != "chore"
    assert route["lane"] == "shaping"
    assert route["shaping_step"]
    assert route["owner"] == "Chelsea"
    assert validate_request_route(route)["status"] == "valid"


def test_us_req_001_rejects_silence_on_a_broad_request():
    result = validate_request_route(
        {
            "request": "Improve onsite optimization",
            "status": "routed",
            "classification": "project",
            "lane": "shaping",
        }
    )

    assert result["status"] == "invalid"
    assert {
        (finding["criterion"], finding["code"])
        for finding in result["findings"]
    } == {
        ("shaping_step", "missing-shaping-step"),
        ("owner", "missing-shaping-owner"),
    }


def test_us_req_001_does_not_absorb_specific_request_into_a_project():
    result = validate_request_route(
        {
            "request": "Add the onsite optimization widget to the sales blog",
            "status": "routed",
            "classification": "project",
            "lane": "shaping",
            "shaping_step": "Create Discovery cards",
            "owner": "Chelsea",
        }
    )

    assert result["status"] == "invalid"
    assert result["findings"][0]["code"] == "specific-request-not-fast-lane"


def test_human_result_explains_the_chore_fast_lane():
    route = route_request("Add the onsite optimization widget to the sales blog")

    assert format_route_result(route) == (
        "CHORE — Route this specific request through the fast lane. "
        "Discovery is not required."
    )


def test_human_result_asks_for_the_missing_shaping_owner():
    route = route_request("Improve onsite optimization")

    assert format_route_result(route) == (
        "NEEDS INPUT — Send this broad request to shaping. "
        "Who owns the next shaping step?"
    )


def test_route_cli_can_emit_a_human_readable_deterministic_result():
    completed = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--format",
            "human",
            "Improve onsite optimization",
            "--owner",
            "Chelsea",
        ],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    assert completed.stdout.strip() == (
        "PROJECT — Send this broad request to shaping. Owner: Chelsea. "
        "Next step: Define explicit in/out scope and create ranked Discovery questions."
    )
