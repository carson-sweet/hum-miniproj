# hum-miniproj

A portable [Agent Skill](https://agentskills.io) implementing the **MiniProject**
operating model — a delivery method for AI-accelerated work that bundles work by
complete improvement rather than by technical layer.

Runs anywhere the Agent Skills standard is supported: Claude Code, Codex, Junie,
and others.

**Status:** Phase 0 and the portable substrate are complete. The MiniProject
behavior itself is not built yet.

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
