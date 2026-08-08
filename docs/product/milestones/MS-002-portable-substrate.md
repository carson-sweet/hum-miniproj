---
created: 2026-08-08
depends_on: MS-001
id: MS-002
owner: Carson Sweet
sequence: 2
source: manual
status: active
target_release: unscheduled
title: Portable substrate
type: milestone
updated: '2026-08-08T19:32:37Z'
---

# MS-002: Portable substrate

**Version 1.2 — 2026-08-08**

## Outcome

The repo scaffold and the enforcement that keeps it portable. `lint_portable.py` runs in CI and fails on harness-specific constructs and provenance leaks, so portability is enforced mechanically rather than by discipline. `install.sh` puts the skill in all three harnesses idempotently and reversibly.

## Measuring success

- [x] `lint_portable.py` passes on the scaffold
- [x] `lint_portable.py` fails on a deliberately planted violation
- [ ] `install.sh` verified in all three harnesses; the skill appears in each harness's skill listing
- [ ] `lint_portable.py` runs in CI on every PR

## Non-goals

- Any MiniProject skill content — that is MS-003
- Hooks, bang preambles, plugin-root variables, or interactive-question primitives; the portable subset is `SKILL.md` + `references/` + `scripts/` only
- Verifying portability by inspection instead of by lint

## Contributing work items

- [#1 — Build the portable substrate](https://github.com/carson-sweet/hum-miniproj/issues/1)

## Notes

Provenance leaks are a lint concern, not just a legal one: any incompatible SPDX tag or verbatim block imported from a differently-licensed source must fail CI.

**2026-08-08 — implementation started tests-first.** `skills/miniproject/` now contains
only the portable subset. Fifteen linter tests cover the allowed tree, deliberately planted
harness constructs, symlink escapes, SPDX expressions, and verbatim-import markers. Five
installer tests cover the canonical copy, all three harness links, repeat installation,
reversible uninstall, and refusal to overwrite unowned paths. The deterministic suite is
green at 114 passed with four live integrations deselected.

Live discovery from a throwaway install succeeded under Codex and Junie: each harness opened
the linked `SKILL.md` from its own temporary default skill directory. Claude discovery remains
unverified because its existing login was unavailable under an isolated `CLAUDE_CONFIG_DIR`;
two credential-isolation approaches both failed closed with `Not logged in`. No probe wrote to
the real harness homes. The CI workflow is present locally but remains unchecked until it runs
on an actual pull request.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.2     | 2026-08-08 | Started TDD implementation; recorded live probe limits. |
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-2). |
