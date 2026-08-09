#!/usr/bin/env python3
"""Route bounded work requests to the fast lane and broad asks to shaping."""
from __future__ import annotations

import argparse
import json
import re
from typing import Any


BROAD_REQUEST = re.compile(
    r"^\s*(?:improve|enhance|optimize|modernize|rethink|revamp)\b",
    re.IGNORECASE,
)
SPECIFIC_REQUEST = re.compile(
    r"^\s*(?:add|correct|fix|rename|remove|update|change)\b",
    re.IGNORECASE,
)


def _present(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_specific_request(request: str) -> bool:
    return bool(SPECIFIC_REQUEST.search(request)) and not BROAD_REQUEST.search(request)


def route_request(request: str, *, shaping_owner: str | None = None) -> dict[str, Any]:
    if is_specific_request(request):
        return {
            "schema_version": 1,
            "request": request,
            "status": "routed",
            "classification": "chore",
            "lane": "fast",
            "discovery_required": False,
        }

    route = {
        "schema_version": 1,
        "request": request,
        "status": "routed" if _present(shaping_owner) else "needs-input",
        "classification": "project",
        "lane": "shaping",
        "shaping_step": "Define explicit in/out scope and create ranked Discovery questions.",
    }
    if _present(shaping_owner):
        route["owner"] = shaping_owner.strip()
    else:
        route["question"] = "Who owns the next shaping step?"
    return route


def validate_request_route(route: dict[str, Any]) -> dict[str, Any]:
    request = str(route.get("request") or "")
    findings = []
    if is_specific_request(request):
        if (
            str(route.get("classification") or "").lower() != "chore"
            or str(route.get("lane") or "").lower() != "fast"
            or route.get("discovery_required") is not False
        ):
            findings.append(
                {
                    "criterion": "classification",
                    "code": "specific-request-not-fast-lane",
                    "message": "A specific bounded request must be a Chore in the fast lane without Discovery.",
                }
            )
    else:
        if str(route.get("classification") or "").lower() == "chore":
            findings.append(
                {
                    "criterion": "classification",
                    "code": "broad-request-as-chore",
                    "message": "A broad request needs Project or Discovery shaping, not the Chore fast lane.",
                }
            )
        if not _present(route.get("shaping_step")):
            findings.append(
                {
                    "criterion": "shaping_step",
                    "code": "missing-shaping-step",
                    "message": "Return a broad request with a named shaping step.",
                }
            )
        if not _present(route.get("owner")):
            findings.append(
                {
                    "criterion": "owner",
                    "code": "missing-shaping-owner",
                    "message": "Return a broad request with an owner for the shaping step.",
                }
            )

    return {
        "schema_version": 1,
        "status": "invalid" if findings else "valid",
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request")
    parser.add_argument("--owner")
    args = parser.parse_args(argv)
    route = route_request(args.request, shaping_owner=args.owner)
    print(json.dumps(route, indent=2))
    return 0 if route["status"] == "routed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
