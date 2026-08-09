"""Token accounting must never quietly under-report. No model calls here."""
import json

import pytest

from eval import cost
from eval.cost import (
    Usage,
    cost_usd,
    format_totals,
    parse_usage,
    record,
    record_unmetered,
    totals,
)

REAL_EVENTS = (
    '{"type":"thread.started","thread_id":"019fe1"}\n'
    '{"type":"turn.started"}\n'
    '{"type":"item.completed","item":{"type":"agent_message","text":"ok"}}\n'
    '{"type":"turn.completed","usage":{"input_tokens":12640,"cached_input_tokens":8960,'
    '"cache_write_input_tokens":0,"output_tokens":5,"reasoning_output_tokens":0}}\n'
)


def test_parse_usage_reads_the_real_schema():
    u = parse_usage(REAL_EVENTS)
    assert u.input_tokens == 12640
    assert u.cached_input_tokens == 8960
    assert u.output_tokens == 5
    assert u.total == 12645


def test_parse_usage_sums_multiple_turns():
    u = parse_usage(REAL_EVENTS + REAL_EVENTS)
    assert u.input_tokens == 25280
    assert u.output_tokens == 10


def test_parse_usage_returns_zero_on_banner_output():
    assert parse_usage("OpenAI Codex v0.145.0\nmodel: gpt-5.6-luna\n").total == 0


def test_parse_usage_survives_malformed_lines():
    assert parse_usage('{broken\n' + REAL_EVENTS).input_tokens == 12640


def test_cost_matches_hand_calculation():
    # 1M input, 1M output on luna = $0.20 + $1.20
    u = Usage(input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost_usd(u, "gpt-5.6-luna") == pytest.approx(1.40)


def test_sol_is_25x_luna_on_input():
    u = Usage(input_tokens=1_000_000)
    assert cost_usd(u, "gpt-5.6-sol") == pytest.approx(5.00)
    assert cost_usd(u, "gpt-5.6-luna") == pytest.approx(0.20)


def test_unknown_model_yields_none_not_a_guess():
    assert cost_usd(Usage(input_tokens=1000), "some-future-model") is None


def test_cached_input_billed_at_full_rate_by_default():
    """Conservative by design — the estimate must not run low."""
    u = Usage(input_tokens=1_000_000, cached_input_tokens=1_000_000)
    assert cost_usd(u, "gpt-5.6-luna") == pytest.approx(0.20)


def test_cached_discount_is_applied_when_configured(monkeypatch):
    monkeypatch.setattr(cost, "CACHED_INPUT_DISCOUNT", 0.1)
    u = Usage(input_tokens=1_000_000, cached_input_tokens=1_000_000)
    assert cost_usd(u, "gpt-5.6-luna") == pytest.approx(0.02)


def test_record_and_totals_roundtrip(tmp_path):
    led = tmp_path / "ledger.jsonl"
    record(role="subject", model="gpt-5.6-luna", usage=parse_usage(REAL_EVENTS), ledger=led)
    record(role="judge", model="gpt-5.6-luna", usage=Usage(input_tokens=1000, output_tokens=10), ledger=led)
    t = totals(ledger=led)
    assert t["calls"] == 2
    assert t["cost_usd"] > 0
    assert t["by_model"]["gpt-5.6-luna"]["calls"] == 2
    assert t["unpriced_calls"] == 0


def test_totals_flags_unpriced_calls_rather_than_ignoring_them(tmp_path):
    led = tmp_path / "ledger.jsonl"
    record(role="subject", model="mystery-model", usage=Usage(input_tokens=999), ledger=led)
    t = totals(ledger=led)
    assert t["unpriced_calls"] == 1
    assert "unpriced" in format_totals(t)


def test_totals_on_missing_ledger_is_zero_not_a_crash(tmp_path):
    assert totals(ledger=tmp_path / "nope.jsonl")["calls"] == 0


def test_ledger_rows_are_valid_json_with_cost(tmp_path):
    led = tmp_path / "ledger.jsonl"
    record(role="subject", model="gpt-5.6-luna", usage=parse_usage(REAL_EVENTS),
           label="fixture-x", ledger=led)
    row = json.loads(led.read_text().splitlines()[0])
    assert row["role"] == "subject"
    assert row["label"] == "fixture-x"
    assert row["input_tokens"] == 12640
    assert isinstance(row["cost_usd"], float)


def test_provider_reported_cost_overrides_price_estimate(tmp_path):
    led = tmp_path / "ledger.jsonl"
    record(
        role="subject",
        model="provider-routed-model",
        usage=Usage(input_tokens=100, output_tokens=10),
        ledger=led,
        cost_override=0.0042,
    )
    row = json.loads(led.read_text())
    assert row["cost_usd"] == 0.0042
    assert row["cost_source"] == "provider"


def test_unavailable_usage_is_flagged_not_reported_as_zero_cost(tmp_path):
    led = tmp_path / "ledger.jsonl"
    record_unmetered(
        role="subject", model="gpt-5.6-luna", harness="junie", ledger=led
    )
    row = json.loads(led.read_text())
    assert row["cost_usd"] is None
    assert row["cost_source"] == "unavailable"
    assert totals(ledger=led)["unpriced_calls"] == 1


def test_totals_can_be_scoped_to_one_parallel_run(tmp_path):
    led = tmp_path / "ledger.jsonl"
    record(
        role="subject", model="gpt-5.6-luna", usage=Usage(input_tokens=100),
        ledger=led, run_id="run-a",
    )
    record(
        role="subject", model="gpt-5.6-luna", usage=Usage(input_tokens=200),
        ledger=led, run_id="run-b",
    )
    scoped = totals(ledger=led, run_id="run-a")
    assert scoped["calls"] == 1
    assert scoped["by_model"]["gpt-5.6-luna"]["input"] == 100
