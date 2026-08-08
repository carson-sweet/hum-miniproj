# Eval Harness — Codex CLI Driver

**Version 1.1 — 2026-08-08**

How `eval/run_contracts.py` executes a contract against a real agent. Companion to
[behavioral testing approach](behavioral-testing.md) and the
[implementation plan](implementation-plan.md) (Phase 3).

---

## Scope

This designs **one driver** — the Codex CLI adapter — behind the harness interface. It
serves two contract sets that happen to need the same machinery:

1. **The MiniProject skill's own contracts** (Phase 3, MS-004). Primary target. Codex is
   one of three claimed harnesses, so a driver is required regardless.
2. **Framework-behavior contracts** such as SweetClaude's 15. These cannot be validly
   self-graded by the agent under test. An external CLI subject and an external judge is
   exactly the isolation that makes them meaningful.

The contract format does not change between the two. Only the fixture and prompt do.

---

## Verified capability

Everything below was confirmed against `codex-cli 0.145.0` on 2026-08-08, not assumed.

```bash
codex exec \
  --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check \
  -C "$FIXTURE" -s read-only --color never \
  -m "$MODEL" \
  --output-schema verdict.schema.json \
  -o last_message.json \
  "$PROMPT" < /dev/null
```

Observed result with a two-field schema:

```json
{"verdict":"PASS","reason":"It proposes the specific name “users” and explains why..."}
```

What each flag buys, and why the design depends on it:

| Flag | Why it is load-bearing |
|---|---|
| `--ephemeral` | No session file persists. Every subject starts genuinely fresh — rule 2 of the testing approach. |
| `--ignore-user-config` | `~/.codex/config.toml` cannot leak the operator's model, instructions, or MCP servers into a result. Auth still resolves. |
| `--ignore-rules` | User and project `.rules` execpolicy files do not silently alter subject behavior. |
| `-C <DIR>` | Working root is the fixture. Tools are scoped to it. |
| `-s <MODE>` | `read-only` for judges, `workspace-write` for subjects that must produce artifacts. |
| `-m <MODEL>` | Pins the model so a regression is attributable rather than guessed at. |
| `--output-schema` | Forces the final message to a JSON shape. The judge returns data, not prose. |
| `-o <FILE>` | Final message written to a file. The banner and transcript go to stderr — see gotcha 2. |
| `--json` | Optional JSONL event stream on stdout. Use for tool-call traces, not for the verdict. Swaps the streams — see gotcha 5. |

---

## Architecture

Three stages, each a separate OS process. Isolation is enforced by process boundary and
working directory, not by prompt instructions.

```
contract.yaml
     │
     ├─► [1] SUBJECT      codex exec -C fixtures/<f>/  -s workspace-write
     │                     sees: skill under test + prompt
     │                     never sees: the contract, the pass criterion
     │                     emits: last_message.txt  +  any files it wrote
     │
     ├─► [2] ASSERT       deterministic, in Python, no model
     │                     type: artifact → filesystem checks
     │                     type: response → defer to [3]
     │
     └─► [3] JUDGE        codex exec -C .judge/ (empty)  -s read-only
                           sees: pass criterion + subject's final message
                           never sees: SKILL.md, the fixture, the contract id
                           emits: {"verdict","reason"} via --output-schema
```

**The judge gets an empty working directory on purpose.** If the judge can read the skill
it is grading against, it grades generously — it recognizes the instruction the subject
was supposed to follow and credits intent. An empty `-C` with `-s read-only` makes that
structurally impossible rather than merely discouraged.

**Artifact assertions never reach the judge.** A file either exists and matches shape, or
it does not. Sending that to a model adds cost, latency, and a failure mode, and removes
the one assertion type the testing approach trusts most.

---

## Module layout

```
eval/
├── run_contracts.py          CLI entry — modes, selection, reporting
├── drivers/
│   ├── base.py               HarnessDriver interface
│   ├── codex.py              this design
│   ├── claude_code.py        Phase 3
│   └── junie.py              Phase 3
├── judge.py                  judge invocation + verdict schema
├── assertions.py             artifact assertions (no model)
├── mutate.py                 negative-control mutation apply/revert
├── schemas/
│   └── verdict.schema.json   {verdict: PASS|FAIL, reason: string}
└── contracts/
    ├── mp-c01.yaml           MiniProject skill contracts
    └── framework/            framework-behavior contracts
```

The driver interface is deliberately small:

