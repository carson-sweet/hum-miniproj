#!/usr/bin/env python3
"""The only writer to the improvement register. Schema-validated.

Phase 4 deliverable, pulled forward because P0.3 cannot measure capture without it.
"""
import argparse
import json
import sys
import time
from pathlib import Path

TYPES = ("correction", "confirmation", "preference", "pattern")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--register", default="register.jsonl")
    ap.add_argument("--type", required=True, choices=TYPES)
    ap.add_argument("--learning", required=True)
    ap.add_argument("--harness", default="unknown")
    ap.add_argument("--skill", default="unknown")
    ap.add_argument("--source-session", default="")
    ap.add_argument("--weight", type=float, default=1.0)
    args = ap.parse_args()

    if not args.learning.strip():
        print("refusing: --learning is empty", file=sys.stderr)
        return 2

    path = Path(args.register)
    existing = sum(1 for _ in path.read_text().splitlines() if _.strip()) if path.exists() else 0
    entry = {
        "id": f"lr-{existing + 1:03d}",
        "date": time.strftime("%Y-%m-%d", time.gmtime()),
        "harness": args.harness,
        "skill": args.skill,
        "type": args.type,
        "learning": args.learning.strip(),
        "source_session": args.source_session,
        "weight": args.weight,
    }
    with path.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")
    print(f"appended {entry['id']} to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
