# MiniProject Skill — User Stories

**Version 1.0 (draft) — 2026-08-08**
**Format:** Gherkin (Given/When/Then)
**Scope:** All personas; SLC subset marked
**Audience:** Internal (Hum) — engineering handoff and eval-contract input
**Depends on:** `docs/product/hum-miniproj-user-personas-draft-v1.0-20260808.md` v1.0

---

## Why Gherkin

Phase 3 of the implementation plan builds a behavioral eval harness where every contract
ships with a negative control. Gherkin scenarios are the direct input to that harness — a
scenario and its failure case become a contract and its mutation. Generic
As-a/I-want/So-that stories would need translating first.

Each story below carries at least one **negative scenario**. That is not stylistic. A
contract that only describes success cannot be shown to detect failure.

---

## The SLC line

**Promise to the MiniProject Owner:** *You can take any proposed piece of work and know,
without leaving your editor, whether it is a real MiniProject — and if it is not, exactly
which criterion is unanswered.*

SLC v1 is **US-OWN-001 through US-OWN-004**. Those four completely deliver that promise to
one persona. Everything below them is real, ranked, and deliberately not v1.

| Story | Persona | In SLC v1 | Milestone |
|-------|---------|-----------|-----------|
| US-OWN-001 | MiniProject Owner | ✅ | MS-003 |
| US-OWN-002 | MiniProject Owner | ✅ | MS-003 |
| US-OWN-003 | MiniProject Owner | ✅ | MS-003 |
| US-OWN-004 | MiniProject Owner | ✅ | MS-002 |
| US-FAC-001 | Refinement Facilitator | — | MS-003 |
| US-FAC-002 | Refinement Facilitator | — | MS-003 |
| US-VAL-001 | Value Definer | — | post-MS-003 |
| US-REQ-001 | Work Requester | — | post-MS-003 |

---

## MiniProject Owner (SLC v1)

### US-OWN-001: Validate a bundle against the four criteria

As a MiniProject Owner
I want to check a proposed bundle against complete, demoable, owned, and launch-ready
So that I do not commit to owning a technical layer wearing a MiniProject label

```gherkin
Scenario: All four criteria have stated answers
  Given a proposed bundle with a stated answer for each of the four criteria
  When I run the bundle validator
  Then it reports no findings
  And it does not comment on the quality of any answer

Scenario: A criterion has no stated answer
  Given a proposed bundle where "launch-ready" is left blank
  When I run the bundle validator
  Then it reports exactly one finding, naming "launch-ready"
  And the other three criteria produce no findings

Scenario: Negative control — the validator must not grade
  Given a bundle whose "demoable" answer is present but weak
  When I run the bundle validator
  Then it reports no finding for "demoable"
  And the decision to accept or revise stays with the owner
```

### US-OWN-002: Reject a partial technical layer

As a MiniProject Owner
I want a bundle that is only a technical layer to fail validation
So that the old frontend/backend/QA split cannot re-enter under a new name

```gherkin
Scenario: Partial technical layer is rejected
  Given a bundle described only as "backend API changes for widget reporting"
  When I run the bundle validator
  Then it reports a finding against "complete"
  And the bundle is not accepted as a MiniProject

Scenario: Complete improvement is accepted
  Given a bundle described as "Inline Widget Reporting, including UI, API, tests, and rollout"
  When I run the bundle validator
  Then no finding is reported against "complete"

Scenario: Negative control — remove the completeness rule
  Given the completeness criterion is deleted from the validator's checks
  When I run the partial-technical-layer bundle
  Then the suite reports a detection failure for this contract
```

### US-OWN-003: Split an oversized bundle

As a MiniProject Owner
I want to split a bundle that one person cannot carry
So that each resulting piece is independently launch-ready

```gherkin
Scenario: Split produces independently valid bundles
  Given a bundle that fails the "owned" criterion
  When I split it into two bundles along complete-improvement lines
  Then each resulting bundle independently passes all four criteria

Scenario: At least one piece can launch alone
  Given a set of bundles produced by a split
  When I check their launch dependencies
  Then at least one bundle is launch-ready without any other shipping first

Scenario: Split along technical layers is caught
  Given a bundle split into "frontend work" and "backend work"
  When I validate each resulting bundle
  Then both report a finding against "complete"
```

### US-OWN-004: Run the validator in any supported harness

As a MiniProject Owner
I want the skill to work in the editor I actually use
So that adopting it does not mean changing tools

