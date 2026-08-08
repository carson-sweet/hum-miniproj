---
id: MS-006
title: Improvement loop
type: milestone
status: new
created: 2026-08-08
target_release: unscheduled
sequence: 6
owner: Carson Sweet
depends_on: MS-005
source: manual
---
# MS-006: Improvement loop

**Version 1.1 — 2026-08-08**

## Outcome

Analyze, identify patterns, propose improvements, confirm impact. The loop reads the register and proposes a diff against a versioned instruction file — it never applies one. Human approval is the gate, and each instruction version carries its contract score so revert is a real operation.

## Measuring success

- [ ] Pattern detector recovers known clusters from the seed corpus with its clustering withheld
- [ ] One full cycle completes end to end: entry → pattern → proposed diff → approved → new contract with negative control → measured before/after
- [ ] Held-out contract score does not regress
- [ ] Where a pattern concerns a production outcome, its new contract asserts on an artifact

## Non-goals

- Applying any proposed diff automatically — human approval is the gate
- Building concurrently with MS-005; analyzing an empty register produces confident nothing
- Measuring success only on targeted contracts; the held-out set is what catches overfitting

## Contributing work items

_None yet._

## Notes

Confidence is Low if built concurrently with MS-005, and moves to moderate when sequenced after capture is proven, with outcome assertions and a held-out set. Held-out score falling while targeted score rises means the loop is overfitting to its own tests.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-6). |
