#!/usr/bin/env python3
"""Create a reversible instruction diff without applying it."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import sys
from pathlib import Path

from improvement_common import ImprovementError, file_sha256, load_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--pattern-id", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--instruction", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        analysis = load_json(args.analysis, label="analysis")
        matches = [
            pattern
            for pattern in analysis.get("patterns", [])
            if isinstance(pattern, dict) and pattern.get("pattern_id") == args.pattern_id
        ]
        if len(matches) != 1:
            raise ImprovementError("analysis must contain exactly one matching pattern")
        pattern = matches[0]
        if pattern.get("target") != args.target:
            raise ImprovementError("proposal target does not match the selected pattern")
        before = args.instruction.read_text(encoding="utf-8")
        after = args.candidate.read_text(encoding="utf-8")
        if before == after:
            raise ImprovementError("candidate is identical to the current instruction")
    except (ImprovementError, OSError) as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2

    base_sha = file_sha256(args.instruction)
    candidate_sha = file_sha256(args.candidate)
    diff = "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=args.target,
            tofile=f"{args.target}.candidate",
        )
    )
    reverse_diff = "".join(
        difflib.unified_diff(
            after.splitlines(keepends=True),
            before.splitlines(keepends=True),
            fromfile=f"{args.target}.candidate",
            tofile=args.target,
        )
    )
    identity = f"{args.pattern_id}\0{args.target}\0{base_sha}\0{candidate_sha}"
    proposal = {
        "schema_version": 1,
        "proposal_id": f"proposal-{hashlib.sha256(identity.encode()).hexdigest()[:16]}",
        "status": "proposed",
        "analysis_sha256": file_sha256(args.analysis),
        "pattern_id": args.pattern_id,
        "target": args.target,
        "entry_ids": pattern.get("entry_ids", []),
        "base_sha256": base_sha,
        "candidate_sha256": candidate_sha,
        "diff": diff,
        "reverse_diff": reverse_diff,
    }
    write_json(args.output, proposal)
    print(f"PROPOSED {proposal['proposal_id']}; no instruction file was changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
