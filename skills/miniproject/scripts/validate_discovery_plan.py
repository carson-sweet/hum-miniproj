#!/usr/bin/env python3
"""Validate ranked Product Refinement Discovery cards and review outcome."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


FORBIDDEN_CARD_KEYS = {
    "implementation",
    "miniproject",
    "technical_bundle",
    "technical_approach",
}
MULTIPLE_OWNERS = re.compile(r"(?:\s+(?:and|&|\+)\s+|[,/;])", re.IGNORECASE)


def _present(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _one_owner(value: Any) -> bool:
    return _present(value) and not MULTIPLE_OWNERS.search(value)


def _finding(item: str, criterion: str, code: str, message: str) -> dict[str, str]:
    return {"item": item, "criterion": criterion, "code": code, "message": message}


def validate_discovery_plan(plan: dict[str, Any]) -> dict[str, Any]:
    findings = []
    scope = plan.get("scope")
    scope_valid = (
        isinstance(scope, dict)
        and isinstance(scope.get("in"), list)
        and isinstance(scope.get("out"), list)
        and bool(scope["in"])
        and bool(scope["out"])
        and all(_present(item) for item in scope["in"] + scope["out"])
    )
    if not scope_valid:
        findings.append(
            _finding(
                "scope",
                "scope",
                "scope-not-in-out",
                "State v1 scope as non-empty in and out lists, not a direction.",
            )
        )

    cards = plan.get("discovery_cards")
    if not isinstance(cards, list):
        cards = []
    ranked = []
    ranks = []
    for index, raw_card in enumerate(cards):
        card = raw_card if isinstance(raw_card, dict) else {}
        item_id = str(card.get("id") or f"card-{index + 1}")
        rank = card.get("rank")
        if isinstance(rank, int) and rank > 0:
            ranks.append(rank)
            ranked.append((rank, item_id))
        else:
            findings.append(
                _finding(item_id, "rank", "missing-rank", "Give every Discovery card a positive rank.")
            )

        for field, message in (
            ("question", "State the Discovery question."),
            ("owner", "Name the Discovery owner."),
            ("useful_output", "Name the useful output Engineering will receive."),
        ):
            if not _present(card.get(field)):
                findings.append(_finding(item_id, field, f"missing-{field}", message))

        if _present(card.get("owner")) and not _one_owner(card.get("owner")):
            findings.append(
                _finding(
                    item_id,
                    "owner",
                    "one-owner-required",
                    "Name exactly one owner for each Discovery card.",
                )
            )

        if FORBIDDEN_CARD_KEYS.intersection(card):
            findings.append(
                _finding(
                    item_id,
                    "product_engineering_boundary",
                    "technical-bundle-in-discovery",
                    "Discovery cards name questions and outputs, not technical bundles.",
                )
            )

    if ranks and sorted(ranks) != list(range(1, len(cards) + 1)):
        findings.append(
            _finding(
                "discovery_cards",
                "rank",
                "invalid-ranking",
                "Ranks must be unique and contiguous from 1 through the card count.",
            )
        )
    if not cards:
        findings.append(
            _finding(
                "discovery_cards",
                "cards",
                "no-discovery-cards",
                "A shaped Project needs at least one ranked Discovery card.",
            )
        )

    review = plan.get("engineering_review")
    if not isinstance(review, dict):
        review = {}
    returned = review.get("returned_cards")
    returned_cards = returned if isinstance(returned, list) else []
    if review.get("status") != "accepted" or returned_cards:
        findings.append(
            _finding(
                "engineering_review",
                "acceptance",
                "cards-returned",
                "Engineering acceptance requires zero Discovery cards returned for re-scoping.",
            )
        )

    return {
        "schema_version": 1,
        "status": "invalid" if findings else "valid",
        "ranked_cards": [item_id for _, item_id in sorted(ranked)],
        "returned_cards": returned_cards,
        "findings": findings,
    }


def format_discovery_plan_result(result: dict[str, Any]) -> str:
    """Render a Discovery-plan result for a person without adding judgment."""
    if result.get("status") == "valid":
        ranked = result.get("ranked_cards") or []
        noun = "card" if len(ranked) == 1 else "cards"
        return (
            f"VALID — The Project has explicit in/out scope, {len(ranked)} ranked "
            f"Discovery {noun}, and Engineering acceptance with no returned cards. "
            "The deterministic validator reported no findings."
        )

    status = "INVALID" if result.get("status") == "invalid" else "ERROR"
    findings = result.get("findings") if isinstance(result.get("findings"), list) else []
    noun = "finding" if len(findings) == 1 else "findings"
    lines = [f"{status} — The deterministic Discovery-plan validator reported {len(findings)} {noun}."]
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        item = finding.get("item") or "plan"
        criterion = finding.get("criterion") or "input"
        lines.append(f"- {item} / {criterion}: {finding.get('message', 'No detail provided.')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("json", "human"), default="json")
    parser.add_argument("plan", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.plan.read_text())
        if not isinstance(data, dict):
            raise ValueError("Discovery plan JSON must be an object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"schema_version": 1, "status": "error", "findings": [{"code": "invalid-json", "message": str(exc)}]}
        print(format_discovery_plan_result(result) if args.format == "human" else json.dumps(result, indent=2))
        return 2

    result = validate_discovery_plan(data)
    print(format_discovery_plan_result(result) if args.format == "human" else json.dumps(result, indent=2))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
