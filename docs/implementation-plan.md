# Implementation Plan

**Version 1.0 — 2026-08-08**

Phased plan for building the MiniProject skill and its behavioral eval harness.
Companion documents: [MiniProject operating model](miniproject-model.md),
[behavioral testing approach](behavioral-testing.md).

---

## Guiding constraints

Four rules bind every phase.

**Portable subset only.** `SKILL.md` + `references/` + `scripts/`, per the
[Agent Skills specification](https://agentskills.io). No hooks, no bang preambles,
no harness-specific path variables, no interactive-question primitives. Enforced by
`lint_portable.py` in CI, not by discipline.

**Capture before analysis.** Nothing that reads the improvement register gets built
until the register demonstrably fills. An analysis loop over an empty register
produces confident nothing.

**No eval is trusted until it has failed on purpose.** Every behavioral contract
ships with a negative control. A contract that has never failed has not been shown
to work.

**Assert on artifacts, not on prose.** A model can describe correct behavior
fluently while producing nothing. Where a contract concerns an outcome, it asserts
on files produced, not on response text.

---

## Phase 0 — Falsification gate

Four load-bearing assumptions. Each spike is designed to kill one. All four run
before any skill content is written.

### P0.1 — Do bundled `scripts/` execute under Codex and Junie?

**Assumption at risk:** deterministic validators substitute for the hook primitive
that the Agent Skills standard does not define. If scripts do not execute, or
execute behind a permission wall that breaks flow, enforcement collapses to
advisory prose.

**Method:** minimal skill with one `scripts/echo_check.py` that writes a sentinel
file. Install to `~/.agents/skills/`, symlink into `.codex/skills/` and
`.junie/skills/`. Invoke in each harness. Check for the sentinel.

**Kill condition:** sentinel absent in either harness → validators become reference
checklists, and `validate_bundle.py` is redesigned.

### P0.2 — Can the behavioral method detect a regression at all?

**Assumption at risk:** the fresh-context-subject with separate-judge method is a
sound base. Its sensitivity is unmeasured — a suite that has only ever returned
green has not demonstrated it can return red.

**Method:** take three contracts covering distinct behavior classes. For each,
delete the governing rule from the instruction set given to the subject. Re-run.
Expect FAIL on all three.

**Kill condition:** any mutation still returns PASS → the method does not
discriminate, and Phase 3 becomes a design problem rather than an engineering one.

### P0.3 — Can register capture be made reliable without a hook?

**Assumption at risk:** improvement capture works in harnesses with no lifecycle
event to hang it on.

**Method:** two variants against a scripted multi-turn session.
Variant A — closeout instruction alone.
Variant B — closeout instruction plus a `register_verify.py` the skill must run,
which exits non-zero when the session added no entry.
Five runs each, per harness. Record capture rate.

**Kill condition:** Variant B under 80% → capture is not solvable in-skill, and
Phase 5 is cut rather than deferred.

### P0.4 — Do the decision points survive without an interactive-question primitive?

**Assumption at risk:** the five decision points work as plain prose.

**Method:** run the Tech Refinement question set as numbered prose in each harness.
Check whether the agent presents bounded choices coherently and waits for an answer.

**Kill condition:** agents answer their own questions or skip the wait → decision
points restructure as single-question turns.

**Phase 0 exit:** all four answered with recorded evidence. Any triggered kill
condition has produced a written plan revision before Phase 1 begins.

---

## Phase 1 — Portable substrate

**Deliverables**

- Repo scaffold: `skills/miniproject/`, `eval/`, `fixtures/`, `install.sh`.
- `scripts/lint_portable.py` — fails on harness-specific constructs (bang preambles,
  plugin-root variables, interactive-question tool references, cross-skill
  invocation). Also fails on provenance leaks: any incompatible SPDX tag or verbatim
  block imported from a differently-licensed source. Runs in CI.
- `install.sh` — writes to `~/.agents/skills/` and symlinks into `~/.codex/skills/`,
  `.junie/skills/`, `.claude/skills/`. Idempotent and reversible.

**Exit criteria**

- Lint passes on the scaffold and fails on a deliberately planted violation.
- Install verified in all three harnesses; the skill appears in each skill listing.

---

## Phase 2 — MiniProject skill

**Deliverables**

```
skills/miniproject/
├── SKILL.md
├── references/
│   ├── work-types.md          Project · Discovery · MiniProject · Chore
│   ├── bundling-criteria.md   the four Tech Refinement questions
│   ├── decision-points.md     the five decision points, one question each
│   └── estimation-policy.md   estimate Chore/MiniProject; time-box Discovery
└── scripts/
    └── validate_bundle.py
```

All content authored from the model document. No prose imported from other
projects.

`validate_bundle.py` checks a proposed MiniProject against the four criteria —
complete, demoable, owned, launch-ready — and returns structured findings. It is
deterministic. It checks that each criterion has a stated answer; it does not grade
the answer.

**Decision to resolve in this phase, with written rationale:** how Discovery is
modeled. See the open questions in the model document.

**Exit criteria**

- Skill activates on a realistic prompt in all three harnesses.
- `validate_bundle.py` rejects a partial-technical-layer bundle and accepts a
  complete-improvement bundle.
- The Chore fast lane observably bypasses bundling.

---

## Phase 3 — Behavioral eval harness

The trust anchor. Built to a higher standard than the rest. Design detail in
[behavioral-testing.md](behavioral-testing.md).

**Deliverables**

- Contract format carrying its own negative control.
- `eval/run_contracts.py` — fresh-context subjects, isolated judge, per-harness
  execution, `--negative-control` mode.
- Contract set covering the four work types, the bundling criteria, and the
  estimation policy.

**Exit criteria**

- Every contract has a negative control, and `--negative-control` reports 100%
  detection.
- Full matrix runs across three harnesses with per-harness results recorded.
- At least one contract asserts on an artifact rather than on response text.

---

## Phase 4 — Improvement capture

Gated on P0.3.

**Deliverables**

- `register.jsonl` schema: `{id, date, harness, skill, type, learning,
  source_session, weight}`. Types: correction, confirmation, preference, pattern.
- `scripts/register_append.py` — the only writer. Schema-validated.
- `scripts/register_verify.py` — exits non-zero when a session closed without an
  entry. Substitute for a lifecycle hook; invoked by the skill's own closeout rather
  than remembered.
- An artifact-type contract asserting the register grew after a full cycle.

**Seed corpus.** Import an existing human-curated learning set as historical
entries, so Phase 5 has a validation set with known structure.

**Exit criteria**

- Capture rate at or above the P0.3 threshold, measured over at least ten sessions
  per harness.
- Register non-empty from live use, not only from the seed import.
- The artifact contract goes red when capture is disabled.

---

## Phase 5 — Improvement loop

Gated on Phase 4 producing live entries. Not built concurrently.

**(1) Analyze** — reads the register, groups by type and target, surfaces
recurrence.

**(2) Identify patterns** — validated against the seed corpus with its known
clustering withheld. A detector that cannot recover patterns a human already found
in a known corpus will not find new ones.

**(3) Propose improvements** — produces a diff against a versioned instruction file
and never applies it. Human approval is the gate. Each instruction version carries
its contract score, so revert is a real operation.

**(4) Confirm impact** — extends the Phase 3 suite with a contract targeting the
specific pattern, including its negative control. Run before and after. Two
additional requirements:

- A **held-out contract set** the loop never reads, run each cycle. Held-out score
  falling while targeted score rises means the loop is overfitting to its own tests.
- Where the pattern concerns a production outcome, the new contract asserts on an
  artifact.

**Exit criteria**

- Pattern detector recovers known clusters from the seed corpus.
- One full cycle completes end to end: entry → pattern → proposed diff → approved →
  new contract with negative control → measured before/after.
- Held-out score does not regress.

---

## Sequence

```
MP-1 · Assumptions falsified or confirmed
├── P0.1  Cross-harness script execution
├── P0.2  Negative control on behavioral method
├── P0.3  Capture without hooks
└── P0.4  Decision points without an interactive primitive
↓
MP-2 · Portable substrate
├── Repo scaffold + install.sh
└── lint_portable.py in CI
↓
MP-3 · MiniProject skill
├── SKILL.md + references
├── validate_bundle.py
└── Discovery modeling decision
↓
MP-4 · Eval harness
├── Contract format + runner
├── Negative-control mode
└── Three-harness matrix
↓
MP-5 · Capture
├── register_append.py + register_verify.py
├── Seed import
└── Artifact contract
↓
MP-6 · Improvement loop
├── Analyze + pattern detection
├── Detector validated on seed corpus
├── Propose-diff-only with approval gate
└── Held-out contract set
```

---

## Process

- Tracked issue before any branch or code. No work directory without one.
- One branch per issue, off `main`.
- Tests before implementation. Higher rigor on the eval harness — it is the trust
  anchor and cannot check its own correctness.
- CI runs `lint_portable.py` and deterministic script tests on every PR. The
  behavioral matrix runs on demand and on model-version change, not per-commit.
- Phase 0 findings are written up before Phase 1 starts, including any that
  invalidate this plan.

---

## Confidence

**High** for Phases 0–4. Greenfield, verified target platforms, no dependency on
external framework internals, and an eval method with a real precedent to build
from.

**Low** for Phase 5 if built concurrently with Phase 4, for the reason the plan is
sequenced the way it is: analyzing an empty register produces nothing, and
confirming impact with an eval that has never failed produces false confidence.
Sequenced after capture is proven, with outcome assertions and a held-out set, it
moves to moderate.

## What would force a revision

- **P0.1 fails** — validators become prose; enforcement is advisory in every harness
  and the value proposition weakens materially.
- **P0.2 fails** — the behavioral method is not portable; Phase 3 becomes research.
  This is the spike most likely to surprise, given how consistently green the
  precedent has been.
- **P0.3 under threshold** — Phase 5 is cut rather than deferred.
