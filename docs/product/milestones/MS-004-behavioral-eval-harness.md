---
id: MS-004
title: Behavioral eval harness
type: milestone
status: new
created: 2026-08-08
target_release: unscheduled
sequence: 4
owner: Carson Sweet
depends_on: MS-003
source: manual
---
# MS-004: Behavioral eval harness

**Version 1.1 — 2026-08-08**

## Outcome

The trust anchor, built to a higher standard than the rest of the repo because it cannot check its own correctness. Contracts carry their own negative controls, and the runner uses fresh-context subjects with an isolated judge across all three harnesses.

## Measuring success

- [ ] Every contract has a negative control
- [ ] `--negative-control` mode reports 100% detection
- [ ] Full matrix runs across three harnesses with per-harness results recorded
- [ ] At least one contract asserts on an artifact produced rather than on response text

## Non-goals

- Running the behavioral matrix per-commit — it runs on demand and on model-version change
- Trusting any contract that has never failed on purpose
- Improvement capture — that is MS-005

## Contributing work items

_None yet._

## Notes

A model can describe correct behavior fluently while producing nothing. Where a contract concerns an outcome, it asserts on files produced.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-4). |
