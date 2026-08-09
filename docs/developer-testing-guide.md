# Developer Guide to Testing the MiniProject Skill

**Version 1.0 — 2026-08-09**

This guide explains how testing works in this repository, why the test harness is designed the way it is, how to run each kind of test safely, how to read the results, and what to do when a test finds a problem. It starts with the basic concepts. No prior experience with language-model evaluation is required.

## Contents

1. [What is being tested](#1-what-is-being-tested)
2. [Why ordinary tests are necessary but not sufficient](#2-why-ordinary-tests-are-necessary-but-not-sufficient)
3. [Essential vocabulary](#3-essential-vocabulary)
4. [The testing layers](#4-the-testing-layers)
5. [How the behavioral harness works](#5-how-the-behavioral-harness-works)
6. [Harness design decisions and rationale](#6-harness-design-decisions-and-rationale)
7. [Strengths and weaknesses of the methodology](#7-strengths-and-weaknesses-of-the-methodology)
8. [Set up a development environment](#8-set-up-a-development-environment)
9. [Run the free deterministic tests](#9-run-the-free-deterministic-tests)
10. [Run a bounded behavioral test](#10-run-a-bounded-behavioral-test)
11. [Run and interpret negative controls](#11-run-and-interpret-negative-controls)
12. [Purpose and use case of each behavioral contract](#12-purpose-and-use-case-of-each-behavioral-contract)
13. [Read results and exit codes](#13-read-results-and-exit-codes)
14. [Investigate a failure](#14-investigate-a-failure)
15. [Take action on findings](#15-take-action-on-findings)
16. [Add or change a deterministic test](#16-add-or-change-a-deterministic-test)
17. [Add or change a behavioral contract](#17-add-or-change-a-behavioral-contract)
18. [Plan a test run without losing cost control](#18-plan-a-test-run-without-losing-cost-control)
19. [Use manual testing alongside the harness](#19-use-manual-testing-alongside-the-harness)
20. [Release and maintenance checklist](#20-release-and-maintenance-checklist)

## 1. What is being tested

The product in this repository is an Agent Skill named `miniproject`. An Agent Skill is a package of written instructions, reference material, and scripts that an AI coding agent can load when it handles a matching request. In this case, the skill teaches an agent how to classify work as a Project, Discovery, MiniProject, or Chore and how to refine, estimate, split, validate, and route that work.

The skill has two kinds of behavior:

- **Deterministic behavior:** Python scripts read structured input and return structured or plain-language output according to fixed rules. Given the same input and code, these scripts should return the same result every time.
- **Agent behavior:** A coding agent reads the skill, understands a realistic request, decides what to do, runs the appropriate script, and presents or records the result. This behavior can vary between runs even when the prompt is identical.

Both kinds must work. A perfect validator is not useful if an agent never invokes it. A persuasive agent response is not trustworthy if the underlying validator accepts invalid data. The test strategy therefore checks the scripts and the agent behavior separately, then checks them together.

The production skill lives in:

```text
skills/miniproject/
```

The test system lives mainly in:

```text
eval/
├── contracts/              Behavioral contract definitions
├── drivers/                Codex, Junie, and Claude adapters
├── tests/                  Deterministic pytest suite
├── assertions.py           File-based result checks
├── mutate.py               Negative-control mutations
├── run_contracts.py        Behavioral test runner
└── cost.py                 Usage ledger and cost reporting
```

## 2. Why ordinary tests are necessary but not sufficient

Most application code has a useful property: the same code and input normally produce the same result. A unit test can call a function, compare the return value with an expected value, and give a stable pass or fail.

The Python validators in this repository work that way, so ordinary unit tests are the right tool for them.

The skill instructions do not have that property. They influence a model rather than directly calculating an answer. The model may follow an instruction on one run and overlook it on another. This is what “probabilistic” means in this guide: identical test setup can produce more than one possible result. A model update, command-line interface (CLI) update, system prompt change, different tool permissions, or a longer conversation can change the result without changing this repository.

That creates several risks that ordinary tests cannot see:

- The instructions can be syntactically valid but ineffective.
- The agent can describe the correct action without performing it.
- A test can pass because the model already knows a sensible rule, even if the skill instruction is missing.
- A test can pass in Codex but fail in Junie or Claude because each harness supplies different surrounding instructions and tools.
- A response-grading model can be influenced by seeing the same instructions as the subject it grades.
- A test can accidentally load the developer's globally installed skill instead of the changed copy being tested.

Behavioral tests address those risks by running real agents in isolated environments and checking what they actually produce. They complement deterministic tests; they do not replace them.

## 3. Essential vocabulary

These terms appear in the runner, contract files, result records, and this guide.

### Model

The language model is the service that interprets text and generates the next response or action. A model does not receive repository files, tools, skills, or conversation history automatically; the coding-agent application decides what context and capabilities to provide.

### Coding agent

A coding agent is the application around a model. It supplies system instructions, file and shell tools, skill discovery, permissions, session storage, and a user interface. Codex, Junie, and Claude Code are coding agents. Changing the application or its configuration can change behavior even when the underlying model stays the same.

### Skill

The package under test: `skills/miniproject/`. It contains instructions, references, and deterministic scripts.

### Subject

The agent performing the test task. Codex, Junie, and Claude are subjects when the harness asks them to use the MiniProject skill.

### Harness

The program and surrounding environment used to run a subject. A harness includes a CLI, its system instructions, tool permissions, skill-discovery rules, authentication method, and session storage. Two harnesses can use similarly capable models and still behave differently.

### Fixture

A disposable working directory prepared for the subject. It contains any starting files the task needs and receives any output files the subject creates. The repository fixture path is named in the contract and copied before every run.

### Contract

A YAML file that makes one narrow behavioral claim. It specifies the subject prompt, fixture, permitted harnesses, expected response or artifact, and the negative control that should break the behavior. Contract files are under `eval/contracts/`.

### Assertion

The check that decides whether the observed result meets the contract. An assertion can inspect a produced file or ask an isolated judge to evaluate response meaning.

### Artifact

A file produced by the subject, such as a validation result, split plan, route record, or Discovery decision. Artifact assertions are deterministic: a file either exists and matches the declared checks or it does not.

### Judge

A separate model call used only for a response assertion. The judge receives the contract criterion and the subject response. It does not receive the skill. Most current contracts avoid a judge by checking artifacts instead.

### Normal run

A behavioral run against the intact production skill. It answers: “Can the skill produce the behavior this contract requires?”

### Mutation

A deliberate edit applied to a disposable copy of the skill. Examples include deleting a rule, reversing a condition, or changing required formatter wording. The production skill is never mutated.

### Negative control

A run against the mutated skill. It answers: “Does this test fail when the rule it claims to test is broken?” A successful negative control is reported as `DETECTED` because the test detected the introduced defect.

This naming can initially feel backward: a failing assertion is the desired outcome in negative-control mode. The runner translates that expected failure into `DETECTED` so the summary is easier to read.

### Model prior

Behavior the model tends to produce without help from this skill. For example, a capable model may already consider a backend-only ticket incomplete. A test of that behavior might remain green after the relevant skill rule is deleted. The result would show that the test measures the model's prior knowledge, not the instruction.

### Detection rate

The number of repeated negative-control runs that detect the mutation. `4/5` means four mutated runs failed the contract as intended and one still passed. The current qualification floor is 4 of 5 for every contract-harness pair.

### Isolation

Keeping the subject's files, session state, skill copy, credentials, and judge context separate from the developer's normal environment and from other runs. Isolation protects user data and makes the evidence trustworthy.

### Contaminated result

A result produced under a broken test boundary, such as loading the global skill instead of the mutated copy or failing before the behavior under test could occur. A contaminated result is not evidence for or against the product behavior.

## 4. The testing layers

The repository uses several layers because each catches a different class of failure. Run the cheaper, more deterministic layers first.

| Layer | What it tests | Cost | When to use it |
| --- | --- | --: | --- |
| Static validation | Repository and skill structure, portable syntax, packaging boundaries | No model cost | Every change |
| Deterministic unit tests | Python logic, CLI output, schemas, drivers, isolation, mutations, accounting | No model cost | Every change |
| Normal behavioral contracts | Whether real agents can perform the intended workflow with the intact skill | Paid | After deterministic tests pass; before claiming cross-harness behavior |
| Repeated negative controls | Whether a contract responds when its target rule is broken | Paid, usually higher | Before trusting a new or materially changed contract |
| Manual user tests | Whether the behavior is understandable and useful in realistic interaction | Human time and possible model cost | Before release and after usability changes |
| Long-session or paraphrase tests | Whether behavior survives varied wording and competing context | Paid and potentially expensive | Targeted hardening after the core workflow works |

### Static validation

Static checks do not run an agent. The portability linter rejects skill constructs that are known to work only in one harness. Packaging tests verify that the editable Python installation includes only the intended package. The Agent Skill validator checks skill metadata and directory shape.

Use this layer to catch problems such as a harness-specific command in `SKILL.md`, an invalid skill header, a missing required file, or an accidental package-discovery expansion.

### Deterministic unit tests

These tests call Python functions and command-line entry points directly. They cover valid input, invalid input, edge cases, human-readable output, installer safety, credential loading, artifact path containment, mutation application, result classification, and driver command construction.

Use this layer whenever a rule can be expressed without asking a model. Deterministic tests are faster, cheaper, and easier to debug than behavioral tests.

### Normal behavioral contracts

Normal mode runs a real agent with the intact skill. It verifies that the entire path works: the harness discovers the skill, the agent understands the task, it invokes the correct tools, it writes the requested artifact when applicable, and the artifact or response satisfies the contract.

Use normal mode before claiming that a workflow works in Codex, Junie, or Claude. A deterministic script test alone does not establish agent use of that script.

### Repeated negative controls

Negative controls deliberately break the skill and confirm that the contract notices. Repetition is important because agent behavior varies. One detection can be luck, and one miss can be noise.

Use this layer before trusting a contract as a regression detector. If the contract cannot reliably detect a known defect, a green normal result is weak evidence.

### Manual user tests

Manual testing asks a realistic question in a fresh user-facing session and evaluates whether the result is understandable and useful. This layer caught the raw-JSON usability failure that the original artifact contract considered valid.

Use manual testing for clarity, workflow fit, confusing prompts, awkward output, and behavior that is difficult to reduce to a safe deterministic assertion.

## 5. How the behavioral harness works

The runner is `eval/run_contracts.py`. A single normal artifact run follows this sequence:

```text
Contract YAML
    │
    ├── selects a fixture, prompt, harness, model, and assertion
    │
    ▼
Create disposable work directory and disposable harness home
    │
    ├── copy the fixture into the work directory
    └── copy the production skill into the isolated skill location
    │
    ▼
Run the subject through the selected CLI
    │
    ▼
Check the produced artifact deterministically
    │
    ▼
Record verdict, details, model, CLI version, duration, session ID, and cost
```

A negative-control run inserts one step before the subject starts:

```text
Copy production skill → apply declared mutation to the copy → confirm mutation changed it → run subject
```

For the one response contract, the final assertion step is different:

```text
Subject response + narrow pass criterion → isolated judge → PASS or FAIL
```

The subject never receives the assertion details. Otherwise it could write directly to the test rather than respond naturally to the user task. The judge never receives the skill. Otherwise it could grade generously because it knows what the skill was trying to teach.

### Contract loading and validation

The runner loads every YAML file under `eval/contracts/`, validates its shape, and optionally filters by contract ID or harness. A contract must include an ID, name, subject, assertion, negative control, and at least one recognized harness.

Artifact contracts must request `workspace-write` and declare at least one file check. Response contracts must provide a pass criterion. Missing or malformed fields cause an input error rather than a silent skip.

### Artifact checking

`eval/assertions.py` supports these checks:

| Check | Meaning | Typical use |
| --- | --- | --- |
| `exists` | A regular file exists | Confirm the subject performed the requested work |
| `absent` | A path does not exist | Confirm forbidden output was not created |
| `contains` | File text matches a regular expression | Check structure, exact output, or required content |
| `min_lines` | File has at least a declared number of lines | Reject files too short to contain the required output |
| `min_bytes` | File has at least a declared size | Reject files too small to contain the required output |

Artifact paths are resolved beneath the disposable work directory. Absolute paths and paths that escape with `..` are rejected.

### Mutation application

`eval/mutate.py` supports:

| Operation | Meaning |
| --- | --- |
| `replace` | Replace exact text with deliberately broken text |
| `delete_lines_matching` | Remove every line matching a regular expression |
| `delete_file` | Remove an entire reference or script from the disposable copy |
| `truncate_after` | Remove everything after a matching line |

Every declared mutation must change the disposable skill. If even one mutation in a multi-edit negative control matches nothing, the entire result is `MUTATION-INERT`. This fail-closed behavior prevents an outdated mutation pattern from creating a false green result.

### Result recording

Completed invocations write:

```text
eval/runs/<run-id>/results.jsonl
eval/runs/<run-id>/cost.json
```

Each result row is JSONL: one complete JSON object per line. It includes the contract, harness, mode, summary verdict, reason, subject model, session identifier when available, duration, detailed artifact checks, repeated-run rate, individual repeat verdicts, and CLI version.

The entire `eval/runs/` directory is gitignored. It can contain large or sensitive subject output and should not be committed by default. Durable findings should summarize exact run IDs, environment versions, exclusions, and aggregate results in a reviewed document.

## 6. Harness design decisions and rationale

### Test the production skill, not a test-only copy

The runner copies `skills/miniproject/` into each isolated environment. A separately maintained test skill could drift from production and make the suite green against code no user receives.

### Use a fresh environment for every repetition

Session history, previous artifacts, caches, and installed skills can influence later behavior. A fresh environment makes each repetition an independent observation and prevents one run from teaching the next run what the test expects.

### Isolate both Codex `HOME` and `CODEX_HOME`

Isolating only `CODEX_HOME` was not sufficient. Codex could still discover the global skill under the process home at `~/.agents/skills/miniproject`, bypassing the mutated copy. The current driver creates a disposable process `HOME`, places `CODEX_HOME` beneath it, installs the canonical skill under the disposable `HOME/.agents/skills`, and links the Codex-specific path to the same copy.

This decision protects evidence validity and prevents test sessions from being written into the user's normal Codex directories.

### Give Junie a disposable home and disable default discovery

Junie's normal macOS Keychain authentication is tied to its usual home path. Changing `JUNIE_HOME` therefore requires an explicit API key. The driver redirects Junie home, logs, cache, extensions, and skill discovery to temporary locations and disables other default discovery paths.

This is more setup than reusing the normal home, but it prevents test sessions and logs from mixing with user data.

### Run Claude inside a disposable container

Claude receives the fixture as its only writable host mount and the skill as a read-only mount. Host Claude state is not mounted. The OAuth token is passed only into the container process environment, and session persistence is disabled.

The container boundary makes file access and skill discovery explicit and repeatable. It also means Docker and the pinned image are part of the test environment and must be available.

### Prefer artifacts over response grading

When the requested outcome is a file or deterministic script result, the harness checks that file directly. This avoids paying a judge to decide something the filesystem can answer exactly and prevents an explanation from substituting for completed work.

Response grading remains appropriate for meaning that cannot be safely reduced to a file pattern. MP-C04 uses it to distinguish one accountable owner from fragmented technical-layer accountability while still allowing specialists to contribute.

### Keep subject and judge contexts separate

A subject that sees the pass criterion can optimize its output for the test. A judge that sees the skill can infer the intended answer and excuse a weak response. Separate contexts reduce both forms of leakage.

This does not make a model judge infallible. It makes the judgment narrower and easier to audit.

### Use the weakest model capable of the task

A highly capable model often follows common-sense rules without the skill. That can make a broken instruction look effective. Phase 0 showed that a stronger model hid a mutation that a weaker model detected consistently.

The default subject is therefore `gpt-5.6-luna` for Codex and Junie. Claude artifact contracts are pinned to Sonnet because the weaker Claude subject once exited successfully without producing required artifacts. Model choice is part of contract design, not merely a cost setting.

### Make harness claims explicit

Each contract lists its supported harnesses. A passing Codex run does not imply a passing Junie or Claude run. Different CLIs provide different system prompts, skill-loading behavior, tool syntax, output formats, and permission models.

### Separate infrastructure failure from product failure

An agent that never starts, times out, loses credentials, or receives invalid CLI flags has not tested the product behavior. The runner reports these as `HARNESS-ERROR` instead of `FAIL` or `DETECTED`.

This distinction prevents infrastructure defects from triggering product decisions or kill conditions.

### Require five mutation samples and judge each cell separately

The minimum qualification unit is one contract on one harness. Four detections out of five clear the current floor. Results are not pooled across harnesses, because ten perfect detections elsewhere must not hide a broken Codex cell.

Five is a pragmatic screening sample, not a statistically precise reliability estimate. It detects obvious flakiness at manageable cost.

### Record versions, raw rates, and costs

A future failure may be caused by a skill change, model change, or CLI change. Recording the model and harness version makes comparison possible. Recording `4/5` instead of only `DETECTED` preserves the difference between a fragile cell and a perfect sample.

### Direct deterministic human output into artifacts

Contracts MP-C09 through MP-C14 require the agent to redirect a bundled script's human-formatted standard output directly into a report file. They forbid reconstruction or editing. The artifact assertion anchors the entire file.

This proves that the production formatter emitted the text. It does not merely prove that the agent could imitate the expected sentence.

### Enforce a metered budget before subject calls

The runner can total metered calls since a shared timestamp and stop before starting another subject when current spend plus a reserve would exceed a cap. This reduces the risk of an accidental full-matrix run consuming an open-ended amount.

The guard is deliberately described as a reserve check, not an absolute billing guarantee. A single call can cost more than the reserve. Junie text mode exposes no usage, so Junie calls are outside the metered cap and must be bounded by the number of selected contracts, harnesses, and repetitions.

Response-judge calls occur after their subject run and are not guarded as a separate “next subject” check. Include judge headroom when the selected contract uses `assert.type: response`.

## 7. Strengths and weaknesses of the methodology

### Strengths

#### It tests real behavior through real harnesses

The subject uses the actual CLI, skill-discovery mechanism, tools, permissions, and model. This catches integration failures that unit tests cannot see.

#### Negative controls test whether a contract is meaningful

A normal green result shows success once. A negative control shows whether the assertion responds when the target rule is broken. This exposes tests that measure model common sense instead of skill influence.

#### Artifact assertions reduce ambiguity

File existence and content can be checked without another model. Artifact checks are cheaper, more reproducible, and better aligned with tasks where something must actually happen.

#### Isolation protects both users and evidence

Disposable homes prevent test sessions, skills, caches, and logs from mixing with user-owned state. They also ensure a mutation cannot be bypassed through a global installation.

#### Cross-harness results prevent accidental portability claims

A contract passes only where it has actually run. The matrix shows whether behavior survives different agent environments.

#### Failure categories point toward different owners and actions

`FAIL`, `BROKEN`, `MUTATION-INERT`, `HARNESS-ERROR`, and `BUDGET-STOP` describe different problems. Treating them separately shortens diagnosis and prevents a harness failure from being misreported as a product regression.

#### Cost and version records make testing auditable

The ledger and run metadata make it possible to explain what was run, under which model and CLI version, and at what known metered cost.

### Weaknesses and limits

#### Five samples do not establish a precise reliability percentage

A 5-of-5 sample does not prove 100% reliability, and 4-of-5 does not prove exactly 80%. The sample is a qualification screen. Treat results near the floor as fragile and rerun when the model, CLI, prompt, or skill changes materially.

#### Contracts cover written examples, not every possible request

A skill can pass the exact contract prompts and fail on a paraphrase or an unexpected workflow. Add prompt variants when real use exposes a meaningful class of wording, but avoid creating many superficial variations that all test the same path.

#### Short isolated runs do not represent long working sessions

In a long session, the skill competes with repository instructions, conversation history, user corrections, and tool output. The current suite does not measure that attention competition.

#### Exact text assertions can be brittle

Exact output tests are appropriate when the script's wording is a product contract. They are inappropriate for prose where many answers are equally useful. A harmless punctuation change will fail an exact text contract and require an intentional decision about compatibility.

#### Regular-expression artifact checks can be shallow

A file can contain the expected words and still be wrong in another way. Prefer structured schema checks when correctness depends on relationships, types, or multiple fields. Keep each regular expression tied to a narrow claim.

#### A response judge introduces another probabilistic component

The judge can misread a response or vary over time. Keep judge criteria narrow, preserve the subject output and reason when diagnosing, and use deterministic artifacts whenever possible.

#### The weakest capable model may fail for capability reasons

A weak subject is sensitive to instruction changes, but it may also be unable to complete a complex task. If normal runs fail even with intact instructions, use a more capable model for that contract and record the override. Do not lower the assertion merely to accommodate an incapable subject.

#### Cross-harness runs are expensive and slow

Fourteen contracts across three harnesses and five mutation repetitions require 210 subject runs before any response judges. Develop one contract and one harness at a time, then expand only after the bounded slice works.

#### Junie cost is unknown in text mode

The runner records Junie calls as unpriced rather than zero. A dollar cap cannot control unknown Junie cost. Scope Junie runs by call count and report the count separately.

#### The reserve is not a hard invoice ceiling

The budget check reserves a configured estimate before the next subject call. A call that costs more than the reserve can cross the requested ceiling. Leave meaningful headroom and start with one contract.

#### A budget stop currently ends before writing the invocation's result files

The runner writes `results.jsonl` after all selected cells finish. If it returns exit 4 partway through, earlier cells from that invocation may have printed to the terminal but are not persisted as a completed run directory. Treat the invocation as incomplete and rerun a narrower selection; do not reconstruct a formal result from partial console output.

#### Raw run data is local and gitignored

This protects the repository from sensitive or bulky model traces, but remote reviewers cannot inspect raw evidence from Git alone. A durable finding must record the exact run IDs, versions, exclusions, and aggregate results. Where long-term raw retention is required, use an approved evidence store rather than committing session traces casually.

#### A test suite can become the target instead of the product

Repeatedly tuning the skill against visible contracts can overfit it to those examples. Future automated improvement work requires held-out contracts that the improvement process cannot read. Until then, use fresh manual tasks as an independent check.

## 8. Set up a development environment

Run all commands from the repository root.

### Install Python dependencies

Python 3.11 or newer is required.

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
```

The virtual environment is local and gitignored.

### Install the harness CLIs you intend to test

You only need a harness CLI when running that harness.

- Codex requires the `codex` CLI and an existing `~/.codex/auth.json` login.
- Junie requires the `junie` CLI and `JUNIE_API_KEY` for isolated runs.
- Claude requires Docker and the repository's Claude test image.

Build the pinned Claude image if it is not already present:

```sh
docker build -t hum-miniproj-claude-test:2.1.226 -f eval/docker/claude.Dockerfile .
```

### Store local behavioral-test credentials

Create `.env.local` in the repository root:

```dotenv
JUNIE_API_KEY=replace-with-your-key
CLAUDE_CODE_OAUTH_TOKEN=replace-with-your-token
```

Restrict the file so only your user account can read it:

```sh
chmod 600 .env.local
```

The loader reads only the requested key. It does not source the file as shell code, interpolate variables, or overwrite an already exported value. `.env.local` is gitignored. Never add it to a commit, paste its values into logs, or place credentials in a contract prompt.

Codex authentication is not copied. The disposable Codex home receives a symlink to the existing `auth.json`.

### Confirm the clean baseline

Before editing, record the branch and working-tree state:

```sh
git status --short --branch
```

Do not discard or stage files you did not create. Test runs use disposable directories, but normal repository edits still share the worktree.

## 9. Run the free deterministic tests

Always start here. The explicit marker exclusion matters: some integration tests launch real Codex subjects and cost money.

```sh
python3 -m pytest -q -m 'not integration'
```

Expected success looks like a count of passed tests plus four deselected integration tests. The exact pass count can increase as tests are added.

Run portability lint separately:

```sh
python3 scripts/lint_portable.py
```

CI runs both commands on pull requests and pushes to `main`.

### Run one deterministic test file while developing

Choose the file closest to the changed behavior:

```sh
python3 -m pytest -q eval/tests/test_validate_bundle.py
python3 -m pytest -q eval/tests/test_contract_runner.py
python3 -m pytest -q eval/tests/test_codex_driver.py
```

Use a focused test during the red-green cycle, then run the entire non-integration suite before committing.

### Purpose of the deterministic test groups

| Test group | Purpose | Run it when changing |
| --- | --- | --- |
| `test_validate_bundle.py` | Bundle presence rules, technical-layer rejection, Chore bypass, JSON and human output | `validate_bundle.py` or bundle rules |
| `test_validate_split.py` | Complete-improvement splits and independent launchability | `validate_split.py` or split workflow |
| `test_validate_board.py` | Refinement resolution, owner count, delivery estimates, Discovery time boxes | `validate_board.py`, refinement, or estimation rules |
| `test_validate_discovery_plan.py` | Scope quality, ranked owned Discovery cards, Engineering acceptance | Discovery shaping or its validator |
| `test_route_request.py` | Chore fast lane and broad-request shaping return | Request routing |
| `test_skill_package.py` | Skill references, activation description, canonical labels, owner language | `SKILL.md` or reference documents |
| `test_user_story_coverage.py` | Every product story has implementation files and executable acceptance coverage | User stories or coverage ledger |
| `test_install.py` | Safe, idempotent cross-harness installation and uninstall | `install.sh` or installed layout |
| `test_assertions.py` | Artifact checks and path containment | Assertion types |
| `test_mutate.py` | Mutation operations and repeated-result classification | Negative-control engine |
| `test_contract_runner.py` | Contract schema, selection, coverage, result writing, model overrides, budget, isolation | Contracts or runner |
| `test_codex_driver.py` | Codex command construction, session behavior, usage parsing, HOME isolation | Codex driver or CLI version |
| `test_junie_driver.py` | Junie discovery isolation, result parsing, required key, session behavior | Junie driver or CLI version |
| `test_claude_driver.py` | Container mounts, token boundary, output and usage parsing | Claude driver or image |
| `test_judge.py` | Judge isolation, strict verdict schema, prompt contents | Response grading |
| `test_cost.py` | Usage parsing, pricing, unpriced calls, run scoping | Cost ledger or models |
| `test_env.py` | Non-executing `.env.local` loading and file permissions | Credential loading |
| `test_lint_portable.py` | Portable skill subset and CI configuration | Skill syntax or CI |
| `test_packaging.py` | Python package discovery boundary | Packaging configuration |

### Interpret a deterministic failure

A deterministic failure is reproducible until code or input changes. Read the first failing assertion and traceback. Run that test alone with more output:

```sh
python3 -m pytest -vv eval/tests/test_validate_bundle.py::test_name_here
```

Then decide which of these is true:

- The implementation violates an intended rule: fix the implementation.
- The intended rule changed: update the implementation, test, documentation, and behavioral contract together.
- The test encoded an assumption that was never part of the rule: narrow or replace the test and document why.
- The failure is environmental: repair the environment and avoid changing product assertions to accommodate it.

## 10. Run a bounded behavioral test

Behavioral tests call paid models. Start with one contract on one harness. Do not begin with the full matrix.

### Set a shared phase timestamp

The timestamp lets multiple commands share one metered budget window:

```sh
phase_start="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

Keep the same shell and variable for the related commands.

### Run one normal contract on Codex

```sh
python3 -m eval.run_contracts \
  --contract MP-C09 \
  --harness codex \
  --max-metered-cost 1.00 \
  --budget-since "$phase_start" \
  --budget-reserve 0.25
```

This is a preflight, not cross-harness qualification. It confirms that the contract loads, Codex starts, the subject can perform the task, and the assertion passes.

### Run the same normal contract across all claimed harnesses

Omit `--harness` after the bounded preflight succeeds:

```sh
python3 -m eval.run_contracts \
  --contract MP-C09 \
  --max-metered-cost 2.50 \
  --budget-since "$phase_start" \
  --budget-reserve 0.25
```

The runner probes required CLIs and credentials before launching subjects. If any selected harness cannot be probed, the invocation stops without scoring behavior.

### Select more than one harness explicitly

Repeat the flag:

```sh
python3 -m eval.run_contracts \
  --contract MP-C09 \
  --harness codex \
  --harness claude \
  --max-metered-cost 2.00 \
  --budget-since "$phase_start"
```

### Keep a failed subject workspace for diagnosis

By default, disposable workspaces are deleted. Use this option only when you need to inspect a failure:

```sh
python3 -m eval.run_contracts \
  --contract MP-C09 \
  --harness codex \
  --keep-workdirs \
  --max-metered-cost 1.00 \
  --budget-since "$phase_start"
```

The runner prints the exact retained path. Inspect only that path. It may contain subject output and event streams, so do not commit it. Remove that exact directory after diagnosis; never sweep a parent sessions, skills, or temporary directory.

## 11. Run and interpret negative controls

Do not trust a new behavioral contract merely because normal mode passes. Confirm that the contract fails when its target rule is deliberately broken.

### Develop with one mutation sample

One sample is useful for fast feedback while authoring:

```sh
python3 -m eval.run_contracts \
  --contract MP-C09 \
  --harness codex \
  --negative-control \
  --repeat 1 \
  --max-metered-cost 1.00 \
  --budget-since "$phase_start"
```

The runner warns that fewer than five repetitions do not establish a detection rate.

### Qualify one contract-harness cell

```sh
python3 -m eval.run_contracts \
  --contract MP-C09 \
  --harness codex \
  --negative-control \
  --repeat 5 \
  --max-metered-cost 2.50 \
  --budget-since "$phase_start" \
  --budget-reserve 0.25
```

Interpret the rate directly:

- `5/5 DETECTED`: the sample has margin above the floor.
- `4/5 DETECTED`: the cell qualifies, but it is fragile and should be called out.
- `3/5 BROKEN` or lower: the contract is not qualified.

Do not average a weak cell with strong cells. Qualification is per contract and harness.

### Expand to every claimed harness

After one harness works, omit `--harness` and choose a budget based on the expected Codex and Claude cost plus a separate Junie call count. A single contract across three harnesses at five repetitions means 15 subject runs.

### What a broken negative control means

`BROKEN` does not automatically mean the product behavior is wrong. It means the contract still passes when its declared target is broken often enough to miss the floor. Common causes are:

- The model follows the rule from its own prior knowledge.
- The mutation does not remove enough of the relevant instruction.
- The assertion is broader than the rule and accepts unrelated good behavior.
- The subject never uses the mutated file or code path.
- The prompt reveals the desired answer so clearly that the skill is unnecessary.
- The chosen model is too strong to reveal instruction influence.

The normal response can still look excellent. The correct action is to redesign the contract or mutation, not to declare the green normal run trustworthy.

## 12. Purpose and use case of each behavioral contract

Every current contract claims Codex, Junie, and Claude. The table describes what each contract is intended to protect and when it is most useful.

| Contract | Purpose | Assertion | Use it when changing | What its mutation probes |
| --- | --- | --- | --- | --- |
| MP-C01 | Ensure inconclusive Discovery closes with a paste-ready `More Discovery` decision, learned fact, and next question | Artifact | Discovery terminal labels, closeout instructions, decision records | Whether the skill still requires the decision artifact and canonical terminal outcome |
| MP-C02 | Ensure bundle validation checks that all four answers are stated without pretending to grade answer quality | Artifact | Bundle validator presence semantics or installer parity | Whether the validator rejects answers such as “no” or “blocked” even though presence-only validation should accept them mechanically |
| MP-C03 | Ensure a fully answered backend-only bundle is rejected as a technical-layer slice | Artifact | Technical-layer detection or complete-improvement rules | Whether disabling the technical-layer condition lets the invalid bundle pass |
| MP-C04 | Preserve one accountable end-to-end owner while allowing specialists to lead and implement in parallel | Response judge | Ownership language, contributor guidance, schedule-pressure behavior | Whether fragmented technical-layer accountability becomes acceptable |
| MP-C05 | Ensure oversized work splits into complete MiniProjects with at least one independently launchable piece | Artifact | Split schema, dependencies, completeness, ownership | Whether reversing independent-launchability logic breaks a valid split |
| MP-C06 | Ensure Tech Refinement resolves every card and Tech Estimation measures delivery work while time-boxing Discovery | Artifact | Board workflow, owner count, estimate keys, Discovery policy | Whether forcing Discovery estimate rejection breaks a valid mixed board |
| MP-C07 | Ensure a broad Project becomes explicit scope plus ranked, owned Discovery cards accepted by Engineering | Artifact | Discovery-plan schema, scope, ranking, ownership, acceptance | Whether a valid accepted plan is rejected by the mutated review condition |
| MP-C08 | Ensure specific requests use the Chore fast lane and broad requests return to shaping with an owner | Artifact | Request specificity or routing | Whether disabling the specific-request branch misroutes the concrete request |
| MP-C09 | Ensure bundle validation is presented as the exact human-readable deterministic result | Artifact with full-file match | Bundle formatter wording or skill reporting instruction | Whether changed formatter wording is detected instead of being reconstructed by the agent |
| MP-C10 | Ensure split validation reports count and independently launchable bundle IDs in plain language | Artifact with full-file match | Split formatter wording or reporting instruction | Whether replacing the informative formatter with a generic success sentence is detected |
| MP-C11 | Ensure Tech Refinement reports the resolved-card count in plain language | Artifact with full-file match | Refinement formatter wording or reporting instruction | Whether replacing the detailed refinement result with a generic success sentence is detected |
| MP-C12 | Ensure Tech Estimation reports compliance with measurement rules in plain language | Artifact with full-file match | Estimation formatter wording or reporting instruction | Whether replacing the detailed estimation result with a generic success sentence is detected |
| MP-C13 | Ensure Discovery-plan validation reports scope, ranked-card count, and Engineering acceptance in plain language | Artifact with full-file match | Discovery formatter wording or reporting instruction | Whether removing the informative opening is detected |
| MP-C14 | Ensure specific and broad request routes are reported in exact plain language | Artifact with full-file match | Router formatter wording or reporting instruction | Whether shortening the Chore result so it loses the fast-lane explanation is detected |

### Choosing the right contract to run

Run the smallest set whose `targets` include the file or rule you changed. Read the YAML before running it:

```sh
sed -n '1,220p' eval/contracts/mp-c09-human-report.yaml
```

If a change affects shared wording in `SKILL.md`, more than one contract may be relevant. The deterministic contract-runner tests confirm that every contract's declared mutation still applies, but they do not prove that every affected behavioral claim has been selected for a paid run.

## 13. Read results and exit codes

### Console summary

A normal result line resembles:

```text
PASS            1/1    MP-C09   codex  Bundle validation is reported in plain language
```

A repeated negative-control line resembles:

```text
DETECTED        4/5    MP-C11   codex  Tech Refinement is reported in plain language
                         runs: DETECTED, DETECTED, BROKEN, DETECTED, DETECTED
```

The leftmost verdict is the classified cell result. The rate and individual run list show the underlying sample.

### Verdicts

| Verdict | Meaning | Immediate action |
| --- | --- | --- |
| `PASS` | Every normal repetition satisfied the assertion | Continue to or confirm negative-control qualification |
| `FAIL` | At least one normal repetition did not satisfy the assertion | Inspect assertion details and retained workspace; determine product, prompt, model, or environment cause |
| `DETECTED` | Negative-control detection met the floor | Record the raw rate; call out 4/5 as fragile |
| `BROKEN` | The mutated skill still passed too often | Do not trust the contract; redesign the contract, prompt, assertion, mutation, or model choice |
| `MUTATION-INERT` | A declared mutation changed nothing | Update the mutation pattern to match current production text; rerun |
| `HARNESS-ERROR` | Subject execution failed or timed out | Repair infrastructure and rerun; do not score product behavior |
| `NO-RUNS` | No repetitions were available for classification | Treat as invalid test execution |
| `BUDGET-STOP` | The next metered call was blocked by the budget guard | Treat invocation as incomplete; narrow the next run or obtain a new budget |

### Process exit codes

| Exit | Meaning |
| --: | --- |
| 0 | All selected cells met their expected result |
| 1 | At least one normal contract failed |
| 2 | At least one negative control was broken |
| 3 | Invalid contract, inert mutation, missing credential, failed probe, or harness error |
| 4 | Metered budget stopped the invocation before another subject call |

### Inspect structured results

After a completed invocation, the runner prints the result directory. Read a compact summary with:

```sh
jq -r '[.contract, .harness, .mode, .verdict, .rate, .model, .cli_version] | @tsv' \
  eval/runs/<run-id>/results.jsonl
```

Read the run cost with:

```sh
jq . eval/runs/<run-id>/cost.json
```

Inspect one full result row when you need assertion details:

```sh
jq . eval/runs/<run-id>/results.jsonl
```

### Inspect phase spend

```sh
python3 -m eval.spend "$phase_start"
```

The total reports calls, known metered cost, model breakdown, and unpriced-call count. Never describe unpriced calls as free.

## 14. Investigate a failure

Begin by classifying the failure before changing anything.

### Step 1: Confirm the mode

A `FAIL` in normal mode and a `BROKEN` result in negative-control mode have different meanings. Confirm the `mode` field in the result row.

### Step 2: Confirm that the harness completed

Check the subject exit code and runner verdict. A timeout, authentication error, unavailable binary, invalid flag, malformed output stream, or container failure is infrastructure. Fix it before drawing a conclusion about the skill.

### Step 3: Read the deterministic assertion detail

Artifact results include checks such as “file does not exist” or “file does not match pattern.” This tells you whether the subject failed to act, wrote the wrong path, produced malformed content, or missed one exact requirement.

### Step 4: Retain one diagnostic workspace

Rerun one contract and harness with `--keep-workdirs`. Do not retain an entire matrix unless necessary. Inspect:

- the produced files;
- `.subject.events`, if available;
- the exact skill path the subject read;
- the subject's final message;
- the CLI and model metadata.

### Step 5: Verify the isolation boundary

If a negative control unexpectedly passes, search the retained event stream for global skill paths. Codex must not load `/Users/.../.agents/skills/miniproject` outside the disposable process home. Junie must use the supplied isolated skill location. Claude must mount the disposable skill read-only inside the container.

An isolation bypass invalidates the result. Fix the harness and discard the contaminated run rather than changing the contract.

### Step 6: Confirm that the mutation targeted the actual rule

Read the mutated disposable file. Verify that the edit removed or reversed the behavior named in the contract. A mutation can be syntactically active but conceptually weak—for example, deleting one sentence while the same rule remains in another reference.

### Step 7: Check for answer leakage

Read the subject prompt without looking at the skill. If the prompt itself states the desired policy or exact answer, the model may pass without the skill. Rewrite the task so it supplies the business situation and requested outcome, not the hidden rule being tested.

### Step 8: Compare harnesses, not just aggregate counts

If Codex is 3/5 while Junie and Claude are 5/5, focus on Codex's context, tools, model, or discovery behavior. Do not average the result to 13/15 and call it acceptable.

### Step 9: Reproduce the smallest failing cell

Use one contract, one harness, and one repetition while diagnosing. Repeated full matrices are expensive and create noisy evidence before the cause is understood.

### Step 10: Record exclusions

If a run is invalid, document the run ID, exact reason, and whether its calls remain in cost totals. Never silently replace an unfavorable valid run, and never keep an invalid run in a behavioral score.

## 15. Take action on findings

Use the failure category and evidence to choose the next action.

### Normal `FAIL`: likely product or integration defect

Possible actions:

- Fix the deterministic script if it returned the wrong result.
- Strengthen or clarify the skill instruction if the agent chose the wrong workflow.
- Correct the contract prompt if it does not represent the intended user task.
- Pin a capable model if the selected subject cannot perform the task even with intact instructions.
- Repair harness permissions if the agent understood the task but could not write the artifact.

Add or update a deterministic test before changing implementation when the defect can be expressed deterministically. Rerun the focused free test, then the focused normal behavioral cell.

### Negative-control `BROKEN`: contract is not a trusted regression test

Possible actions:

- Replace a prior-driven claim with a counter-prior rule that genuinely depends on the skill.
- Narrow the assertion to the exact rule under mutation.
- Strengthen the mutation so the rule is removed everywhere the subject can learn it.
- Remove answer leakage from the prompt.
- Use a weaker capable subject to make instruction influence visible.
- Drop the contract if no practical test can distinguish skill behavior from model prior.

Do not “fix” a broken negative control by merely lowering the qualification floor. The point of the control is to challenge the test.

### `MUTATION-INERT`: test maintenance defect

Update the exact mutation pattern after verifying the current production text. Run `test_every_contract_has_an_applicable_negative_control` before spending on a subject:

```sh
python3 -m pytest -q \
  eval/tests/test_contract_runner.py::test_every_contract_has_an_applicable_negative_control
```

### `HARNESS-ERROR`: infrastructure defect

Check the probe, credentials, CLI version, container image, timeout, output parser, sandbox permissions, and working directory. Add a driver unit test when the error reflects a CLI contract that could recur.

Do not weaken a product assertion to make an infrastructure failure disappear.

### Fragile 4/5 detection

The cell qualifies but has no margin. Record it as fragile. Review the missed run for a pattern, but avoid speculative prompt tuning based on one sample. Prioritize strengthening when the contract protects a high-impact behavior or when the same harness shows other misses.

### Manual usability failure with green automation

Treat the user test as real evidence that the automation omitted a requirement. Define the missing outcome precisely, add the cheapest deterministic check that can represent it, and add or strengthen a behavioral contract when agent behavior is involved.

The human-readable output contracts were created through exactly this path after raw JSON passed automation but failed the user experience.

### A changed product requirement

Update the rule, deterministic validator or script, unit tests, behavioral contract, negative control, documentation, and user-story coverage together. The contract should describe the new behavior, not preserve an obsolete requirement merely because it was previously green.

## 16. Add or change a deterministic test

Use test-driven development for rule changes.

### Step 1: State the behavior in one sentence

Example: “A specific request must route to the Chore fast lane without entering Discovery.”

If the sentence contains several independent rules, split it into focused tests.

### Step 2: Choose the nearest test file

Place validator behavior beside that validator's existing tests. Place runner, mutation, driver, or accounting behavior in its corresponding test module.

### Step 3: Write the failing test

Include the smallest input that demonstrates the behavior. Assert on structured fields, exit codes, or exact deterministic text rather than implementation internals when possible.

### Step 4: Confirm the test fails for the expected reason

Run only that test. A syntax error or unrelated fixture failure is not the intended red state.

### Step 5: Implement the smallest complete behavior

Change production code or skill content. Avoid adding behavior that the test does not require unless it is part of the same explicit rule.

### Step 6: Run the focused tests and full free suite

```sh
python3 -m pytest -q eval/tests/test_route_request.py
python3 -m pytest -q -m 'not integration'
python3 scripts/lint_portable.py
```

### Step 7: Decide whether behavioral evidence is also required

If the change affects only deterministic formatting already invoked by an agent, a deterministic test may be sufficient for the script itself, but an existing human-output contract may also need rerunning. If the change affects what an agent should decide, invoke, write, or explain, update or add a behavioral contract.

## 17. Add or change a behavioral contract

### Step 1: Define one narrow behavioral claim

A contract should be able to fail for one understandable reason. “The agent handles MiniProjects correctly” is too broad. “A specific request routes to the Chore fast lane” is testable.

### Step 2: Decide whether the claim belongs in a behavioral test

If a Python function can answer the question exactly, write a deterministic test first. Use a behavioral contract for agent decisions, tool invocation, cross-harness integration, produced work, or user-facing behavior.

### Step 3: Choose an artifact assertion whenever work must happen

Ask the subject to write a file or redirect deterministic output. Use response judging only when the outcome is genuinely semantic and cannot be represented safely as an artifact.

### Step 4: Create a realistic prompt

Write the prompt as a developer or product teammate would state the task. Include necessary facts and requested output. Do not include the policy sentence the skill is supposed to contribute. Explicitly ask the agent to use the MiniProject skill when the contract tests behavior after activation; activation itself is tested separately.

### Step 5: Use a disposable fixture

Reuse `fixtures/p0-2` for a file-light task or add the smallest fixture needed. Do not point a contract at a live repository, user home, or external production system.

### Step 6: Write the assertion

For artifacts, start with existence and add the narrowest content or structure checks needed. Avoid patterns that pass on a token appearing in an unrelated context. Use full-file anchors only when exact output is part of the product contract.

For a response assertion, describe acceptable and unacceptable meaning. Avoid stylistic preferences unless style is the behavior under test.

### Step 7: Design the negative control before trusting the normal run

Ask: “What small change would definitely break the rule this contract claims to protect?” Apply that change to the disposable skill, not the fixture or assertion.

A useful mutation is specific enough to name the missing rule and strong enough that a compliant subject should change behavior. If the model still succeeds from prior knowledge, redesign the claim rather than multiplying repetitions indefinitely.

### Step 8: Declare only harnesses you will run

The current project requires all three harnesses for its product claims. In a future context, do not list a harness merely because support is expected. Listing it is a claim that needs evidence.

### Step 9: Add deterministic contract checks

At minimum, confirm:

- the contract schema loads;
- every mutation applies to a fresh production copy;
- the contract maps to the intended user story;
- the assertion type and sandbox agree;
- model overrides are explicit where needed;
- exact output contracts mutate the actual formatter wording.

Run:

```sh
python3 -m pytest -q eval/tests/test_contract_runner.py
```

### Step 10: Run one bounded normal preflight

Use one harness and one repetition with a small explicit budget. Fix harness or assertion problems before expanding.

### Step 11: Run one bounded negative-control preflight

Confirm the mutation is behaviorally visible once. This is development feedback, not qualification.

### Step 12: Qualify the negative control

Run five repetitions on one harness. If it clears the floor, expand to the other claimed harnesses. If it fails, redesign before spending on the full matrix.

### Step 13: Run the final normal matrix

Use the final prompt, assertion, mutation, model, and isolation implementation. Pre-change and diagnostic runs do not substitute for a final normal result.

### Step 14: Document the result

Record:

- contract and harness;
- exact run ID;
- mode and raw rate;
- model and CLI version;
- metered cost and unpriced calls;
- any excluded runs and exact reasons;
- limitations and cells at the floor.

## 18. Plan a test run without losing cost control

### Count subject calls before running

Use this calculation:

```text
contracts × harnesses × repetitions = subject calls
```

Examples:

- One normal contract on Codex: `1 × 1 × 1 = 1` subject call.
- One five-run negative control across all harnesses: `1 × 3 × 5 = 15` subject calls.
- All 14 negative controls across all harnesses: `14 × 3 × 5 = 210` subject calls.

Response contracts may also create judge calls. Junie calls are unpriced in the ledger but still consume provider usage.

### Use a written phase budget

Choose a ceiling before the first paid call. Record the shared UTC start timestamp. Use the same `--budget-since` value for every command in the phase.

### Leave headroom

Set the runner's cap below the actual approved ceiling. The reserve is an estimate, and one call can exceed it. The hardening phase used an internal stop below the user-approved limit for this reason.

### Expand in stages

Use this order:

1. One normal run on one harness.
2. One negative-control run on one harness.
3. Five negative-control runs on that harness.
4. Five negative-control runs on the remaining harnesses.
5. Final normal matrix on the final contract.

Stop when a stage fails. Do not pay for downstream cells while the contract is known to be broken.

### Audit spend after each command

```sh
python3 -m eval.spend "$phase_start"
```

Report known cost and unpriced call count separately.

### Do not run paid integration tests accidentally

Use:

```sh
python3 -m pytest -q -m 'not integration'
```

Do not use an unfiltered repository-wide `pytest` command unless paid integration execution is intentional, bounded, and authorized.

## 19. Use manual testing alongside the harness

Automation answers whether declared contracts pass. Manual testing answers whether the workflow makes sense to a person using it.

### Use a fresh session

A fresh session avoids hints from prior discussion and shows whether the installed skill can activate and guide the task from normal user context.

### Use a realistic request

Do not paste the contract YAML or expected result. Ask the way a teammate would ask. For example, provide an incomplete MiniProject proposal and request deterministic validation in plain language.

### Observe both action and presentation

Check:

- Did the agent use the skill?
- Did it invoke the appropriate deterministic script?
- Did it create the requested artifact?
- Did it distinguish mechanical validation from human assessment?
- Is the result understandable without reading raw JSON?
- Did it stop or ask for input at the intended workflow boundary?

### Convert a meaningful failure into coverage

When a manual test exposes a repeatable requirement gap:

1. Save the exact request and observed result.
2. State the missing requirement in one sentence.
3. Add a deterministic test if the requirement belongs to a script.
4. Add or strengthen a behavioral contract if the agent's action or presentation is involved.
5. Create a negative control that breaks the newly protected behavior.
6. Rerun the manual task in another fresh session after automation passes.

Do not automate subjective preferences simply because they appeared once. Add coverage for behavior that is product-relevant, explainable, and stable enough to maintain.

## 20. Release and maintenance checklist

Use the relevant parts of this checklist for any skill or harness change.

### Before paid tests

- [ ] Confirm the working tree and ownership of existing changes.
- [ ] Add or update deterministic tests first.
- [ ] Run the focused deterministic tests.
- [ ] Run `python3 -m pytest -q -m 'not integration'`.
- [ ] Run `python3 scripts/lint_portable.py`.
- [ ] Confirm every changed contract's mutation applies.
- [ ] Review the prompt for answer leakage.
- [ ] Choose the smallest contract and harness selection.
- [ ] Calculate subject-call count.
- [ ] Record the approved budget and shared UTC start timestamp.
- [ ] Confirm `.env.local` is mode 600 and gitignored.

### During behavioral testing

- [ ] Run one bounded normal preflight.
- [ ] Run one bounded negative-control preflight.
- [ ] Stop on `HARNESS-ERROR`, `MUTATION-INERT`, or `BROKEN` and diagnose before expanding.
- [ ] Preserve exact run IDs and versions.
- [ ] Audit metered spend and unpriced Junie calls after each command.
- [ ] Retain only the smallest diagnostic workspace needed.

### Before accepting evidence

- [ ] Confirm the subject loaded the disposable skill copy.
- [ ] Confirm every selected subject exited successfully.
- [ ] Confirm the final prompt, mutation, assertion, and model were used.
- [ ] Confirm normal mode passed on every claimed harness.
- [ ] Confirm negative-control rate per contract-harness cell.
- [ ] Call out any 4-of-5 cell as fragile.
- [ ] Exclude contaminated, aborted, and infrastructure-failed runs with reasons.
- [ ] Include discarded calls in cost reporting.

### Before committing or publishing

- [ ] Run the full free deterministic suite again.
- [ ] Run portability lint and diff checks.
- [ ] Check that no credential, retained event stream, or `eval/runs/` artifact is staged.
- [ ] Update the durable results report when claims or evidence changed.
- [ ] Update README or documentation navigation when adding a new guide.
- [ ] State what remains untested.

## Related documents

- [Behavioral Testing Approach](behavioral-testing.md) explains the governing testing principles in a shorter design document.
- [Hardening and Behavioral Testing Report](hardening-and-behavioral-testing-report.md) records the current results, costs, excluded evidence, and remaining limits.
- [Implementation Plan](implementation-plan.md) defines the phased delivery and falsification gates.
- `spikes/ms-004-behavioral-eval/FINDING.md` records the foundational harness qualification.
- `spikes/human-output-hardening/FINDING.md` records the human-output hardening matrix and the Codex isolation defect.
