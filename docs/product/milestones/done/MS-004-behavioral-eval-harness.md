---
closed_date: '2026-08-09T00:16:02Z'
created: 2026-08-08
depends_on: MS-003
id: MS-004
owner: Carson Sweet
sequence: 4
source: manual
status: done
target_release: unscheduled
title: Behavioral eval harness
type: milestone
updated: '2026-08-09T00:16:02Z'
---


# MS-004: Behavioral eval harness

**Version 1.2 — 2026-08-09**

## Outcome

The trust anchor, built to a higher standard than the rest of the repo because it cannot check its own correctness. Contracts carry their own negative controls, and the runner uses fresh-context subjects with an isolated judge across all three harnesses.

## Measuring success

- [x] Every contract has a negative control
- [x] `--negative-control` mode reports 100% detection
- [x] Full matrix runs across three harnesses with per-harness results recorded
- [x] At least one contract asserts on an artifact produced rather than on response text

## Non-goals

- Running the behavioral matrix per-commit — it runs on demand and on model-version change
- Trusting any contract that has never failed on purpose
- Improvement capture — that is MS-005

## Contributing work items

- [#5 — Build the behavioral eval harness](https://github.com/carson-sweet/hum-miniproj/issues/5)

## Notes

A model can describe correct behavior fluently while producing nothing. Where a contract concerns an outcome, it asserts on files produced.

**2026-08-09 — three-harness trust anchor completed tests-first.** The runner targets
the production MiniProject skill and executes every contract in fresh disposable
subject homes across Codex, Junie, and Docker-isolated Claude. Results are recorded
per contract and harness; harness failures and inert mutations are distinct from
behavioral failures. Run-scoped cost accounting prevents ledger contamination, and
Junie calls without provider usage are explicitly unmetered rather than priced at zero.

The Phase 0 estimation and bundling contracts were replaced because they measured model
priors. MP-C01 now checks a produced Discovery decision artifact, MP-C02 proves the
validator checks presence rather than answer quality, MP-C03 checks structured validator
output, and MP-C04 distinguishes specialist contribution from fragmented accountability.
Qualification also strengthened the production skill's canonical Discovery labels and
single-owner language.

The final normal matrix passed 12/12 in
`eval/runs/20260809T000730Z-541029000/`. Every current negative control detected 5/5
on every claimed harness; exact qualification paths, corrections, limitations, and
the Claude/Junie isolation boundaries are recorded in
`spikes/ms-004-behavioral-eval/FINDING.md`.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.2     | 2026-08-09 | Completed the harness; recorded final qualification.    |
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-4). |
