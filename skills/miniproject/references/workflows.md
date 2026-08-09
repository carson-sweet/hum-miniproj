# Executable workflows

Create the artifact for the current decision, run the named script using its path
inside this skill, and revise until it exits 0. Exit 1 means the artifact has
findings. Exit 2 means the input itself is invalid.

## Validate one MiniProject

For a user-facing report, run
`scripts/validate_bundle.py --format human BUNDLE.json`. Use the default JSON
format only for machine-readable output or an explicitly requested JSON artifact.

```json
{
  "work_type": "miniproject",
  "name": "Complete improvement name",
  "criteria": {
    "complete": "Behavior or operational result delivered end to end",
    "demoable": "Observable proof",
    "owned": "One owner through release",
    "launch_ready": "Verification, rollout, and recovery conditions"
  }
}
```

The validator checks presence without grading weak answers, but it rejects an
explicit frontend, backend, API, data, infrastructure, QA, or testing-only boundary.

## Validate a split

Run `scripts/validate_split.py SPLIT.json`. Include at least two complete
MiniProjects. Give every bundle a unique `id`, list sibling `dependencies`, and
leave at least one dependency list empty so one piece can launch independently.

```json
{
  "source": "Oversized improvement",
  "bundles": [
    {
      "id": "first-result",
      "work_type": "miniproject",
      "name": "First independently useful result",
      "dependencies": [],
      "criteria": {
        "complete": "Complete behavior",
        "demoable": "Observable proof",
        "owned": "One owner",
        "launch_ready": "Safe release conditions"
      }
    }
  ]
}
```

Do not split into frontend, backend, data, infrastructure, or QA bundles.

## Close Tech Refinement

Run `scripts/validate_board.py BOARD.json` with `stage: tech_refinement`.
Resolve every incoming card exactly once as a named MiniProject, a Chore, or More
Discovery. Name exactly one owner for each MiniProject. Keep PR sequences, test
details, implementation detail, and rollout steps out of the board artifact.

```json
{
  "stage": "tech_refinement",
  "project": "Project name",
  "cards": [
    {
      "id": "D-1",
      "resolution": {
        "work_type": "miniproject",
        "name": "Complete improvement",
        "owner": "One person"
      }
    },
    {
      "id": "D-2",
      "resolution": {
        "work_type": "discovery",
        "terminal_outcome": "More Discovery",
        "owner": "One person",
        "next_question": "The next question"
      }
    }
  ]
}
```

## Check Tech Estimation

Run `scripts/validate_board.py BOARD.json` with `stage: tech_estimation`.
Give every Chore and MiniProject an `effort_estimate`. Give every Discovery item a
`time_box` and `target_output`; never give it `story_points`, `effort_estimate`,
`effort_size`, or `delivery_estimate`.

```json
{
  "stage": "tech_estimation",
  "items": [
    {"id": "C-1", "work_type": "chore", "effort_estimate": "1"},
    {
      "id": "D-1",
      "work_type": "discovery",
      "time_box": "2 days",
      "target_output": "Named decision artifact"
    }
  ]
}
```

## Shape a broad Project

Run `scripts/validate_discovery_plan.py PLAN.json`. State v1 scope as non-empty
`in` and `out` lists. Rank every Discovery card, and give each a question, owner,
and useful output. Do not specify technical bundles. Engineering records its review
separately; completion requires `accepted` with zero returned cards.

```json
{
  "project": "Broad goal",
  "scope": {"in": ["Included outcome"], "out": ["Excluded outcome"]},
  "discovery_cards": [
    {
      "id": "D-1",
      "rank": 1,
      "question": "Question to answer",
      "owner": "One person",
      "useful_output": "Inspectable result"
    }
  ],
  "engineering_review": {"status": "accepted", "returned_cards": []}
}
```

Do not invent Engineering acceptance. If review is pending, say so and leave the
workflow incomplete until Engineering supplies the review result.

## Route a work request

Run `scripts/route_request.py REQUEST --owner OWNER`.

- A specific bounded request becomes a Chore in the fast lane without Discovery.
- A broad request returns to shaping as a Project with an explicit in/out-scope and
  ranked-Discovery next step.
- If a broad request has no shaping owner, ask only who owns that next step; never
  return silence or invent the owner.
