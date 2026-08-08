"""Codex CLI driver.

Verified against codex-cli 0.145.0. See docs/eval-codex-driver.md for why each
isolation flag is load-bearing.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from eval.cost import Usage, parse_usage, record
from eval.drivers.base import ProbeResult, SessionResult, SubjectResult

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


@contextmanager
def isolated_codex_home(source_home: Path | None = None) -> Iterator[Path]:
    """Yield a disposable CODEX_HOME with only linked authentication.

    Harness state must never share a directory with user-owned sessions or skills.
    The auth payload stays in its original protected file; the temporary home only
    receives a symlink to it.
    """
    source = Path(source_home) if source_home is not None else Path.home() / ".codex"
    auth = source.expanduser() / "auth.json"
    if not auth.is_file():
        raise FileNotFoundError(f"Codex authentication not found at {auth}")

    with tempfile.TemporaryDirectory(prefix="codex-eval-home-") as tmp:
        home = Path(tmp)
        (home / "skills").mkdir()
        (home / "auth.json").symlink_to(auth.resolve())
        yield home


class CodexDriver:
    name = "codex"

    def __init__(self, *, codex_home: Path | None = None) -> None:
        self.codex_home = Path(codex_home) if codex_home is not None else None

    def subprocess_env(self) -> dict[str, str] | None:
        if self.codex_home is None:
            return None
        env = os.environ.copy()
        env["CODEX_HOME"] = str(self.codex_home)
        return env

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
        persist: bool = False,
    ) -> list[str]:
        # Multi-turn needs the session on disk, so --ephemeral is dropped and the
        # session is deleted afterwards instead. Weaker isolation, stated plainly.
        flags = tuple(f for f in ISOLATION_FLAGS if f != "--ephemeral") if persist else ISOLATION_FLAGS
        cmd = [BIN, "exec", *flags]
        cmd += ["-C", str(fixture)]
        cmd += ["-s", "workspace-write" if writable else "read-only"]
        cmd += ["-m", model]
        cmd += ["--color", "never"]
        cmd += ["-o", str(out_file)]
        # Always JSONL: turn.completed carries the usage that meters the call.
        cmd += ["--json"]
        cmd.append(prompt)
        return cmd

    def build_resume_command(
        self,
        *,
        session_id: str,
        prompt: str,
        model: str,
        out_file: Path,
        writable: bool,
    ) -> list[str]:
        """Resume accepts a NARROWER option set than exec — see gotcha 6.

        No -s, no -C, no --color. The working directory is inherited, but the
        sandbox otherwise falls back to read-only. Resume accepts -c, so pin its
        sandbox_mode through that supported override.
        """
        cmd = [BIN, "exec", "resume", session_id]
        cmd += [f for f in ISOLATION_FLAGS if f != "--ephemeral"]
        sandbox = "workspace-write" if writable else "read-only"
        cmd += ["-c", f'sandbox_mode="{sandbox}"']
        cmd += ["-m", model, "--json", "-o", str(out_file)]
        cmd.append(prompt)
        return cmd

    def delete_session(self, session_id: str) -> bool:
        try:
            # --force: without a TTY, delete refuses to confirm and silently fails.
            proc = subprocess.run([BIN, "delete", "--force", session_id], capture_output=True,
                                  text=True, timeout=60, stdin=subprocess.DEVNULL,
                                  env=self.subprocess_env())
            return proc.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

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

    @staticmethod
    def parse_diagnostics(stream: str) -> list[dict]:
        """Keep completed tool/error events needed to diagnose harness failures."""
        diagnostics = []
        for line in stream.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "error":
                diagnostics.append(event)
                continue
            item = event.get("item")
            if (event.get("type") == "item.completed" and isinstance(item, dict)
                    and item.get("type") not in {"agent_message", "reasoning"}):
                diagnostics.append(item)
        return diagnostics

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
                env=self.subprocess_env(),
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

    def run_session(
        self,
        *,
        fixture: Path,
        prompts: list[str],
        model: str,
        writable: bool = True,
        timeout_s: int = 180,
        delete_after: bool = True,
    ) -> SessionResult:
        """Run a scripted multi-turn session in a disposable Codex home.

        Turn 1 persists the session (no --ephemeral) so later turns can resume it.
        Every turn is metered. A caller-supplied CODEX_HOME is mandatory because
        persistent eval sessions must never enter the user's session store.
        """
        if self.codex_home is None:
            raise ValueError("run_session requires an isolated codex_home")

        fixture = Path(fixture)
        out_file = fixture / ".session_last_message.txt"
        session_id: str | None = None
        turns: list[dict] = []
        codes: list[int] = []
        total = Usage()

        for i, prompt in enumerate(prompts):
            if i == 0:
                cmd = self.build_subject_command(
                    fixture=fixture, prompt=prompt, model=model,
                    out_file=out_file, writable=writable, persist=True)
            else:
                if not session_id:
                    break
                cmd = self.build_resume_command(
                    session_id=session_id, prompt=prompt, model=model,
                    out_file=out_file, writable=writable)
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=timeout_s, stdin=subprocess.DEVNULL,
                                      cwd=str(fixture), env=self.subprocess_env())
                stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
                code = 124

            usage = parse_usage(stdout)
            total = total + usage
            record(role=f"session-turn{i + 1}", model=model, usage=usage,
                   harness=self.name, label=fixture.name)
            if session_id is None:
                session_id = self.parse_events(stdout)
            message = out_file.read_text() if out_file.exists() else ""
            if out_file.exists():
                out_file.unlink()
            turns.append({
                "prompt": prompt,
                "message": message.strip(),
                "exit_code": code,
                "diagnostics": self.parse_diagnostics(stdout + "\n" + stderr),
            })
            codes.append(code)

        if delete_after and session_id:
            self.delete_session(session_id)

        return SessionResult(session_id=session_id, turns=turns, workdir=fixture,
                             usage=total, exit_codes=tuple(codes))
