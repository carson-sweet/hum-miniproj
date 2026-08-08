"""Harness-agnostic types. Nothing Codex-specific escapes a driver."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from eval.cost import Usage


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
    usage: Usage | None = None


@dataclass(frozen=True)
class SessionResult:
    """A multi-turn session persisted only inside a disposable harness home."""
    session_id: str | None
    turns: list[dict]
    workdir: Path
    usage: "Usage | None" = None
    exit_codes: tuple[int, ...] = ()

    @property
    def ok(self) -> bool:
        return bool(self.session_id) and all(c == 0 for c in self.exit_codes)

    def completed(self, expected_turns: int) -> bool:
        return self.ok and len(self.turns) == expected_turns


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