```python
class HarnessDriver(Protocol):
    name: str
    def run_subject(self, fixture: Path, prompt: str, *,
                    model: str, writable: bool, timeout_s: int) -> SubjectResult: ...
    def probe(self) -> ProbeResult:   # binary present, authenticated, model reachable
        ...
```

`SubjectResult` carries `final_message`, `workdir`, `exit_code`, `model`, `session_id`,
`duration_s`, and `events_path` when `--json` was captured. Nothing Codex-specific
escapes the driver.

---

## Contract format — the one addition

The format in [behavioral-testing.md](behavioral-testing.md) stands. One optional block is
added, because subjects and judges need different sandbox policies and a contract asserting
on artifacts must be allowed to write:

```yaml
id: MP-C03
name: Discovery is time-boxed, never estimated
targets: skills/miniproject/references/estimation-policy.md
subject:
  fixture: fixtures/project-with-discovery/
  prompt: "Estimate the Discovery card for reading customer sites."
  sandbox: read-only          # NEW — read-only | workspace-write. Default read-only.
  timeout_s: 120              # NEW — per-subject wall clock. Default 120.
assert:
  type: response
  pass: >
    Gives a time-box or decision-output framing.
    Contains no effort estimate for the Discovery item.
negative_control:
  mutate: remove the never-estimate-Discovery rule from estimation-policy.md
  expect: FAIL
harnesses: [claude-code, codex, junie]
```

A contract with `assert.type: artifact` must declare `sandbox: workspace-write`. The
runner rejects the combination of an artifact assertion with a read-only subject at load
time, rather than reporting a confusing FAIL later.

---

## Fixture and skill installation

Each subject run gets a **disposable copy**, never the working tree:

1. Create a temporary `CODEX_HOME` and symlink the real `auth.json` into it.
2. Install the skill under test into `$CODEX_HOME/skills/<name>/`.
3. Create a separate disposable fixture workdir and copy the fixture into it.
4. Run `codex exec -C <workdir>` with `CODEX_HOME` set to the temporary home.
5. Assert against the workdir.
6. Delete both temporary roots (unless `--keep-workdirs` preserves the fixture).

Copying is what makes negative controls safe. A mutation is applied to the copy, so a
crashed run can never leave a mutated skill in the repo.

The temporary home is a safety boundary, not test tidiness. Harness skills and persisted
multi-turn sessions must never be installed in `~/.agents/skills`, `~/.codex/skills`, or
`~/.codex/sessions`; those directories contain user-owned state. Authentication is linked,
not copied, and the harness never reads or logs its payload.

---

## Negative control mode

`--negative-control` is the mode that makes the suite trustworthy, and it inverts the
pass condition.

For each contract:

1. Copy the skill into a temp install
2. Apply `negative_control.mutate` to the copy
3. Run subject and judge exactly as normal
4. Expect the declared `expect:` value (normally `FAIL`)
5. **A contract that still PASSES under its own mutation is reported as BROKEN** — not as
   passing, and not as failing

The critical detail is step 5's reporting. A broken contract is worse than a failing one,
because it looks like coverage while measuring nothing. It gets its own exit code and its
own section in the report.

### Making mutations machine-applicable

`mutate:` in the format above is prose — fine for a human, not executable. The runner
requires a structured form:

```yaml
negative_control:
  expect: FAIL
  mutate:
    file: skills/miniproject/references/estimation-policy.md
    op: delete_lines_matching
    pattern: "^Do not estimate Discovery"
```

Supported ops: `delete_lines_matching`, `replace`, `delete_file`, `truncate_after`. Each
is deterministic and reversible against the copy. If a mutation matches nothing, the
runner reports **mutation-inert** and refuses to score the contract — a mutation that
changed nothing proves nothing.

---

## Reporting and attribution

One JSONL row per contract-harness-mode, written to `eval/runs/<timestamp>/results.jsonl`
(already gitignored):

```json
{"contract":"MP-C03","harness":"codex","mode":"normal","verdict":"PASS",
 "model":"gpt-5.6-sol","cli_version":"0.145.0","session_id":"019fe178-...",
 "duration_s":8.4,"reason":"Gives a time-box, no effort estimate."}
```

`model` and `cli_version` are captured from the run, not from config. When the suite goes
red after an upgrade, the diff between two runs names the cause instead of leaving it to
inference.

Exit codes: `0` all green · `1` one or more FAIL · `2` one or more BROKEN (mutation
survived) · `3` mutation-inert or driver probe failure.

---

## Gotchas found while verifying

These cost real time to discover. They are documented so nobody rediscovers them.

