# hum-miniproj

A portable [Agent Skill](https://agentskills.io) for organizing AI-accelerated delivery around complete improvements instead of frontend, backend, data, infrastructure, testing, and rollout handoffs.

The skill classifies and routes work as a **Project**, **Discovery**, **MiniProject**, or **Chore**; shapes broad goals; validates owner-led delivery bundles; splits oversized work; closes Tech Refinement; and checks Tech Estimation.

It supports Codex, Junie, Claude Code, and other harnesses implementing the Agent Skills standard.

## Quick start / TL;DR

Install the skill for Codex, Junie, and Claude Code:

```sh
git clone https://github.com/carson-sweet/hum-miniproj.git
cd hum-miniproj
./install.sh
```

Start a fresh agent session, then try:

> Use the MiniProject skill to classify and route this request: “Add the account-status field to the customer export.” Return the result in plain language.

Or validate a proposed MiniProject:

> Use the MiniProject skill to validate this proposal. Complete: a locked-out customer resets their password and signs in. Demoable: recover a locked account end to end and show expired links fail. Owned: Alice owns the result through release readiness. Launch-ready: recovery is verified, observable, rate-limited, and reversible. Return the deterministic result in plain language.

For practical workflows, examples, paste-ready prompts, and checklists, start with the [MiniProject User Guide](docs/user-guide.md).

## The operating model

| Work type | Use it for | Required result |
| --- | --- | --- |
| **Project** | A broad product or business goal that needs shaping and sequencing | Explicit scope plus ranked Discovery and delivery work |
| **Discovery** | A bounded effort to answer a question before responsible delivery work can be defined | A decision artifact and one terminal outcome |
| **MiniProject** | A complete improvement one accountable owner can carry through release readiness | A complete, demoable, owned, launch-ready result |
| **Chore** | A small, specific, low-variance request | The requested correction or maintenance result through the fast lane |

A MiniProject may cross several technical components and use several small pull requests. It keeps one person accountable for the complete outcome while specialists contribute in parallel.

Every MiniProject answers four questions:

- **Complete:** What complete behavior or operational result will be delivered?
- **Demoable:** How will someone observe the improvement working?
- **Owned:** Who carries the complete result through implementation, verification, and release readiness?
- **Launch-ready:** What must be true for the improvement to be safe to release?

Read the [formal operating model](docs/miniproject-model.md) for the rationale and the [user guide](docs/user-guide.md) for day-to-day use.

## What the skill can do

- Classify and route a new request.
- Send specific work through the Chore fast lane.
- Return broad goals to Project shaping with a named owner and next step.
- Shape explicit Project scope and ranked, owned Discovery cards.
- Define and close time-boxed Discovery with `Ready to shape`, `More Discovery`, or `Stop`.
- Validate one MiniProject against the four required criteria.
- Reject explicitly technical-layer-only MiniProject boundaries.
- Split oversized work into complete improvements with at least one independently launchable result.
- Resolve every Tech Refinement card as a MiniProject, Chore, or More Discovery.
- Estimate Chores and MiniProjects while giving Discovery a time box and target output rather than a delivery estimate.
- Return deterministic workflow results in plain language or JSON when explicitly requested.

## Installation

Normal use requires Bash plus at least one supported, authenticated coding agent. Python and the evaluation dependencies are required only for development and testing.

### Default installation

From the repository root:

```sh
./install.sh
```

The installer writes one canonical copy to `~/.agents/skills/miniproject` and creates harness-specific links under `~/.codex/skills`, `~/.junie/skills`, and `~/.claude/skills`. It is idempotent and refuses to overwrite paths it does not own.

Start a fresh agent session after installing or updating the skill.

### Install under another home

```sh
./install.sh --home /absolute/path/to/home
```

### Uninstall

```sh
./install.sh --uninstall
```

Uninstall removes only paths marked as owned by this installer.

## Usage examples

### Classify and route work

> Use the MiniProject skill to classify and route this request: “[request].” If an owner or decision is missing, ask only for that missing information.

### Validate a MiniProject

> Use the MiniProject skill to validate this proposal and report only the deterministic result in plain language. Name: [name]. Complete: [answer]. Demoable: [answer]. Owned: [answer]. Launch-ready: [answer].

### Split oversized work

> Use the MiniProject skill to split “[source work]” into complete, independently useful MiniProjects. Do not split by technical layer. Ensure at least one result can launch without a sibling, run the split validator, and report its result in plain language.

### Shape a broad Project

> Use the MiniProject skill to shape “[broad goal].” Establish explicit v1 in/out scope and ranked Discovery cards with one question, owner, time box, and useful output each. Do not invent Engineering acceptance.

### Close Tech Refinement

> Use the MiniProject skill to resolve every incoming card exactly once as a named MiniProject, Chore, or More Discovery. Keep implementation details off the board, run the board validator, and report its result in plain language.

More examples and full workflow instructions are in the [MiniProject User Guide](docs/user-guide.md).

## Deterministic validation and human judgment

The bundled validators provide stable mechanical checks. A valid result means the artifact passed the script's defined rules; it is not automatically a judgment that the answers are persuasive, the work is correctly prioritized, or the scope is the best possible size.

For example, the single-bundle validator checks that all four criterion answers are stated and rejects an explicitly technical-layer-only boundary. It does not otherwise grade answer quality. When both checks are needed, ask the agent to report the deterministic result first and the human-quality assessment separately.

## Project status

All eight product user stories are implemented. The current skill has deterministic coverage and recorded normal behavioral passes across Codex, Junie, and Claude for all 14 contracts. The foundational and human-output contract groups have repeated negative-control qualification; semantic contracts MP-C05 through MP-C08 have normal three-harness acceptance but have not received five-run mutation qualification.

Known limits include narrow prompt coverage, no long-session reliability measurement, one Codex human-output contract at the 4-of-5 qualification floor, unknown Junie text-mode cost, and local gitignored raw run artifacts.

See the [Hardening and Behavioral Testing Report](docs/hardening-and-behavioral-testing-report.md) for exact results, evidence boundaries, excluded runs, cost, and limitations.

## Documentation

| Document | Start here when you need to |
| --- | --- |
| [MiniProject User Guide](docs/user-guide.md) | Use the operating model, follow a workflow, interpret validation, or copy a prompt |
| [MiniProject operating model](docs/miniproject-model.md) | Understand the formal model and its rationale |
| [Developer Testing Guide](docs/developer-testing-guide.md) | Set up, run, interpret, diagnose, or extend the test suite |
| [Hardening and Behavioral Testing Report](docs/hardening-and-behavioral-testing-report.md) | Review current results, costs, evidence quality, and remaining risk |
| [Behavioral Testing Approach](docs/behavioral-testing.md) | Understand the design principles behind behavioral contracts and negative controls |
| [Implementation Plan](docs/implementation-plan.md) | Review the phased build plan and falsification gates |

## Repository layout

```text
skills/miniproject/     Production Agent Skill, references, and deterministic scripts
eval/contracts/         Behavioral contracts and their negative controls
eval/drivers/           Codex, Junie, and Claude harness adapters
eval/tests/             Deterministic pytest suite
fixtures/               Disposable behavioral-test starting state
spikes/                 Recorded findings and qualification summaries
docs/                   User, design, testing, and evidence documentation
install.sh              Idempotent cross-harness installer and uninstaller
```

## Development and testing

Python 3.11 or newer is required for the evaluation package.

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
python3 -m pytest -q -m 'not integration'
python3 scripts/lint_portable.py
```

The explicit pytest marker exclusion matters: integration tests invoke real model subjects and can incur cost. Do not run paid behavioral tests without a bounded plan and explicit budget.

The [Developer Testing Guide](docs/developer-testing-guide.md) explains environment setup, harness isolation, contract purposes, negative controls, result interpretation, cost controls, and how to respond to findings.

## Contributing

- Keep the production skill portable across supported Agent Skills harnesses.
- Add deterministic tests before implementation when changing executable rules.
- Give every behavioral contract an applicable negative control.
- Prefer deterministic artifact assertions when the requested outcome is a file or script result.
- Run the full non-integration suite and portability lint before opening a pull request.
- State what remains untested and do not present unpriced calls as free.

For detailed contribution and test-development procedures, follow the [Developer Testing Guide](docs/developer-testing-guide.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
