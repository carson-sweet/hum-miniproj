---
id: MS-001
title: Assumptions falsified or confirmed
type: milestone
status: active
created: 2026-08-08
target_release: unscheduled
sequence: 1
owner: Carson Sweet
source: manual
---
# MS-001: Assumptions falsified or confirmed

**Version 1.1 — 2026-08-08**

## Outcome

Phase 0, the falsification gate. Four load-bearing assumptions each get a spike designed to kill them, and all four run before any skill content is written. The milestone is not "the spikes passed" — it is that each assumption has a recorded answer, and that any triggered kill condition has been written up as a plan revision. A confirmed kill that reshapes the plan completes this milestone just as legitimately as four green results.

## Measuring success

- [ ] P0.1 answered with recorded evidence: bundled `scripts/` either do or do not execute under Codex and Junie, sentinel file checked in each harness
- [ ] P0.2 answered with recorded evidence: three mutated contracts re-run, FAIL expected on all three
- [ ] P0.3 answered with recorded evidence: capture rate measured over five runs each of Variant A and Variant B, per harness
- [ ] P0.4 answered with recorded evidence: decision points run as numbered prose in each harness, agent observed to present bounded choices and wait
- [ ] Every triggered kill condition has produced a written plan revision before Phase 1 begins

## Non-goals

- Writing any `SKILL.md` content — the gate runs first
- Building `validate_bundle.py` or the eval runner
- Treating a green spike as proof the method is sensitive; that is P0.2's job, not an assumption

## Contributing work items

_None yet._

## Notes

**2026-08-08 — P0.1 half-answered.** Codex: bundled scripts execute, symlink install works,
`agents/openai.yaml` not required, and the eval driver's isolation flags do not suppress
skill discovery. Evidence and limits in `spikes/p0-1-script-execution/FINDING.md`. The
criterion stays unchecked: Junie is untested, and the permission-wall half (interactive
approval) was not exercised.

Kill conditions per the plan: P0.1 failure demotes validators to reference checklists and forces a `validate_bundle.py` redesign. P0.2 failure makes Phase 3 a design problem rather than an engineering one. P0.3 under 80% on Variant B cuts Phase 5 rather than deferring it. P0.4 failure restructures decision points as single-question turns.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-1). |
