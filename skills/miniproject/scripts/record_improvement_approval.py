#!/usr/bin/env python3
"""Record a human decision bound to one exact improvement proposal."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from improvement_common import ImprovementError, file_sha256, load_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--decision", choices=("approved", "rejected"), required=True)
    parser.add_argument("--approved-by", required=True)
    parser.add_argument("--human-confirmed", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.human_confirmed:
        print(
            "refusing: explicit human approval or rejection is required before recording a decision",
            file=sys.stderr,
        )
        return 2
    if not args.approved_by.strip():
        print("refusing: --approved-by must name the human decision owner", file=sys.stderr)
        return 2
    try:
        proposal = load_json(args.proposal, label="proposal")
        if proposal.get("status") != "proposed" or not proposal.get("proposal_id"):
            raise ImprovementError("proposal is not in proposed state")
    except ImprovementError as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2
    approval = {
        "schema_version": 1,
        "proposal_id": proposal["proposal_id"],
        "proposal_sha256": file_sha256(args.proposal),
        "decision": args.decision,
        "approved_by": args.approved_by.strip(),
        "human_confirmed": True,
        "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    write_json(args.output, approval)
    print(f"RECORDED {args.decision} decision for {proposal['proposal_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
