# MS-005 and MS-006 acceptance

**Version 1.1 — 2026-08-09**
**Author: Eigen (synthetic cognitive entity)**
**Verdict: MS-005 and MS-006 meet all eight milestone criteria.**

## Method

Implementation was test-first. Capture began with failing tests for schema-valid append, invalid-register refusal, current-session verification, seed-versus-live separation, and the single-writer declaration. The improvement loop began with failing tests for withheld-cluster recovery, non-mutating reversible proposals, explicit human approval, score-bearing version records, full valid-cycle completion, missing approval, held-out regression, production artifact contracts, and stale identity hashes.

Deterministic tests were followed by isolated behavioral subjects. Every Codex run used a disposable `HOME` and `CODEX_HOME`; every Junie run used a disposable `JUNIE_HOME`; every Claude run executed in the disposable container harness. No subject used the user's real session or skill directories.

## MS-005 results

MP-C15 ran ten fresh normal sessions per harness. Codex passed 10/10 (`20260809T125850Z-224658000`), Junie passed 10/10 (`20260809T125851Z-116791000`), and Claude passed 10/10 (`20260809T125850Z-690736000`). These entries were produced by live subjects; seed entries use `seed:` source-session identifiers and cannot satisfy live verification.

The disabled-writer mutation was detected by Codex (`20260809T132857Z-300024000`), Junie (`20260809T133153Z-367075000`), and Claude (`20260809T132857Z-786906000`). An earlier Junie mutation run survived because the subject repaired the register outside the writer. That run is not acceptance evidence. The skill was corrected to forbid every alternate write path, and the final rerun detected the mutation.

Five-run qualification subsequently detected the finalized mutation 5/5 in Codex, 5/5 in Junie, and 5/5 in Claude (`20260809T143303Z-055364000`). Every harness exceeded the configured 4/5 floor.

## MS-006 results

The deterministic detector recovered the four known seed clusters without cluster labels in the seed corpus. A complete cycle now traverses register entry, recurring pattern, separate candidate, forward and reverse diffs, explicit human approval bound to the proposal hash, a new contract with a negative control, targeted before/after scores, held-out before/after scores, and a version record bound to current and previous instruction hashes.

The finalized full-cycle MP-C16 contract passed in Codex (`20260809T133354Z-081947000`), Junie (`20260809T133354Z-815852000`), and Claude (`20260809T133354Z-526118000`). The finalized mutation was detected in Codex (`20260809T132653Z-892431000`), Junie (`20260809T132654Z-655630000`), and Claude (`20260809T133720Z-070201000`).

The first MP-C16 negative-control design allowed the model to rewrite constructed inputs around the mutation. Those broken runs are excluded. The replacement uses a fixed, hash-bound cycle packet and a neutral one-shot instruction that forbids input repair and result reconstruction. This makes the deterministic validator the completion authority.

Five-run qualification subsequently detected the finalized fixed-packet mutation 5/5 in Codex, 5/5 in Junie, and 5/5 in Claude (`20260809T145716Z-056142000`). Every harness exceeded the configured 4/5 floor.

## Deterministic and packaging result

The final free suite passed 219 tests with four paid integration tests deselected. Portability lint passed, and the standard Agent Skill validator reported the skill valid. The installed package remains standard-library-only at runtime, including inside the minimal Claude container.

## Cost

The isolated implementation worktree ledger recorded 75 rows and approximately $5.8041 in metered cost, including 22 unpriced rows. Junie subject usage is unavailable and is recorded as unpriced rather than free. The ledger also includes diagnostic, driver-test, and replaced contract runs; no excluded run is used to satisfy a milestone criterion.

The bounded five-run hardening phase recorded 40 calls: 30 metered calls costing $4.6211 and 10 Junie calls with unavailable usage. MP-C15 cost $1.8271 metered and MP-C16 cost $2.7940 metered. The phase stayed below its $6 metered ceiling.

## Remaining limits

Capture still depends on instruction-driven closeout because the Agent Skills standard has no lifecycle hook; `register_verify.py` makes a miss visible but cannot force an agent to invoke it. Human approval is an explicit recorded attestation, not cryptographic proof of human identity. Broader paraphrase and long-session reliability remain future hardening work.
