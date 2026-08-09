---
id: MS-006
title: Improvement loop
type: milestone
status: done
created: 2026-08-08
target_release: unscheduled
sequence: 6
owner: Carson Sweet
depends_on: MS-005
source: manual
---
# MS-006: Improvement loop

**Version 1.2 — 2026-08-09**

## Outcome

Analyze, identify patterns, propose improvements, confirm impact. The loop reads the register and proposes a diff against a versioned instruction file — it never applies one. Human approval is the gate, and each instruction version carries its contract score so revert is a real operation.

## Measuring success

- [x] Pattern detector recovers known clusters from the seed corpus with its clustering withheld
- [x] One full cycle completes end to end: entry → pattern → proposed diff → approved → new contract with negative control → measured before/after
- [x] Held-out contract score does not regress
- [x] Where a pattern concerns a production outcome, its new contract asserts on an artifact

## Non-goals

- Applying any proposed diff automatically — human approval is the gate
- Building concurrently with MS-005; analyzing an empty register produces confident nothing
- Measuring success only on targeted contracts; the held-out set is what catches overfitting

## Contributing work items

- US-IMP-002 — improve instructions without self-applying or overfitting

## Notes

Confidence is Low if built concurrently with MS-005, and moves to moderate when sequenced after capture is proven, with outcome assertions and a held-out set. Held-out score falling while targeted score rises means the loop is overfitting to its own tests.

**2026-08-09 — completed after MS-005 qualification.** The deterministic detector recovered all four withheld seed clusters. The loop now binds analysis, pattern, base instruction, candidate, forward and reverse diffs, exact human approval, targeted and held-out scores, and current/previous instruction hashes. No loop script applies the proposal.

The finalized full-cycle contract passed in Codex `20260809T133354Z-081947000`, Junie `20260809T133354Z-815852000`, and Claude `20260809T133354Z-526118000`. Its fixed-packet negative control was detected in Codex `20260809T132653Z-892431000`, Junie `20260809T132654Z-655630000`, and Claude `20260809T133720Z-070201000`.

The finalized mutation later qualified at 5/5 in Codex, 5/5 in Junie, and 5/5 in Claude under run `20260809T145716Z-056142000`, exceeding the 4/5 per-harness floor.

Deterministic acceptance separately proves that a held-out regression fails, a production-outcome cycle without an artifact contract fails, a missing or mismatched approval fails, and stale version hashes fail. The initial mutation design let subjects compensate while constructing the cycle; it was discarded and replaced with a fixed, hash-bound packet plus a one-shot no-repair prompt.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.3     | 2026-08-09 | Recorded three-harness five-run mutation qualification. |
| 1.2     | 2026-08-09 | Completed pattern, approval, reversible diff, score, and held-out gates. |
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-6). |
