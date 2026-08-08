---
closed_date: '2026-08-08T19:52:38Z'
created: 2026-08-08
depends_on: MS-001
id: MS-002
owner: Carson Sweet
sequence: 2
source: manual
status: done
target_release: unscheduled
title: Portable substrate
type: milestone
updated: '2026-08-08T19:52:38Z'
---


# MS-002: Portable substrate

**Version 1.4 — 2026-08-08**

## Outcome

The repo scaffold and the enforcement that keeps it portable. `lint_portable.py` runs in CI and fails on harness-specific constructs and provenance leaks, so portability is enforced mechanically rather than by discipline. `install.sh` puts the skill in all three harnesses idempotently and reversibly.

## Measuring success

- [x] `lint_portable.py` passes on the scaffold
- [x] `lint_portable.py` fails on a deliberately planted violation
- [x] `install.sh` verified in all three harnesses; the skill appears in each harness's skill listing
- [x] `lint_portable.py` runs in CI on every PR

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

Live discovery from a throwaway install succeeded under Codex, Junie, and Claude: each harness
opened the linked `SKILL.md` from its own temporary default skill directory. Claude used a
`CLAUDE_CODE_OAUTH_TOKEN` loaded from the mode-600 `.env.local`, an isolated
`CLAUDE_CONFIG_DIR`, no session persistence, and a read-only tool surface. It returned the exact
frontmatter description from the installed skill. The token was absent from every file in the
throwaway tree.

**Claude isolation residual:** `CLAUDE_CONFIG_DIR` does not fully redirect Claude's state. The
four probe invocations created four mode-600 `.claude.json.backup.*` files in the real
`~/.claude/backups/`, one at each invocation timestamp:

- `.claude.json.backup.1786217922892`
- `.claude.json.backup.1786218058265`
- `.claude.json.backup.1786218159059`
- `.claude.json.backup.1786218274685`

Those exact files were left untouched; no sweep or cleanup was attempted. No file under the real
Claude home contained the throwaway project path. Future automated Claude runs need a stronger
outer-home isolation boundary before they are considered safe.

**2026-08-08 — pull-request CI verified.** The first PR run correctly failed before tests because
setuptools discovered unrelated top-level directories as packages. The failure was reproduced in
a clean virtual environment, a regression test was added first, and package discovery was bounded
to `eval*`. A fresh editable install then succeeded locally. GitHub Actions run
`31275468001` passed the editable install, portability lint, and all 115 deterministic tests.
All four milestone criteria are met.

---

## Changelog

| Version | Date       | Change summary                                          |
|---------|------------|---------------------------------------------------------|
| 1.4     | 2026-08-08 | Verified PR CI and marked all criteria complete.        |
| 1.3     | 2026-08-08 | Verified Claude discovery; recorded isolation residual. |
| 1.2     | 2026-08-08 | Started TDD implementation; recorded live probe limits. |
| 1.1     | 2026-08-08 | Added YAML frontmatter; status to canonical vocabulary. |
| 1.0     | 2026-08-08 | Imported from `docs/implementation-plan.md` v1.0 (MP-2). |
