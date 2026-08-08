"""Contract runner. Steps 4-5 of docs/eval-codex-driver.md.

    python3 -m eval.run_contracts                    # normal mode
    python3 -m eval.run_contracts --negative-control # apply each declared mutation
    python3 -m eval.run_contracts --contract MP-C01

Exit codes: 0 all good · 1 a contract failed · 2 a mutation survived (BROKEN)
· 3 a mutation was inert, or the harness probe failed.

Runs serially. Each contract installs the skill at a shared path so the harness
can discover it, and mutations differ per contract, so parallel runs would
clash. Concurrency needs per-run skill roots first.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from eval.assertions import check_artifact
from eval.drivers.codex import CodexDriver
from eval.judge import judge
from eval.mutate import apply_mutation

REPO = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = REPO / "eval" / "contracts"
SKILL_SRC = REPO / "spikes" / "p0-2-detection" / "skill"
RUNS_DIR = REPO / "eval" / "runs"
MODEL = "gpt-5.6-sol"

AGENTS_ROOT = Path.home() / ".agents" / "skills"
HARNESS_SKILL_ROOT = {"codex": Path.home() / ".codex" / "skills"}
DRIVERS = {"codex": CodexDriver}


@dataclass
class Outcome:
    contract: str
    harness: str
    mode: str
    verdict: str
    reason: str = ""
    model: str | None = None
    session_id: str | None = None
    duration_s: float = 0.0
    checks: list = field(default_factory=list)


def load_contracts(only: str | None) -> list[dict]:
    out = []
    for path in sorted(CONTRACTS_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        if only and data["id"] != only:
            continue
        if data["assert"]["type"] == "artifact" and data["subject"].get("sandbox") != "workspace-write":
            raise SystemExit(
                f"{data['id']}: artifact assertion requires sandbox: workspace-write"
            )
        out.append(data)
    return out


def install_skill(src: Path, harness: str) -> tuple[Path, Path]:
    name = yaml.safe_load(src.joinpath("SKILL.md").read_text().split("---")[1])["name"]
    agents_dir = AGENTS_ROOT / name
    link = HARNESS_SKILL_ROOT[harness] / name
    for p in (agents_dir, link):
        if p.exists() and not p.is_symlink():
            raise SystemExit(f"refusing: {p} exists and is not ours")
    uninstall(agents_dir, link)
    agents_dir.parent.mkdir(parents=True, exist_ok=True)
    link.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, agents_dir)
    link.symlink_to(agents_dir)
    return agents_dir, link


def uninstall(agents_dir: Path, link: Path) -> None:
    if link.is_symlink():
        link.unlink()
    shutil.rmtree(agents_dir, ignore_errors=True)


def run_one(contract: dict, harness: str, negative: bool, keep: bool) -> Outcome:
    mode = "negative-control" if negative else "normal"
    cid = contract["id"]
    driver = DRIVERS[harness]()
    agents_dir, link = install_skill(SKILL_SRC, harness)
    work = Path(tempfile.mkdtemp(prefix=f"eval-{cid}-"))

    try:
        if negative:
            m = apply_mutation(agents_dir, contract["negative_control"]["mutate"])
            if not m.applied:
                return Outcome(cid, harness, mode, "MUTATION-INERT", m.detail)

        shutil.copytree(contract["subject"]["fixture"], work, dirs_exist_ok=True)
        sub = contract["subject"]
        result = driver.run_subject(
            fixture=work,
            prompt=sub["prompt"],
            model=MODEL,
            writable=sub.get("sandbox") == "workspace-write",
            timeout_s=sub.get("timeout_s", 180),
        )

        if contract["assert"]["type"] == "artifact":
            checks = [
                (spec, check_artifact(work, spec)) for spec in contract["assert"]["checks"]
            ]
            passed = all(o.passed for _, o in checks)
            reason = "; ".join(o.detail for _, o in checks)
            details = [{"spec": s, "passed": o.passed, "detail": o.detail} for s, o in checks]
        else:
            v = judge(
                criterion=contract["assert"]["pass"],
                subject_output=result.final_message,
                model=MODEL,
            )
            passed, reason, details = v.passed, v.reason, []

        if negative:
            expected_fail = contract["negative_control"].get("expect", "FAIL") == "FAIL"
            verdict = "BROKEN" if (passed and expected_fail) else "DETECTED"
        else:
            verdict = "PASS" if passed else "FAIL"

        return Outcome(cid, harness, mode, verdict, reason, result.model,
                       result.session_id, round(result.duration_s, 1), details)
    finally:
        uninstall(agents_dir, link)
        if keep:
            print(f"    workdir kept: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract")
    ap.add_argument("--harness", default="codex", choices=sorted(DRIVERS))
    ap.add_argument("--negative-control", action="store_true")
    ap.add_argument("--keep-workdirs", action="store_true")
    args = ap.parse_args()

    driver = DRIVERS[args.harness]()
    probe = driver.probe()
    if not probe.ok:
        print(f"probe failed: {probe.detail}")
        return 3
    print(f"harness {args.harness} ({probe.version})  mode "
          f"{'negative-control' if args.negative_control else 'normal'}\n")

    contracts = load_contracts(args.contract)
    if not contracts:
        print("no contracts matched")
        return 3

    outcomes = []
    for c in contracts:
        o = run_one(c, args.harness, args.negative_control, args.keep_workdirs)
        outcomes.append(o)
        print(f"  {o.verdict:<15} {o.contract}  {c['name']}")
        if o.reason:
            print(f"                  {o.reason[:150]}")

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_dir = RUNS_DIR / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "results.jsonl").open("w") as fh:
        for o in outcomes:
            fh.write(json.dumps({**o.__dict__, "cli_version": probe.version}) + "\n")

    verdicts = [o.verdict for o in outcomes]
    print(f"\n{len(outcomes)} contract(s). results: {run_dir}")
    if "MUTATION-INERT" in verdicts:
        print("MUTATION-INERT present — a mutation changed nothing, so it scored nothing.")
        return 3
    if "BROKEN" in verdicts:
        print("BROKEN — a contract survived its own mutation. It is not measuring the rule.")
        return 2
    if "FAIL" in verdicts:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
