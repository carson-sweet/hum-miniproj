"""P0.3 under Junie, isolated from the user's Junie home."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from eval.config import SUBJECT_MODEL
from eval.drivers.junie import JunieDriver

HERE = Path(__file__).resolve().parent
SESSION = json.loads((HERE / "SESSION.json").read_text())
SKILL_NAME = "mp-classify"


def captured(workdir: Path) -> tuple[bool, str]:
    register = workdir / "register.jsonl"
    if not register.exists():
        return False, "no register.jsonl"
    valid = 0
    for line in register.read_text().splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("learning") and entry.get("type"):
            valid += 1
    return valid >= 1, f"{valid} valid entr{'y' if valid == 1 else 'ies'}"


def one_run(variant: str, keep: bool) -> dict:
    work = Path(tempfile.mkdtemp(prefix=f"p03-junie-{variant}-"))
    try:
        with tempfile.TemporaryDirectory(prefix="junie-eval-home-") as home_string:
            home = Path(home_string)
            skill_root = home / "skills"
            skill_root.mkdir()
            shutil.copytree(HERE / f"skill-{variant}", skill_root / SKILL_NAME)
            result = JunieDriver(junie_home=home, skill_root=skill_root).run_session(
                fixture=work, prompts=SESSION, model=SUBJECT_MODEL, timeout_s=300,
            )
        ok, detail = captured(work)
        return {
            "harness": "junie", "variant": variant,
            "valid": result.completed(len(SESSION)), "captured": ok, "detail": detail,
            "session_id": result.session_id, "turn_count": len(result.turns),
            "turns": result.turns, "exit_codes": list(result.exit_codes),
        }
    finally:
        if keep:
            print(f"    workdir kept: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--variant", choices=["a", "b", "both"], default="both")
    parser.add_argument("--keep-workdirs", action="store_true")
    args = parser.parse_args()

    if not os.environ.get("JUNIE_API_KEY"):
        print("refusing: isolated Junie runs require JUNIE_API_KEY in the environment")
        return 3

    variants = ["a", "b"] if args.variant == "both" else [args.variant]
    rows, rates = [], {}
    invalid_runs = 0
    for variant in variants:
        hits = 0
        valid = 0
        for index in range(args.runs):
            row = one_run(variant, args.keep_workdirs)
            rows.append(row)
            if row["valid"]:
                valid += 1
                hits += row["captured"]
            else:
                invalid_runs += 1
            state = "INVALID" if not row["valid"] else ("CAPTURED" if row["captured"] else "MISSED")
            print(f"variant {variant.upper()} run {index + 1}: {state} {row['detail']} exits={row['exit_codes']}")
        rates[variant] = hits / valid if valid else 0.0
        print(f"variant {variant.upper()}: {hits}/{valid} valid run(s) ({rates[variant] * 100:.0f}%)")

    decision_eligible = args.runs >= 5 and invalid_runs == 0
    for row in rows:
        row["requested_runs_per_variant"] = args.runs
        row["decision_eligible"] = decision_eligible
    kind = "runs" if decision_eligible else "preflight"
    output = HERE / "evidence" / f"junie-{kind}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.jsonl"
    with output.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    print(f"evidence: {output}")

    if invalid_runs:
        print("INVALID — the P0.3 kill condition was not evaluated")
        return 3
    if not decision_eligible:
        print("PRELIMINARY — the P0.3 kill condition was not evaluated")
        return 0
    if "b" in rates:
        passed = rates["b"] >= 0.8
        print(f"Variant B {rates['b'] * 100:.0f}% — kill condition {'not triggered' if passed else 'TRIGGERED'}")
        return 0 if passed else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
