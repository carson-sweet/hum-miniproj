#!/usr/bin/env python3
"""Fail closed unless an improvement cycle is approved, bound, and non-regressing."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from improvement_common import (
    ImprovementError,
    file_sha256,
    load_json,
    validate_score,
    write_json,
)


def finding(criterion: str, code: str, message: str) -> dict[str, str]:
    return {"criterion": criterion, "code": code, "message": message}


def resolve_artifact(root: Path, reference: object, *, label: str) -> Path:
    if not isinstance(reference, str) or not reference.strip():
        raise ImprovementError(f"{label} reference is missing")
    candidate = (root / reference).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        raise ImprovementError(f"{label} path escapes the cycle directory") from None
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        cycle = load_json(args.cycle, label="cycle")
    except ImprovementError as exc:
        write_json(
            args.output,
            {
                "schema_version": 1,
                "status": "invalid",
                "checked": [],
                "findings": [finding("cycle", "invalid-cycle", str(exc))],
            },
        )
        print(f"INVALID — {exc}", file=sys.stderr)
        return 2

    root = args.cycle.resolve().parent
    findings: list[dict[str, str]] = []
    checked = ["proposal", "approval", "contract", "scores", "instruction_version"]

    artifacts: dict[str, tuple[Path, dict] | None] = {}
    for label in ("proposal", "approval", "contract", "instruction_version"):
        try:
            path = resolve_artifact(root, cycle.get(label), label=label)
            if label == "contract":
                value = load_json(path, label=label)
            else:
                value = load_json(path, label=label)
            artifacts[label] = (path, value)
        except ImprovementError as exc:
            findings.append(finding(label, f"missing-or-invalid-{label}", str(exc)))
            artifacts[label] = None

    proposal_item = artifacts["proposal"]
    approval_item = artifacts["approval"]
    if proposal_item:
        proposal_path, proposal = proposal_item
        if proposal.get("status") != "proposed" or not proposal.get("diff") or not proposal.get("reverse_diff"):
            findings.append(
                finding("proposal", "invalid-proposal", "proposal must contain forward and reverse diffs")
            )
    else:
        proposal_path, proposal = None, {}

    if approval_item and proposal_item:
        _, approval = approval_item
        if (
            approval.get("decision") != "approved"
            or approval.get("human_confirmed") is not True
            or not approval.get("approved_by")
            or approval.get("proposal_id") != proposal.get("proposal_id")
            or approval.get("proposal_sha256") != file_sha256(proposal_path)
        ):
            findings.append(
                finding(
                    "approval",
                    "approval-mismatch",
                    "a human-approved decision must bind to the exact proposal",
                )
            )

    contract_item = artifacts["contract"]
    if contract_item:
        _, contract = contract_item
        negative = contract.get("negative_control")
        if not isinstance(negative, dict) or not negative.get("mutate"):
            findings.append(
                finding("contract", "negative-control-required", "target contract lacks a mutation")
            )
        assertion = contract.get("assert")
        if cycle.get("production_outcome") is True and (
            not isinstance(assertion, dict) or assertion.get("type") != "artifact"
        ):
            findings.append(
                finding(
                    "contract",
                    "artifact-contract-required",
                    "production outcomes require an artifact assertion",
                )
            )

    scores = cycle.get("scores")
    score_rates: dict[str, dict[str, float]] = {}
    try:
        if not isinstance(scores, dict) or set(scores) != {"targeted", "held_out"}:
            raise ImprovementError("scores must contain targeted and held_out")
        for group in ("targeted", "held_out"):
            pair = scores[group]
            if not isinstance(pair, dict) or set(pair) != {"before", "after"}:
                raise ImprovementError(f"{group} scores must contain before and after")
            score_rates[group] = {
                "before": validate_score(pair["before"], label=f"{group}.before"),
                "after": validate_score(pair["after"], label=f"{group}.after"),
            }
        if score_rates["targeted"]["after"] <= score_rates["targeted"]["before"]:
            findings.append(
                finding("scores", "target-not-improved", "targeted contract score did not improve")
            )
        if score_rates["held_out"]["after"] < score_rates["held_out"]["before"]:
            findings.append(
                finding("scores", "held-out-regression", "held-out contract score regressed")
            )
    except ImprovementError as exc:
        findings.append(finding("scores", "invalid-scores", str(exc)))

    version_item = artifacts["instruction_version"]
    if version_item and proposal_item:
        _, version = version_item
        if (
            not version.get("version_id")
            or version.get("target") != proposal.get("target")
            or version.get("content_sha256") != proposal.get("candidate_sha256")
            or version.get("previous_content_sha256") != proposal.get("base_sha256")
            or version.get("scores") != scores
        ):
            findings.append(
                finding(
                    "instruction_version",
                    "version-hash-mismatch",
                    "instruction version is not bound to the reversible proposal and cycle scores",
                )
            )

    verdict = {
        "schema_version": 1,
        "cycle_id": cycle.get("cycle_id"),
        "status": "valid" if not findings else "invalid",
        "checked": checked,
        "findings": findings,
    }
    write_json(args.output, verdict)
    if findings:
        print(f"INVALID — {len(findings)} improvement-cycle finding(s)", file=sys.stderr)
        return 1
    print("VALID — approved improvement increased the target score without held-out regression")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
