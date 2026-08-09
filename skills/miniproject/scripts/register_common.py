#!/usr/bin/env python3
"""Shared read-only validation for the MiniProject improvement register."""
from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path


TYPES = {"correction", "confirmation", "preference", "pattern"}
FIELDS = {
    "id",
    "date",
    "harness",
    "skill",
    "type",
    "learning",
    "source_session",
    "weight",
}
ID_RE = re.compile(r"^lr-[0-9a-f]{16}$")


class RegisterValidationError(ValueError):
    pass


def default_register_path() -> Path:
    configured = os.environ.get("MINIPROJECT_REGISTER")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "share" / "miniproject" / "improvement-register.jsonl"


def validate_entry(entry: object, *, context: str = "entry") -> dict:
    if not isinstance(entry, dict):
        raise RegisterValidationError(f"{context}: expected an object")
    unknown = set(entry) - FIELDS
    missing = FIELDS - set(entry)
    if missing:
        raise RegisterValidationError(f"{context}: missing {', '.join(sorted(missing))}")
    if unknown:
        raise RegisterValidationError(f"{context}: unknown {', '.join(sorted(unknown))}")
    if not isinstance(entry["id"], str) or not ID_RE.fullmatch(entry["id"]):
        raise RegisterValidationError(f"{context}: invalid id")
    try:
        parsed_date = date.fromisoformat(entry["date"])
    except (TypeError, ValueError):
        raise RegisterValidationError(f"{context}: invalid date") from None
    if parsed_date.isoformat() != entry["date"]:
        raise RegisterValidationError(f"{context}: date must use YYYY-MM-DD")
    for field in ("harness", "skill", "learning", "source_session"):
        if not isinstance(entry[field], str) or not entry[field].strip():
            raise RegisterValidationError(f"{context}: {field} must be non-empty")
    if len(entry["learning"].strip()) > 1000:
        raise RegisterValidationError(f"{context}: learning exceeds 1000 characters")
    if entry["type"] not in TYPES:
        raise RegisterValidationError(f"{context}: invalid type")
    weight = entry["weight"]
    if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not 0 < weight <= 10:
        raise RegisterValidationError(f"{context}: weight must be greater than 0 and at most 10")
    return entry


def load_register(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries: list[dict] = []
    seen: set[str] = set()
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RegisterValidationError(f"line {line_number}: invalid JSON: {exc.msg}") from None
        validate_entry(entry, context=f"line {line_number}")
        if entry["id"] in seen:
            raise RegisterValidationError(f"line {line_number}: duplicate id {entry['id']}")
        seen.add(entry["id"])
        entries.append(entry)
    return entries


def is_seed(entry: dict) -> bool:
    return entry["source_session"].startswith("seed:")
