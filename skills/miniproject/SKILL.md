---
name: miniproject
description: Decide what kind of work a request is and how it belongs on a board by classifying it as a Project, Discovery, MiniProject, or Chore; shape complete owner-led improvements; apply the estimation policy; and validate proposed bundles. Use when planning, refining, splitting, estimating, or reviewing any delivery request, including a feature, bug, typo, one-line fix, technical-layer ticket, or broad product goal.
---

# MiniProject

Bundle delivery around a complete improvement, not a technical layer. Keep one
owner responsible for the path from behavior through safe release while allowing
multiple small implementation changes and reviews.

## Workflow

1. Read [work-types.md](references/work-types.md) and classify the request before
   estimating or splitting it.
2. Follow the route for that work type:
   - **Chore fast lane:** identify it as a Chore and do not run bundle validation.
     Handle it as a small, specific, low-variance request.
   - **Discovery:** define the question, owner, time box, decision artifact, and
     terminal outcome. Do not provide an implementation estimate.
   - **Project:** identify the sequencing goal and the Discovery questions needed
     before delivery bundles are trustworthy.
   - **MiniProject:** gather a stated answer for each bundle criterion, then run
     the deterministic validator.
3. Read [bundling-criteria.md](references/bundling-criteria.md) when shaping,
   splitting, or reviewing a MiniProject.
4. Read [estimation-policy.md](references/estimation-policy.md) before discussing
   effort or timing.
5. Read [decision-points.md](references/decision-points.md) when facilitating
   prioritization, refinement, estimation, or sprint selection.

## Validate a MiniProject

Represent the proposal as JSON:

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

Run the bundled `scripts/validate_bundle.py` using its path inside this skill and
pass the proposal file. Treat exit 0 as structurally valid, exit 1 as missing
answers, and exit 2 as invalid input.

The validator checks presence only. Never claim it approved the quality of an
answer. If it reports missing criteria, obtain those answers and rerun it. If the
answers reveal a technical-layer slice, reshape the work into a complete
improvement or return it to Discovery.

## Interaction rules

- Ask only the unresolved decision needed for the current step. Do not answer it
  on the user's behalf.
- Keep implementation sequence, test detail, and rollout mechanics in the
  owner's plan unless another participant needs visibility.
- Do not turn a MiniProject into one giant change. End-to-end ownership and small
  reviewable changes are compatible.
- State uncertainty directly. Route unclear work to Discovery instead of forcing
  a confident bundle.
