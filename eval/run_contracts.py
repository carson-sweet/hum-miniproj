"""Run behavioral contracts against isolated Codex, Junie, and Claude subjects.

    python3 -m eval.run_contracts
    python3 -m eval.run_contracts --negative-control --repeat 5
    python3 -m eval.run_contracts --harness codex --contract MP-C01

Exit codes: 0 all good; 1 contract failure; 2 broken negative control;
3 inert mutation, invalid contract, credential failure, or harness failure;
4 metered budget exhausted before the next subject call.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml

from eval.assertions import check_artifact
from eval.config import JUDGE_MODEL, subject_model
from eval.cost import format_totals, totals
from eval.drivers.claude import ClaudeDriver
from eval.drivers.codex import CodexDriver, isolated_codex_home
from eval.drivers.junie import JunieDriver
from eval.env import load_local_value
from eval.judge import judge
from eval.mutate import apply_mutations

REPO = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = REPO / "eval" / "contracts"
SKILL_SRC = REPO / "skills" / "miniproject"
RUNS_DIR = REPO / "eval" / "runs"
LOCAL_ENV = REPO / ".env.local"

ALL_HARNESSES = ("codex", "junie", "claude")
DETECTION_FLOOR = 0.8
ALLOWED_SUBJECT_ENV = {"MINIPROJECT_REGISTER", "MINIPROJECT_SOURCE_SESSION"}


class BudgetExceeded(RuntimeError):
    """Raised before a subject call would consume the reserved budget."""


@contextmanager
def subject_environment(values: dict[str, str] | None) -> Iterator[None]:
    """Temporarily expose allowlisted non-secret contract inputs to one subject."""
    values = values or {}
    previous = {key: os.environ.get(key) for key in values}
    try:
        os.environ.update(values)
        yield
    finally:
        for key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def enforce_metered_budget(
    *, max_cost_usd: float, since: str, reserve_usd: float
) -> float:
    """Fail before a call when current spend plus its reserve exceeds the cap."""
    spent = float(totals(since=since)["cost_usd"])
    if spent + reserve_usd > max_cost_usd:
        raise BudgetExceeded(
            f"metered spend ${spent:.4f} plus ${reserve_usd:.4f} reserve "
            f"would exceed ${max_cost_usd:.4f} cap"
        )
    return spent


def classify(
    verdicts: list[str], negative: bool, floor: float = DETECTION_FLOOR
) -> tuple[str, str]:
    """Collapse repeated runs into one verdict plus a rate."""
    n = len(verdicts)
    if not n:
        return "NO-RUNS", "0/0"
    if "HARNESS-ERROR" in verdicts:
        return "HARNESS-ERROR", f"{verdicts.count('HARNESS-ERROR')}/{n} error"
    if "MUTATION-INERT" in verdicts:
        return "MUTATION-INERT", f"{verdicts.count('MUTATION-INERT')}/{n} inert"
    good = "DETECTED" if negative else "PASS"
    hits = verdicts.count(good)
    rate = f"{hits}/{n}"
    if negative:
        return ("DETECTED" if hits / n >= floor else "BROKEN"), rate
    return ("PASS" if hits == n else "FAIL"), rate


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
    rate: str = ""
    runs: list = field(default_factory=list)


def validate_contract(data: dict) -> dict:
    """Reject contract shapes that could silently weaken an eval claim."""
    if not isinstance(data, dict):
        raise ValueError("contract must be a mapping")
    for key in ("id", "name", "subject", "assert", "negative_control", "harnesses"):
        if key not in data:
            raise ValueError(f"contract missing required field {key!r}")

    subject = data["subject"]
    assertion = data["assert"]
    negative = data["negative_control"]
    if not isinstance(subject, dict) or not subject.get("fixture") or not subject.get("prompt"):
        raise ValueError(f"{data['id']}: subject requires fixture and prompt")
    environment = subject.get("environment", {})
    if not isinstance(environment, dict):
        raise ValueError(f"{data['id']}: subject.environment must be a mapping")
    unsafe_environment = set(environment) - ALLOWED_SUBJECT_ENV
    if unsafe_environment or any(not isinstance(value, str) for value in environment.values()):
        raise ValueError(
            f"{data['id']}: subject.environment may contain only "
            f"{', '.join(sorted(ALLOWED_SUBJECT_ENV))} string values"
        )
    if not isinstance(assertion, dict) or assertion.get("type") not in {"response", "artifact"}:
        raise ValueError(f"{data['id']}: assert.type must be response or artifact")
    if assertion["type"] == "response" and not assertion.get("pass"):
        raise ValueError(f"{data['id']}: response assertion requires pass criterion")
    if assertion["type"] == "artifact":
        if subject.get("sandbox") != "workspace-write":
            raise ValueError(f"{data['id']}: artifact assertion requires sandbox: workspace-write")
        if not assertion.get("checks"):
            raise ValueError(f"{data['id']}: artifact assertion requires checks")
    if not isinstance(negative, dict) or not negative.get("mutate"):
        raise ValueError(f"{data['id']}: negative_control requires mutate")
    mutation = negative["mutate"]
    if not isinstance(mutation, (dict, list)) or isinstance(mutation, list) and not mutation:
        raise ValueError(f"{data['id']}: negative_control.mutate must not be empty")

    harnesses = data["harnesses"]
    if not isinstance(harnesses, list) or not harnesses:
        raise ValueError(f"{data['id']}: harnesses must not be empty")
    unknown = set(harnesses) - set(ALL_HARNESSES)
    if unknown:
        raise ValueError(f"{data['id']}: unknown harnesses: {', '.join(sorted(unknown))}")
    return data


def load_contracts(only: str | None) -> list[dict]:
    contracts = []
    for path in sorted(CONTRACTS_DIR.glob("*.yaml")):
        data = validate_contract(yaml.safe_load(path.read_text()))
        if only and data["id"] != only:
            continue
        contracts.append(data)
    return contracts


def select_harnesses(contract: dict, requested: list[str] | None) -> list[str]:
    claims = set(contract["harnesses"])
    restriction = set(requested) if requested else set(ALL_HARNESSES)
    return [name for name in ALL_HARNESSES if name in claims and name in restriction]


def select_subject_model(contract: dict, harness: str) -> str:
    overrides = contract["subject"].get("models", {})
    return str(overrides.get(harness) or subject_model(harness))


def install_skill(src: Path, skill_root: Path) -> Path:
    name = yaml.safe_load(src.joinpath("SKILL.md").read_text().split("---")[1])["name"]
    destination = skill_root / name
    if destination.exists():
        raise RuntimeError(f"refusing to overwrite isolated skill path: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, destination)
    return destination


def install_codex_skill(src: Path, codex_home: Path) -> Path:
    """Install once under disposable HOME and link the Codex-specific path."""
    codex_home = Path(codex_home)
    installed = install_skill(src, codex_home.parent / ".agents" / "skills")
    link = codex_home / "skills" / installed.name
    if link.exists() or link.is_symlink():
        raise RuntimeError(f"refusing to overwrite isolated skill path: {link}")
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(installed)
    return installed


@contextmanager
def isolated_subject_driver(harness: str) -> Iterator[tuple[object, Path]]:
    """Yield a driver plus the exact disposable skill copy it will load."""
    if harness == "codex":
        with isolated_codex_home() as home:
            installed = install_codex_skill(SKILL_SRC, home)
            yield CodexDriver(codex_home=home), installed
        return

    with tempfile.TemporaryDirectory(prefix=f"{harness}-eval-home-") as raw_home:
        home = Path(raw_home)
        skill_root = home / "skills"
        installed = install_skill(SKILL_SRC, skill_root)
        if harness == "junie":
            yield JunieDriver(junie_home=home, skill_root=skill_root), installed
            return
        if harness == "claude":
            yield ClaudeDriver(skill_dir=installed), installed
            return
        raise ValueError(f"unknown harness: {harness}")


def probe_harness(harness: str):
    if harness == "codex":
        return CodexDriver().probe()
    with tempfile.TemporaryDirectory(prefix=f"{harness}-probe-") as raw_home:
        home = Path(raw_home)
        if harness == "junie":
            return JunieDriver(junie_home=home, skill_root=home / "skills").probe()
        if harness == "claude":
            return ClaudeDriver(skill_dir=SKILL_SRC).probe()
    raise ValueError(f"unknown harness: {harness}")


def load_credentials(harnesses: list[str]) -> None:
    required = {
        "junie": "JUNIE_API_KEY",
        "claude": "CLAUDE_CODE_OAUTH_TOKEN",
    }
    for harness in harnesses:
        key = required.get(harness)
        if key is None:
            continue
        load_local_value(LOCAL_ENV, key)
        if not os.environ.get(key):
            raise RuntimeError(f"{harness} requires {key}; add it to {LOCAL_ENV}")


def run_one(contract: dict, harness: str, negative: bool, keep: bool) -> Outcome:
    mode = "negative-control" if negative else "normal"
    cid = contract["id"]
    work = Path(tempfile.mkdtemp(prefix=f"eval-{cid}-{harness}-"))

    try:
        with isolated_subject_driver(harness) as (driver, installed_skill):
            if negative:
                mutation = apply_mutations(
                    installed_skill, contract["negative_control"]["mutate"]
                )
                if not mutation.applied:
                    return Outcome(cid, harness, mode, "MUTATION-INERT", mutation.detail)

            fixture = Path(contract["subject"]["fixture"])
            fixture = fixture if fixture.is_absolute() else REPO / fixture
            shutil.copytree(fixture, work, dirs_exist_ok=True)
            subject = contract["subject"]
            model = select_subject_model(contract, harness)
            with subject_environment(subject.get("environment")):
                result = driver.run_subject(
                    fixture=work,
                    prompt=subject["prompt"],
                    model=model,
                    writable=subject.get("sandbox") == "workspace-write",
                    timeout_s=subject.get("timeout_s", 180),
                    events_file=work / ".subject.events" if keep else None,
                )

        if result.exit_code != 0:
            reason = f"subject exit {result.exit_code}: {result.stdout[-500:]}"
            return Outcome(
                cid, harness, mode, "HARNESS-ERROR", reason, result.model,
                result.session_id, round(result.duration_s, 1),
            )

        if contract["assert"]["type"] == "artifact":
            checks = [
                (spec, check_artifact(work, spec))
                for spec in contract["assert"]["checks"]
            ]
            passed = all(outcome.passed for _, outcome in checks)
            reason = "; ".join(outcome.detail for _, outcome in checks)
            details = [
                {"spec": spec, "passed": outcome.passed, "detail": outcome.detail}
                for spec, outcome in checks
            ]
        elif not result.final_message.strip():
            passed, reason, details = False, "subject emitted no final response", []
        else:
            verdict = judge(
                criterion=contract["assert"]["pass"],
                subject_output=result.final_message,
                model=JUDGE_MODEL,
            )
            passed, reason, details = verdict.passed, verdict.reason, []

        if negative:
            verdict_name = "BROKEN" if passed else "DETECTED"
        else:
            verdict_name = "PASS" if passed else "FAIL"

        return Outcome(
            cid,
            harness,
            mode,
            verdict_name,
            reason,
            result.model,
            result.session_id,
            round(result.duration_s, 1),
            details,
        )
    finally:
        if keep:
            print(f"    workdir kept: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


def write_results(run_dir: Path, outcomes: list[Outcome], versions: dict[str, str]) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "results.jsonl"
    with path.open("w") as handle:
        for outcome in outcomes:
            row = {**outcome.__dict__, "cli_version": versions.get(outcome.harness)}
            handle.write(json.dumps(row) + "\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract")
    parser.add_argument("--harness", action="append", choices=ALL_HARNESSES)
    parser.add_argument("--negative-control", action="store_true")
    parser.add_argument("--keep-workdirs", action="store_true")
    parser.add_argument(
        "--repeat", type=int, default=1,
        help="runs per contract; negative controls need 5 to score a rate",
    )
    parser.add_argument(
        "--max-metered-cost",
        type=float,
        help="stop before the next subject call would exceed this USD cap",
    )
    parser.add_argument(
        "--budget-since",
        help="include ledger rows at or after this UTC timestamp in the cap",
    )
    parser.add_argument(
        "--budget-reserve",
        type=float,
        default=0.25,
        help="USD reserved for each next subject call (default: 0.25)",
    )
    args = parser.parse_args()

    if args.max_metered_cost is not None and args.max_metered_cost <= 0:
        print("invalid budget: --max-metered-cost must be positive")
        return 3
    if args.budget_reserve < 0:
        print("invalid budget: --budget-reserve may not be negative")
        return 3

    try:
        contracts = load_contracts(args.contract)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"invalid contract: {exc}")
        return 3
    if not contracts:
        print("no contracts matched")
        return 3

    selected = []
    for contract in contracts:
        for harness in select_harnesses(contract, args.harness):
            if harness not in selected:
                selected.append(harness)
    if not selected:
        print("no contract claims the requested harness")
        return 3

    try:
        load_credentials(selected)
    except (OSError, ValueError, PermissionError, RuntimeError) as exc:
        print(f"credential setup failed: {exc}")
        return 3

    versions = {}
    for harness in selected:
        probe = probe_harness(harness)
        if not probe.ok:
            print(f"{harness} probe failed: {probe.detail}")
            return 3
        versions[harness] = probe.version or "unknown"
        print(f"harness {harness} ({versions[harness]})")

    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    budget_since = args.budget_since or started_at
    run_id = f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{time.time_ns() % 1_000_000_000:09d}"
    os.environ["EVAL_RUN_ID"] = run_id
    print(f"mode {'negative-control' if args.negative_control else 'normal'}")
    print(f"judge {JUDGE_MODEL}\n")
    if args.max_metered_cost is not None:
        print(
            f"metered budget ${args.max_metered_cost:.2f} since {budget_since}; "
            f"${args.budget_reserve:.2f} reserved per next subject call"
        )
        if "junie" in selected:
            print("note: Junie usage is unavailable and is not included in the metered cap")
        print()
    if args.negative_control and args.repeat < 5:
        print(
            f"note: --repeat {args.repeat}; the plan asks for 5 to score a detection rate.\n"
        )

    outcomes = []
    for contract in contracts:
        for harness in select_harnesses(contract, args.harness):
            runs = []
            for _ in range(args.repeat):
                if args.max_metered_cost is not None:
                    try:
                        enforce_metered_budget(
                            max_cost_usd=args.max_metered_cost,
                            since=budget_since,
                            reserve_usd=args.budget_reserve,
                        )
                    except BudgetExceeded as exc:
                        print(f"BUDGET-STOP — {exc}")
                        return 4
                runs.append(
                    run_one(
                        contract, harness, args.negative_control, args.keep_workdirs
                    )
                )
            verdict, rate = classify(
                [run.verdict for run in runs], args.negative_control
            )
            last = runs[-1]
            outcome = Outcome(
                contract["id"],
                harness,
                last.mode,
                verdict,
                last.reason,
                last.model,
                last.session_id,
                last.duration_s,
                last.checks,
                rate,
                [run.verdict for run in runs],
            )
            outcomes.append(outcome)
            print(
                f"  {outcome.verdict:<15} {outcome.rate:<6} "
                f"{outcome.contract:<8} {outcome.harness}  {contract['name']}"
            )
            if args.repeat > 1:
                print(f"                         runs: {', '.join(outcome.runs)}")

    run_dir = RUNS_DIR / run_id
    write_results(run_dir, outcomes, versions)
    spend = totals(since=started_at, run_id=run_id)
    (run_dir / "cost.json").write_text(json.dumps(spend, indent=2))

    verdicts = [outcome.verdict for outcome in outcomes]
    print(f"\n{len(outcomes)} contract-harness result(s). results: {run_dir}")
    print("cost this run: " + format_totals(spend))
    if "HARNESS-ERROR" in verdicts:
        print("HARNESS-ERROR present — infrastructure failed, so behavior was not scored.")
        return 3
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
