"""Compose steps 1-3 against the throwaway fixture.

Not a contract runner. This proves the mechanism works end to end — disposable
workdir, real subject, deterministic artifact assertions in both directions, and
an isolated judge — before run_contracts.py is built on top of it.

    python3 -m eval.smoke
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from eval.assertions import check_artifact
from eval.drivers.codex import CodexDriver
from eval.judge import judge

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "fixtures" / "throwaway"
MODEL = "gpt-5.6-sol"

PROMPT = (
    "Read notes.md. Write a file named bundle.md in the working directory that "
    "states the open question and names a single owner under a '## Owner' heading. "
    "Then briefly say what you did."
)

CRITERION = (
    "Does the output report that a bundle file was written, naming a single owner "
    "rather than deferring the decision or asking who should own it?"
)


def main() -> int:
    driver = CodexDriver()

    probe = driver.probe()
    print(f"[1] probe        {'ok' if probe.ok else 'FAILED'} — {probe.version or probe.detail}")
    if not probe.ok:
        return 3

    with tempfile.TemporaryDirectory(prefix="eval-smoke-") as tmp:
        workdir = Path(tmp) / "fx"
        shutil.copytree(FIXTURE, workdir)

        result = driver.run_subject(
            fixture=workdir, prompt=PROMPT, model=MODEL, writable=True, timeout_s=180
        )
        print(
            f"[1] subject      exit={result.exit_code} {result.duration_s:.1f}s "
            f"model={result.model} session={(result.session_id or '')[:8]}"
        )
        if result.timed_out:
            print("    TIMED OUT")
            return 3

        checks = [
            ({"kind": "exists", "path": "bundle.md"}, True),
            ({"kind": "contains", "path": "bundle.md", "pattern": r"^## Owner"}, True),
            ({"kind": "exists", "path": "never-written.md"}, False),
        ]
        assertions_ok = True
        for spec, expected in checks:
            outcome = check_artifact(workdir, spec)
            agrees = outcome.passed is expected
            assertions_ok &= agrees
            print(
                f"[3] assert       {'ok ' if agrees else 'BAD'} "
                f"{spec['kind']:<9} expected={'PASS' if expected else 'FAIL'} "
                f"got={'PASS' if outcome.passed else 'FAIL'} — {outcome.detail}"
            )

        verdict = judge(
            criterion=CRITERION,
            subject_output=result.final_message,
            model=MODEL,
            timeout_s=120,
        )
        print(f"[2] judge        {verdict.verdict} — {verdict.reason}")

    green = assertions_ok and verdict.passed
    print(f"\n{'GREEN' if green else 'RED'}: steps 1-3 composed on the throwaway fixture")
    return 0 if green else 1


if __name__ == "__main__":
    sys.exit(main())
