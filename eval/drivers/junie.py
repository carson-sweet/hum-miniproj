"""Junie CLI driver with a hard user-home isolation boundary."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from eval.cost import record_unmetered
from eval.drivers.base import ProbeResult, SessionResult, SubjectResult

BIN = "junie"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


class JunieDriver:
    name = "junie"

    def __init__(self, *, junie_home: Path, skill_root: Path) -> None:
        self.junie_home = Path(junie_home)
        self.skill_root = Path(skill_root)
        if self.junie_home.resolve() == (Path.home() / ".junie").resolve():
            raise ValueError("the real ~/.junie is not a valid harness home")

    def subprocess_env(self, *, require_auth: bool = True) -> dict[str, str]:
        env = os.environ.copy()
        if require_auth and not env.get("JUNIE_API_KEY"):
            raise RuntimeError(
                "isolated Junie runs require JUNIE_API_KEY; Keychain auth is tied to ~/.junie"
            )
        env["JUNIE_HOME"] = str(self.junie_home)
        env["JUNIE_LOG_DIR"] = str(self.junie_home / "logs")
        return env

    def probe(self) -> ProbeResult:
        path = shutil.which(BIN)
        if path is None:
            return ProbeResult(False, self.name, detail=f"{BIN} binary not found on PATH")
        proc = subprocess.run(
            [BIN, "--version"], capture_output=True, text=True, timeout=30,
            stdin=subprocess.DEVNULL, env=self.subprocess_env(require_auth=False),
        )
        return ProbeResult(
            proc.returncode == 0,
            self.name,
            version=proc.stdout.strip() if proc.returncode == 0 else None,
            detail=f"found at {path}" if proc.returncode == 0 else proc.stderr.strip(),
        )

    def build_command(
        self, *, fixture: Path, prompt: str, model: str, session_id: str | None = None,
        output_format: str = "json-stream",
    ) -> list[str]:
        cmd = [
            BIN,
            "--project", str(fixture),
            "--cache-dir", str(self.junie_home / "cache"),
            "--extensions-default-location", str(self.junie_home / "extensions"),
            "--skill-default-locations=false",
            "--skill-location", str(self.skill_root),
            "--config-default-locations=false",
            "--model-default-locations=false",
            "--mcp-default-locations=false",
            "--command-default-location=false",
            "--agent-default-location=false",
            "--share-anonymous-statistics=false",
            "--skip-update-check",
            "--agent-mode", "chat",
            "--model", model,
            "--output-format", output_format,
        ]
        if session_id is not None:
            cmd += ["--session-id", session_id, "--resume"]
        cmd += ["--task", prompt]
        return cmd

    def build_subject_command(
        self, *, fixture: Path, prompt: str, model: str,
    ) -> list[str]:
        return self.build_command(
            fixture=fixture, prompt=prompt, model=model, output_format="text"
        )

    @staticmethod
    def parse_text_result(stream: str) -> str:
        cleaned = ANSI.sub("", stream).replace("\r", "")
        marker = "TASK RESULT"
        if marker not in cleaned:
            return ""
        return cleaned.split(marker, 1)[1].strip()

    @staticmethod
    def parse_stream(stream: str) -> dict:
        session_id = None
        final_message = ""
        diagnostics = []
        errors = []
        usage_rows = []
        for line in stream.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = event.get("type")
            if kind == "session" and event.get("sessionId"):
                session_id = str(event["sessionId"])
            elif kind == "result":
                final_message = str(event.get("result") or "")
                raw_rows = event.get("errorCode")
                if isinstance(raw_rows, list):
                    for row in raw_rows:
                        if not isinstance(row, dict) or not row.get("model"):
                            continue
                        uncached = int(row.get("inputTokens") or 0)
                        cached = int(row.get("cacheInputTokens") or 0)
                        created = int(row.get("cacheCreateTokens") or 0)
                        usage_rows.append(
                            {
                                "model": str(row["model"]),
                                "calls": int(row.get("calls") or 0),
                                "cost": float(row.get("cost") or 0.0),
                                "input_tokens": uncached + cached + created,
                                "cached_input_tokens": cached,
                                "output_tokens": int(row.get("outputTokens") or 0),
                            }
                        )
            elif kind == "step":
                diagnostics.append({k: event[k] for k in ("name", "details", "output") if k in event})
            elif kind == "error":
                errors.append(str(event.get("message") or "unknown Junie error"))
        return {
            "session_id": session_id,
            "final_message": final_message,
            "diagnostics": diagnostics,
            "errors": errors,
            "usage_rows": usage_rows,
        }

    def run_session(
        self, *, fixture: Path, prompts: list[str], model: str, timeout_s: int = 300,
    ) -> SessionResult:
        fixture = Path(fixture)
        self.junie_home.mkdir(parents=True, exist_ok=True)
        self.skill_root.mkdir(parents=True, exist_ok=True)
        session_id = None
        turns = []
        codes = []

        for prompt in prompts:
            cmd = self.build_command(
                fixture=fixture, prompt=prompt, model=model, session_id=session_id,
            )
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout_s,
                    stdin=subprocess.DEVNULL, cwd=str(fixture),
                    env=self.subprocess_env(),
                )
                parsed = self.parse_stream(proc.stdout + "\n" + proc.stderr)
                code = proc.returncode if not parsed["errors"] else 1
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
                parsed = self.parse_stream(stdout + "\n" + stderr)
                code = 124

            if session_id is None:
                session_id = parsed["session_id"]
            turns.append({
                "prompt": prompt,
                "message": parsed["final_message"],
                "exit_code": code,
                "diagnostics": parsed["diagnostics"],
                "errors": parsed["errors"],
            })
            codes.append(code)
            if not session_id:
                break

        return SessionResult(
            session_id=session_id, turns=turns, workdir=fixture, exit_codes=tuple(codes),
        )

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
        """Run one subject turn inside disposable Junie state and fixture roots."""
        del writable  # The caller-provided fixture is disposable; Junie has no sandbox flag.
        fixture = Path(fixture)
        self.junie_home.mkdir(parents=True, exist_ok=True)
        self.skill_root.mkdir(parents=True, exist_ok=True)
        cmd = self.build_subject_command(fixture=fixture, prompt=prompt, model=model)
        started = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                stdin=subprocess.DEVNULL,
                cwd=str(fixture),
                env=self.subprocess_env(),
            )
            stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            code = 124

        stream = stdout + "\n" + stderr
        final_message = self.parse_text_result(stream)
        if events_file is not None:
            Path(events_file).write_text(stream)
        record_unmetered(
            role="subject", model=model, harness=self.name, label=fixture.name
        )

        return SubjectResult(
            final_message=final_message,
            workdir=fixture,
            exit_code=code,
            stdout=stream,
            model=model,
            session_id=None,
            duration_s=time.monotonic() - started,
            events_path=Path(events_file) if events_file else None,
            timed_out=timed_out,
        )
