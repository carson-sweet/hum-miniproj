"""Deterministic artifact assertions. No model involved, by design.

A file either exists and matches shape, or it does not. Routing that through a
judge would add cost, latency, and a failure mode to the one assertion type the
testing approach actually trusts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssertionOutcome:
    passed: bool
    detail: str


def _resolve(workdir: Path, rel: str) -> Path:
    workdir = Path(workdir).resolve()
    candidate = (workdir / rel).resolve()
    if not candidate.is_relative_to(workdir):
        raise ValueError(f"path {rel!r} escapes workdir {str(workdir)!r}")
    return candidate


def check_artifact(workdir: Path, spec: dict) -> AssertionOutcome:
    kind = spec.get("kind")
    path = _resolve(workdir, spec["path"])
    rel = spec["path"]

    if kind == "exists":
        ok = path.is_file()
        return AssertionOutcome(ok, f"{rel} {'exists' if ok else 'does not exist'}")

    if kind == "absent":
        ok = not path.exists()
        return AssertionOutcome(ok, f"{rel} {'is absent' if ok else 'unexpectedly exists'}")

    if kind == "contains":
        if not path.is_file():
            return AssertionOutcome(False, f"{rel} does not exist")
        pattern = spec["pattern"]
        ok = re.search(pattern, path.read_text(), re.MULTILINE) is not None
        return AssertionOutcome(ok, f"{rel} {'matches' if ok else 'does not match'} {pattern!r}")

    if kind == "min_lines":
        if not path.is_file():
            return AssertionOutcome(False, f"{rel} does not exist")
        actual = len(path.read_text().splitlines())
        want = spec["count"]
        return AssertionOutcome(actual >= want, f"{rel} has {actual} lines, wanted >= {want}")

    if kind == "min_bytes":
        if not path.is_file():
            return AssertionOutcome(False, f"{rel} does not exist")
        actual = path.stat().st_size
        want = spec["count"]
        return AssertionOutcome(actual >= want, f"{rel} is {actual} bytes, wanted >= {want}")

    raise ValueError(f"unknown assertion kind: {kind!r}")
