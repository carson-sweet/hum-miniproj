"""Junie CLI driver with a hard user-home isolation boundary."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from eval.drivers.base import ProbeResult, SessionResult

BIN = "junie"


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
            "--model", model,
            "--output-format", "json-stream",
        ]
        if session_id is not None:
            cmd += ["--session-id", session_id, "--resume"]
        cmd += ["--task", prompt]
        return cmd

    @staticmethod
    def parse_stream(stream: str) -> dict:
        session_id = None
        final_message = ""
        diagnostics = []
        errors = []
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
            elif kind == "step":
                diagnostics.append({k: event[k] for k in ("name", "details", "output") if k in event})
            elif kind == "error":
                errors.append(str(event.get("message") or "unknown Junie error"))
        return {
            "session_id": session_id,
            "final_message": final_message,
            "diagnostics": diagnostics,
            "errors": errors,
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
