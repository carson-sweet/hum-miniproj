# User-story implementation acceptance

**Version 1.3 — 2026-08-09**
**Verdict: all eight user stories are implemented; human-readable workflow hardening passes.**

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

`eval/user_story_coverage.yaml` is the machine-checked ledger. A deterministic test
extracts all story IDs from the product document and fails unless every ID has existing
implementation files and executable acceptance tests.

## Deterministic acceptance

- 196 deterministic tests passed with four paid integration tests deselected.
- The story-focused suite passed 40/40 before that correction; the strengthened board
  and Discovery-owner suites then passed 9/9.
- Portability lint and the standard Agent Skill validator passed.

The 196-test CI-equivalent run is the authoritative deterministic total.

## Three-harness acceptance

One non-repeated acceptance pass was run per current user-facing workflow. No hardening
or five-run mutation matrix was performed.

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

All six human-output contracts pass normally in all three harnesses. Their repeated
negative controls detected 89 of 90 mutations; every contract-harness cell met the
4/5 floor. See the hardening finding for trustworthy run IDs, discarded contaminated
evidence, and spend.

## Remaining boundary

This evidence establishes implementation and repeated mutation detection for the exact
human-readable workflow contracts. It does not establish broader request-language
coverage, long-session behavior, or a measured user-success threshold. MP-C11 Codex
detected exactly 4/5, so refinement reporting has no margin above the current floor.
