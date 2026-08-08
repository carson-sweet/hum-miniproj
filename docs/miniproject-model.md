# MiniProject Operating Model

**Version 1.0 — 2026-08-08**

The methodology this skill implements. Source: *Fewer Handoffs, Faster Launches —
MiniProject Operating Model*, June 2026.

---

## Why the old model is misfiring

The agile gold standard was to break work into the smallest testable units —
frontend, backend, data, infra, design, analytics, QA. That created leverage when
each technical layer took meaningful time, and it optimized for card completion,
independent testing, and predictable handoffs across specialists.

It assumes implementation is slower than coordination.

That assumption no longer holds. Implementation compressed; coordination did not.
A body of work that once justified several owners and many cards may now be a
fraction of the size, but every owner still needs context, review, sequencing, and
coordination. Same handoffs, smaller work, worse ratio.

The consequence: the process becomes the bottleneck **during** the work, not just
before it.

## What actually slows things down

Not the code path — the coordination surface area.

Every extra card and owner adds seams: context sharing, dependency management,
partial ownership, repeated explanation, review queues, and "who owns this?"
moments.

Two corollaries:

- **Tiny cards are not free.** A board full of small tasks can still carry a large
  coordination bill.
- **Parallelism is no longer automatic leverage.** More hands can mean more handoffs
  when the underlying tasks are smaller.

The target is to reduce seams during the work so ideas reach first launch faster.

## The shift

| Old default | New default |
|---|---|
| Split by technical layer: frontend, backend, infra, data, analytics, QA | Bundle by complete improvement: one coherent problem, one owner, launch-ready by design |

Small PRs stay. What stops is making the shared planning board carry every
implementation crumb.

## What a MiniProject is

Small enough for one owner to carry. Complete enough to ship.

A MiniProject is a complete, demoable improvement. It can touch frontend, backend,
data, AI, tests, analytics, and deployment — but it has one owner and one coherent
launch-ready result.

Four properties, all required:

- **Complete** — not a partial technical layer.
- **Demoable** — something real to show.
- **Owned** — one owner carries the path.
- **Launch-ready** — safe to release, even if held.

## Ownership

MiniProjects give owners more room to operate. That room comes with responsibility
for the whole path from problem to working improvement:

1. Understand the problem
2. Shape the technical approach
3. Choose how to use AI
4. Break work into PRs
5. Get feedback
6. Test, QA, and manage release risk

Owners are problem owners, not ticket takers.

## The partnership

| Product / CSX / Business | Engineering |
|---|---|
| Define the customer need, priority, urgency, launch goals, and what matters most | Define MiniProject boundaries, sequencing, technical approach, testing, and release safety |

Stakeholders request Projects, Discovery, or Chores. Engineering creates
MiniProjects once the work has enough shape to bundle safely.

## The four work types

A shared map, not a new bureaucracy.

**Project** — a larger initiative or product/business goal that may contain multiple
pieces of work.

**Discovery** — work to understand, decide, design, rank, or de-risk before build.

**MiniProject** — a complete improvement one owner carries end to end.

**Chore** — a small, specific request with low coordination overhead.

Small requests get speed. Broad requests get shaping.

## Why specificity matters

The fastest path is a Chore.

- **Specific ask** — "Add the onsite optimization widget to the sales blog." Clear,
  bounded, low variance.
- **Broad ask** — "Improve onsite optimization." Worth considering, but it needs
  Discovery or Project shaping before timing is predictable.

The broader the ask, the more Engineering must reason through bundles,
dependencies, testing, release safety, and sequencing.

## The five decision points

The model fits an existing operating rhythm rather than inventing a shadow
workflow. Each recurring meeting gets one sharper question.

| # | Meeting | Question |
|---|---|---|
| 1 | Product Prioritization | What Projects should Product focus on? |
| 2 | Product Refinement | What Discovery cards belong inside each Project? |
| 3 | Tech Refinement | Based on Discovery, what MiniProjects are in the Project? |
| 4 | Tech Estimation | What effort is associated with each Chore and MiniProject? Discovery is time-bound. |
| 5 | Sprint Planning | What does the business want in the next sprint? |

### Product Refinement

Turns a broad Project into the specific questions that need answers before Tech can
confidently bundle delivery. Output is Discovery cards with owners and useful
outputs — not a full technical breakdown.

### Tech Refinement

Uses Discovery output to bundle complete improvements one owner can carry end to
end. Four questions:

1. What is complete and demoable?
2. What can one owner carry end to end?
3. What can be tested and made launch-ready?
4. What needs more Discovery first?

PR sequence, implementation details, tests, rollout steps, and escalation points
stay inside the owner's plan unless they need team visibility.

### Tech Estimation

- **Chore** — small, specific, low variance. Estimate normally.
- **Discovery** — often time-bound. Produce a decision, approach, or next step.
- **MiniProject** — estimate as a complete improvement: behavior, tests, and release
  readiness.

**Key rule:** do not estimate Discovery like normal implementation when the right
output is learning, ranking, design, or de-risking.

**The cliff:** specific asks stay in the fast lane. Broad asks move into Project
sequencing, which is healthy but carries more timing variance.

### Sprint Planning

Chooses from ready work across three lanes:

- **Fast lane** — pull the Chore when it is useful and specific.
- **Learn lane** — pull Discovery when the next decision needs a time-bound answer.
- **Build lane** — pull MiniProjects when the bundle is complete enough for one owner
  to make launch-ready.

The board shows complete improvements and decision work. The owner's plan carries PR
sequence, test details, rollout mechanics, and other implementation crumbs.

## What this is not

- Not giant PRs
- Not less review
- Not less Product input
- Not owners working alone
- Not every request becoming a Project
- Not process for process' sake

The goal is not to do less planning. It is to spend less time coordinating fragments
and more time launching complete improvements.

## Takeaway

Less refinement purgatory. Faster first launch.

MiniProjects are complete improvements: one owner, one coherent path, launch-ready
by design.

---

## Open modeling questions

Carried into implementation, not resolved here.

**How is Discovery modeled?** Every phase sequence in conventional tooling
terminates in shipped code. Discovery's correct output is a decision, approach, or
next step. Whether it gets its own phase sequence ending in a decision artifact, or
is modeled as an unestimated container with a required output type, is unresolved.

**Where is the MiniProject/Chore boundary enforced?** The distinction is judgment —
"complete and demoable" versus "small, specific, low variance." Encoding judgment as
a hard check tends to produce either a check that always passes or one that
obstructs. The current approach is to check that each criterion has a stated answer,
not to grade the answer.

**How much survives single-operator use?** The model's payoff is reduced coordination
between people. An operator working with an AI agent has already banked much of
that. The bundling discipline — complete improvement over technical layer — is the
part expected to transfer regardless.
