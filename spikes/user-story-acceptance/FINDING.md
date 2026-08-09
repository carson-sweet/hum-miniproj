# User-story implementation acceptance

**Version 1.5 — 2026-08-09**
**Verdict: all ten user stories are implemented; human-readable workflow hardening and improvement-cycle acceptance pass.**

The first live user test exposed that bundle validation returned raw JSON instead
of a human-readable result. US-OWN-001 now requires and tests deterministic
plain-language reporting. Its fresh-session user retest passed. The same reporting
contract is now implemented and tested for split validation, Tech Refinement, Tech
Estimation, Discovery-plan validation, and request routing. Split validation also
passed a live user test. Repeated hardening evidence is in
`spikes/human-output-hardening/FINDING.md`.

## Story evidence

| Story | Implemented behavior | Acceptance evidence |
|---|---|---|
| US-OWN-001 | Human-readable four-criterion presence validation without grading weak answers | `eval/tests/test_validate_bundle.py`; MP-C02; MP-C09 |
| US-OWN-002 | Fully answered technical-layer-only bundles fail `complete` | `eval/tests/test_validate_bundle.py`; MP-C03 |
| US-OWN-003 | Complete-improvement splits require an independently launchable piece | `eval/tests/test_validate_split.py`; MP-C05 |
| US-OWN-004 | Installer exposes identical validator behavior in Codex, Junie, and Claude paths | `eval/tests/test_install.py`; MP-C02 |
| US-FAC-001 | Every refinement card resolves once, MiniProjects have one owner, implementation crumbs stay off-board | `eval/tests/test_validate_board.py`; MP-C06 |
| US-FAC-002 | Delivery work is estimated; Discovery has a time box and output but no effort estimate | `eval/tests/test_validate_board.py`; MP-C06 |
| US-VAL-001 | Broad Projects produce explicit scope and ranked, owned Discovery cards accepted without re-scoping | `eval/tests/test_validate_discovery_plan.py`; MP-C07 |
| US-REQ-001 | Specific asks use the Chore fast lane; broad asks return with a shaping step and owner | `eval/tests/test_route_request.py`; MP-C08 |
| US-IMP-001 | Completed workflows append schema-valid, session-bound live learnings through one writer | `eval/tests/test_improvement_capture.py`; MP-C15 |
| US-IMP-002 | Recurring learnings produce approved, reversible, score-bound proposals that cannot regress held-out behavior | `eval/tests/test_improvement_loop.py`; MP-C16 |

`eval/user_story_coverage.yaml` is the machine-checked ledger. A deterministic test
extracts all story IDs from the product document and fails unless every ID has existing
implementation files and executable acceptance tests.

## Deterministic acceptance

- 220 deterministic tests passed with four paid integration tests deselected.
- The story-focused suite passed 40/40 before that correction; the strengthened board
  and Discovery-owner suites then passed 9/9.
- Portability lint and the standard Agent Skill validator passed.

The current 220-test CI-equivalent run is the authoritative deterministic total. MS-005 and MS-006 behavioral evidence is recorded separately in `spikes/ms-005-ms-006-acceptance/FINDING.md`.

## Three-harness acceptance

Every current user-facing workflow has normal three-harness acceptance. MP-C15 additionally ran ten fresh capture sessions per harness. Every current contract has received five-run mutation qualification in each claimed harness.

| Contract | Codex | Junie | Claude | Results |
|---|---:|---:|---:|---|
| MP-C02 — presence and portable validator | PASS | PASS | PASS | `eval/runs/20260809T005158Z-551261000/` |
| MP-C03 — technical-layer rejection | PASS | PASS | PASS | `eval/runs/20260809T003938Z-889108000/` |
| MP-C05 — complete split | PASS | PASS | PASS | `eval/runs/20260809T004140Z-281271000/` |
| MP-C06 — refinement and estimation | PASS | PASS | PASS | `eval/runs/20260809T004450Z-480971000/` |
| MP-C07 — ranked Discovery plan | PASS | PASS | PASS | `eval/runs/20260809T004724Z-586238000/` |
| MP-C08 — request routing | PASS | PASS | PASS | `eval/runs/20260809T005019Z-203062000/` |
| MP-C09 — human-readable bundle result | PASS | PASS | PASS | Hardened |
| MP-C10 — human-readable split result | PASS | PASS | PASS | Hardened |
| MP-C11 — human-readable refinement result | PASS | PASS | PASS | Hardened |
| MP-C12 — human-readable estimation result | PASS | PASS | PASS | Hardened |
| MP-C13 — human-readable Discovery result | PASS | PASS | PASS | Hardened |
| MP-C14 — human-readable request routes | PASS | PASS | PASS | Hardened |
| MP-C15 — improvement capture | 10/10 | 10/10 | 10/10 | `spikes/ms-005-ms-006-acceptance/FINDING.md` |
| MP-C16 — approved improvement cycle | PASS | PASS | PASS | `spikes/ms-005-ms-006-acceptance/FINDING.md` |

All six human-output contracts pass normally in all three harnesses. Their final repeated negative controls detected 90 of 90 mutations. MP-C11 Codex improved from 4 of 5 to 5 of 5 after a no-repair contract guard was added. See the hardening finding for trustworthy run IDs, discarded contaminated evidence, and spend.

MP-C05 through MP-C08 and MP-C15 through MP-C16 all detected their final negative controls 5 of 5 in Codex, Junie, and Claude. Semantic qualification and follow-up run IDs are recorded in `docs/hardening-and-behavioral-testing-report.md`; continuous-improvement qualification is recorded in `spikes/ms-005-ms-006-acceptance/FINDING.md`.

## Remaining boundary

This evidence establishes implementation and repeated mutation detection for the exact workflow contracts. It does not establish broader request-language coverage, long-session behavior, or a measured user-success threshold.
