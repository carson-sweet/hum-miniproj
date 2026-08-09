---
name: miniproject
description: Decide what kind of work a request is and how it belongs on a board; classify and route it as a Project, Discovery, MiniProject, or Chore; shape ranked Discovery cards; run Tech Refinement and Tech Estimation checks; split oversized bundles along complete-improvement boundaries; validate owner-led, launch-ready MiniProjects; capture workflow learnings; and run human-approved improvement cycles. Use during Product Refinement, Tech Refinement, Tech Estimation, sprint planning, work intake, bundle validation, splitting, or improvement review for any feature, bug, typo, technical-layer ticket, specific customer ask, or broad product goal.
---

# MiniProject

Bundle delivery around a complete improvement, not a technical layer. Keep one
owner responsible for the path from behavior through safe release while allowing
multiple small implementation changes and reviews.

## Workflow

1. Read [work-types.md](references/work-types.md) and classify the request before
   estimating or splitting it.
2. Read [workflows.md](references/workflows.md), choose the executable workflow, and
   run its bundled script:
   - **Validate a proposed bundle:** use `scripts/validate_bundle.py`.
   - **Validate a proposed split:** use `scripts/validate_split.py`.
   - **Close Tech Refinement:** use `scripts/validate_board.py` with stage
     `tech_refinement`.
   - **Check Tech Estimation:** use `scripts/validate_board.py` with stage
     `tech_estimation`.
   - **Shape a broad Project:** use `scripts/validate_discovery_plan.py`.
   - **Route a work request:** use `scripts/route_request.py`; ask for the shaping
     owner when a broad request does not name one.
3. Follow the route for the resulting work type:
   - **Chore fast lane:** identify it as a Chore and do not run bundle validation.
     Handle it as a small, specific, low-variance request.
   - **Discovery:** define the question, owner, time box, decision artifact, and
     terminal outcome. Do not provide an implementation estimate: no story points,
     effort size, or delivery estimate, even alongside a time box.
     Use exactly one terminal label: Ready to shape, More Discovery, or Stop; do
     not invent a synonym such as Inconclusive.
   - **Project:** identify the sequencing goal and the Discovery questions needed
     before delivery bundles are trustworthy.
   - **MiniProject:** gather a stated answer for each bundle criterion, then run
     the deterministic validator.
4. Read [bundling-criteria.md](references/bundling-criteria.md) when shaping,
   splitting, or reviewing a MiniProject.
5. Read [estimation-policy.md](references/estimation-policy.md) before discussing
   effort or timing.
6. Read [decision-points.md](references/decision-points.md) when facilitating
   prioritization, refinement, estimation, or sprint selection.
7. Close every completed workflow with the improvement-capture procedure below.
8. Read [improvement-loop.md](references/improvement-loop.md) when analyzing the
   register or proposing an instruction improvement. Its approval and held-out gates
   are mandatory.

## Execute the selected workflow

Use the exact input schema in [workflows.md](references/workflows.md). Write the
artifact, run the corresponding script using its path inside this skill, and use
its structured findings to revise the artifact. Do not claim that a workflow is
valid unless the script exits 0.

For every user-facing workflow, pass `--format human` and return that
human-formatted output as the result. Use the default JSON format only when the
user explicitly requests machine-readable output or an exact JSON artifact. Do
not paste raw JSON as the user-facing result.

For a single MiniProject, represent the proposal as JSON:

```json
{
  "work_type": "miniproject",
  "name": "Recover a locked account",
  "criteria": {
    "complete": "What improvement is delivered end to end",
    "demoable": "How someone will see it work",
    "owned": "Who carries behavior through release",
    "launch_ready": "What makes it safe to release"
  }
}
```

Run `scripts/validate_bundle.py --format human` and pass the proposal file. Treat
exit 0 as valid, exit 1 as findings that require revision, and exit 2 as invalid
input. Do not add an answer-quality assessment that the deterministic validator
did not perform.

The validator checks answer presence and rejects an explicitly technical-layer-only
boundary. It does not grade whether any other answer is persuasive. If it reports
findings, revise or split the work and rerun it.

## Capture an improvement learning

Before returning the final result for a completed workflow, append exactly one concise
procedural learning to the improvement register and verify that this session added it.
Prefer a user correction, then a stated preference, then a recurring pattern; otherwise
record a confirmation of the rule the completed workflow exercised. Never capture secrets,
credentials, customer data, or a transcript.

Resolve this skill's directory from the loaded `SKILL.md`. Choose a source-session value
that uniquely identifies the current interaction and reuse the same value for both calls.
Use the active harness name and the instruction file most directly concerned as `--skill`.
Honor `MINIPROJECT_REGISTER` or an explicit user-provided register path; otherwise the
scripts use `~/.local/share/miniproject/improvement-register.jsonl`.

```bash
python3 <skill-dir>/scripts/register_append.py \
  --type <correction|confirmation|preference|pattern> \
  --learning "<durable procedural learning>" \
  --harness <codex|junie|claude|other> \
  --skill <target instruction path> \
  --source-session <current-session-id>
python3 <skill-dir>/scripts/register_verify.py \
  --source-session <current-session-id> --require-live
```

If verification fails, do not claim capture succeeded. Correct the append input and rerun
both scripts. `register_append.py` is the register's only writer. Import the bundled seed
corpus through its `--import-seed references/improvement-seed.jsonl` option; seed entries never
satisfy live-capture verification.

Never create, edit, repair, or append to the register through shell redirection, a file-edit
tool, another script, or manually constructed JSON. If `register_append.py` cannot write a
valid entry, report capture failure; do not bypass the only-writer boundary to satisfy the
verifier.

## Run an improvement cycle

Follow [improvement-loop.md](references/improvement-loop.md). Analyze only after live
capture is proven, prepare a candidate in a separate file, and generate a reversible diff.
Never apply the proposal. Stop for explicit human approval, add a targeted contract with a
negative control, measure the current and candidate instructions against both targeted and
held-out contracts, record the version scores, and run
`scripts/validate_improvement_cycle.py`. A held-out regression or missing approval blocks
the cycle.

## Interaction rules

- Ask only the unresolved decision needed for the current step. Do not answer it
  on the user's behalf.
- Keep implementation sequence, test detail, and rollout mechanics in the
  owner's plan unless another participant needs visibility.
- Do not turn a MiniProject into one giant change. End-to-end ownership and small
  reviewable changes are compatible.
- When staffing one MiniProject across several people, name one accountable owner and label every other participant as a contributor; never assign contributors ownership of UI, API, data, verification, rollout, or another technical-layer slice.
- In an ownership answer, use accountable only for the one end-to-end owner.
  Specialists may lead or implement technical work as contributors, but do not call
  a specialist accountable for a technical slice.
- State uncertainty directly. Route unclear work to Discovery instead of forcing
  a confident bundle.
