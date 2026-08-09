#!/usr/bin/env python3
"""Fail when a MiniProject session closed without a matching valid capture."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from register_common import (
    RegisterValidationError,
    default_register_path,
    is_seed,
    load_register,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", type=Path, default=default_register_path())
    parser.add_argument("--source-session", default=os.environ.get("MINIPROJECT_SOURCE_SESSION"))
    parser.add_argument("--skill")
    parser.add_argument("--min-entries", type=int, default=1)
    parser.add_argument("--require-live", action="store_true")
    args = parser.parse_args()
    if args.min_entries < 1:
        print("FAIL: --min-entries must be at least 1", file=sys.stderr)
        return 2
    try:
        entries = load_register(args.register.expanduser())
    except RegisterValidationError as exc:
        print(f"FAIL: invalid register: {exc}", file=sys.stderr)
        return 2

    matches = entries
    if args.source_session:
        matches = [entry for entry in matches if entry["source_session"] == args.source_session]
    if args.skill:
        matches = [entry for entry in matches if entry["skill"] == args.skill]
    if args.require_live:
        matches = [entry for entry in matches if not is_seed(entry)]
    if len(matches) < args.min_entries:
        filters = []
        if args.source_session:
            filters.append(f"source session {args.source_session!r}")
        if args.skill:
            filters.append(f"skill {args.skill!r}")
        if args.require_live:
            filters.append("live entries")
        description = ", ".join(filters) or "valid entries"
        print(
            f"FAIL: found {len(matches)} matching {description}; need {args.min_entries}",
            file=sys.stderr,
        )
        return 1
    print(f"OK: found {len(matches)} matching entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
