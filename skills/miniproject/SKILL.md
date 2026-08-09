---
name: miniproject
description: Decide what kind of work a request is and how it belongs on a board; classify and route it as a Project, Discovery, MiniProject, or Chore; shape ranked Discovery cards; run Tech Refinement and Tech Estimation checks; split oversized bundles along complete-improvement boundaries; and validate owner-led, launch-ready MiniProjects. Use during Product Refinement, Tech Refinement, Tech Estimation, sprint planning, work intake, bundle validation, or splitting for any feature, bug, typo, technical-layer ticket, specific customer ask, or broad product goal.
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

## Execute the selected workflow

Use the exact input schema in [workflows.md](references/workflows.md). Write the
artifact, run the corresponding script using its path inside this skill, and use
its structured findings to revise the artifact. Do not claim that a workflow is
valid unless the script exits 0.

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

Run `scripts/validate_bundle.py` and pass the proposal file. Treat exit 0 as valid,
exit 1 as findings that require revision, and exit 2 as invalid input.

The validator checks answer presence and rejects an explicitly technical-layer-only
boundary. It does not grade whether any other answer is persuasive. If it reports
findings, revise or split the work and rerun it.

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
