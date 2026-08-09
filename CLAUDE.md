# hum-miniproj

A portable Agent Skill implementing the MiniProject operating model — a delivery
method for AI-accelerated work that bundles work by complete improvement rather
than by technical layer. Runs anywhere the Agent Skills standard is supported.

## Key directories

- `skills/miniproject/` — the portable skill: SKILL.md, references, validator
- `eval/` — behavioral contract harness; drivers, judge, assertions
- `fixtures/` — disposable fixtures copied to temp for each subject run
- `docs/` — design documents

## Commands

```bash
# Install
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# Test — fast, deterministic, no model calls
python3 -m pytest -m "not integration"

# Test — hits the real Codex CLI, costs model calls
python3 -m pytest -m integration

# Prove the harness end to end on the throwaway fixture
python3 -m eval.smoke

# Run the production behavioral matrix across Codex, Junie, and Claude
python3 -m eval.run_contracts

# Qualify every negative control (five trials per contract and harness)
python3 -m eval.run_contracts --negative-control --repeat 5

# What have model calls cost?
python3 -m eval.spend
```

Every model call is metered to `eval/runs/ledger.jsonl`. Default models are the
cheapest capable option (`gpt-5.6-luna`); override with `EVAL_SUBJECT_MODEL` /
`EVAL_JUDGE_MODEL` when capability is genuinely the variable under test.

Integration tests and the smoke run require `codex` on PATH and an authenticated
Codex session. The production behavioral matrix additionally requires Junie,
the pinned Claude Docker image, and `JUNIE_API_KEY` plus
`CLAUDE_CODE_OAUTH_TOKEN` in the gitignored `.env.local`. `python3 -m eval.smoke`
exits 0 green, 1 red, 3 on probe failure.

## Project-specific rules

- Every behavioral contract ships with a negative control — a declared mutation
  that should make it fail. A contract that has never failed has not been shown
  to work.
- The eval harness is a primary engineering artifact, not a supporting concern.
- The skill must stay portable across harnesses (Claude Code, Codex, Junie) —
  no harness-specific assumptions in SKILL.md.
- `eval/runs/` is regenerated output, not source. Never commit it.

## SweetClaude

- Read `.sweetclaude/state/phase.yaml` and `.sweetclaude/state/improvement-register.md` at session start if they exist. If `.sweetclaude/state/phase.yaml` exists and `.sweetclaude/disabled` does not exist, invoke `sweetclaude:status` automatically at session start.
- Follow the interaction model in `/Users/carsonsweet/.claude/plugins/cache/sweetclaude-stable/sweetclaude/4.5.2/rules/interaction-model.md`.
- Respect the current deference level. Ask if not set.
- Never push for phase advancement. The user decides when to move on.
