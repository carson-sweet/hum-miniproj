"""Harness-agnostic types. Nothing Codex-specific escapes a driver."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ProbeResult:
    ok: bool
    harness: str
    version: str | None = None
    model: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class SubjectResult:
    final_message: str
    workdir: Path
    exit_code: int
    stdout: str
    model: str | None
    session_id: str | None
    duration_s: float
    events_path: Path | None = None
    timed_out: bool = False


class HarnessDriver(Protocol):
    name: str

    def probe(self) -> ProbeResult:
        ...

    def run_subject(
        self,
        *,
        fixture: Path,
        prompt: str,
        model: str,
        writable: bool,
        timeout_s: int,
    ) -> SubjectResult:
        ...
