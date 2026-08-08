"""The judge: a second Codex process with an empty working directory.

Isolation is structural. The judge sees the pass criterion and the subject's
final message, and its working root contains nothing else. A judge that can read
the skill it grades against credits intent instead of behavior.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from eval.cost import parse_usage, record
from eval.drivers.codex import BIN, isolated_codex_home

SCHEMA_PATH = Path(__file__).parent / "schemas" / "verdict.schema.json"
VALID_VERDICTS = ("PASS", "FAIL")

_JUDGE_ISOLATION = ("--ephemeral", "--ignore-user-config", "--skip-git-repo-check")


@dataclass(frozen=True)
class Verdict:
    verdict: str
    reason: str

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"


def load_verdict_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def parse_verdict(raw: str) -> Verdict:
    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"judge output is not valid JSON: {raw[:200]!r}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"judge output is not valid JSON object: {raw[:200]!r}")

    for field in ("verdict", "reason"):
        if field not in data:
            raise ValueError(f"judge output missing required field {field!r}: {raw[:200]!r}")

    if data["verdict"] not in VALID_VERDICTS:
        raise ValueError(f"{data['verdict']!r} is not a valid verdict")

    return Verdict(verdict=data["verdict"], reason=str(data["reason"]))


def render_judge_prompt(criterion: str, subject_output: str) -> str:
    return (
        "You are grading one output against one criterion. You have no other context, "
        "and you should not speculate about what produced the output.\n\n"
        "CRITERION:\n"
        f"{criterion}\n\n"
        "OUTPUT UNDER TEST:\n"
        "<<<BEGIN OUTPUT\n"
        f"{subject_output}\n"
        "END OUTPUT>>>\n\n"
        "Answer PASS only if the output satisfies the criterion as written. "
        "If it merely describes or promises the behavior without exhibiting it, answer FAIL."
    )


def build_judge_command(
    *,
    workdir: Path,
    prompt: str,
    model: str,
    schema_path: Path,
    out_file: Path,
) -> list[str]:
    cmd = [BIN, "exec", *_JUDGE_ISOLATION]
    cmd += ["-C", str(workdir)]
    cmd += ["-s", "read-only"]
    cmd += ["-m", model]
    cmd += ["--color", "never", "--json"]
    cmd += ["--output-schema", str(schema_path)]
    cmd += ["-o", str(out_file)]
    cmd.append(prompt)
    return cmd


def judge(
    *,
    criterion: str,
    subject_output: str,
    model: str,
    timeout_s: int = 120,
) -> Verdict:
    with tempfile.TemporaryDirectory(prefix="eval-judge-") as tmp, isolated_codex_home() as codex_home:
        workdir = Path(tmp)
        out_file = workdir / "verdict.json"
        cmd = build_judge_command(
            workdir=workdir,
            prompt=render_judge_prompt(criterion, subject_output),
            model=model,
            schema_path=SCHEMA_PATH,
            out_file=out_file,
        )
        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            stdin=subprocess.DEVNULL,
            env=env,
        )
        record(role="judge", model=model, usage=parse_usage(proc.stdout), harness="codex")
        if not out_file.exists():
            raise RuntimeError(
                f"judge produced no verdict file (exit {proc.returncode}): "
                f"{(proc.stdout + proc.stderr)[-500:]}"
            )
        return parse_verdict(out_file.read_text())
