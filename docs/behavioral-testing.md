# Behavioral Testing Approach

**Version 1.2 — 2026-08-09**

How a skill made of instructions gets tested. Companion to the
[implementation plan](implementation-plan.md).

For setup instructions, commands, contract-by-contract use cases, result interpretation, and failure response, see the [developer testing guide](developer-testing-guide.md).

---

## Why this is the primary artifact

A skill is instructions to a language model. It has no compiler, no type checker,
and no stack trace. Its failure mode is not an exception — it is quiet
non-compliance that looks exactly like success.

It can stop working when:

- a model version changes,
- a harness alters its system prompt or tool surface,
- an edit three lines away shifts how the whole document reads,
- or context length pushes an instruction out of effective attention.

None of those produce an error. All of them produce plausible output. So the eval
harness is not a supporting concern in this repo — it is the thing that makes the
skill trustworthy, and it is engineered accordingly.

## Three design rules

### 1. Every contract ships with a negative control

A behavioral test that has never failed has not been shown to work. It may be
measuring something that cannot fail, or measuring nothing at all.

So each contract declares how to break the skill, and the harness can run in a mode
that applies every declared mutation and confirms each contract goes red. **A
contract that survives its own mutation is reported as broken, not as passing.**

**Detection is measured as a rate, not a verdict.** P0.2 found a contract that detected
its mutation 2 times in 5 — a single run would have scored it either way. Run the
negative control five times; a contract detecting in fewer than 4 is not measuring its
rule.

**Run contracts against the weakest model that can do the task.** A strong model follows a
sensible rule from its own priors, which hides whether the instruction is doing any work.
Measured: MP-C01 detected its mutation 2 of 5 times on `gpt-5.6-sol` and 5 of 5 on
`gpt-5.6-luna`. The weaker subject is the more sensitive instrument, and it costs 25x less.
Reserve strong models for contracts where capability is genuinely the variable.

**Run it before trusting a contract, not only after.** A contract whose mutation goes
undetected is measuring the model's prior rather than the instruction. That is the
cheapest way to find contracts that look like coverage and are not, and P0.2 found one
in four.

This is the single rule most likely to prevent the failure this approach was
designed against: a green suite sitting next to a feature that does not work.

### 2. Subject and judge are isolated

The subject runs in a fresh context, with tools scoped to a fixture, and no
visibility into the contract it is being tested against. The judge sees only the
contract criterion and the subject's output — never the skill under test.

A judge that has read the instructions grades generously against them. A subject
that can see the pass criterion writes to it.

For Codex, isolate both `HOME` and `CODEX_HOME`. The disposable skill must live
under the disposable `HOME/.agents/skills`; setting only `CODEX_HOME` still lets
Codex discover and execute the globally installed user skill. Junie disables all
default skill locations and receives only its disposable `--skill-location`.
Claude receives only the disposable skill mounted into its container.

### 3. Assert on artifacts wherever an outcome is claimed

Two assertion types:

- `type: response` — behavior in the reply. Appropriate for tone, framing, sequencing,
  and refusal behavior.
- `type: artifact` — a file exists, grew, or matches a shape after the session.

The second exists because of a specific and recurring failure: a model can describe
the correct behavior fluently, pass a response-level check, and produce nothing.
Any contract about something happening — a register entry written, a bundle
recorded, a validator run — must assert on the artifact.

## Contract format

```yaml
id: MP-C03
name: Discovery is time-boxed, never estimated
targets: skills/miniproject/references/estimation-policy.md
subject:
  fixture: fixtures/project-with-discovery/
  prompt: "Estimate the Discovery card for reading customer sites."
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

`harnesses` is the claim being made. A contract is green only when it is green
everywhere it claims to hold — the same `SKILL.md` gets a different system prompt
and often a different model under each agent, so a result from one says little
about the others.

## Runner

`eval/run_contracts.py`

| Mode | Behavior |
|---|---|
| default | Run each contract's subject and judge; report per-harness results |
| `--negative-control` | Apply each declared mutation, re-run, report any contract that still passes |
| `--harness NAME` | Restrict to one harness |
| `--repeat N` | Run each selected contract and harness N times |
| `--max-metered-cost USD` | Stop before the next subject call when spend plus the reserve would exceed the cap |
| `--budget-since UTC` | Apply the cap across multiple invocations from one shared UTC start time |
| `--budget-reserve USD` | Reserve room for the next subject call; defaults to $0.25 |

Results are recorded per run with the model version and harness version, so a
regression can be attributed rather than guessed at.

The metered cap covers providers whose usage is available. Junie usage is recorded
as unavailable and must be reported separately; it cannot be represented as zero
cost or silently counted inside the cap.

## Held-out contracts

Once an automated improvement loop optimizes against a contract set, the set stops
measuring quality and starts measuring itself.

A held-out subset is never read by any analysis or improvement process. It runs each
cycle alongside the main set. Targeted score rising while held-out score falls is
the signal that the loop is overfitting, and it is the only reliable detector for
that failure.

## What this approach does not claim

**It does not measure quality.** It measures compliance with stated contracts.
A skill can pass every contract and still be a bad skill.

**It does not cover the whole behavior surface.** Contracts cover what has been
written down. Behavior nobody thought to write down is untested by construction.

**Passing in isolation is not passing in production.** A contract exercised on a
clean fixture with a short prompt says little about the same instruction competing
for attention in a long real session. This is a known gap, and it is the reason
artifact assertions exist — they at least measure a real effect rather than a
described intention.
