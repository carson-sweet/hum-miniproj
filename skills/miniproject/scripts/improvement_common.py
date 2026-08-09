#!/usr/bin/env python3
"""Shared deterministic helpers for MiniProject improvement-cycle artifacts."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


class ImprovementError(ValueError):
    pass


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, *, label: str = "artifact") -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ImprovementError(f"{label} does not exist: {path}") from None
    except json.JSONDecodeError as exc:
        raise ImprovementError(f"{label} is invalid JSON: {exc.msg}") from None
    if not isinstance(value, dict):
        raise ImprovementError(f"{label} must be a JSON object")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def parse_score(raw: str) -> dict[str, int]:
    try:
        passed_raw, total_raw = raw.split("/", 1)
        passed, total = int(passed_raw), int(total_raw)
    except (ValueError, AttributeError):
        raise ImprovementError(f"invalid score {raw!r}; expected PASSED/TOTAL") from None
    validate_score({"passed": passed, "total": total}, label="score")
    return {"passed": passed, "total": total}


def validate_score(score: object, *, label: str) -> float:
    if not isinstance(score, dict) or set(score) != {"passed", "total"}:
        raise ImprovementError(f"{label} must contain only passed and total")
    passed, total = score["passed"], score["total"]
    if (
        isinstance(passed, bool)
        or isinstance(total, bool)
        or not isinstance(passed, int)
        or not isinstance(total, int)
        or total <= 0
        or passed < 0
        or passed > total
    ):
        raise ImprovementError(f"{label} must satisfy 0 <= passed <= total and total > 0")
    return passed / total
