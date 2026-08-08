# hum-miniproj

A portable Agent Skill implementing the MiniProject operating model — a delivery
method for AI-accelerated work that bundles work by complete improvement rather
than by technical layer. Runs anywhere the Agent Skills standard is supported.

## Key directories

- `skills/miniproject/` — the portable skill: SKILL.md, references, validators (not yet created)
- `eval/` — behavioral contract harness with negative controls (not yet created)
- `docs/` — design documents

## Commands

```bash
# Install
# TODO: no package manifest yet (.gitignore suggests Python + venv)

# Test
# TODO: no test runner configured yet (.gitignore suggests pytest)

# Build
# TODO: add build command
```

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
