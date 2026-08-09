# Human-readable workflow hardening

**Version 1.0 — 2026-08-09**
**Verdict: PASS at the configured 80% negative-control floor.**

## Scope

MP-C09 through MP-C14 require exact plain-language output for bundle validation,
split validation, Tech Refinement, Tech Estimation, Discovery-plan validation,
and request routing. Each artifact must be created by redirecting the bundled
script's human-formatted stdout, not reconstructed by the subject.

## Isolation defect found and fixed

The first Codex negative control was false. The driver isolated `CODEX_HOME`, but
Codex still loaded `/Users/carsonsweet/.agents/skills/miniproject`, bypassing the
mutated disposable copy. Evidence in the retained event stream showed the global
path explicitly.

The driver now gives Codex a disposable `HOME` and `CODEX_HOME`, installs the
canonical skill under disposable `HOME/.agents/skills/miniproject`, and links the
Codex-specific skill path to it. Deterministic tests pin that layout. Results from
pre-fix Codex runs and aborted diagnostic matrices are excluded below.

## Trustworthy normal results

| Contract | Codex isolated run | Junie and Claude run | Result |
|---|---|---|---|
| MP-C09 | `20260809T044314Z-374577000` | `20260809T045218Z-513752000` | 3/3 PASS |
| MP-C10 | `20260809T044417Z-478154000` | `20260809T045309Z-302516000` | 3/3 PASS |
| MP-C11 | `20260809T044528Z-120479000` | `20260809T045425Z-089260000` | 3/3 PASS |
| MP-C12 | `20260809T044642Z-225328000` | `20260809T045600Z-454105000` | 3/3 PASS |
| MP-C13 | `20260809T044743Z-015329000` | `20260809T045701Z-330235000` | 3/3 PASS |
| MP-C14 | `20260809T044845Z-650793000` | `20260809T045808Z-351491000` | 3/3 PASS |

All listed normal runs use the final direct-redirection prompts. Earlier normal
preflights and their pre-isolation Codex cells are discarded.

## Five-run negative controls

| Contract | Codex | Junie | Claude | Results |
|---|---:|---:|---:|---|
| MP-C09 | 5/5 | 5/5 | 5/5 | `20260809T033449Z-260543000`; `20260809T034014Z-920973000` |
| MP-C10 | 5/5 | 5/5 | 5/5 | `20260809T034439Z-409022000` |
| MP-C11 | 4/5 | 5/5 | 5/5 | `20260809T035657Z-296839000` |
| MP-C12 | 5/5 | 5/5 | 5/5 | `20260809T041005Z-487095000` |
| MP-C13 | 5/5 | 5/5 | 5/5 | `20260809T042033Z-092977000` |
| MP-C14 | 5/5 | 5/5 | 5/5 | `20260809T043354Z-604641000` |

Detection was 89/90 overall. Every contract-harness cell met the configured 4/5
floor. MP-C11 Codex sits exactly at that floor and should be treated as fragile,
not as evidence of excess reliability.

## Budget

The phase started at `2026-08-09T03:04:43Z`. The user-approved ceiling was $10
of metered usage; matrix commands used an internal $9 stop and final verification
used $9.50, both with a $0.25 next-call reserve. All phase activity—including
discarded diagnostic attempts—used 185 recorded calls and $8.6668 metered.
Forty-four Junie calls have unavailable usage and are reported separately rather
than treated as zero cost.

## Remaining limits

- Exact contract prompts are hardened; broader paraphrase coverage is not.
- Long-session competition for attention is not measured.
- MP-C11 Codex has no detection margin above the 80% floor.
