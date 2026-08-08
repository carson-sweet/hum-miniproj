"""Print what this repo has spent on model calls.

    python3 -m eval.spend            # everything
    python3 -m eval.spend 2026-08-08 # since a timestamp prefix
"""
import sys

from eval.cost import LEDGER, format_totals, totals

since = sys.argv[1] if len(sys.argv) > 1 else None
t = totals(since=since)
print(f"ledger: {LEDGER}")
print(format_totals(t))