```gherkin
Scenario Outline: Validator executes across harnesses
  Given the skill is installed via install.sh
  When I invoke the bundle validator in <harness>
  Then it executes and returns structured findings
  And the findings are identical to every other harness for the same input

  Examples:
    | harness      |
    | Claude Code  |
    | Codex        |
    | Junie        |

Scenario: Negative control — a harness-specific construct is planted
  Given a bang preamble is added to SKILL.md
  When lint_portable.py runs in CI
  Then it fails and names the offending construct
```

---

## Refinement Facilitator

### US-FAC-001: Classify every Discovery card

As a Refinement Facilitator
I want every Discovery card resolved before Tech Refinement ends
So that nothing enters Sprint Planning unclassified

```gherkin
Scenario: Every card is resolved
  Given a Project with 5 Discovery cards
  When Tech Refinement completes
  Then each card is exactly one of a named MiniProject, a Chore, or needs-more-Discovery
  And zero cards remain unclassified

Scenario: Each MiniProject has exactly one owner
  Given Tech Refinement has produced 3 MiniProjects
  When I review the owner assignments
  Then each MiniProject names exactly one owner
  And no MiniProject names two or more

Scenario: Implementation detail stays off the board
  Given a MiniProject with a planned 4-PR sequence
  When Tech Refinement records it
  Then the board shows the MiniProject only
  And the PR sequence lives in the owner plan
```

### US-FAC-002: Apply the estimation policy

As a Refinement Facilitator
I want Discovery time-boxed rather than estimated
So that learning work does not carry false implementation precision

```gherkin
Scenario: Chores and MiniProjects are estimated
  Given a Chore and a MiniProject leaving Tech Estimation
  When I check their measures
  Then both carry an effort estimate

Scenario: Discovery is time-boxed
  Given a Discovery item leaving Tech Estimation
  When I check its measure
  Then it carries a time-box and a target output
  And it carries no effort estimate

Scenario: Negative control — Discovery is pointed
  Given a Discovery item is assigned story points
  When the estimation policy check runs
  Then it reports a violation naming the item
```

---

## Value Definer

### US-VAL-001: Turn a broad Project into ranked Discovery cards

As a Value Definer
I want to name the open questions without specifying technical bundles
So that Engineering can bundle safely and I stay in the loop

```gherkin
Scenario: Cards carry owner and useful output
  Given a prioritized Project
  When I produce its Discovery cards
  Then each card names an owner and a useful output

Scenario: Cards are accepted without rescoping
  Given a complete set of Discovery cards
  When Engineering reviews them at Tech Refinement
  Then zero cards are returned for re-scoping

Scenario: Direction-only scope is caught
  Given a v1 scope stated as "improve onsite optimization"
  When I check it against the scope rule
  Then it is flagged as a direction rather than an in/out list
```

---

## Work Requester

### US-REQ-001: File a request that lands in the right lane

As a Work Requester
I want a quick answer on whether my ask is fast or needs shaping
So that specific customer requests are not absorbed into Projects

```gherkin
Scenario: Specific ask enters the fast lane
  Given a request "Add the onsite optimization widget to the sales blog"
  When it is classified
  Then it is a Chore
  And it enters the fast lane without Discovery

Scenario: Broad ask returns with a named next step
  Given a request "Improve onsite optimization"
  When it is classified
  Then it is not a Chore
  And it returns with a named shaping step and its owner

Scenario: Negative control — silence on a broad ask
  Given a broad ask is classified but no shaping step is named
  When the request contract runs
  Then it fails, because silence is the failure mode this guards
```

---

## Deliberate deviation from the skill template

`sweetclaude:product-user-stories` specifies per-story files at
`{base_path}/stories/US-{abbr}-{NNN}.md`. Those are **not** written here. The ID pattern in
`scripts/schema.py` (`^(ISSUE|EP|MS|SP|TH|RM|REL|PITCH|CYC|I)-\d{2,}$`) does not accept
`US-OWN-001`, so per-story files would fail frontmatter validation and be skipped by the
roadmap cache on every rebuild. Stories live in this document until they are promoted into
`ISSUE-NNN` work items, which the cache does index.

---

## Additional development

1. **Success thresholds are unmeasured.** "Under 5 minutes" (personas doc) and "zero cards
   returned" are plausible targets, not observed baselines.
2. **No stories for the improvement loop** (MS-005, MS-006). Deliberate — the plan gates
   those on P0.3 and on capture producing live entries.
3. **Negative controls here are sketched, not specified.** Phase 3 turns each into a
   declared mutation with an expected failure.
4. **US-VAL-001 and US-REQ-001 assume a classifier** that the plan does not yet scope.
   They may become Discovery rather than implementation.

---

## Changelog

| Version | Date       | Change summary                                        |
|---------|------------|-------------------------------------------------------|
| 1.0     | 2026-08-08 | Initial draft. 8 stories, Gherkin, SLC subset marked.  |
