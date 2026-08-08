# P0.4 — Do the decision points survive without an interactive-question primitive?

**Version 1.0 — 2026-08-08**
**Verdict: YES under Codex and Junie. Kill condition not triggered.**

Evidence in `evidence/`. Probe skill in `skill/`, prompt in `PROMPT.txt`, pass criterion in
`CRITERION.txt`.

---

## Assumption at risk

The five decision points work as plain prose. Neither Codex nor Junie exposes an
interactive-question primitive, so a decision point is only numbered text in a `SKILL.md`.
If agents answer their own questions or skip the wait, the decision points have to
restructure as single-question turns.

## Method

A probe skill (`skill/`) presenting the four Tech Refinement questions as numbered prose,
instructing the agent to ask question 1 and stop. Prompt: *"Run Tech Refinement for the
Advanced Site Optimization Widgets project."* Three runs per harness, `gpt-5.6-sol` in both,
judged by an isolated judge against a fixed criterion.

## Result

| Harness | Runs | Verdict |
|---|---|---|
| Codex | 3 | PASS 3 of 3 |
| Junie | 3 | PASS 3 of 3 |

Six for six. No run answered its own question, worked through several questions in one
turn, or proceeded to name MiniProjects.

Codex, run 1 — the whole reply:

```
For the Advanced Site Optimization Widgets project, what is complete and demoable?
```

## Two behavioural differences worth recording

**Junie frames the turn as complete.** All three Junie runs wrapped the output in
`TASK RESULT` / `Changes` / `Verification` structure, with the question demoted to a
trailing note:

```
### Notes
- Question 1: What is complete and demoable?
```

Behaviourally correct — it did not answer. Presentationally, it reads as a finished task
carrying a note rather than a pending question. A user skimming that output could
reasonably think refinement had completed. Codex asked a bare question and stopped.

**Codex sometimes supplies context, not answers.** Run 2 posed the question and listed the
candidate work beneath it. That is context-gathering, not self-answering, and it passed —
but the line between the two is thinner than the criterion makes it sound.

## What this does NOT establish

**"Waiting" was inferred, not observed.** In non-interactive mode, ending the turn is the
only thing an agent *can* do. What these runs show is that agents do not answer their own
questions. Whether an interactive session actually pauses and accepts the answer is a
different question, and it is untested.

**Single-turn only.** The probe never delivered an answer to question 1, so the sequence —
answer given, agent proceeds to question 2, still does not run ahead — is unexercised. That
is the behaviour the decision points actually depend on.

**One question, not five decision points.** Only Tech Refinement's set was run, as the plan
specifies. The other four decision points are assumed to behave alike, which is an
assumption rather than a finding.

**Claude Code untested.**

## Follow-on

- Run a two-turn version: answer question 1, confirm the agent asks question 2 and stops
  again rather than completing the whole set.
- Decide whether Junie's `TASK RESULT` framing needs mitigating in the skill text — for
  example, instructing the agent to end with the question as the last line.
- Run the remaining four decision points once the skill exists in Phase 2.
