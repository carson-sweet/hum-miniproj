---
id: MS-002
title: Portable substrate
type: milestone
status: new
created: 2026-08-08
target_release: unscheduled
sequence: 2
owner: Carson Sweet
depends_on: MS-001
source: manual
---
# MS-002: Portable substrate

**Version 1.1 — 2026-08-08**

## Outcome

The repo scaffold and the enforcement that keeps it portable. `lint_portable.py` runs in CI and fails on harness-specific constructs and provenance leaks, so portability is enforced mechanically rather than by discipline. `install.sh` puts the skill in all three harnesses idempotently and reversibly.

## Measuring success

- [ ] `lint_portable.py` passes on the scaffold
- [ ] `lint_portable.py` fails on a deliberately planted violation
- [ ] `install.sh` verified in all three harnesses; the skill appears in each harness's skill listing
- [ ] `lint_portable.py` runs in CI on every PR

## Non-goals

- Any MiniProject skill content — that is MS-003
- Hooks, bang preambles, plugin-root variables, or interactive-question primitives; the portable subset is `SKILL.md` + `references/` + `scripts/` only
- Verifying portability by inspection instead of by lint

## Contributing work items

_None yet._

## Notes

Provenance leaks are a lint concern, not just a legal one: any incompatible SPDX tag or verbatim block imported from a differently-licensed source must fail CI.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-2). |
