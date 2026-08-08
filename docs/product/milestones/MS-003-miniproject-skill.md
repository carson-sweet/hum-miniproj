---
id: MS-003
title: MiniProject skill
type: milestone
status: new
created: 2026-08-08
target_release: unscheduled
sequence: 3
owner: Carson Sweet
depends_on: MS-002
source: manual
---
# MS-003: MiniProject skill

**Version 1.1 — 2026-08-08**

## Outcome

The skill itself — `SKILL.md`, the four reference documents, and `validate_bundle.py`. All content authored from the model document, with no prose imported from other projects. The validator is deterministic: it checks that each of the four criteria has a stated answer, and does not grade the answer.

## Measuring success

- [ ] Skill activates on a realistic prompt in all three harnesses
- [ ] `validate_bundle.py` rejects a partial-technical-layer bundle
- [ ] `validate_bundle.py` accepts a complete-improvement bundle
- [ ] The Chore fast lane observably bypasses bundling
- [ ] How Discovery is modeled is decided and recorded with written rationale

## Non-goals

- Grading the quality of a bundling answer — the validator checks presence, not merit
- Importing prose from other projects; all content is authored from the model document
- The eval harness — that is MS-004

## Contributing work items

_None yet._

## Notes

The Discovery modeling decision is called out in the plan as the open question to resolve in this phase, and it carries a written-rationale requirement. See the open questions in `docs/miniproject-model.md`.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-3). |
