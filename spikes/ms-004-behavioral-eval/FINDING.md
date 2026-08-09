# MS-004 — Behavioral eval harness

**Version 1.0 — 2026-08-09**
**Verdict: complete. The final normal matrix passed 12/12 and every current
negative control detected 5/5 on every claimed harness.**

## Final normal matrix

Decision-eligible results are in the gitignored run directory
`eval/runs/20260809T000730Z-541029000/`.

| Contract | Codex | Junie | Claude |
|---|---:|---:|---:|
| MP-C01 Discovery decision artifact | PASS | PASS | PASS |
| MP-C02 presence-only validation | PASS | PASS | PASS |
| MP-C03 partial-bundle validation artifact | PASS | PASS | PASS |
| MP-C04 one accountable owner | PASS | PASS | PASS |

The run recorded one JSONL row per contract-harness pair, including mode, verdict,
reason, model, duration, session identifier when available, repeated-run rate,
and CLI version. It made 19 metered calls and cost $0.4205, plus four Junie calls
whose provider does not expose usage in the required text-output mode.

## Negative-control qualification

Every row below is the final contract and subject-model combination. The target
is 100% detection even though the runner's minimum qualification floor is 4/5.

| Contract | Codex | Junie | Claude | Evidence |
|---|---:|---:|---:|---|
| MP-C01 | 5/5 | 5/5 | 5/5 | `eval/runs/20260808T235206Z-140082000/` |
| MP-C02 | 5/5 | 5/5 | 5/5 | `eval/runs/20260808T224155Z-057293000/`; Claude/Sonnet confirmation in `eval/runs/20260808T224933Z-727855000/` |
| MP-C03 | 5/5 | 5/5 | 5/5 | Codex: `eval/runs/20260808T222620Z-545969000/`; Junie: `eval/runs/20260808T222622Z-528350000/`; Claude/Sonnet: `eval/runs/20260809T000528Z-106633000/` |
| MP-C04 | 5/5 | 5/5 | 5/5 | `eval/runs/20260808T233418Z-769941000/` |

Each repetition receives a fresh fixture, disposable harness home, and fresh copy
of the production `skills/miniproject` package. A mutation that does not apply is
reported as `MUTATION-INERT`, and subject execution failures are reported as
`HARNESS-ERROR`; neither can be mistaken for behavioral detection.

## Contract corrections

The Phase 0 contracts were not accepted unchanged.

- The old MP-C01 estimation contract was prior-driven. It was replaced with a
  produced Discovery decision artifact that must use the canonical `More Discovery`
  terminal value, record the learned SAML fact, and state the unresolved mapping
  question.
- The old MP-C02 backend-slice contract remained prior-driven on weak and strong
  models. It was replaced with a counter-prior validator contract proving that the
  deterministic validator checks answer presence, not answer quality.
- MP-C03 remains artifact-based. Claude subjects are pinned to Sonnet after Haiku
  once exited successfully without producing the requested files; Sonnet then
  detected the mutation 5/5 and passed the final normal matrix.
- MP-C04's criterion was narrowed to the actual rule: specialists may lead and
  implement work as contributors, but accountability cannot fragment by technical
  layer. Qualification exposed a normal response that kept one overall owner while
  calling specialists accountable for API and data slices, so the production skill
  now reserves the word `accountable` for the single end-to-end owner. Its final
  mutation inverts that rule and was detected 5/5 in all harnesses.
- Behavioral prompts explicitly invoke the MiniProject skill. Automatic activation
  is already established by MS-003; MS-004 measures behavior after loading, not a
  second activation claim.

## Harness boundaries

- **Codex:** each subject uses a temporary `CODEX_HOME`; only the isolated skill
  copy is installed there. No subject session or skill is written under the user's
  normal Codex directories.
- **Junie:** each subject uses a temporary `JUNIE_HOME` and isolated skill root.
  Single-turn evaluation uses text output because Junie's JSON-stream mode can emit
  an empty `TASK RESULT`. Text mode does not expose usage, so Junie calls are recorded
  as unmetered with unknown cost rather than falsely priced at zero.
- **Claude:** every subject runs in disposable Docker container image
  `hum-miniproj-claude-test:2.1.226`. The fixture is the only writable host mount,
  the disposable skill copy is read-only, no host Claude state is mounted, the OAuth
  token exists only in the container process environment, and session persistence is
  disabled.

Cost accounting uses a per-process run identifier, preventing concurrent or prior
ledger rows from contaminating a run's totals. Provider-reported costs are retained
when available.

## Decision

All four MS-004 criteria are met. The runner targets the production skill, carries
an applicable negative control on every contract, records the full three-harness
matrix, and includes deterministic produced-artifact assertions. MS-005 can now use
this harness as its behavioral trust anchor.
