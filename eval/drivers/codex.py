"""Codex CLI driver.

Verified against codex-cli 0.145.0. See docs/eval-codex-driver.md for why each
isolation flag is load-bearing.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from eval.cost import Usage, parse_usage, record
from eval.drivers.base import ProbeResult, SubjectResult

BIN = "codex"

ISOLATION_FLAGS = (
    "--ephemeral",
    "--ignore-user-config",
    "--ignore-rules",
    "--skip-git-repo-check",
)

_HEADER_PATTERNS = {
    "model": re.compile(r"^model:\s*(.+)$", re.MULTILINE),
    "session_id": re.compile(r"^session id:\s*(.+)$", re.MULTILINE),
    "provider": re.compile(r"^provider:\s*(.+)$", re.MULTILINE),
}


class CodexDriver:
    name = "codex"

    def probe(self) -> ProbeResult:
        path = shutil.which(BIN)
        if path is None:
            return ProbeResult(
                ok=False,
                harness=self.name,
                detail=f"{BIN} binary not found on PATH",
            )
        try:
            proc = subprocess.run(
                [BIN, "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                stdin=subprocess.DEVNULL,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return ProbeResult(ok=False, harness=self.name, detail=f"probe failed: {exc}")

        if proc.returncode != 0:
            return ProbeResult(
                ok=False, harness=self.name, detail=f"exit {proc.returncode}: {proc.stderr.strip()}"
            )
        return ProbeResult(
            ok=True,
            harness=self.name,
            version=proc.stdout.strip(),
            detail=f"found at {path}",
        )

    def build_subject_command(
        self,
        *,
        fixture: Path,
        prompt: str,
        model: str,
        out_file: Path,
        writable: bool = False,
        events_file: Path | None = None,
    ) -> list[str]:
        cmd = [BIN, "exec", *ISOLATION_FLAGS]
        cmd += ["-C", str(fixture)]
        cmd += ["-s", "workspace-write" if writable else "read-only"]
        cmd += ["-m", model]
        cmd += ["--color", "never"]
        cmd += ["-o", str(out_file)]
        # Always JSONL: turn.completed carries the usage that meters the call.
        cmd += ["--json"]
        cmd.append(prompt)
        return cmd

    @staticmethod
    def parse_header(stdout: str) -> dict[str, str | None]:
        return {key: (m.group(1).strip() if (m := pat.search(stdout)) else None)
                for key, pat in _HEADER_PATTERNS.items()}

    @staticmethod
    def parse_events(stream: str) -> str | None:
        """Recover the thread id from --json output.

        In --json mode there is no banner on either stream, so parse_header finds
        nothing and attribution would silently vanish.
        """
        for line in stream.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "thread.started" and event.get("thread_id"):
                return str(event["thread_id"])
        return None

    def run_subject(
        self,
        *,
        fixture: Path,
        prompt: str,
        model: str,
        writable: bool,
        timeout_s: int,
        events_file: Path | None = None,
    ) -> SubjectResult:
        fixture = Path(fixture)
        out_file = fixture / ".subject_last_message.txt"
        cmd = self.build_subject_command(
            fixture=fixture,
            prompt=prompt,
            model=model,
            out_file=out_file,
            writable=writable,
            events_file=events_file,
        )

        started = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                # Gotcha 1: without this codex blocks on stdin even with a prompt arg.
                stdin=subprocess.DEVNULL,
            )
            stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            code = 124
        duration = time.monotonic() - started

        if events_file is not None and stdout:
            Path(events_file).write_text(stdout)

        final_message = out_file.read_text() if out_file.exists() else ""
        if out_file.exists():
            out_file.unlink()

        # Gotcha 2: the banner and transcript go to stderr; stdout carries only the
        # final message. Parsing stdout would also let a reply containing a line like
        # "model: x" poison the attribution metadata.
        usage = parse_usage(stdout)
        record(role="subject", model=model, usage=usage, harness=self.name,
               label=str(Path(fixture).name))

        meta = self.parse_header(stderr)
        if meta["model"] is None and meta["session_id"] is None:
            meta = self.parse_header(stdout)
        if meta["session_id"] is None:
            # --json mode: no banner on either stream, id lives in thread.started.
            meta["session_id"] = self.parse_events(stdout)

        return SubjectResult(
            final_message=final_message.strip(),
            workdir=fixture,
            exit_code=code,
            stdout=stdout + stderr,
            model=meta["model"] or model,
            session_id=meta["session_id"],
            duration_s=duration,
            events_path=Path(events_file) if events_file else None,
            timed_out=timed_out,
            usage=usage,
        )
