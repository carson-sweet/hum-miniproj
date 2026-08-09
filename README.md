# hum-miniproj

A portable [Agent Skill](https://agentskills.io) implementing the **MiniProject**
operating model — a delivery method for AI-accelerated work that bundles work by
complete improvement rather than by technical layer.

Runs anywhere the Agent Skills standard is supported: Claude Code, Codex, Junie,
and others.

**Status:** All ten product user stories and all six implementation milestones are complete. All 16 behavioral contracts passed five-run negative-control qualification in Codex, Junie, and Claude. Broader prompt-paraphrase and long-session hardening remain open.

## Quick start / TL;DR

The skill is implemented and its planned acceptance and hardening work is complete. Install `skills/miniproject/` in any Agent Skills-compatible tool, then ask the agent to classify, refine, validate, estimate, or split work using the MiniProject operating model. The [MiniProject operating model](docs/miniproject-model.md) explains the workflows, and the [Hardening and Behavioral Testing Report](docs/hardening-and-behavioral-testing-report.md) documents how the implementation was verified.

Free local verification does not invoke model providers:

```sh
python3 -m pytest -q -m 'not integration'
python3 scripts/lint_portable.py
```

Do not remove the pytest marker exclusion unless you intentionally want to run paid behavioral tests with configured credentials and a bounded budget.

## Testing summary

| Evidence | Final result |
| --- | ---: |
| Product implementation | 10 of 10 user stories; 6 of 6 milestones |
| Deterministic suite | 220 passed; 4 paid integration tests deselected |
| Portability lint | PASS |
| Standard Agent Skill validation | PASS |
| Normal behavioral acceptance | 48 of 48 contract-harness cells passed |
| Repeated negative-control qualification | 240 of 240 final mutations detected |
| Per-cell mutation floor | Every cell passed 5 of 5, exceeding the configured 4-of-5 floor |
| Harnesses | Codex, Junie, and Claude |

The 16 behavioral contracts cover foundational MiniProject rules, user-story semantics, human-readable workflow results, and the continuous-improvement workflow. Fifteen assert on produced artifacts; one judges the response because its requirement concerns how accountable ownership is framed. The final matrix includes five mutation repetitions for every contract in every harness, so a strong aggregate cannot hide a weak contract-harness cell.

Two human-output workflows—bundle validation and split validation—also passed manual fresh-session user tests after the first bundle test exposed raw JSON as unusable output. The other four human-output workflows have automated three-harness evidence but have not each received a separate manual fresh-session user test.

The repository ledgers contain 1,190 recorded calls and $39.1985 in metered model fees. Of those calls, 248 have unavailable pricing, and substantial early work predates metering, so this is a lower bound rather than an all-project total. The detailed report separates each bounded hardening phase, excluded runs, and unpriced Junie calls.

These results establish compliance for the recorded prompts, models, CLI versions, and isolated environments. They do not measure arbitrary prompt paraphrases, long-session instruction competition, persuasive answer quality, or future model drift. Those are documented follow-on risks, not unfinished implementation-plan milestones.

Full methodology, run identifiers, exclusions, cost boundaries, and the final-results amendment are in the [Hardening and Behavioral Testing Report](docs/hardening-and-behavioral-testing-report.md).

## The problem

The agile default splits work by technical layer — frontend, backend, data, infra,
QA — because implementation used to be the expensive part. AI compressed
implementation. It did not compress coordination.

The result is a worse ratio: the same handoffs spread over smaller work. A board
full of tiny cards still carries a large coordination bill, and the process becomes
the bottleneck during the work rather than before it.

## The model

Four work types, one bundling rule:

| Type | What it is |
|---|---|
| **Project** | A container for sequenced work toward a product or business goal. |
| **Discovery** | Time-boxed work to understand, decide, design, rank, or de-risk. Never estimated like implementation. |
| **MiniProject** | A complete, demoable improvement one owner carries end to end. |
| **Chore** | A small, specific, low-variance request. Stays in the fast lane. |

A MiniProject is **complete** (not a partial technical layer), **demoable**
(something real to show), **owned** (one owner carries the whole path), and
**launch-ready** (safe to release, even if held).

PRs stay small. Ownership gets bigger.

## What this repo will contain

```
skills/miniproject/     The portable skill — SKILL.md, references, validators
eval/                   Behavioral contract harness with negative controls
docs/                   Design documents
```

## Design docs

- [MiniProject operating model](docs/miniproject-model.md) — the methodology this skill implements
- [Implementation plan](docs/implementation-plan.md) — phased plan with falsification gate
- [Behavioral testing approach](docs/behavioral-testing.md) — how LLM-driven skills get tested
- [Hardening and behavioral testing report](docs/hardening-and-behavioral-testing-report.md) — methodology, results, evidence boundaries, cost, and remaining risks
- [MS-005 and MS-006 acceptance finding](spikes/ms-005-ms-006-acceptance/FINDING.md) — implementation, live capture matrix, improvement-cycle evidence, discarded runs, and remaining limits

## Why behavioral testing matters here

A skill is instructions to a language model, not code. It has no compiler, no type
checker, and no stack trace. It can silently stop working when a model version
changes, when a harness alters its system prompt, or when an edit three lines away
shifts how the whole document reads.

So the eval harness is not a supporting concern — it is the primary engineering
artifact. Every behavioral contract in this repo ships with a **negative control**:
a declared mutation that should make it fail. A contract that has never failed has
not been shown to work.

## License

Apache-2.0. See [LICENSE](LICENSE).
