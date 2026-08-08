"""P0.3 — can register capture be made reliable without a hook?

Two variants against a scripted multi-turn session, N runs each, per harness.
Capture is an artifact assertion: register.jsonl gains a valid entry, or it does
not. No judge, so no judge variance in the measurement.

    python3 spikes/p0-3-capture/run.py --runs 5
    python3 spikes/p0-3-capture/run.py --runs 1 --variant b
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from eval.config import SUBJECT_MODEL
from eval.cost import format_totals, totals
from eval.drivers.codex import CodexDriver, isolated_codex_home

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SESSION = json.loads((HERE / "SESSION.json").read_text())
SKILL_NAME = "mp-classify"


def install(variant: str, codex_home: Path) -> Path:
    src = HERE / f"skill-{variant}"
    destination = codex_home / "skills" / SKILL_NAME
    if destination.exists():
        raise SystemExit(f"refusing to overwrite isolated skill path: {destination}")
    shutil.copytree(src, destination)
    return destination


def captured(workdir: Path) -> tuple[bool, str]:
    reg = workdir / "register.jsonl"
    if not reg.exists():
        return False, "no register.jsonl"
    valid = 0
    for line in reg.read_text().splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("learning") and e.get("type"):
            valid += 1
    return valid >= 1, f"{valid} valid entr{'y' if valid == 1 else 'ies'}"


def one_run(variant: str, keep: bool) -> dict:
    work = Path(tempfile.mkdtemp(prefix=f"p03-{variant}-"))
    try:
        with isolated_codex_home() as codex_home:
            install(variant, codex_home)
            result = CodexDriver(codex_home=codex_home).run_session(
                fixture=work, prompts=SESSION, model=SUBJECT_MODEL,
                writable=True, timeout_s=240,
            )
        ok, detail = captured(work)
        return {
            "variant": variant,
            "valid": result.completed(len(SESSION)),
            "captured": ok,
            "detail": detail,
            "session_id": result.session_id,
            "turn_count": len(result.turns),
            "turns": result.turns,
            "exit_codes": list(result.exit_codes),
        }
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--variant", choices=["a", "b", "both"], default="both")
    ap.add_argument("--keep-workdirs", action="store_true")
    args = ap.parse_args()

    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    variants = ["a", "b"] if args.variant == "both" else [args.variant]
    print(f"P0.3 capture — subject {SUBJECT_MODEL}, {args.runs} run(s) per variant, "
          f"{len(SESSION)} turns each\n")

    rows, rates = [], {}
    invalid_runs = 0
    for v in variants:
        hits = 0
        valid = 0
        for i in range(args.runs):
            r = one_run(v, args.keep_workdirs)
            rows.append(r)
            if r["valid"]:
                valid += 1
                hits += r["captured"]
            else:
                invalid_runs += 1
            print(f"  variant {v.upper()} run {i + 1}: "
                  f"{'INVALID ' if not r['valid'] else ('CAPTURED' if r['captured'] else 'MISSED  ')}  "
                  f"{r['detail']}  exits={r['exit_codes']}")
        rates[v] = hits / valid if valid else 0.0
        print(f"  variant {v.upper()} capture rate: {hits}/{valid} valid run(s) "
              f"({rates[v] * 100:.0f}%)\n")

    decision_eligible = args.runs >= 5 and invalid_runs == 0
    for row in rows:
        row["requested_runs_per_variant"] = args.runs
        row["decision_eligible"] = decision_eligible

    evidence_kind = "runs" if decision_eligible else "preflight"
    out = HERE / "evidence" / f"{evidence_kind}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    spend = totals(since=started)
    print("cost: " + format_totals(spend))
    print(f"evidence: {out}")

    if invalid_runs:
        print(f"\nINVALID — {invalid_runs} harness run(s) did not complete every turn. "
              "The P0.3 kill condition was not evaluated.")
        return 3

    if not decision_eligible:
        print(f"\nPRELIMINARY — the P0.3 decision requires at least 5 runs per variant. "
              "The kill condition was not evaluated.")
        return 0

    if "b" in rates:
        verdict = "PASS" if rates["b"] >= 0.8 else "KILL"
        print(f"\nVariant B {rates['b'] * 100:.0f}% — kill condition "
              f"{'not triggered' if verdict == 'PASS' else 'TRIGGERED (Phase 5 is cut)'}")
        return 0 if verdict == "PASS" else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
