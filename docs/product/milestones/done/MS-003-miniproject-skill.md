---
closed_date: '2026-08-08T21:13:31Z'
created: 2026-08-08
depends_on: MS-002
id: MS-003
owner: Carson Sweet
sequence: 3
source: manual
status: done
target_release: unscheduled
title: MiniProject skill
type: milestone
updated: '2026-08-08T21:13:31Z'
---


# MS-003: MiniProject skill

**Version 1.4 — 2026-08-08**

## Outcome

The skill itself — `SKILL.md`, the four reference documents, and `validate_bundle.py`. All content authored from the model document, with no prose imported from other projects. The validator is deterministic: it checks that each of the four criteria has a stated answer, and does not grade the answer.

## Measuring success

- [x] Skill activates on a realistic prompt in all three harnesses
- [x] `validate_bundle.py` rejects a partial-technical-layer bundle
- [x] `validate_bundle.py` accepts a complete-improvement bundle
- [x] The Chore fast lane observably bypasses bundling
- [x] How Discovery is modeled is decided and recorded with written rationale

## Non-goals

- Grading the quality of a bundling answer — the validator checks presence, not merit
- Importing prose from other projects; all content is authored from the model document
- The eval harness — that is MS-004

## Contributing work items

- [#3 — Build the MiniProject skill](https://github.com/carson-sweet/hum-miniproj/issues/3)

## Notes

The Discovery modeling decision is called out in the plan as the open question to resolve in this phase, and it carries a written-rationale requirement. See the open questions in `docs/miniproject-model.md`.

**2026-08-08 — Discovery model decided.** Discovery is a first-class, time-boxed work item
with a required decision artifact and exactly three terminal outcomes: ready to shape, more
Discovery required, or stop. It is not estimated like implementation and does not use a
shipped-code lifecycle. The rationale is recorded in `docs/miniproject-model.md`.

**2026-08-08 — skill and validator implemented tests-first.** The package contains the planned
four references and deterministic validator. Focused tests went red before each implementation
slice and now cover partial rejection, complete acceptance, presence-not-grading, blank answers,
Chore bypass, CLI exit behavior, package structure, and trigger terms. The full deterministic
suite passes 128 tests with four live integrations deselected; portability lint and the standard
skill validator both pass.

Codex and Junie automatically activated the current skill on a realistic typo-fix planning
prompt. Codex selected the Chore fast lane and skipped bundle validation. Junie's trace loaded
the skill and work-types reference but emitted an empty final result. Claude discovered an
earlier description but did not invoke it automatically, and a stronger-isolation rerun changed
real Claude state despite an OS write sandbox. At that point the all-harness criterion remained
open. Evidence, exact paths, and the resulting container boundary are in
`spikes/ms-003-activation/FINDING.md`.

**2026-08-08 — Claude activation verified in a disposable container.** Claude Code 2.1.226
ran in a Linux container with no host Claude-state mount, the skill mounted read-only, and
session persistence disabled. Its trace automatically dispatched `miniproject`; its response
classified the request as a Chore, selected the fast lane, and skipped Discovery and bundle
validation. The debug log contained no OAuth token. All five milestone criteria are met.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.4     | 2026-08-08 | Verified isolated Claude activation; all criteria met.  |
| 1.3     | 2026-08-08 | Implemented the skill; recorded activation evidence.    |
| 1.2     | 2026-08-08 | Recorded the approved Discovery model and rationale.    |
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-3). |
