# MiniProject User Guide

**Version 1.0 — 2026-08-09**

This guide is for people using the MiniProject operating model in product planning, work intake, refinement, estimation, sprint selection, and day-to-day delivery. It explains how to use the MiniProject skill with Codex, Junie, or Claude; how to choose the right work type; what information to provide; what results to expect; and how to respond when work is unclear, incomplete, or too large.

## Contents

1. [What the MiniProject model is for](#1-what-the-miniproject-model-is-for)
2. [Install and start using the skill](#2-install-and-start-using-the-skill)
3. [The four work types](#3-the-four-work-types)
4. [Classify a request](#4-classify-a-request)
5. [The four MiniProject criteria](#5-the-four-miniproject-criteria)
6. [Use ownership correctly](#6-use-ownership-correctly)
7. [Run the end-to-end planning workflow](#7-run-the-end-to-end-planning-workflow)
8. [Route a new request](#8-route-a-new-request)
9. [Validate a proposed MiniProject](#9-validate-a-proposed-miniproject)
10. [Split work that is too large](#10-split-work-that-is-too-large)
11. [Shape a broad Project](#11-shape-a-broad-project)
12. [Close Tech Refinement](#12-close-tech-refinement)
13. [Run Tech Estimation](#13-run-tech-estimation)
14. [Run and close Discovery](#14-run-and-close-discovery)
15. [Select work for a sprint](#15-select-work-for-a-sprint)
16. [Understand validator results](#16-understand-validator-results)
17. [Keep the board useful](#17-keep-the-board-useful)
18. [Common mistakes and corrections](#18-common-mistakes-and-corrections)
19. [A complete worked example](#19-a-complete-worked-example)
20. [Prompt library](#20-prompt-library)
21. [Frequently asked questions](#21-frequently-asked-questions)
22. [Working checklist](#22-working-checklist)

## 1. What the MiniProject model is for

The MiniProject model organizes delivery around complete improvements rather than technical layers. A complete improvement is something a customer, teammate, operator, or stakeholder can observe and evaluate. It may require changes to several technical components, but those components remain part of one owned outcome.

The model addresses a common delivery problem: work is often split into frontend, backend, data, infrastructure, testing, and rollout tickets. Each ticket may be clear to one specialist, but nobody owns the full path from intended behavior to a safe release. Coordination grows while the useful outcome remains incomplete.

A MiniProject keeps that path together. One person is accountable for the end-to-end improvement. Other people can contribute in parallel, and implementation can still use several small pull requests. The model changes the ownership boundary, not the preferred size of a code review.

The model also prevents every request from being forced through the same process. Small, specific requests use the Chore fast lane. Uncertain work becomes Discovery. Broad goals become Projects that are shaped before delivery work is promised. Clear, complete improvements become MiniProjects.

Use the model when you need to:

- classify a new request;
- decide whether work is ready for delivery;
- shape a broad product or business goal;
- turn Discovery results into delivery work;
- validate whether a proposed MiniProject is complete;
- split oversized work without creating technical-layer handoffs;
- assign end-to-end ownership;
- estimate delivery work without pretending uncertainty is known;
- keep a planning board focused on decisions instead of implementation detail;
- select ready work without reclassifying it merely to fit a sprint.

## 2. Install and start using the skill

### Install from this repository

From the repository root, run:

```sh
./install.sh
```

The installer places one canonical copy under `~/.agents/skills/miniproject` and creates links for Codex, Junie, and Claude. Running the installer again updates the copy safely. It refuses to overwrite an existing skill or link that it does not own.

To install under a different user home, provide an absolute path:

```sh
./install.sh --home /absolute/path/to/home
```

To remove only the files owned by this installer:

```sh
./install.sh --uninstall
```

After installation, start a fresh agent session so the harness discovers the current skill version.

### Ask the agent to use the skill

The skill is designed to activate for work intake, Project shaping, Discovery, MiniProject validation, Tech Refinement, Tech Estimation, sprint planning, bugs, features, technical-layer proposals, and specific customer requests.

For predictable use, name it directly:

> Use the MiniProject skill to classify and route this request: “Add the account-status field to the customer export.”

You do not need to know which bundled script to run. The agent should choose the workflow, create the required artifact, run the deterministic validator or router, and return the human-readable result.

### What to expect from the agent

The agent should:

1. classify the request before estimating or splitting it;
2. choose the matching workflow;
3. ask only for the unresolved decision needed at that point;
4. avoid inventing owners, decisions, or Engineering approval;
5. create and validate the structured artifact behind the result;
6. return a plain-language result unless you explicitly request JSON;
7. distinguish deterministic validation from human judgment.

If the agent returns raw JSON when you requested a normal user-facing result, ask it to rerun the bundled workflow with human formatting and return only that result.

## 3. The four work types

Every request belongs in one of four types. Classify it before estimating it, assigning it to a sprint, or splitting it into implementation tasks.

| Work type | Use it when | Required result |
| --- | --- | --- |
| Project | The goal contains several improvements or unresolved sequencing decisions | A shaped sequence of Discovery and delivery work |
| Discovery | A question must be answered before responsible delivery work can be defined | A decision artifact and one explicit terminal outcome |
| MiniProject | A complete improvement is clear enough for one owner to carry through release readiness | A complete, demoable, owned, launch-ready improvement |
| Chore | The request is small, specific, low variance, and does not need product shaping | The requested correction or maintenance result |

### Project

A Project is a container for a broader product or business goal. It is not one oversized delivery ticket. It holds the sequence of questions and improvements needed to move toward that goal.

Examples:

- Improve account recovery.
- Increase successful onboarding for small teams.
- Modernize internal reporting.
- Reduce failed payments.

These goals do not yet describe one complete, bounded improvement. They may contain several useful releases, unresolved questions, or sequencing decisions.

A Project becomes actionable by defining explicit in-scope and out-of-scope outcomes, then creating ranked Discovery cards for the questions that must be answered first.

### Discovery

Discovery is bounded work performed to learn, decide, design, rank, or reduce risk. It is not an open-ended research bucket and not a delivery task with a softer estimate.

Every Discovery item needs:

- one question;
- one owner;
- a time box;
- a named decision artifact;
- one terminal outcome when the time box ends.

Example:

> Question: Can the current identity provider support secure password-reset links that expire and cannot be reused?

> Owner: Alice

> Time box: Two days

> Decision artifact: Account-recovery security note with recommendation and unresolved risks

Discovery ends with exactly one of these labels:

- **Ready to shape:** enough is known to define a MiniProject or Chore.
- **More Discovery:** another question must be answered; state that next question and give it a new time box.
- **Stop:** the work should not proceed; record why.

### MiniProject

A MiniProject is a complete improvement one accountable owner can carry from intended behavior through verification and safe release. It answers four questions: complete, demoable, owned, and launch-ready.

Example:

> A locked-out customer can request a reset link, choose a new password, and sign in again.

That outcome may require UI, API, email, data, security, test, monitoring, and rollout work. Those are implementation concerns inside the MiniProject, not separate ownership boundaries on the planning board.

### Chore

A Chore is small, specific, and low variance. It stays in the fast lane and bypasses MiniProject bundle validation.

Examples:

- Correct a misspelled label.
- Add a known field to an existing export.
- Update a pinned dependency after compatibility is already established.
- Remove a retired feature flag.
- Repair one known configuration value.

A request is not a Chore merely because the code change might be small. If the expected outcome, product behavior, or safe approach is unclear, use Discovery or shaping first.

## 4. Classify a request

Use the following sequence.

### Step 1: Is the request specific and low variance?

If the requested result is already clear, requires little coordination, and does not need product shaping, classify it as a Chore.

Example:

> “Change the support-email link in the account footer from the old address to the new address.”

This is a specific correction. It does not need Discovery or four-criterion bundle validation.

### Step 2: Is there a question blocking a responsible delivery boundary?

If an important unknown prevents you from deciding what to build, how to make it safe, or where to draw the improvement boundary, classify the work as Discovery.

Example:

> “Determine whether our identity provider can support account recovery without exposing whether an email address has an account.”

The useful result is a decision, not shipped recovery code.

### Step 3: Is one complete improvement clear?

If you can state the end-to-end result, show how it will be demonstrated, name one owner, and describe what makes it safe to release, classify it as a MiniProject.

Example:

> “A locked-out customer can securely reset a password and sign in again. Alice owns the result through release readiness.”

### Step 4: Does the goal contain several improvements or unresolved sequencing?

If the request is broad, contains several outcomes, or still needs ranked questions before delivery bundles are trustworthy, classify it as a Project.

Example:

> “Improve account recovery.”

That may include self-service reset, administrator assistance, recovery notifications, fraud controls, support tooling, and reporting. Shape the Project before treating it as one delivery item.

### Do not classify by department or component

These are not MiniProject boundaries by themselves:

- Build the frontend.
- Implement the backend API.
- Add the database tables.
- Configure the infrastructure.
- Write the automated tests.
- Prepare the rollout.

They may be important implementation steps, but none describes a complete observable improvement. Keep them in the accountable owner's implementation plan.

### Ask the skill to classify

Paste-ready prompt:

> Use the MiniProject skill to classify and route this request. Explain the classification in plain language and ask only for the next unresolved decision if one is needed: “[request]”.

## 5. The four MiniProject criteria

A MiniProject needs a stated answer for all four criteria. These answers define the delivery boundary and give reviewers a common way to challenge it.

### Complete

Question:

> What complete improvement will be delivered?

Describe the behavior or operational result that exists when the work is finished. Do not describe only one technical layer.

Strong example:

> A locked-out customer can request a password reset, set a new password through a valid recovery link, and sign in successfully without administrator help.

Weak example:

> The password-reset backend endpoints are implemented.

The weak version may be finished code, but it does not establish that the customer can recover access.

### Demoable

Question:

> How will someone see the improvement work?

Name observable proof. A demonstration does not require a graphical interface; an operational result, report, workflow, or verified system behavior can be demoable.

Strong example:

> Start with a locked customer account, request recovery, follow the delivered reset link, choose a new password, and sign in. Also show that an expired or previously used link cannot reset the password.

Weak example:

> Inspect the API responses.

The weak version demonstrates one internal component rather than the complete improvement.

### Owned

Question:

> Who carries the improvement through implementation, verification, and release readiness?

Name one accountable owner for the end-to-end result. Contributors can lead and implement parts of the work, but accountability does not fragment by technical layer.

Strong example:

> Alice is the accountable owner through implementation, integration, verification, and release readiness. Ben contributes the API work and Chen contributes the data changes.

Weak example:

> Alice owns the UI, Ben owns the API, Chen owns data, and Dana owns testing.

The weak version divides accountability across the same handoffs the MiniProject is intended to reduce.

### Launch-ready

Question:

> What must be true for this improvement to be safe to launch?

Name the relevant verification, compatibility, security, observability, rollout, rollback, or migration conditions. Include only what matters for this improvement.

Strong example:

> Recovery and sign-in are verified end to end; reset links expire and cannot be reused; requests are rate-limited without revealing whether an account exists; recovery failures are observable; and the feature can be disabled without disrupting normal sign-in.

Weak example:

> The endpoints have tests.

Tests may contribute to readiness, but they do not cover the full set of relevant release conditions.

### Stated answers versus persuasive answers

The deterministic validator checks that all four answers are present and not blank. It also rejects an explicitly technical-layer-only boundary. It does not otherwise grade whether an answer is convincing, safe, complete enough, or appropriately sized.

This distinction matters. A proposal with answers such as “no,” “not yet,” “unknown,” and “blocked” can pass the presence check because all four fields are stated. That mechanical pass does not mean the proposal is a viable MiniProject.

Use the deterministic result to catch missing fields and known structural violations. Then use human judgment to review the quality of the answers.

When you want both, say so explicitly:

> First run the deterministic MiniProject validator and report its result. Then separately review whether each answer is persuasive enough for Tech Refinement. Keep the two judgments distinct.

## 6. Use ownership correctly

### One accountable owner

Every MiniProject has one person accountable for the complete result. That person keeps the path connected across behavior, implementation, integration, verification, and release readiness.

The accountable owner does not need to personally perform every task. Ownership means ensuring the complete result is delivered, not being the sole contributor.

### Multiple contributors

Contributors can work in parallel. A specialist may lead the API implementation, data migration, UI work, security review, test automation, or rollout preparation.

Use language such as:

- “Ben leads the API implementation as a contributor.”
- “Chen implements the migration task in Alice's delivery plan.”
- “Dana performs the security review.”

Reserve “accountable owner of the MiniProject” for the one person carrying the end-to-end result.

### Small changes remain encouraged

One MiniProject does not mean one giant branch or pull request. The owner may organize several small changes, reviews, feature flags, or deployments. Keep implementation mechanics in the owner's plan while the board tracks the complete improvement.

### Do not invent an owner

If a request does not name the person responsible for the next step, the agent should ask who owns it. It should not select a name from context or assign the person asking the question.

Paste-ready answer when ownership is unknown:

> The work is not ready to proceed as an owned MiniProject. Who is the one accountable owner through implementation, verification, and release readiness?

## 7. Run the end-to-end planning workflow

The model uses one decision question at each stage. The answer should change the work; if it does not, the question does not belong at that stage.

### Product prioritization

Decision:

> Which Projects matter enough to shape now?

Output:

> An ordered set of product or business goals.

Do not turn broad goals into detailed implementation cards during prioritization.

### Product Refinement

Decision:

> Which Discovery questions must be answered inside each Project?

Output:

> Ranked, owned, time-boxed Discovery cards with useful decision artifacts.

State explicit v1 scope before creating the cards. Discovery should reduce uncertainty that matters to sequencing or delivery boundaries.

### Tech Refinement

Decision:

> Given what Discovery established, what complete MiniProjects and Chores make up the Project?

Output:

> Named MiniProjects, Chores, and any work returned to More Discovery.

Every incoming card must resolve exactly once. Do not leave unclassified cards or create duplicate resolutions for the same card.

### Tech Estimation

Decision:

> What effort belongs to each Chore and complete MiniProject?

Output:

> Delivery estimates for Chores and MiniProjects; time boxes and target outputs for Discovery.

Do not estimate technical-layer fragments independently and present their sum as the MiniProject estimate.

### Sprint selection

Decision:

> Which ready work best serves the current business priority?

Output:

> Selected Chores, Discovery items, and MiniProjects.

Do not change a work type merely to make it fit the sprint. If a MiniProject is too large or uncertain, split it by complete improvement or return the unresolved question to Discovery.

## 8. Route a new request

Request routing is the fastest way to start when the work type is not already known.

### Specific request

Example:

> Add the onsite optimization widget to the sales blog.

The router should classify a bounded request like this as a Chore and send it through the fast lane without Discovery.

Prompt:

> Use the MiniProject skill to route this request and report the deterministic result in plain language: “Add the onsite optimization widget to the sales blog.”

Expected kind of result:

> CHORE — Route this specific request through the fast lane. Discovery is not required.

### Broad request

Example:

> Improve onsite optimization.

The router should classify this as a Project and return it to shaping. A shaping owner is required.

Prompt when the owner is known:

> Use the MiniProject skill to route this request with Chelsea as the shaping owner and report the deterministic result in plain language: “Improve onsite optimization.”

Expected kind of result:

> PROJECT — Send this broad request to shaping. Owner: Chelsea. Next step: define explicit in/out scope and create ranked Discovery questions.

Prompt when the owner is not known:

> Use the MiniProject skill to route this request: “Improve onsite optimization.” Do not invent an owner; ask only for the missing decision.

The agent should ask who owns shaping rather than returning silence or choosing a person.

## 9. Validate a proposed MiniProject

### Information to provide

Give the agent:

- the MiniProject name;
- the complete answer;
- the demoable answer;
- the owned answer;
- the launch-ready answer;
- whether you want only deterministic validation or a separate quality review as well.

Prompt template:

> Use the MiniProject skill to validate this proposed MiniProject. Return the deterministic validator result in plain language. Do not assess answer quality unless I ask separately.
>
> Name: [name]
>
> Complete: [complete improvement]
>
> Demoable: [observable proof]
>
> Owned: [one accountable owner]
>
> Launch-ready: [safe-release conditions]

### What the agent does

The agent should create the structured bundle artifact, run the bundled validator with human formatting, and return its result. You normally do not need to create JSON yourself.

### If the validator reports findings

Read the criterion and finding. Common findings are:

- a required answer is missing or blank;
- the proposal is explicitly a frontend, backend, API, data, infrastructure, QA, or testing-only slice.

Revise the boundary or supply the missing answer, then rerun the validator.

### If the validator reports valid

A valid result means the mechanical checks passed. Review the answers:

- Does “complete” describe the whole useful improvement?
- Does “demoable” prove the same end-to-end result?
- Does “owned” name one accountable person rather than component owners?
- Does “launch-ready” address the actual risks of this change?
- Is the bundle small enough for one owner to carry responsibly?

If those answers are weak, refine or split the work even though the validator is green.

## 10. Split work that is too large

Split along independently useful improvement boundaries, not technical components.

### Requirements for a valid split

- Create at least two resulting MiniProjects.
- Give each a unique ID and name.
- Answer all four criteria for each result.
- Name one accountable owner for each result.
- List dependencies between sibling MiniProjects.
- Leave at least one dependency list empty so something can launch independently.

### Strong split

Source Project:

> Account recovery improvements

Result 1:

> Customer self-service account recovery: a locked-out customer resets a password and signs in without administrator help. No sibling dependency. Alice owns it.

Result 2:

> Administrator-assisted access restoration: an authorized administrator restores access for a blocked customer and initiates secure recovery. It may depend on self-service. Ben owns it.

Each result delivers a useful end-to-end outcome. The first can launch without waiting for the second.

### Weak split

- Password-reset frontend
- Recovery API
- Recovery database changes
- Recovery QA

None is independently useful to a customer or operator. Each creates a handoff and waits for siblings before producing the improvement.

### Prompt template

> Use the MiniProject skill to split “[oversized work]” into complete MiniProjects. Split by independently useful outcomes, not frontend/backend/data/testing layers. For each result, provide complete, demoable, owned, launch-ready, and sibling dependencies. Do not invent owners; ask for one if needed. Run the deterministic split validator and report its result in plain language.

### Interpret a valid split

The split validator checks structure, complete criterion answers, dependency references, and independent launchability. It does not guarantee that the chosen boundaries are the best product sequence. Review the split for usefulness, owner capacity, and sensible ordering.

## 11. Shape a broad Project

A broad goal needs explicit scope and ranked Discovery before delivery bundles can be trusted.

### Step 1: Define v1 scope

Create non-empty lists for:

- what is in scope;
- what is explicitly out of scope.

Example:

> Project: Onsite optimization v1

> In scope: sales-blog widget placement; widget performance reporting

> Out of scope: site-wide redesign; automated content generation

“Improve onsite optimization” is direction, not sufficient scope. The in/out boundary makes the next questions specific.

### Step 2: Create ranked Discovery cards

Every Discovery card needs:

- a unique ID;
- a rank;
- one question;
- one owner;
- one useful, inspectable output.

Do not define technical implementation bundles in Discovery cards.

Example:

> D-1, rank 1: Which sales-blog placements produce meaningful engagement without reducing article completion? Owner: Alice. Useful output: placement recommendation with measured tradeoffs.

> D-2, rank 2: Which widget events and report views are required for a useful v1 performance report? Owner: Ben. Useful output: agreed event and reporting contract.

### Step 3: Obtain Engineering review

Engineering records whether the plan is accepted or returns specific cards for re-scoping. Do not invent acceptance.

The Project-shaping workflow is complete only when Engineering records `accepted` and returns zero cards.

### Prompt template

> Use the MiniProject skill to shape “[broad goal]” as a Project. Help me define explicit v1 in/out scope, then create ranked Discovery cards with one question, one owner, and one useful output each. Ask only for unresolved decisions. Do not invent Engineering acceptance. When review is supplied, run the Discovery-plan validator and report the result in plain language.

## 12. Close Tech Refinement

Tech Refinement converts established knowledge into resolved work. Every incoming card ends as exactly one of:

- a named MiniProject;
- a Chore;
- More Discovery with an owner and next question.

### Inputs

Provide:

- the Project name;
- the incoming card IDs;
- relevant Discovery decisions;
- proposed classification and name for each resolved card;
- one owner for each MiniProject;
- owner and next question for More Discovery.

### What stays off the board

Do not put these in the Tech Refinement board artifact:

- pull-request sequence;
- implementation steps;
- test-plan details;
- rollout steps;
- technical subtasks.

Those belong in the accountable owner's delivery plan unless another participant needs them for a decision.

### Prompt template

> Use the MiniProject skill to close Tech Refinement for “[Project].” Resolve each incoming card exactly once as a named MiniProject, Chore, or More Discovery. Require one owner per MiniProject and an owner plus next question for More Discovery. Keep implementation, PR, test, and rollout detail off the board. Run the board validator and report its human-readable result.

### Review the result

Check that:

- every incoming card appears once;
- no card has multiple resolutions;
- MiniProjects describe complete improvements;
- each MiniProject has exactly one owner;
- Chores are genuinely specific and low variance;
- unresolved work returns to Discovery rather than receiving a confident delivery estimate.

## 13. Run Tech Estimation

Estimate according to the work type.

### Chore

Estimate normally when an estimate is useful. The work is already specific and low variance.

### MiniProject

Estimate the complete improvement, including behavior, integration, verification, and release readiness. The owner can still execute through several small technical changes.

### Discovery

Give Discovery a time box and target output. Do not give it story points, effort size, effort estimate, or delivery estimate, even alongside the time box.

The commitment is to produce a decision artifact and terminal outcome within the investment boundary, not to guarantee a delivery result.

### Project

Do not give one delivery estimate while important Discovery remains unresolved. Sequence known work, answer the load-bearing questions, then estimate the resulting MiniProjects and Chores. Communicate remaining uncertainty directly.

### Prompt template

> Use the MiniProject skill to run Tech Estimation on these items. Require effort estimates for Chores and complete MiniProjects. Require a time box and target output for Discovery, with no story points or delivery estimate. Do not estimate unresolved Projects as one delivery total. Run the deterministic board validator and report its result in plain language.

### If a Discovery item already has story points

Remove the story points. Preserve or add:

- the question;
- owner;
- time box;
- target or decision artifact.

The time box controls investment. Story points would imply a delivery forecast the work is not ready to support.

## 14. Run and close Discovery

### Start with one question

A Discovery card should answer one decision-changing question. If the card contains several independent questions, split or rank them.

### Name the artifact before starting

Examples:

- recommendation memo;
- prototype and findings;
- compatibility matrix;
- measured baseline;
- security assessment;
- customer interview synthesis;
- ranked option comparison;
- decision record.

The artifact makes the outcome inspectable. “We learned a lot” is not sufficient closure.

### End when the time box ends

Do not silently extend Discovery until certainty appears. At the end of the time box, record what was learned and choose exactly one terminal outcome.

#### Ready to shape

Use when enough is known to create a responsible Chore or MiniProject boundary.

Record:

- the answer;
- evidence or decision artifact;
- important constraints;
- recommended next work type.

#### More Discovery

Use when a remaining question still blocks responsible shaping.

Record:

- what was learned;
- the unresolved question;
- why it matters;
- the next explicit time box and output.

#### Stop

Use when the work should not continue.

Record:

- the evidence;
- the reason to stop;
- any condition that would justify revisiting the decision.

### Prompt template for closeout

> Use the MiniProject skill to close this Discovery item. Record the question, owner, time box, decision artifact, what was learned, and exactly one terminal label: Ready to shape, More Discovery, or Stop. If More Discovery is required, state the next question. Do not give the Discovery item an implementation estimate.

## 15. Select work for a sprint

Sprint selection chooses among ready work; it does not repair classification or readiness problems.

Ask:

> Which ready work best serves the current business priority?

Select from:

- Chores that are specific and ready;
- Discovery items with a question, owner, time box, and output;
- MiniProjects with complete, demoable, owned, and launch-ready answers.

Do not:

- turn a broad Project into a MiniProject to fit the sprint;
- call uncertain work a Chore because it appears small;
- split a MiniProject into technical-layer tickets to make each estimate smaller;
- omit release-readiness work from the estimate;
- keep Discovery open without a new question and time box.

If a valuable item is not ready, state the missing decision and send it to the appropriate workflow rather than selecting it under a misleading label.

## 16. Understand validator results

The bundled scripts provide stable mechanical checks. The agent should normally return their human-readable output.

### Valid

`VALID` means the input passed the script's defined rules. It does not mean every judgment about usefulness, risk, priority, or answer quality has been settled.

Next action:

- review the human-quality questions appropriate to the workflow;
- record any remaining assumptions;
- proceed to the next planning stage only if the work is genuinely ready.

### Findings

A finding means the artifact violates a defined rule, such as a missing criterion, technical-layer-only bundle, missing owner, duplicate resolution, invalid Discovery estimate, unresolved dependency, missing scope, or pending Engineering review.

Next action:

- revise the named field or boundary;
- do not explain away the finding in prose;
- rerun the same validator;
- repeat until it exits successfully or the work is routed elsewhere.

### Invalid input

Invalid input means the artifact itself cannot be interpreted according to the expected structure. Examples include malformed JSON, an unknown work type, wrong field types, or a missing top-level section.

Next action:

- correct the artifact structure;
- rerun the validator;
- do not treat the result as a product finding.

### Deterministic-only request

If you ask for “only the deterministic validator result,” the agent should return that result without adding an answer-quality assessment.

Use this when you need a repeatable mechanical gate or are testing the validator itself.

### Human review request

If you want judgment after validation, request it separately. A useful structure is:

1. deterministic result;
2. quality assessment by criterion;
3. first unresolved decision;
4. recommended route.

Keeping these separate prevents a mechanical pass from being mistaken for approval and prevents subjective concerns from being presented as validator findings.

## 17. Keep the board useful

The board should show what the work is, why it is ready, who owns the outcome, and where uncertainty remains. It should not duplicate the owner's implementation plan.

### Put on the board

- work type;
- clear name;
- Project or parent context;
- complete, demoable, owned, launch-ready answers for MiniProjects;
- question, owner, time box, output, and terminal result for Discovery;
- effort estimate for Chores and MiniProjects;
- dependencies that affect sequencing;
- current planning status.

### Keep in the owner's plan

- branch and pull-request sequence;
- technical subtasks;
- detailed test cases;
- code ownership mechanics;
- rollout commands;
- internal coordination notes;
- low-level implementation decisions.

Move a detail onto the board only when another participant needs it to make a planning or release decision.

### Preserve complete ownership with parallel delivery

The board names one MiniProject owner. The owner's plan may show several contributors and small changes. This keeps accountability clear without sacrificing parallel work or reviewability.

## 18. Common mistakes and corrections

### Mistake: calling a technical layer a MiniProject

Example:

> Backend API changes for widget reporting

Correction:

> Define the complete reporting behavior a user or operator receives. Keep API work inside that MiniProject's implementation plan.

### Mistake: making every request go through Discovery

Correction:

> Route specific, low-variance work to the Chore fast lane. Discovery exists for meaningful uncertainty, not ceremony.

### Mistake: calling every feature request a MiniProject

Correction:

> Classify based on clarity and scope. A broad feature goal may be a Project; an unresolved question may be Discovery; a small specific change may be a Chore.

### Mistake: splitting by frontend, backend, data, and QA

Correction:

> Split by independently useful improvements. At least one result should be launchable without waiting for every sibling.

### Mistake: assigning component owners

Correction:

> Name one accountable end-to-end owner. Name specialists as contributors who lead or implement technical work.

### Mistake: treating launch-ready as already launched

Correction:

> Launch-ready means safe to release, even if release is intentionally held. A business or operational decision may still control the launch date.

### Mistake: treating “has tests” as complete launch readiness

Correction:

> Add the specific verification, observability, compatibility, rollout, rollback, migration, or security conditions relevant to the improvement.

### Mistake: estimating Discovery with story points

Correction:

> Give it a time box and target decision artifact. Do not add a delivery estimate beside the time box.

### Mistake: leaving Discovery open when time expires

Correction:

> Record the evidence and choose Ready to shape, More Discovery, or Stop. If more work is needed, state the next question and create a new time box.

### Mistake: putting implementation sequence on the planning board

Correction:

> Keep PRs, tests, and rollout steps in the owner's plan unless another participant needs them for a decision.

### Mistake: treating a mechanical pass as approval

Correction:

> Review whether the answers are persuasive and the scope is responsible. The validator checks defined structure, not overall product judgment.

### Mistake: inventing Engineering acceptance

Correction:

> Leave review pending and ask Engineering to record its decision. The agent should not approve on Engineering's behalf.

### Mistake: changing classification to fit a sprint

Correction:

> Preserve the correct work type. Resolve uncertainty, split by complete outcome, or select different ready work.

## 19. A complete worked example

This example follows a broad goal from intake through ready delivery work.

### Initial request

> Improve account recovery.

### Classification

This is a Project. It contains several possible improvements and unresolved sequencing decisions.

### Project scope

In scope:

- customer self-service password recovery;
- administrator-assisted restoration for blocked accounts;
- recovery notifications and auditability.

Out of scope for v1:

- passwordless authentication;
- replacing the identity provider;
- redesigning all sign-in screens.

### Ranked Discovery

#### D-1: Self-service security constraints

Question:

> What reset-link expiration, reuse, rate-limiting, and account-enumeration controls are required for v1?

Owner:

> Alice

Time box:

> Two days

Useful output:

> Approved recovery security contract

#### D-2: Blocked-account restoration

Question:

> Which blocked-account states may an administrator restore, and what authorization and audit evidence are required?

Owner:

> Ben

Time box:

> Two days

Useful output:

> State-transition and authorization decision record

### Discovery closeout

D-1 outcome:

> Ready to shape. The security contract defines one-hour expiry, one-time use, rate limiting, generic request responses, and observable failures.

D-2 outcome:

> Ready to shape. The decision record identifies eligible states, administrator role requirements, immutable audit fields, and notification rules.

### Tech Refinement results

#### MiniProject 1: Customer self-service account recovery

Complete:

> A locked-out customer requests a password reset, sets a new password through a valid recovery link, and signs in without administrator help.

Demoable:

> Recover a locked customer account end to end and show that expired or previously used links cannot reset the password.

Owned:

> Alice is accountable through implementation, integration, verification, and release readiness.

Launch-ready:

> Recovery and sign-in are verified end to end; links expire and cannot be reused; requests are rate-limited without account disclosure; success and failure are observable; and recovery can be disabled without breaking normal sign-in.

Dependencies:

> None

#### MiniProject 2: Administrator-assisted account restoration

Complete:

> An authorized administrator restores access for a blocked customer and initiates a secure path that lets the customer sign in again.

Demoable:

> Block an account, restore it as an authorized administrator, complete recovery as the customer, and show that an unauthorized user cannot restore access.

Owned:

> Ben is accountable through implementation, integration, verification, and release readiness.

Launch-ready:

> Authorization and state transitions are verified; every restoration is audit-logged; the customer is notified without exposing credentials; success and failure are observable; and the capability can be disabled while preserving the audit trail.

Dependencies:

> May depend on customer self-service account recovery

### Why the split works

Each result is a complete improvement with its own demonstration, owner, and safe-release conditions. The self-service result can launch independently. The split is not frontend/backend/data; those implementation steps remain inside Alice's and Ben's delivery plans.

### Tech Estimation

Estimate each complete MiniProject. Do not create separate board estimates for API, UI, database, tests, and rollout. Those details inform the owner's estimate for the full improvement.

### Sprint selection

If self-service is ready and best serves the current priority, select it. Administrator assistance can remain sequenced behind it. Do not pull only the recovery API into the sprint and call that the MiniProject.

## 20. Prompt library

These prompts are starting points. Replace bracketed text with your situation.

### Classify and route

> Use the MiniProject skill to classify and route this request: “[request].” Return the deterministic human-readable route. If a required owner or decision is missing, ask only for that missing information.

### Validate one MiniProject mechanically

> Use the MiniProject skill to validate this proposal and report only the deterministic validator result in plain language. Do not assess answer quality.
>
> Name: [name]
>
> Complete: [answer]
>
> Demoable: [answer]
>
> Owned: [answer]
>
> Launch-ready: [answer]

### Validate and then review quality

> Use the MiniProject skill to validate this proposal. First report the deterministic result. Then separately assess whether each answer is persuasive, identify the first unresolved criterion, and ask only the question needed to resolve it.

### Split oversized work

> Use the MiniProject skill to split “[source work]” into complete, independently useful MiniProjects. Do not split by technical layer. Give each result complete, demoable, owned, launch-ready, and sibling dependencies. Ensure at least one result can launch without a sibling. Run the split validator and report its result in plain language.

### Shape a Project

> Use the MiniProject skill to shape “[broad goal].” Establish explicit v1 in/out scope, then create ranked Discovery cards with one question, owner, time box, and useful decision artifact each. Do not invent Engineering acceptance.

### Close Tech Refinement

> Use the MiniProject skill to close Tech Refinement for “[Project].” Resolve every incoming card exactly once as a named MiniProject, Chore, or More Discovery. Require one owner per MiniProject. Keep implementation details off the board. Validate the board and return the human-readable result.

### Run Tech Estimation

> Use the MiniProject skill to run Tech Estimation. Give Chores and complete MiniProjects effort estimates. Give Discovery a time box and target output with no story points or delivery estimate. Validate the board and return the human-readable result.

### Close Discovery

> Use the MiniProject skill to close this Discovery item. Produce a paste-ready decision record with the question, owner, time box, artifact, what was learned, and exactly one outcome: Ready to shape, More Discovery, or Stop. If more Discovery is required, state the next question.

### Review ownership under parallel staffing

> Use the MiniProject skill to define ownership for this MiniProject. Name exactly one accountable end-to-end owner and describe how the specialists contribute in parallel without owning technical-layer slices: [people and specialties].

### Prepare sprint selection

> Use the MiniProject skill to review these candidate items for sprint selection. Preserve each correct work type. Identify which are ready, what decision blocks each unready item, and which ready work best serves [business priority].

## 21. Frequently asked questions

### Does every feature need to be a MiniProject?

No. A broad feature goal can be a Project, an unresolved question can be Discovery, and a small specific change can be a Chore. Classification follows the nature of the work, not the requester's label.

### Can a MiniProject include frontend, backend, data, and infrastructure work?

Yes. A complete improvement often crosses several components. Those are implementation concerns inside one end-to-end boundary.

### Can several people work on one MiniProject?

Yes. One person remains accountable for the result; other people contribute, lead specialist work, and review changes.

### Does one owner mean one pull request?

No. The owner can coordinate multiple small, reviewable changes and deployments.

### Does demoable mean there must be a UI?

No. An API capability, operational workflow, migration result, report, alert, or performance improvement can be demoable when its useful outcome is observable end to end.

### Does launch-ready mean launched?

No. It means the improvement is safe to release. Release may be intentionally held for a business, operational, or sequencing decision.

### Can a validator decide whether the scope is too large?

Not by itself. The validator checks stated fields and defined structural rules. Use owner capacity, delivery risk, demo coherence, and independent usefulness to decide whether to split.

### Why can “no,” “unknown,” or “blocked” pass bundle validation?

The single-bundle validator intentionally checks whether all four answers are stated rather than grading most answer content. It can reject an explicit technical-layer-only boundary, but a presence pass is not a human approval.

### What if we do not know the owner yet?

The agent should ask for the owner. Do not move the work into delivery as an unowned MiniProject.

### What if Engineering has not reviewed a Discovery plan?

Leave review pending. The Project-shaping workflow is incomplete until Engineering records acceptance with no returned cards.

### What if Discovery ends without a full answer?

Record what was learned and choose More Discovery with the next question, or Stop with the reason. Do not label it complete without a terminal decision artifact.

### Can Discovery have an estimate and a time box?

Use only the time box as the investment limit. Do not add story points, effort size, or delivery estimate.

### How should bugs be classified?

A small, known, low-variance correction can be a Chore. A bug requiring investigation begins as Discovery. A clear end-to-end behavior restoration with meaningful coordination or release risk can be a MiniProject.

### How should a specific customer request be classified?

Classify the work itself. A specific, bounded, low-variance request can use the Chore fast lane. A broad request or one with unresolved product questions needs shaping or Discovery.

### What if every split result depends on another result?

Reconsider the boundaries or sequencing. A valid split requires at least one independently launchable piece. If nothing has independent value, the proposed split may only be a technical decomposition of one MiniProject.

### Should test and rollout work appear on the board?

Their relevant outcomes belong in the MiniProject's launch-ready answer and estimate. Detailed test cases and rollout mechanics usually belong in the owner's plan.

### Should the agent answer refinement questions for us?

No. The agent can expose the unresolved decision, structure information, and validate artifacts. It should not invent priorities, owners, acceptance, or product choices that participants must supply.

## 22. Working checklist

### New request

- [ ] Classify before estimating or splitting.
- [ ] Use the Chore fast lane for specific, low-variance work.
- [ ] Use Discovery when a question blocks responsible shaping.
- [ ] Use MiniProject only when one complete improvement is clear.
- [ ] Use Project for broad goals, multiple improvements, or unresolved sequencing.

### Discovery

- [ ] State one decision-changing question.
- [ ] Name one owner.
- [ ] Set a time box.
- [ ] Name the useful decision artifact.
- [ ] Close with Ready to shape, More Discovery, or Stop.
- [ ] Do not add story points or a delivery estimate.

### MiniProject

- [ ] Complete describes the whole improvement, not a technical layer.
- [ ] Demoable proves the same end-to-end outcome.
- [ ] Owned names one accountable person.
- [ ] Launch-ready addresses the relevant release conditions.
- [ ] Contributors are not assigned technical-slice accountability.
- [ ] The deterministic validator has run successfully.
- [ ] Human review has considered answer quality and scope.

### Split

- [ ] Every result is independently useful rather than a component.
- [ ] Every result answers all four criteria.
- [ ] Every result names one owner.
- [ ] Dependencies refer to valid sibling IDs.
- [ ] At least one result has no sibling dependency.
- [ ] The deterministic split validator has run successfully.

### Tech Refinement

- [ ] Every incoming card resolves exactly once.
- [ ] Every resolution is a MiniProject, Chore, or More Discovery.
- [ ] Every MiniProject has one owner.
- [ ] More Discovery states an owner and next question.
- [ ] Implementation detail remains in owner plans.

### Tech Estimation

- [ ] Every Chore and MiniProject has an effort estimate when needed.
- [ ] Every Discovery item has a time box and target output.
- [ ] No Discovery item has story points or delivery estimates.
- [ ] No unresolved Project has a false-precision delivery total.

### Sprint selection

- [ ] Select work that is ready and serves the priority.
- [ ] Preserve the correct work type.
- [ ] Return unready work to its missing decision.
- [ ] Do not split by technical layer merely to fit the sprint.

## Related documents

- [MiniProject operating model](miniproject-model.md) provides the formal model and rationale.
- [Developer testing guide](developer-testing-guide.md) explains how maintainers test the skill and behavioral harness.
- [Hardening and behavioral testing report](hardening-and-behavioral-testing-report.md) records the current evidence and limitations.
