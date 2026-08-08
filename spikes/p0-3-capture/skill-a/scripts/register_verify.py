#!/usr/bin/env python3
"""Exit non-zero when a session closed without adding a register entry.

Substitute for the lifecycle hook the Agent Skills standard does not define. It
is invoked by the skill's own closeout rather than remembered by the agent.
"""
import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--register", default="register.jsonl")
    ap.add_argument("--min-entries", type=int, default=1)
    args = ap.parse_args()

    path = Path(args.register)
    if not path.exists():
        print(f"FAIL: {path} does not exist — this session captured nothing.", file=sys.stderr)
        return 1

    valid = 0
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("learning") and entry.get("type"):
            valid += 1

    if valid < args.min_entries:
        print(f"FAIL: {valid} valid entries, need {args.min_entries}. "
              f"Append one with register_append.py before closing out.", file=sys.stderr)
        return 1
    print(f"OK: {valid} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