1. **stdin must be redirected.** With stdin not a TTY, `codex exec` prints `Reading
   additional input from stdin...` and blocks — even when a prompt argument is supplied.
   Every invocation needs `< /dev/null`. This is the failure that will hang CI.
2. **The banner goes to *stderr*, not stdout.** stdout carries only the final message;
   the header block (workdir, model, session id) and the transcript go to stderr. Read the
   answer from `-o`, and parse attribution metadata from **stderr**. Parsing stdout for
   metadata silently yields nothing, and would also let a reply containing a line like
   `model: x` poison the record. Found by a caught defect, not by reading the help text.
3. **Pin the model.** The default resolved to `gpt-5.6-sol` here. Unpinned, a provider-side
   default change reads as a behavioral regression in the skill.
4. **`--ignore-user-config` does not break auth.** Auth resolves through `CODEX_HOME`
   independently, so the isolation flag is free.
5. **`--json` swaps the streams and removes the banner.** Without it, stdout is the final
   message and stderr carries the banner. With it, stdout is JSONL and stderr carries
   nothing but the stdin notice — so banner parsing finds nothing on *either* stream and
   attribution silently vanishes. In JSON mode the id is `thread_id` on the
   `thread.started` event, not `session id`. Any driver supporting both modes needs both
   extraction paths, and a test for each.
6. **`codex exec resume` accepts fewer options than `codex exec`.** It rejects `-s`, `-C`,
   and `--color` with exit 2. The working directory is inherited, but a live regression
   proved the sandbox falls back to read-only. Resume accepts `-c`, so the driver pins
   `sandbox_mode="workspace-write"` (or `"read-only"`) through that supported override.
7. **Noninteractive `codex delete` requires `--force`.** Without it, deletion cannot confirm
   and silently leaves the session behind. Multi-turn cleanup targets only the recorded UUID,
   inside the temporary `CODEX_HOME`; it never discovers cleanup targets by sweeping a
   session directory.

---

## Cost and runtime

Every contract-harness pair costs two model calls (subject, judge), and negative-control
mode doubles it:

```
calls = contracts × harnesses × 2 × (1 + negative_control)
```

15 contracts × 3 harnesses = 180 calls for a full matrix with negative controls. That is
why the implementation plan runs the behavioral matrix on demand and on model-version
change, not per-commit. Practical controls:

- `--harness codex` during development — 60 calls
- `--contract MP-C03` for a single contract while authoring
- Artifact-only contracts skip the judge entirely, halving their cost
- Subjects across contracts are independent, so the runner parallelizes with a
  concurrency cap; the judge for a contract starts as soon as its subject finishes

---

## What this does not solve

**Codex judging Codex is not full independence.** Subject and judge are separate contexts
with separate working directories, which removes the grading-generously failure. It does
not remove shared-model blind spots: a behavior both instances misread identically passes.
Mitigation is to allow `judge.model` to differ from `subject.model` — the driver supports
it via `-m`, and cross-model judging should be the default once P0.2 establishes a
baseline.

**The judge is still a model.** `--output-schema` guarantees the *shape* of the verdict,
never its correctness. This is why artifact assertions are preferred wherever an outcome
is claimed, and why judged contracts need their negative control most.

**Fixture conditions are not production conditions.** Unchanged from
[behavioral-testing.md](behavioral-testing.md): a short prompt on a clean fixture says
little about the same instruction competing for attention in a long real session.

**This driver proves nothing about Junie.** P0.1 asks whether bundled `scripts/` execute
under Codex *and* Junie. A working Codex driver answers half of that question.

---

## Build order

| Step | Deliverable | Gate |
|---|---|---|
| 1 | `drivers/codex.py` + `probe()` | `probe()` green on a machine with Codex installed |
| 2 | `judge.py` + `verdict.schema.json` | Judge returns valid JSON on a hand-written pair |
| 3 | `assertions.py` | Artifact assertion passes and fails on a planted fixture |
| 4 | `run_contracts.py` single-contract path | One real contract runs end to end |
| 5 | `mutate.py` + `--negative-control` | A deliberately weakened skill turns the contract red |
| 6 | Parallelism, reporting, exit codes | Full matrix runs unattended |

Step 5 is the real gate. Until a contract has been observed going red under its own
mutation, steps 1–4 have produced a harness that has never been shown to work.

---

## Changelog

| Version | Date       | Change summary                                                     |
|---------|------------|--------------------------------------------------------------------|
| 1.1     | 2026-08-08 | Isolated CODEX_HOME; documented resume and deletion constraints.   |
| 1.0     | 2026-08-08 | Initial design, verified against codex-cli 0.145.0.                 |
