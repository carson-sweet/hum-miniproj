# MS-003 activation and Chore routing

**Version 1.1 — 2026-08-08**
**Status: automatic activation verified in Codex, Junie, and Claude.**

## Prompt

> Plan this request for our board: correct the misspelled "Notifcations" label
> in account settings. It is a one-line copy change with a known location and no
> behavior change. Tell me the work type and what process to apply.

The prompt is realistic and does not name the skill. It tests automatic activation
from the frontmatter description rather than explicit invocation.

## Current-skill results

| Harness | Activated | Observable result |
|---|---|---|
| Codex | yes | Classified Chore, selected the Chore fast lane, and explicitly skipped Discovery and bundle validation |
| Junie | yes | Trace read `miniproject` and `references/work-types.md`; CLI emitted an empty `TASK RESULT`, so response behavior was not scored |
| Claude | yes | Dispatched the `miniproject` skill, classified Chore, selected the fast lane, and explicitly skipped Discovery and bundle validation |

Codex and Junie ran from temporary harness homes with the current skill after its
trigger description was strengthened. Both exited 0. The Codex response supplies
live evidence for the Chore bypass; deterministic tests separately prove that the
validator returns `bypass` without checking criteria for a Chore.

## Trigger regression and revision

Claude's first realistic run listed the `miniproject` skill in its debug trace but
did not load it. It answered from model priors and called the request a Bug. The
frontmatter description was revised to put the classification use case first and
name board planning, bugs, typos, and one-line fixes explicitly. A deterministic
test protects those trigger terms. Codex and Junie activated with the revised
description. Claude then activated in a disposable Linux container with no host
Claude-state mount.

Claude's documented behavior is to match the task against the skill description
for automatic invocation. Explicit `/miniproject` invocation is therefore not a
substitute for this criterion.

## Claude isolation boundary

The probe used a temporary `CLAUDE_CONFIG_DIR`, a token held only in process
memory, no session persistence, and an OS sandbox that denied writes to both
`~/.claude/` and `~/.claude.json`. A direct write probe confirmed the denial before
Claude started. The Claude process still caused or coincided with state maintenance
outside that process boundary:

- removed `~/.claude/backups/.claude.json.backup.1786219191897`;
- created `~/.claude/backups/.claude.json.backup.1786219735619`; and
- changed the content hash of `~/.claude.json` from
  `f6e8715f8717ff650764bf88a93a2a4165800fae35ee7818fabe162834703669`
  to `e477cf2f2bb9c14ccd6b46cd77f1f5515cb1cf79789fcf40f229893b16a6c75e`.

The temporary tree contained no copy of the OAuth token. No cleanup or restoration
was attempted. Because other Claude processes may have been active, causality for
the config-content change cannot be proven from timestamps alone; the boundary is
still unsafe because the observed state changed during the probe.

The successful rerun used a disposable Linux container built with Claude Code
2.1.226. The container received only the OAuth token as a process environment
variable and a read-only mount of `skills/miniproject/`; it had no mount of the
host's `~/.claude/` or `~/.claude.json`. Session persistence was disabled. The
container was removed automatically after the run, and its debug log did not
contain the OAuth token.

The trace reported `SkillTool returning 3 newMessages for skill miniproject`.
Claude's final response identified the request as a Chore, instructed use of the
Chore fast lane, and explicitly skipped bundle validation and Discovery. The run
exited 0.

Retain this container boundary for future automated Claude subjects. A process
sandbox around a host Claude CLI remains insufficient if Claude delegates state
maintenance to an already-running host process.

## Decision

The all-three-harness activation criterion passes. Codex, Junie, and Claude each
automatically loaded the current skill from the same realistic prompt. Codex and
Claude also produced the expected Chore fast-lane behavior; Junie's activation is
trace-proven but its CLI emitted no final result.
