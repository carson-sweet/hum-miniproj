#!/usr/bin/env python3
"""Validate a proposed split into independently useful MiniProjects."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .validate_bundle import validate_bundle
except ImportError:  # Direct execution from the installed skill.
    from validate_bundle import validate_bundle


def validate_split(proposal: dict[str, Any]) -> dict[str, Any]:
    bundles = proposal.get("bundles")
    if not isinstance(bundles, list) or len(bundles) < 2:
        return {
            "schema_version": 1,
            "status": "invalid",
            "independently_launchable": [],
            "findings": [
                {
                    "bundle": None,
                    "criterion": "split",
                    "code": "needs-multiple-bundles",
                    "message": "A split must contain at least two proposed MiniProjects.",
                }
            ],
        }

    findings = []
    ids = []
    independently_launchable = []
    for index, raw_bundle in enumerate(bundles):
        bundle = raw_bundle if isinstance(raw_bundle, dict) else {}
        bundle_id = str(bundle.get("id") or f"bundle-{index + 1}")
        ids.append(bundle_id)
        validation = validate_bundle(bundle)
        for finding in validation["findings"]:
            findings.append({"bundle": bundle_id, **finding})

        dependencies = bundle.get("dependencies")
        if not isinstance(dependencies, list) or not all(
            isinstance(item, str) and item.strip() for item in dependencies
        ):
            findings.append(
                {
                    "bundle": bundle_id,
                    "criterion": "launch_ready",
                    "code": "invalid-dependencies",
                    "message": "State sibling dependencies as a list of bundle ids.",
                }
            )
        elif not dependencies:
            independently_launchable.append(bundle_id)

    duplicates = {bundle_id for bundle_id in ids if ids.count(bundle_id) > 1}
    for bundle_id in sorted(duplicates):
        findings.append(
            {
                "bundle": bundle_id,
                "criterion": "split",
                "code": "duplicate-id",
                "message": "Every resulting MiniProject needs a unique id.",
            }
        )

    known = set(ids)
    for raw_bundle in bundles:
        if not isinstance(raw_bundle, dict):
            continue
        bundle_id = str(raw_bundle.get("id") or "")
        dependencies = raw_bundle.get("dependencies")
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if dependency not in known:
                findings.append(
                    {
                        "bundle": bundle_id,
                        "criterion": "launch_ready",
                        "code": "unknown-dependency",
                        "message": f"Unknown sibling dependency: {dependency}",
                    }
                )

    if not independently_launchable:
        findings.append(
            {
                "bundle": None,
                "criterion": "launch_ready",
                "code": "no-independent-piece",
                "message": "At least one resulting MiniProject must launch without a sibling.",
            }
        )

    return {
        "schema_version": 1,
        "status": "invalid" if findings else "valid",
        "independently_launchable": independently_launchable,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("proposal", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.proposal.read_text())
        if not isinstance(data, dict):
            raise ValueError("split JSON must be an object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"schema_version": 1, "status": "error", "findings": [{"code": "invalid-json", "message": str(exc)}]}, indent=2))
        return 2

    result = validate_split(data)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
