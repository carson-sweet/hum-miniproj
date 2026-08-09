#!/usr/bin/env python3
"""Validate Tech Refinement and Tech Estimation board artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


IMPLEMENTATION_DETAIL_KEYS = {
    "implementation",
    "implementation_details",
    "prs",
    "pr_sequence",
    "rollout_steps",
    "test_details",
}
ESTIMATE_KEYS = {"effort_estimate", "effort_size", "story_points", "delivery_estimate"}
MULTIPLE_OWNERS = re.compile(r"(?:\s+(?:and|&|\+)\s+|[,/;])", re.IGNORECASE)


def _present(value: Any) -> bool:
    return not (value is None or isinstance(value, str) and not value.strip())


def _one_owner(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not MULTIPLE_OWNERS.search(value)


def _finding(item: str, criterion: str, code: str, message: str) -> dict[str, str]:
    return {"item": item, "criterion": criterion, "code": code, "message": message}


def _validate_refinement(board: dict[str, Any]) -> dict[str, Any]:
    cards = board.get("cards")
    if not isinstance(cards, list):
        cards = []
    findings = []
    unclassified = []

    for index, raw_card in enumerate(cards):
        card = raw_card if isinstance(raw_card, dict) else {}
        item_id = str(card.get("id") or f"card-{index + 1}")
        resolution = card.get("resolution")
        if not isinstance(resolution, dict):
            unclassified.append(item_id)
            findings.append(
                _finding(
                    item_id,
                    "classification",
                    "unclassified",
                    "Resolve the card as a named MiniProject, Chore, or More Discovery.",
                )
            )
            continue

        work_type = str(resolution.get("work_type") or "").strip().lower()
        if work_type not in {"miniproject", "chore", "discovery"}:
            unclassified.append(item_id)
            findings.append(
                _finding(
                    item_id,
                    "classification",
                    "unclassified",
                    "Resolve the card as a named MiniProject, Chore, or More Discovery.",
                )
            )
            continue

        if work_type in {"miniproject", "chore"} and not _present(resolution.get("name")):
            findings.append(
                _finding(item_id, "name", "missing-name", "Name the resolved delivery item.")
            )

        if work_type == "miniproject":
            owner = resolution.get("owner")
            if not _one_owner(owner) or "owners" in resolution:
                findings.append(
                    _finding(
                        item_id,
                        "owner",
                        "one-owner-required",
                        "A MiniProject must name exactly one end-to-end owner.",
                    )
                )

        if work_type == "discovery":
            if str(resolution.get("terminal_outcome") or "").strip().lower() != "more discovery":
                findings.append(
                    _finding(
                        item_id,
                        "terminal_outcome",
                        "more-discovery-required",
                        'Use the terminal outcome "More Discovery" for an unresolved card.',
                    )
                )
            for field, message in (
                ("owner", "Name the owner of the next Discovery."),
                ("next_question", "State the next Discovery question."),
            ):
                if not _present(resolution.get(field)):
                    findings.append(_finding(item_id, field, f"missing-{field}", message))

        if IMPLEMENTATION_DETAIL_KEYS.intersection(resolution):
            findings.append(
                _finding(
                    item_id,
                    "board_boundary",
                    "implementation-detail-on-board",
                    "Keep PR sequence, test detail, and rollout mechanics in the owner's plan.",
                )
            )

    return {
        "schema_version": 1,
        "stage": "tech_refinement",
        "status": "invalid" if findings else "valid",
        "resolved": len(cards) - len(unclassified),
        "unclassified": unclassified,
        "findings": findings,
    }


def _validate_estimation(board: dict[str, Any]) -> dict[str, Any]:
    items = board.get("items")
    if not isinstance(items, list):
        items = []
    findings = []
    for index, raw_item in enumerate(items):
        item = raw_item if isinstance(raw_item, dict) else {}
        item_id = str(item.get("id") or f"item-{index + 1}")
        work_type = str(item.get("work_type") or "").strip().lower()

        if work_type in {"chore", "miniproject"}:
            if not _present(item.get("effort_estimate")):
                findings.append(
                    _finding(
                        item_id,
                        "measure",
                        "missing-effort-estimate",
                        "Chores and MiniProjects leaving estimation need an effort estimate.",
                    )
                )
            continue

        if work_type == "discovery":
            if any(_present(item.get(key)) for key in ESTIMATE_KEYS):
                findings.append(
                    _finding(
                        item_id,
                        "measure",
                        "discovery-estimated",
                        "Discovery uses a time box and target output, never an effort estimate.",
                    )
                )
            if not _present(item.get("time_box")):
                findings.append(
                    _finding(
                        item_id,
                        "measure",
                        "missing-time-box",
                        "Discovery leaving estimation needs a time box.",
                    )
                )
            if not _present(item.get("target_output")):
                findings.append(
                    _finding(
                        item_id,
                        "measure",
                        "missing-target-output",
                        "Discovery leaving estimation needs a target output.",
                    )
                )
            continue

        findings.append(
            _finding(
                item_id,
                "classification",
                "unsupported-work-type",
                "Tech Estimation accepts Chores, MiniProjects, and Discovery items.",
            )
        )

    return {
        "schema_version": 1,
        "stage": "tech_estimation",
        "status": "invalid" if findings else "valid",
        "findings": findings,
    }


def validate_board(board: dict[str, Any]) -> dict[str, Any]:
    stage = str(board.get("stage") or "").strip().lower()
    if stage == "tech_refinement":
        return _validate_refinement(board)
    if stage == "tech_estimation":
        return _validate_estimation(board)
    return {
        "schema_version": 1,
        "stage": stage or None,
        "status": "error",
        "findings": [
            _finding(
                "board",
                "stage",
                "unsupported-stage",
                "stage must be tech_refinement or tech_estimation.",
            )
        ],
    }


def format_board_result(result: dict[str, Any]) -> str:
    """Render a board result for a person without adding judgment."""
    stage = result.get("stage")
    if result.get("status") == "valid":
        if stage == "tech_refinement":
            resolved = int(result.get("resolved") or 0)
            noun = "card" if resolved == 1 else "cards"
            return (
                f"VALID — Tech Refinement resolved {resolved} {noun}. "
                "The deterministic validator reported no findings."
            )
        return (
            "VALID — Tech Estimation satisfies the measurement rules for every item. "
            "The deterministic validator reported no findings."
        )

    status = "INVALID" if result.get("status") == "invalid" else "ERROR"
    label = {
        "tech_refinement": "Tech Refinement",
        "tech_estimation": "Tech Estimation",
    }.get(stage, "Board validation")
    findings = result.get("findings") if isinstance(result.get("findings"), list) else []
    noun = "finding" if len(findings) == 1 else "findings"
    lines = [f"{status} — {label} reported {len(findings)} {noun}."]
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        item = finding.get("item") or "board"
        criterion = finding.get("criterion") or "input"
        lines.append(f"- {item} / {criterion}: {finding.get('message', 'No detail provided.')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("json", "human"), default="json")
    parser.add_argument("board", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.board.read_text())
        if not isinstance(data, dict):
            raise ValueError("board JSON must be an object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"schema_version": 1, "status": "error", "findings": [{"code": "invalid-json", "message": str(exc)}]}
        print(format_board_result(result) if args.format == "human" else json.dumps(result, indent=2))
        return 2

    result = validate_board(data)
    print(format_board_result(result) if args.format == "human" else json.dumps(result, indent=2))
    return {"valid": 0, "invalid": 1}.get(result["status"], 2)


if __name__ == "__main__":
    raise SystemExit(main())
