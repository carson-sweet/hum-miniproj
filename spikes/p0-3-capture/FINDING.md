# P0.3 — capture without hooks

**Version 1.1 — 2026-08-08**
**Verdict: Variant B met the threshold in both harnesses. Kill condition not triggered.**

Decision-eligible evidence is in `evidence/runs-20260808T184733Z.jsonl` for Codex
and `evidence/junie-runs-20260808T191936Z.jsonl` for Junie. The result is an
artifact assertion; no judge was used.

## Codex result

| Variant | Capture rate | Result |
|---|---:|---|
| A — closeout instruction | 5/5 (100%) | captured every run |
| B — closeout + verifier | 4/5 (80%) | met the threshold exactly |

All 30 turns exited 0. The one Variant B miss was behavioral rather than a
harness failure: its closeout response ended without invoking either register
script. The other four Variant B runs wrote one valid entry and verified it.

The verifier did not improve the observed capture rate over Variant A in this
sample. Its demonstrated value is failure detection when invoked; whether it
raises capture reliability remains unproven.

Cost: 30 `gpt-5.6-luna` calls, $0.3815 metered.

The plan's kill condition is not triggered for Codex.

## Junie result

| Variant | Capture rate | Result |
|---|---:|---|
| A — closeout instruction | 5/5 (100%) | captured every run |
| B — closeout + verifier | 5/5 (100%) | captured every run |

All 30 turns exited 0. Every run wrote at least one valid register entry; two
runs wrote two valid entries. Variant B cleared the 80% floor, so the plan's kill
condition is not triggered for Junie.

Across both harnesses, Variant A captured 10 of 10 and Variant B captured 9 of
10. P0.3 is answered: register capture without a lifecycle hook met the specified
reliability floor.

## Junie isolation gate

An early one-run Junie Variant B probe resumed all three turns and captured a
valid entry, but it was excluded from the P0.3 measurement because Junie's
documented `--cache-dir` does not redirect `~/.junie/sessions` or its logs. The
probe wrote a known session and six known log files into the user home. Those
exact paths were removed from the index and moved to a recoverable temporary
quarantine; no directory sweep was used.

Junie supports a `JUNIE_HOME` override, but its macOS Keychain account is keyed to
the absolute Junie-home path. Redirecting the home therefore removes access to
the existing login. `run_junie.py` now enforces the safe boundary: it requires a
`JUNIE_API_KEY`, creates a temporary `JUNIE_HOME`, redirects logs and cache beneath
it, disables all default discovery locations, and refuses to fall back to the
real user home. The key was loaded from the gitignored, mode-600 `.env.local`;
the runner reads that one value directly without sourcing shell code.

The isolated one-run credential preflight captured successfully and was labeled
non-decision-eligible. The subsequent ten-session matrix ran entirely under
temporary Junie homes. A content fingerprint of every file under `~/.junie` was
identical before and after the matrix.

## Invalid and preliminary runs

The first attempted Variant B run produced no valid evidence. Turn 1 succeeded,
but turns 2 and 3 exited 2 because the resume command included options accepted
by `codex exec` but rejected by `codex exec resume` (`-s`, `-C`, and `--color`).
The closeout turn never ran, so the missing register was a harness failure rather
than a capture failure. That invalid evidence was removed.

Two diagnostic preflights exposed a second CLI plumbing defect: resumed turns
inherited the working directory but fell back to a read-only sandbox. The
closeout turn invoked both register scripts; append failed with `PermissionError`
and verify correctly reported no entry. `codex exec resume` rejects `-s`, but
accepts `-c`, so the driver now pins `sandbox_mode="workspace-write"` through the
supported config override. These misses are not evidence about capture behavior.

A post-fix preflight captured successfully. Preflights are labeled
`preflight-*`, carry `decision_eligible: false`, and never evaluate the kill
condition; the plan requires at least five runs per variant.

## Safety finding

Every Codex subject ran with a temporary `CODEX_HOME` containing only a symlink
to the real `auth.json` and the variant skill. Persisted sessions, skill files,
and targeted `codex delete --force <recorded UUID>` cleanup were confined to that
temporary home. A path-set fingerprint of `~/.codex/sessions`,
`~/.codex/skills`, and `~/.agents/skills` was identical before and after the live
runs. Every decision-eligible Junie subject likewise ran under a temporary
`JUNIE_HOME`; the real Junie home remained byte-for-byte unchanged.
