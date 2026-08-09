#!/usr/bin/env python3
"""The only writer to the schema-validated MiniProject improvement register."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from register_common import (
    TYPES,
    RegisterValidationError,
    default_register_path,
    load_register,
    validate_entry,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", type=Path, default=default_register_path())
    parser.add_argument("--import-seed", type=Path)
    parser.add_argument("--type", choices=sorted(TYPES))
    parser.add_argument("--learning")
    parser.add_argument("--harness")
    parser.add_argument("--skill")
    parser.add_argument("--source-session")
    parser.add_argument("--weight", type=float, default=1.0)
    return parser.parse_args()


def new_entry(args: argparse.Namespace, existing_ids: set[str]) -> dict:
    source_session = args.source_session or os.environ.get("MINIPROJECT_SOURCE_SESSION")
    required = {
        "--type": args.type,
        "--learning": args.learning,
        "--harness": args.harness,
        "--skill": args.skill,
        "--source-session or MINIPROJECT_SOURCE_SESSION": source_session,
    }
    missing = [flag for flag, value in required.items() if not value or not str(value).strip()]
    if missing:
        raise RegisterValidationError(f"single append requires {', '.join(missing)}")
    while True:
        entry_id = f"lr-{uuid.uuid4().hex[:16]}"
        if entry_id not in existing_ids:
            break
    entry = {
        "id": entry_id,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "harness": args.harness.strip(),
        "skill": args.skill.strip(),
        "type": args.type,
        "learning": args.learning.strip(),
        "source_session": source_session.strip(),
        "weight": args.weight,
    }
    return validate_entry(entry, context="new entry")


def seed_entries(path: Path) -> list[dict]:
    entries = load_register(path)
    if not entries:
        raise RegisterValidationError("seed import is empty")
    for entry in entries:
        if not entry["source_session"].startswith("seed:"):
            raise RegisterValidationError(
                f"seed entry {entry['id']} must use a source_session beginning with 'seed:'"
            )
    return entries


def main() -> int:
    args = parse_args()
    if args.import_seed and any(
        value is not None for value in (args.type, args.learning, args.harness, args.skill, args.source_session)
    ):
        print("refusing: --import-seed cannot be combined with single-entry fields", file=sys.stderr)
        return 2

    register = args.register.expanduser()
    register.parent.mkdir(parents=True, exist_ok=True)
    lock_path = register.with_suffix(register.suffix + ".lock")
    try:
        with lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                existing = load_register(register)
            except RegisterValidationError as exc:
                raise RegisterValidationError(f"invalid existing register: {exc}") from None
            existing_ids = {entry["id"] for entry in existing}
            additions = seed_entries(args.import_seed) if args.import_seed else [new_entry(args, existing_ids)]
            duplicates = existing_ids.intersection(entry["id"] for entry in additions)
            if duplicates:
                raise RegisterValidationError(
                    f"register already contains {', '.join(sorted(duplicates))}"
                )
            payload = "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in additions)
            with register.open("a", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
    except (OSError, RegisterValidationError) as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2

    if args.import_seed:
        print(f"IMPORTED {len(additions)} seed entries into {register}")
    else:
        print(f"APPENDED {additions[0]['id']} to {register}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
