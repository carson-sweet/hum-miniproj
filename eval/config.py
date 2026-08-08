"""Model selection, in one place.

Defaults are the cheapest capable option. A behavioural contract tests whether an
instruction changes behaviour, and a strong model often follows the rule from its
own priors — which is exactly how MP-C02 ended up measuring nothing. A cheaper
model has weaker priors, so contracts discriminate better AND cost 25x less.

Override per run:
    EVAL_SUBJECT_MODEL=gpt-5.6-sol python3 -m eval.run_contracts
"""
import os

SUBJECT_MODEL = os.environ.get("EVAL_SUBJECT_MODEL", "gpt-5.6-luna")
JUDGE_MODEL = os.environ.get("EVAL_JUDGE_MODEL", "gpt-5.6-luna")
