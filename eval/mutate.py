"""Negative-control mutations, applied to a disposable copy of the skill.

Every op reports whether it actually changed anything. A mutation that matched
nothing is inert, and the runner must refuse to score a contract whose mutation
was inert rather than reporting a green negative control for a rule it never
removed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MutationResult:
    applied: bool
    matched: int
    detail: str


def _resolve(skill_dir: Path, rel: str) -> Path:
    skill_dir = Path(skill_dir).resolve()
    candidate = (skill_dir / rel).resolve()
    if not candidate.is_relative_to(skill_dir):
        raise ValueError(f"mutation target {rel!r} escapes skill dir {str(skill_dir)!r}")
    return candidate


def apply_mutation(skill_dir: Path, spec: dict) -> MutationResult:
    op = spec.get("op")
    rel = spec["file"]
    target = _resolve(skill_dir, rel)

    if op not in ("delete_lines_matching", "replace", "delete_file", "truncate_after"):
        raise ValueError(f"unknown mutation op: {op!r}")

    if op == "delete_file":
        if not target.exists():
            return MutationResult(False, 0, f"{rel} does not exist; mutation inert")
        target.unlink()
        return MutationResult(True, 1, f"deleted {rel}")

    if not target.is_file():
        return MutationResult(False, 0, f"{rel} does not exist; mutation inert")

    original = target.read_text()

    if op == "delete_lines_matching":
        pattern = re.compile(spec["pattern"])
        kept = [ln for ln in original.splitlines(keepends=True) if not pattern.search(ln)]
        matched = len(original.splitlines()) - len(kept)
        if matched == 0:
            return MutationResult(False, 0, f"no line in {rel} matched {spec['pattern']!r}; mutation inert")
        target.write_text("".join(kept))
        return MutationResult(True, matched, f"deleted {matched} line(s) from {rel}")

    if op == "replace":
        pattern = spec["pattern"]
        matched = original.count(pattern)
        if matched == 0:
            return MutationResult(False, 0, f"{pattern!r} not found in {rel}; mutation inert")
        target.write_text(original.replace(pattern, spec["value"]))
        return MutationResult(True, matched, f"replaced {matched} occurrence(s) in {rel}")

    pattern = re.compile(spec["pattern"])
    lines = original.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if pattern.search(line):
            target.write_text("".join(lines[: i + 1]))
            return MutationResult(True, 1, f"truncated {rel} after line {i + 1}")
    return MutationResult(False, 0, f"no line in {rel} matched {spec['pattern']!r}; mutation inert")
