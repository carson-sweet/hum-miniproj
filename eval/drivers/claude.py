"""Claude Code driver contained by an ephemeral Docker runtime."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from eval.cost import Usage, record
from eval.drivers.base import ProbeResult, SubjectResult

BIN = "docker"
IMAGE = os.environ.get("EVAL_CLAUDE_IMAGE", "hum-miniproj-claude-test:2.1.226")


class ClaudeDriver:
    name = "claude"

    def __init__(self, *, skill_dir: Path, image: str = IMAGE) -> None:
        self.skill_dir = Path(skill_dir)
        self.image = image

    def subprocess_env(self) -> dict[str, str]:
        env = os.environ.copy()
        if not env.get("CLAUDE_CODE_OAUTH_TOKEN"):
            raise RuntimeError(
                "isolated Claude runs require CLAUDE_CODE_OAUTH_TOKEN in process memory"
            )
        return env

    def probe(self) -> ProbeResult:
        path = shutil.which(BIN)
        if path is None:
            return ProbeResult(False, self.name, detail="docker binary not found on PATH")
        inspect = subprocess.run(
            [BIN, "image", "inspect", self.image],
            capture_output=True,
            text=True,
            timeout=30,
            stdin=subprocess.DEVNULL,
        )
        if inspect.returncode != 0:
            return ProbeResult(
                False,
                self.name,
                detail=(
                    f"container image {self.image!r} not found; build it with "
                    "docker build -t hum-miniproj-claude-test:2.1.226 "
                    "-f eval/docker/claude.Dockerfile ."
                ),
            )
        version = subprocess.run(
            [BIN, "run", "--rm", self.image, "--version"],
            capture_output=True,
            text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,
        )
        return ProbeResult(
            version.returncode == 0,
            self.name,
            version=version.stdout.strip() if version.returncode == 0 else None,
            detail=f"image {self.image}" if version.returncode == 0 else version.stderr.strip(),
        )

    def build_subject_command(
        self,
        *,
        fixture: Path,
        prompt: str,
        model: str,
        writable: bool,
    ) -> list[str]:
        fixture_mode = "rw" if writable else "ro"
        cmd = [
            BIN,
            "run",
            "--rm",
            "--network",
            "bridge",
            "--env",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "--volume",
            f"{Path(fixture).resolve()}:/workspace:{fixture_mode}",
            "--volume",
            f"{self.skill_dir.resolve()}:/root/.claude/skills/miniproject:ro",
            "--workdir",
            "/workspace",
            self.image,
            "--print",
            prompt,
            "--output-format",
            "json",
            "--no-session-persistence",
            "--model",
            model,
            "--effort",
            "low",
            "--permission-mode",
            "acceptEdits" if writable else "dontAsk",
            "--allowedTools",
            "Skill",
            "Read",
        ]
        if writable:
            cmd += ["Write", "Edit", "Bash(python3 *)"]
        return cmd

    @staticmethod
    def parse_result(raw: str, *, requested_model: str) -> dict:
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError as exc:
            raise ValueError("Claude output is not valid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("Claude output is not a valid JSON object")

        usage_data = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        uncached = int(usage_data.get("input_tokens") or 0)
        cached = int(usage_data.get("cache_read_input_tokens") or 0)
        created = int(usage_data.get("cache_creation_input_tokens") or 0)
        usage = Usage(
            input_tokens=uncached + cached + created,
            cached_input_tokens=cached,
            output_tokens=int(usage_data.get("output_tokens") or 0),
        )

        model = requested_model
        usage_rows = []
        model_usage = data.get("modelUsage")
        if isinstance(model_usage, dict) and model_usage:
            for model_id, row in model_usage.items():
                if not isinstance(row, dict):
                    continue
                canonical = str(row.get("canonicalModel") or model_id)
                row_cached = int(row.get("cacheReadInputTokens") or 0)
                row_created = int(row.get("cacheCreationInputTokens") or 0)
                row_usage = Usage(
                    input_tokens=int(row.get("inputTokens") or 0) + row_cached + row_created,
                    cached_input_tokens=row_cached,
                    output_tokens=int(row.get("outputTokens") or 0),
                )
                usage_rows.append(
                    {
                        "model": canonical,
                        "usage": row_usage,
                        "cost": float(row.get("costUSD") or 0.0),
                    }
                )
                if requested_model.lower() in canonical.lower():
                    model = canonical

        return {
            "final_message": str(data.get("result") or ""),
            "session_id": str(data.get("session_id") or "") or None,
            "model": model,
            "usage": usage,
            "usage_rows": usage_rows,
        }

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
        cmd = self.build_subject_command(
            fixture=fixture, prompt=prompt, model=model, writable=writable
        )
        started = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                stdin=subprocess.DEVNULL,
                env=self.subprocess_env(),
            )
            stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            code = 124

        if events_file is not None:
            Path(events_file).write_text(stdout + stderr)

        try:
            parsed = self.parse_result(stdout, requested_model=model)
        except ValueError:
            parsed = {
                "final_message": "",
                "session_id": None,
                "model": model,
                "usage": Usage(),
                "usage_rows": [],
            }
            if code == 0:
                code = 1

        if parsed["usage_rows"]:
            for row in parsed["usage_rows"]:
                record(
                    role="subject",
                    model=row["model"],
                    usage=row["usage"],
                    harness=self.name,
                    label=Path(fixture).name,
                    cost_override=row["cost"],
                )
        else:
            record(
                role="subject",
                model=parsed["model"],
                usage=parsed["usage"],
                harness=self.name,
                label=Path(fixture).name,
            )
        return SubjectResult(
            final_message=parsed["final_message"],
            workdir=Path(fixture),
            exit_code=code,
            stdout=stdout + stderr,
            model=parsed["model"],
            session_id=parsed["session_id"],
            duration_s=time.monotonic() - started,
            events_path=Path(events_file) if events_file else None,
            timed_out=timed_out,
            usage=parsed["usage"],
        )
