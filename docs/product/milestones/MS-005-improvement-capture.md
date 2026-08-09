---
id: MS-005
title: Improvement capture
type: milestone
status: done
created: 2026-08-08
target_release: unscheduled
sequence: 5
owner: Carson Sweet
depends_on: MS-004
source: manual
---
# MS-005: Improvement capture

**Version 1.2 — 2026-08-09**

## Outcome

The register fills from live use. `register_append.py` is the only writer and is schema-validated; `register_verify.py` exits non-zero when a session closed without an entry, substituting for the lifecycle hook the Agent Skills standard does not define. A seed corpus of human-curated learnings is imported so MS-006 has a validation set with known structure.

## Measuring success

- [x] Capture rate at or above the P0.3 threshold, measured over at least ten sessions per harness
- [x] Register non-empty from live use, not only from the seed import
- [x] The artifact-type contract goes red when capture is disabled
- [x] `register_append.py` is the only writer, and is schema-validated

## Non-goals

- The analysis loop — that is MS-006, and it is explicitly not built concurrently
- Relying on the agent remembering to capture; verification is invoked by the skill's own closeout
- Counting seed-import entries toward the live-use criterion

## Contributing work items

- US-IMP-001 — capture a learning from live use

## Notes

Gated on P0.3 from MS-001. If Variant B came in under 80%, the plan cuts MS-006 rather than deferring it — so that result changes this milestone's downstream, not this milestone.

**2026-08-09 — completed.** MP-C15 produced valid live entries in 10 of 10 fresh sessions in each supported harness: Codex `20260809T125850Z-224658000`, Junie `20260809T125851Z-116791000`, and Claude `20260809T125850Z-690736000`. Seed entries are distinguished by `source_session` values beginning with `seed:` and cannot satisfy `--require-live` or session-bound verification.

The disabled-writer mutation was detected in Codex `20260809T132857Z-300024000`, Claude `20260809T132857Z-786906000`, and Junie `20260809T133153Z-367075000`. The first Junie mutation run exposed an attempted direct repair after the writer failed; the skill now forbids shell, file-tool, alternate-script, and manual-register bypasses, and a deterministic package test enforces that instruction.

The finalized mutation later qualified at 5/5 in Codex, 5/5 in Junie, and 5/5 in Claude under run `20260809T143303Z-055364000`, exceeding the 4/5 per-harness floor.

`register_append.py` is named as the only writer in `references/improvement-register.schema.json`; it validates both existing and new entries before appending under an exclusive lock. `register_verify.py` validates the whole register and can require the exact source session and at least one non-seed entry.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.3     | 2026-08-09 | Recorded three-harness five-run mutation qualification. |
| 1.2     | 2026-08-09 | Completed live capture, schema, verifier, and mutation gates. |
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-5). |
