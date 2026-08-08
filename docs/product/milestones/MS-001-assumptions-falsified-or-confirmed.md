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

- [x] P0.1 answered with recorded evidence: bundled `scripts/` either do or do not execute under Codex and Junie, sentinel file checked in each harness
- [x] P0.2 answered with recorded evidence: mutated contracts re-run five times each, detection rate recorded per contract
- [ ] P0.3 answered with recorded evidence: capture rate measured over five runs each of Variant A and Variant B, per harness
- [x] P0.4 answered with recorded evidence: decision points run as numbered prose in each harness, agent observed to present bounded choices and wait
- [x] Every triggered kill condition has produced a written plan revision before Phase 1 begins

## Non-goals

- Writing any `SKILL.md` content — the gate runs first
- Building `validate_bundle.py` or the eval runner
- Treating a green spike as proof the method is sensitive; that is P0.2's job, not an assumption

## Contributing work items

_None yet._

## Notes

**2026-08-08 — P0.1 half-answered.** Codex: bundled scripts execute, symlink install works,
`agents/openai.yaml` not required, and the eval driver's isolation flags do not suppress
skill discovery. Evidence and limits in `spikes/p0-1-script-execution/FINDING.md`.

**2026-08-08 — P0.1 closed.** Junie also executes the bundled script, same model string
(`gpt-5.6-sol`), sentinel token matched. Kill condition not triggered in either harness.
Criterion checked. Residual: both harnesses ran permissive approval settings, so the
"permission wall that breaks flow" half of the assumption is still unexercised.

**2026-08-08 — P0.2 answered.** The method detects regressions: MP-C03 (artifact) and
MP-C04 (counter-prior response) went red 2 of 2 under mutation. But MP-C02 never detects
(measures a model prior) and MP-C01 detects only 2 of 5 (probabilistic). The kill condition
literally fired, and its stated conclusion is contradicted by the evidence — the method
discriminates; the contracts were the problem. Five-part plan revision proposed in
`spikes/p0-2-detection/FINDING.md`, required before Phase 1.

**2026-08-08 — P0.2 criterion restated.** The original wording ("FAIL expected on all
three") restated the pre-spike kill condition, which the v1.1 plan revision replaced. It now
matches the revised method: five runs per contract, detection rate recorded. P0.2's question
— can the method detect a regression at all — is answered yes. Bringing MP-C01 and MP-C02 up
to the 4-of-5 floor is Phase 3 contract work, not a Phase 0 gate item.

**2026-08-08 — plan revision written.** P0.2's kill condition fired, and
`docs/implementation-plan.md` v1.1 and `docs/behavioral-testing.md` v1.1 now carry the five
resulting changes.

**2026-08-08 — P0.4 answered.** Tech Refinement questions run as numbered prose, 3 runs per
harness, PASS 6 of 6 under Codex and Junie. Kill condition not triggered. Caveat recorded in
the finding: "waiting" was inferred from turn-end, not observed — headless agents can only
end the turn. Junie consistently frames the turn as TASK RESULT with the question demoted to
a note.

**2026-08-08 — P0.2 matrix re-run on gpt-5.6-luna.** 3 of 4 contracts now clear the 4-of-5
floor (MP-C01 5/5, MP-C03 5/5, MP-C04 4/5 at the floor); MP-C02 remains broken at 1/5 and
needs replacing. Subject model is a contract-design variable, recorded as plan revision v1.2.
Full metered cost of the matrix: $0.2864.

Kill conditions per the plan: P0.1 failure demotes validators to reference checklists and forces a `validate_bundle.py` redesign. P0.2 failure makes Phase 3 a design problem rather than an engineering one. P0.3 under 80% on Variant B cuts Phase 5 rather than deferring it. P0.4 failure restructures decision points as single-question turns.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-1). |
