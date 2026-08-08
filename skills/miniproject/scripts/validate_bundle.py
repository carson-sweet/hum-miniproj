#!/usr/bin/env python3
"""Validate that a proposed MiniProject answers all four bundle questions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CRITERIA = {
    "complete": "State what complete improvement will be delivered.",
    "demoable": "State how the improvement will be demonstrated.",
    "owned": "State who will own the work end to end.",
    "launch_ready": "State what will make the improvement safe to launch.",
}


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return structured presence findings without grading any answer."""
    work_type = str(bundle.get("work_type", "")).strip().lower()
    if work_type == "chore":
        return {
            "schema_version": 1,
            "work_type": "chore",
            "status": "bypass",
            "checked": [],
            "findings": [],
            "message": "Chore fast lane: bundle validation not required.",
        }

    if work_type != "miniproject":
        return {
            "schema_version": 1,
            "work_type": work_type or None,
            "status": "error",
            "checked": [],
            "findings": [
                {
                    "criterion": "work_type",
                    "code": "unsupported-work-type",
                    "message": "work_type must be miniproject or chore.",
                }
            ],
        }

    answers = bundle.get("criteria")
    if not isinstance(answers, dict):
        answers = {}

    findings = []
    for criterion, message in CRITERIA.items():
        answer = answers.get(criterion)
        if not isinstance(answer, str) or not answer.strip():
            findings.append(
                {
                    "criterion": criterion,
                    "code": "missing-answer",
                    "message": message,
                }
            )

    return {
        "schema_version": 1,
        "work_type": "miniproject",
        "status": "invalid" if findings else "valid",
        "checked": list(CRITERIA),
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path, help="JSON bundle proposal")
    args = parser.parse_args(argv)

    try:
        data = json.loads(args.bundle.read_text())
        if not isinstance(data, dict):
            raise ValueError("bundle JSON must be an object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {
            "schema_version": 1,
            "work_type": None,
            "status": "error",
            "checked": [],
            "findings": [
                {
                    "criterion": "input",
                    "code": "invalid-json",
                    "message": str(exc),
                }
            ],
        }
        print(json.dumps(result, indent=2))
        return 2

    result = validate_bundle(data)
    print(json.dumps(result, indent=2))
    return {"valid": 0, "bypass": 0, "invalid": 1}.get(result["status"], 2)


if __name__ == "__main__":
    raise SystemExit(main())
