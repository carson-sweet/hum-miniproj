#!/usr/bin/env python3
"""Group validated improvement entries by learning type and instruction target."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

from improvement_common import write_json
from register_common import RegisterValidationError, is_seed, load_register


def pattern_id(kind: str, target: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", target.lower()).strip("-")
    if not slug:
        slug = hashlib.sha256(target.encode()).hexdigest()[:12]
    return f"pattern-{kind}-{slug[:80]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-occurrences", type=int, default=2)
    args = parser.parse_args()
    if args.min_occurrences < 2:
        print("refusing: --min-occurrences must be at least 2", file=sys.stderr)
        return 2
    try:
        entries = load_register(args.register)
    except RegisterValidationError as exc:
        print(f"refusing: invalid register: {exc}", file=sys.stderr)
        return 2

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for entry in entries:
        groups[(entry["type"], entry["skill"])].append(entry)
    patterns = []
    for (kind, target), members in sorted(groups.items()):
        if len(members) < args.min_occurrences:
            continue
        patterns.append(
            {
                "pattern_id": pattern_id(kind, target),
                "type": kind,
                "target": target,
                "count": len(members),
                "weight": sum(float(entry["weight"]) for entry in members),
                "entry_ids": sorted(entry["id"] for entry in members),
                "learnings": [entry["learning"] for entry in members],
            }
        )
    output = {
        "schema_version": 1,
        "register_sha256": hashlib.sha256(args.register.read_bytes()).hexdigest(),
        "entry_count": len(entries),
        "live_entry_count": sum(not is_seed(entry) for entry in entries),
        "seed_entry_count": sum(is_seed(entry) for entry in entries),
        "min_occurrences": args.min_occurrences,
        "patterns": patterns,
    }
    write_json(args.output, output)
    print(f"ANALYZED {len(entries)} entries; found {len(patterns)} recurring patterns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
