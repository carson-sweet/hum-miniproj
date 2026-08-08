# MiniProject Skill — User Personas

**Version 1.0 (draft) — 2026-08-08**
**Status:** Provisional — built without discovery research
**Audience:** Internal (Hum)
**Sources:** `Fewer_Handoffs_Faster_Launches_MiniProject_Model_whimsy_v7.pdf` (June 2026);
`docs/miniproject-model.md`; hum.works and hum.works/meet-the-team

---

## Method and its limits

These are **role archetypes**, not profiles of individuals. The deck's partnership model
already assigns responsibility by role — Product/CSX/Business define value, Engineering
bundles delivery — so roles are the natural unit. Each persona lists the people who
currently occupy it, for grounding only; no personal characteristics are attributed to
anyone.

They are **provisional**. There is no `discovery.yaml` behind them. Triggers,
deal-breakers, and failure modes are derived from what the deck states, not from talking
to users. Treat every deal-breaker as a hypothesis worth testing before it shapes the
skill.

---

## The four personas

| # | Persona | Role | Occupied by |
|---|---------|------|-------------|
| 1 | **MiniProject Owner** | Software Engineer / Senior SWE | Andrew Bancroft, Lisa Dina, Esha Datta |
| 2 | **Refinement Facilitator** | Director of Engineering / CTO | Dylan DiGioia, Niall Little |
| 3 | **Value Definer** | Principal Product Designer / Product | Chelsea Hitzler |
| 4 | **Work Requester** | Customer Success / AM / BD | Jake Minturn, Carson Fiori, Heather Trice, John Challice |

Persona 1 is the primary user. The skill is used *by* the owner, *during* Tech
Refinement by the facilitator, and *felt* by personas 3 and 4 through what reaches them.

---

## 1. MiniProject Owner — primary

Carries one complete improvement end to end: problem, technical approach, how AI is used,
PR sequencing, feedback, testing, QA, release risk. The deck's core shift — *engineers are
problem owners, not ticket takers*.

**Trigger.** Tech Refinement hands them a named bundle. Before committing, they must
decide whether it is genuinely complete, demoable, ownable by one person, and launch-ready
— or a technical layer wearing a MiniProject label.

**Deal-breakers.** Ceremony that adds process without removing coordination. Working in
only one harness. Grading their answer instead of checking an answer exists. Any push
toward giant PRs.

**Task 1 — Validate a bundle before owning it.** Success is binary:

- Validator flags every criterion with no stated answer, and none that has one
- Revise / split / proceed reached in under 5 minutes without leaving the editor
- Runs identically in Claude Code, Codex, and Junie

Fails when: all four answered "yes" without evidence and the validator accepts it; the
validator drifts into grading quality; a partial technical layer passes on aspiration.

**Task 2 — Split an oversized bundle.** Success: each resulting bundle independently
passes all four criteria, at least one can launch without the others, and none is a single
technical layer. Fails when the split reproduces frontend/backend/QA seams under new
names, or when every piece depends on every other.

---

## 2. Refinement Facilitator

Runs Tech Refinement and Tech Estimation. Converts Discovery output into bundles one
engineer can own, and decides what still needs Discovery. Accountable for keeping
implementation crumbs in the owner plan and off the shared board.

**Trigger.** Product Refinement output lands. The Project cannot enter Sprint Planning
until its cards become bundles, Chores, or Discovery flags.

**Deal-breakers.** Can't be run live inside the existing meeting — the deck is explicit
that this sharpens existing decision points rather than inventing a shadow workflow.
Pushes full technical breakdowns onto the board. Requires everyone to install something.

**Task 1 — Run Tech Refinement.** Success: every Discovery card resolves into exactly one
of a named MiniProject with one owner, a Chore, or a needs-more-Discovery flag; zero cards
unclassified at close; every bundle has exactly one owner, never two.

**Task 2 — Apply the estimation policy.** Success: 100% of items leaving Tech Estimation
carry the right measure — estimates for Chores and MiniProjects, time-boxes for Discovery.
No Discovery item carries story points. Fails when Discovery gets pointed like
implementation and its variance goes invisible.

---

## 3. Value Definer

Defines customer need, priority, urgency, launch goals, and what matters most. Produces
Discovery cards specific enough for Engineering to bundle safely — without specifying the
bundles.

**Trigger.** Prioritization selects a Project. It is still a broad ask, and Engineering
cannot bundle it until the open questions are named and ranked.

**Deal-breakers.** Anything that reduces Product input — listed as an explicit non-goal in
the deck. Being asked to specify technical bundles or release safety. Cards bounced back
without a stated reason.

**Task — Turn a broad Project into ranked Discovery cards.** Success: every card names its
owner *and* its useful output; Engineering accepts the set at Tech Refinement with zero
cards returned for re-scoping; v1 scope is an explicit in/out list, not a direction.

---

## 4. Work Requester

Closest to the customer. Requests Projects, Discovery, or Chores and supplies customer
examples, urgency, workarounds, and account impact. Does not create MiniProjects —
Engineering does that once the work has shape.

**Trigger.** A publisher client hits a limitation or asks for something specific. The
requester needs to know quickly whether it is fast or needs shaping.

**Deal-breakers.** Every request becoming a Project — an explicit non-goal. Having to
learn engineering vocabulary to file correctly. Broad asks disappearing silently.

**Task — File a request so it lands in the right lane.** Success: a specific bounded ask
is classified as a Chore and enters the fast lane without Discovery; a broad ask returns
with a named shaping step and owner, never silence; classification stated within one
refinement cycle. Fails when a specific ask gets absorbed into a Project and loses its
speed, or when a broad ask is accepted as a Chore and stalls mid-sprint.

---

## Anti-profile

**Teams whose bottleneck is implementation rather than coordination.** The model's entire
premise is that AI compressed implementation and left coordination untouched. A team that
has not felt that compression takes on overhead with no offsetting saving.

Also out of scope: organizations looking to reduce code review or Product involvement
(both explicit non-goals); teams wanting a replacement issue tracker rather than a
bundling discipline; solo developers with no handoffs and therefore no coordination tax.

---

## Diversity check

The persona set spans four functions, three seniority bands, and both requester and
builder sides of the partnership model. Two known gaps:

- **No customer persona.** Hum's actual end users — editors and publishers at BMJ,
  Emerald, OUP — never touch this skill. Correct for an internal delivery tool, but worth
  stating so it isn't mistaken for an oversight.
- **No skeptic persona.** Everyone modeled here is assumed to accept the operating model.
  The engineer who thinks the old board worked fine is the one most likely to reveal where
  the skill is annoying, and is not represented.

---

## Additional development

Not covered here, and worth doing before these harden:

1. **Validate the deal-breakers.** Every one is inferred from the deck. Ask three
   engineers what would actually make them stop using it.
2. **Test the 5-minute criterion** in Task 1. It is a plausible number, not a measured one.
3. **Add the skeptic.** Recruit from whoever pushes back hardest in Tech Refinement.
4. **Run `/sweetclaude:product-discovery`** to ground segments, scenarios, and JTBD, then
   revise this document to v2.

---

## Changelog

| Version | Date       | Change summary                                                    |
|---------|------------|-------------------------------------------------------------------|
| 1.0     | 2026-08-08 | Initial draft from the June 2026 deck and hum.works team roles.    |
