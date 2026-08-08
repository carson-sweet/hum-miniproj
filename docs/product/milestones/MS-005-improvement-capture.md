---
id: MS-005
title: Improvement capture
type: milestone
status: new
created: 2026-08-08
target_release: unscheduled
sequence: 5
owner: Carson Sweet
depends_on: MS-004
source: manual
---
# MS-005: Improvement capture

**Version 1.1 — 2026-08-08**

## Outcome

The register fills from live use. `register_append.py` is the only writer and is schema-validated; `register_verify.py` exits non-zero when a session closed without an entry, substituting for the lifecycle hook the Agent Skills standard does not define. A seed corpus of human-curated learnings is imported so MS-006 has a validation set with known structure.

## Measuring success

- [ ] Capture rate at or above the P0.3 threshold, measured over at least ten sessions per harness
- [ ] Register non-empty from live use, not only from the seed import
- [ ] The artifact-type contract goes red when capture is disabled
- [ ] `register_append.py` is the only writer, and is schema-validated

## Non-goals

- The analysis loop — that is MS-006, and it is explicitly not built concurrently
- Relying on the agent remembering to capture; verification is invoked by the skill's own closeout
- Counting seed-import entries toward the live-use criterion

## Contributing work items

_None yet._

## Notes

Gated on P0.3 from MS-001. If Variant B came in under 80%, the plan cuts MS-006 rather than deferring it — so that result changes this milestone's downstream, not this milestone.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-5). |
