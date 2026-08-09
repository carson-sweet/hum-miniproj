#!/usr/bin/env python3
"""Bind a proposed instruction version to targeted and held-out contract scores."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from improvement_common import ImprovementError, load_json, parse_score, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--version-id", required=True)
    parser.add_argument("--targeted-before", required=True)
    parser.add_argument("--targeted-after", required=True)
    parser.add_argument("--held-out-before", required=True)
    parser.add_argument("--held-out-after", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        proposal = load_json(args.proposal, label="proposal")
        if proposal.get("status") != "proposed":
            raise ImprovementError("proposal is not in proposed state")
        scores = {
            "targeted": {
                "before": parse_score(args.targeted_before),
                "after": parse_score(args.targeted_after),
            },
            "held_out": {
                "before": parse_score(args.held_out_before),
                "after": parse_score(args.held_out_after),
            },
        }
    except ImprovementError as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2
    version = {
        "schema_version": 1,
        "version_id": args.version_id,
        "proposal_id": proposal["proposal_id"],
        "target": proposal["target"],
        "content_sha256": proposal["candidate_sha256"],
        "previous_content_sha256": proposal["base_sha256"],
        "scores": scores,
    }
    write_json(args.output, version)
    print(f"RECORDED instruction version {args.version_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
