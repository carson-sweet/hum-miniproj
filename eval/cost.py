"""Token accounting. Every model call in this repo is metered and logged.

Written after a session that spent an unmeasured amount because nothing counted
tokens. Costs are estimated conservatively: cached input is billed at the full
input rate unless CACHED_INPUT_DISCOUNT says otherwise, so the number errs high
rather than flattering the total.

Prices are USD per million tokens, as listed by the provider on 2026-08-08.
An unknown model yields cost None rather than a guess.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path

PRICING: dict[str, tuple[float, float]] = {
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.6-terra": (2.00, 12.00),
    "gpt-5.6-sol": (5.00, 30.00),
    "gpt-5.5": (5.00, 30.00),
    "gpt-5.4": (2.50, 15.00),
    "gpt-5.3-codex": (1.75, 14.00),
    "gpt-5.2": (1.75, 14.00),
    "gpt-5": (1.25, 10.00),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3.5-flash-lite": (0.25, 1.50),
    "gemini-3.6-flash": (0.75, 3.75),
    "gemini-3.1-pro-preview": (2.00, 12.00),
    "grok-4.3": (1.25, 2.50),
    "grok-4.5": (2.00, 6.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-opus-5": (5.00, 25.00),
}

# Cached input is commonly discounted, but the exact rate is unconfirmed for these
# endpoints. Default 1.0 bills it at full price so the estimate never runs low.
CACHED_INPUT_DISCOUNT = float(os.environ.get("CACHED_INPUT_DISCOUNT", "1.0"))

LEDGER = Path(__file__).resolve().parent / "runs" / "ledger.jsonl"


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            self.input_tokens + other.input_tokens,
            self.cached_input_tokens + other.cached_input_tokens,
            self.output_tokens + other.output_tokens,
            self.reasoning_output_tokens + other.reasoning_output_tokens,
        )


def parse_usage(events_jsonl: str) -> Usage:
    """Sum usage across turn.completed events in a --json stream."""
    total = Usage()
    for line in events_jsonl.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        u = event.get("usage")
        if not isinstance(u, dict):
            continue
        total = total + Usage(
            int(u.get("input_tokens") or 0),
            int(u.get("cached_input_tokens") or 0),
            int(u.get("output_tokens") or 0),
            int(u.get("reasoning_output_tokens") or 0),
        )
    return total


def cost_usd(usage: Usage, model: str) -> float | None:
    price = PRICING.get(model)
    if price is None:
        return None
    in_rate, out_rate = price
    uncached = max(usage.input_tokens - usage.cached_input_tokens, 0)
    cached = min(usage.cached_input_tokens, usage.input_tokens)
    dollars = (
        uncached * in_rate
        + cached * in_rate * CACHED_INPUT_DISCOUNT
        + usage.output_tokens * out_rate
    ) / 1_000_000
    return round(dollars, 6)


def record(*, role: str, model: str, usage: Usage, harness: str = "codex",
           label: str = "", ledger: Path | None = None,
           cost_override: float | None = None,
           run_id: str | None = None) -> float | None:
    """Append one metered call to the ledger. Returns its cost."""
    estimated = cost_usd(usage, model)
    dollars = round(cost_override, 6) if cost_override is not None else estimated
    path = ledger or LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "role": role,
        "harness": harness,
        "model": model,
        "label": label,
        "run_id": run_id or os.environ.get("EVAL_RUN_ID"),
        **asdict(usage),
        "cost_usd": dollars,
        "cost_source": "provider" if cost_override is not None else (
            "estimate" if estimated is not None else "unpriced"
        ),
    }
    with path.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    return dollars


def record_unmetered(
    *,
    role: str,
    model: str,
    harness: str,
    label: str = "",
    ledger: Path | None = None,
    run_id: str | None = None,
) -> None:
    """Record a real call whose provider surface exposes no usage data."""
    path = ledger or LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "role": role,
        "harness": harness,
        "model": model,
        "label": label,
        "run_id": run_id or os.environ.get("EVAL_RUN_ID"),
        **asdict(Usage()),
        "cost_usd": None,
        "cost_source": "unavailable",
    }
    with path.open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def totals(
    ledger: Path | None = None,
    since: str | None = None,
    run_id: str | None = None,
) -> dict:
    path = ledger or LEDGER
    if not path.exists():
        return {"calls": 0, "cost_usd": 0.0, "unpriced_calls": 0, "by_model": {}}
    calls = unpriced = 0
    cost = 0.0
    by_model: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if since and row.get("ts", "") < since:
            continue
        if run_id and row.get("run_id") != run_id:
            continue
        calls += 1
        m = by_model.setdefault(row.get("model", "?"),
                                {"calls": 0, "cost_usd": 0.0, "input": 0, "output": 0})
        m["calls"] += 1
        m["input"] += row.get("input_tokens", 0)
        m["output"] += row.get("output_tokens", 0)
        if row.get("cost_usd") is None:
            unpriced += 1
        else:
            cost += row["cost_usd"]
            m["cost_usd"] = round(m["cost_usd"] + row["cost_usd"], 6)
    return {"calls": calls, "cost_usd": round(cost, 4),
            "unpriced_calls": unpriced, "by_model": by_model}


def format_totals(t: dict) -> str:
    lines = [f"{t['calls']} call(s), ${t['cost_usd']:.4f}"]
    for model, m in sorted(t["by_model"].items(), key=lambda kv: -kv[1]["cost_usd"]):
        lines.append(f"  {model:<22} {m['calls']:>3} calls  "
                     f"{m['input']:>8} in  {m['output']:>6} out  ${m['cost_usd']:.4f}")
    if t["unpriced_calls"]:
        lines.append(f"  ({t['unpriced_calls']} call(s) on unpriced models — cost unknown)")
    return "\n".join(lines)
