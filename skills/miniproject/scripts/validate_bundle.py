#!/usr/bin/env python3
"""Validate that a proposed MiniProject answers all four bundle questions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


CRITERIA = {
    "complete": "State what complete improvement will be delivered.",
    "demoable": "State how the improvement will be demonstrated.",
    "owned": "State who will own the work end to end.",
    "launch_ready": "State what will make the improvement safe to launch.",
}

TECHNICAL_LAYER_ONLY = re.compile(
    r"(?:^|\b)(?:only\s+)?(?:the\s+)?"
    r"(?:frontend|backend|api|database|data(?:\s+layer)?|infrastructure|qa|testing?)"
    r"\s+(?:work|changes?|tasks?|endpoints?|components?|migration|layer)(?:\b|$)",
    re.IGNORECASE,
)


def is_technical_layer_only(bundle: dict[str, Any], complete_answer: str) -> bool:
    """Detect an explicit technical-layer boundary without grading answer quality."""
    name = str(bundle.get("name") or "")
    return bool(TECHNICAL_LAYER_ONLY.search(name) or TECHNICAL_LAYER_ONLY.search(complete_answer))


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

    complete_answer = answers.get("complete")
    if (
        isinstance(complete_answer, str)
        and complete_answer.strip()
        and is_technical_layer_only(bundle, complete_answer)
    ):
        findings.append(
            {
                "criterion": "complete",
                "code": "technical-layer-only",
                "message": (
                    "Name a complete behavior or operational improvement, not a "
                    "frontend, backend, data, infrastructure, testing, or other "
                    "technical-layer slice."
                ),
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
