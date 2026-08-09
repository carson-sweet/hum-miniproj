# Hardening and Behavioral Testing Report

**Version 1.3 — 2026-08-09**

**Author: Eigen (synthetic cognitive entity)**

**Decision: the implemented MiniProject workflows pass their recorded normal three-harness checks. All 16 behavioral contracts meet the configured repeated-mutation floor in Codex, Junie, and Claude. The final qualified cells detected 240 of 240 mutations.**

## Executive summary

The MiniProject skill is tested as both deterministic software and probabilistic agent behavior. The deterministic layer checks its validators, installer, coverage ledger, eval runner, and portability rules. The behavioral layer installs a fresh copy of the production skill into isolated Codex, Junie, and Claude environments, asks each agent to perform a realistic task, and evaluates the response or produced artifact.

The current evidence is:

- 220 deterministic tests passed, with four paid integration tests deselected.
- Portability lint and the standard Agent Skill validator passed.
- All 16 current contracts have a recorded normal pass in all three harnesses: 48 of 48 unique contract-harness cells.
- MP-C01 through MP-C04 detected their mutations 60 of 60 times.
- MP-C05 through MP-C08 detected their final mutations 60 of 60 times. Initial Junie repair escapes on MP-C05 and MP-C07 led to a no-repair contract guard and clean 5-of-5 reruns.
- MP-C09 through MP-C14 detected their final mutations 90 of 90 times. MP-C11 Codex improved from 4 of 5 to 5 of 5 after the same no-repair guard was added.
- MP-C15 and MP-C16 detected their mutations 30 of 30 times. Every contract-harness cell passed 5 of 5.
- The hardening phase used $8.6668 of metered model usage against a user-approved $10 ceiling. Forty-four Junie calls in that phase exposed no provider usage data and therefore have unknown cost.
- The bounded MP-C15/MP-C16 hardening phase used $4.6211 of metered model usage against a $6 ceiling. Ten Junie calls in that phase exposed no provider usage data and therefore have unknown cost.
- The semantic and MP-C11 hardening phase used $7.8097 of metered model usage against a final approved $8.75 ceiling. Thirty-five Junie subject calls in that phase exposed no provider usage data and therefore have unknown cost.

This establishes contract compliance for the tested prompts and environments. It does not establish general product quality, behavior under arbitrary paraphrases, or reliability in long sessions where other instructions compete for attention.

## Amendment: final hardening qualification

This amendment records the hardening completed after the earlier results that left MP-C05 through MP-C08 without five-run mutation qualification and left MP-C11 at 4 of 5 on Codex. Those earlier conclusions are superseded and must not be used as the current readiness assessment.

| Evidence area | Earlier recorded result | Amended final result |
| --- | --- | --- |
| MP-C05–MP-C08 semantic contracts | Normal three-harness acceptance only | 60 of 60 final mutations detected; every contract-harness cell passed 5 of 5 |
| MP-C11 on Codex | 4 of 5 mutation detections | 5 of 5 after the no-repair guard, followed by a fresh normal Codex pass |
| All behavioral contracts | Qualification incomplete | All 16 contracts passed in all three harnesses; 240 of 240 final mutations detected |
| Normal behavioral acceptance | Partial groups reported at different times | 48 of 48 unique contract-harness cells passed |
| Deterministic acceptance | Earlier suite sizes | 220 passed, with four paid integration tests deliberately deselected |

The qualification defect exposed during this work was in the test boundary: some subjects could repair the deliberately mutated validator instead of behaving under the supplied mutation. The harness now explicitly forbids modifying or repairing the installed skill or validator. A deterministic regression test pins that restriction. Initial escaped cells and an incomplete budget-stopped run remain in cost accounting but are excluded from the final behavioral scores.

## Scope

### System under test

The production artifact is `skills/miniproject/`, including:

- the skill instructions in `SKILL.md`;
- the work-type, workflow, bundling, and estimation references;
- deterministic validators for bundles, splits, board stages, Discovery plans, and request routing.

The behavioral runner is `eval/run_contracts.py`. Contract definitions are in `eval/contracts/`. The runner copies the production skill for every subject run; it does not test a separately maintained fixture version of the skill.

### Claims tested

The 16 current contracts cover five evidence groups:

| Group | Contracts | Claim |
| --- | --- | --- |
| Foundational behavior | MP-C01–MP-C04 | Discovery closeout, presence-only validation, technical-layer rejection, and one accountable owner |
| User-story semantics | MP-C05–MP-C08 | Complete splits, refinement and estimation, Discovery shaping, and request routing |
| Human-readable output | MP-C09–MP-C14 | Exact plain-language results for all six interactive validator/router workflows |
| Continuous improvement | MP-C15–MP-C16 | Live improvement capture and a gated, non-self-applying improvement cycle |
| Portability | all claimed harnesses | The same production skill works in Codex, Junie, and Claude |

## Testing methodology

### 1. Deterministic tests run first

Paid behavioral runs are gated behind the deterministic suite. The CI-equivalent command excludes tests marked `integration` because those launch paid subjects:

```sh
python3 -m pytest -q -m 'not integration'
python3 scripts/lint_portable.py
python3 /path/to/skill-creator/scripts/quick_validate.py skills/miniproject
```

The deterministic suite verifies the validator rules, schema rejection, installer behavior, user-story coverage ledger, artifact assertions, mutation application, runner classification, budget enforcement, and subject-home isolation. Contract tests also pin the exact human-readable output patterns and require each output contract to mutate the formatter wording it claims to protect.

### 2. Each behavioral contract carries its own negative control

A contract contains:

- the realistic user prompt;
- the fixture copied into the subject workspace;
- the harnesses where the behavior is claimed;
- a response or artifact assertion;
- a mutation that deliberately breaks the relevant production rule;
- the expected result when that mutation is active.

Normal mode asks whether the production skill produces the required behavior. Negative-control mode first mutates a disposable skill copy, then asks whether the same assertion goes red. A test that remains green after its rule is removed or reversed is classified `BROKEN`, because it has not shown that it measures the skill rather than a model prior.

Mutation failures and infrastructure failures are kept separate:

- `MUTATION-INERT` means the declared edit did not change the disposable skill.
- `HARNESS-ERROR` means the subject did not complete successfully.
- `DETECTED` means the mutated skill failed the contract as intended.
- `BROKEN` means the mutated skill still passed too often.

Neither an inert mutation nor a harness error is counted as behavioral detection.

### 3. Repeated qualification uses a rate

Model behavior is sampled, not assumed deterministic. Qualification runs each negative control five times per claimed harness. The configured floor is 4 of 5, or 80%, for every contract-harness cell. The raw hit count is retained even when the cell clears the floor; a 4-of-5 result is reported as fragile rather than rounded up to the same confidence as 5 of 5.

Normal acceptance is one pass per contract and harness. It proves that the intact skill can satisfy the contract in the recorded environment, not a population-level reliability rate.

### 4. Artifact assertions are preferred for outcomes

Fifteen current contracts assert on produced files. MP-C04 is the sole response-judged contract because its claim concerns how accountability is framed. Artifact contracts check that a file exists and matches the required structure or content. This prevents a fluent explanation of what should be done from passing when the requested work was never performed.

Human-readable contracts MP-C09 through MP-C14 are stricter: the prompt requires the agent to run the bundled script with human formatting and redirect that script's standard output directly to the report file. The agent is explicitly forbidden from reconstructing or editing the report or modifying or repairing the installed skill or validator. Semantic artifact contracts MP-C05 through MP-C08 carry the same no-repair guard. Assertions match the entire file using start and end anchors, allowing only an optional trailing newline.

### 5. Subject, skill, and judge are isolated

Every repetition receives a fresh fixture and fresh copy of the production skill. The subject cannot see the contract assertion or intended answer. For the one response contract, the judge sees only the pass criterion and subject output; it does not see the skill under test.

Harness boundaries are:

- **Codex:** a disposable process `HOME` and nested `CODEX_HOME` are created. The canonical skill copy is installed beneath disposable `HOME/.agents/skills` and linked beneath disposable `CODEX_HOME/skills`. Only `auth.json` is symlinked from the real Codex home.
- **Junie:** a disposable `JUNIE_HOME`, log directory, cache directory, and isolated skill root are used. Default skill discovery locations are disabled. The API key is read from the gitignored, mode-600 `.env.local` file without sourcing it as shell code.
- **Claude:** subjects run in a disposable Docker container. The fixture is the only writable host mount, the isolated skill is read-only, host Claude state is not mounted, and the OAuth token exists only in the container process environment.

This boundary is part of test correctness, not only hygiene: a subject that loads the globally installed skill can bypass the mutated copy and make a broken negative control appear green.

### 6. Models and harness versions are recorded

The final recorded matrices used:

| Harness | Subject model | Recorded versions |
| --- | --- | --- |
| Codex | `gpt-5.6-luna` | `codex-cli 0.145.0` for the foundational/user-story runs; `0.147.0` for human-output hardening |
| Junie | `gpt-5.6-luna` | Junie `26.8.3 (2548.5)` |
| Claude | `claude-sonnet-5` | Claude Code `2.1.226` |

The weaker Luna subject was chosen deliberately. Phase 0 showed that stronger models can follow sensible rules from their own priors, masking whether the skill instruction contributes anything. Claude artifact contracts were pinned to Sonnet after Haiku once exited successfully without producing the requested files.

### 7. Results and cost are recorded per run

Each run writes a gitignored `eval/runs/<run-id>/results.jsonl` with contract, harness, mode, verdict, reason, model, session identifier when available, duration, repeat rate, individual repeat verdicts, and CLI version. A companion `cost.json` contains run-scoped metering. `EVAL_RUN_ID` prevents concurrent or previous ledger rows from contaminating the run total.

The runner can enforce a shared metered budget across invocations:

```sh
python3 -m eval.run_contracts \
  --negative-control --repeat 5 \
  --max-metered-cost 9.00 \
  --budget-since 2026-08-09T03:04:43Z \
  --budget-reserve 0.25
```

Before each next subject call, current metered spend plus the reserve is compared with the cap. Junie text mode exposes no usage, so those calls are reported as unpriced and are never represented as zero-cost coverage.

## Hardening work performed

### Human-readable behavior became an explicit contract

The first live user test revealed a product-level failure that the JSON artifact contracts did not catch: the validator was mechanically correct, but the agent returned raw JSON rather than a useful plain-language result. Human formatting was added to all six interactive workflows, then protected with MP-C09 through MP-C14.

The normal contracts require exact script-produced messages for:

- bundle validation;
- split validation;
- Tech Refinement;
- Tech Estimation;
- Discovery-plan validation;
- specific and broad request routing.

The corresponding negative controls change the actual formatter wording. They do not merely remove a CLI flag or alter an irrelevant instruction.

### Codex global-skill bypass was removed

The first Codex hardening negative control was invalid. The runner isolated `CODEX_HOME`, but Codex still discovered `/Users/carsonsweet/.agents/skills/miniproject` through the real process `HOME`. It therefore executed the unmutated global skill instead of the disposable copy. The retained event stream named the global path explicitly.

The driver now isolates both `HOME` and `CODEX_HOME`. Deterministic tests pin the directory layout and verify that subprocesses do not receive the user's real home. All pre-fix Codex results were excluded from the decision tables.

### User-owned directories were removed from the test boundary

Early test tooling had installed skills and persisted sessions under user-owned directories. That design made test cleanup capable of deleting user data. Current Codex and Junie subjects use disposable homes, and cleanup is scoped to the exact temporary directory or recorded session identifier. Directory-wide session sweeps are not part of the current workflow.

### Resume-command failures were separated from behavior

An early capture run treated missing output as a behavioral failure even though `codex exec resume` had exited 2: unlike `codex exec`, resume rejects `-s`, `-C`, and `--color`. A second diagnostic found that resumed turns needed the supported `-c sandbox_mode="workspace-write"` override. These plumbing failures were fixed; the affected evidence was removed and never counted toward a kill condition.

### Subject repair of mutated validators was blocked

The first repeated semantic matrix found that Junie could repair the deliberately mutated validator or reproduce its expected result: MP-C05 detected 4 of 5 and MP-C07 detected only 3 of 5. The same weakness explained MP-C11 Codex's earlier 4-of-5 result. A failing deterministic contract test was added first, then all semantic and human-output prompts were changed to forbid modifying or repairing the installed MiniProject skill or validator. Post-fix MP-C05 Junie, MP-C07 Junie, and MP-C11 Codex reruns each detected 5 of 5. MP-C08 was qualified entirely under the strengthened prompt.

## Results

### Deterministic acceptance

| Check                                   |                   Result |
| --------------------------------------- | -----------------------: |
| Pytest excluding paid integration tests | 220 passed, 4 deselected |
| Portability lint                        |                     PASS |
| Agent Skill validator                   |                     PASS |
| Diff whitespace check                   |                     PASS |

### Normal three-harness acceptance

Every current contract has at least one trustworthy normal pass on Codex, Junie, and Claude: 48 of 48 unique contract-harness cells.

| Contract | Behavior                                 | Codex | Junie | Claude |
| -------- | ---------------------------------------- | ----: | ----: | -----: |
| MP-C01   | Discovery decision artifact              |  PASS |  PASS |   PASS |
| MP-C02   | Presence-only bundle validation          |  PASS |  PASS |   PASS |
| MP-C03   | Technical-layer bundle rejection         |  PASS |  PASS |   PASS |
| MP-C04   | One accountable owner                    |  PASS |  PASS |   PASS |
| MP-C05   | Complete, independently launchable split |  PASS |  PASS |   PASS |
| MP-C06   | Refinement and estimation rules          |  PASS |  PASS |   PASS |
| MP-C07   | Ranked Discovery plan and acceptance     |  PASS |  PASS |   PASS |
| MP-C08   | Specific/broad request routing           |  PASS |  PASS |   PASS |
| MP-C09   | Human-readable bundle result             |  PASS |  PASS |   PASS |
| MP-C10   | Human-readable split result              |  PASS |  PASS |   PASS |
| MP-C11   | Human-readable refinement result         |  PASS |  PASS |   PASS |
| MP-C12   | Human-readable estimation result         |  PASS |  PASS |   PASS |
| MP-C13   | Human-readable Discovery result          |  PASS |  PASS |   PASS |
| MP-C14   | Human-readable routing results           |  PASS |  PASS |   PASS |
| MP-C15   | Live improvement capture                 |  PASS |  PASS |   PASS |
| MP-C16   | Gated improvement cycle                  |  PASS |  PASS |   PASS |

The foundational matrix is recorded under run `20260809T000730Z-541029000`. User-story semantic runs for MP-C05 through MP-C08 are `20260809T004140Z-281271000`, `20260809T004450Z-480971000`, `20260809T004724Z-586238000`, and `20260809T005019Z-203062000`. MP-C15 normal runs are `20260809T125850Z-224658000`, `20260809T125851Z-116791000`, and `20260809T125850Z-690736000`; MP-C16 normal runs are `20260809T133354Z-081947000`, `20260809T133354Z-815852000`, and `20260809T133354Z-526118000`. The exact human-output run IDs appear in the evidence index below.

### Repeated negative-control qualification

| Contract | Codex | Junie | Claude | Total | Qualification |
| --- | --: | --: | --: | --: | --- |
| MP-C01 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C02 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C03 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C04 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C05 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C06 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C07 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C08 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C09 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C10 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C11 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C12 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C13 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C14 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C15 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |
| MP-C16 | 5/5 | 5/5 | 5/5 | 15/15 | qualified |

Across all four behavioral groups, the final qualified cells detected 240 of 240 mutations. This aggregate is descriptive only; qualification is decided per contract and harness, not by allowing strong cells to hide a weak one.

### Live user tests

The first human bundle-validation test exposed raw JSON output and failed the usability expectation. After human formatting was implemented, a fresh-session bundle test produced the deterministic plain-language result. A subsequent fresh-session split-validation test also produced the expected plain-language result. The remaining four human-output workflows have three-harness behavioral evidence but have not each received a separate manual fresh-session user test.

## Evidence qualification and discarded runs

Only runs using the final task, assertion, mutation, intended subject model, successful harness execution, and correct isolation boundary are decision-eligible. A contamination-prevention-only prompt change remains evidence-preserving when it only forbids repairing the installed skill or validator: a cell that already detected 5 of 5 under the weaker prompt remains eligible, while any cell with an escape is rerun. The following were excluded:

- the original P0.3 file that called capture failure after resume exited 2;
- capture diagnostics where the resumed sandbox was read-only;
- pre-fix Codex hardening runs that loaded the global skill;
- early human-output preflights using prompts that allowed the agent to reconstruct the report rather than redirect script output;
- initial MP-C05 and MP-C07 Junie cells that exposed validator-repair escapes before the no-repair guard;
- budget-stopped MP-C08 run `20260809T173335Z-105869000`, which wrote no result artifact;
- aborted or incomplete matrices.

Discarded calls remain included in phase cost totals. They are excluded only from behavioral pass/fail claims.

## Cost accounting

### Human-output hardening phase

The hardening phase began at `2026-08-09T03:04:43Z` with a user-approved metered ceiling of $10. Matrix commands used an internal $9 stop, final normal verification used $9.50, and both reserved $0.25 before each next subject call.

| Measure                            |  Result |
| ---------------------------------- | ------: |
| Recorded calls                     |     185 |
| Metered cost                       | $8.6668 |
| Junie calls with unavailable usage |      44 |

The total includes contaminated and aborted diagnostic calls, not only the runs in the decision tables.

### MP-C15 and MP-C16 hardening phase

The continuous-improvement hardening phase began at `2026-08-09T14:32:49Z` with a $6 metered ceiling and $0.75 reserved before each next subject call. The two contract matrices ran sequentially so they shared one reliable budget window.

| Measure                            |  Result |
| ---------------------------------- | ------: |
| Recorded calls                     |      40 |
| Metered calls                      |      30 |
| Metered cost                       | $4.6211 |
| Junie calls with unavailable usage |      10 |

MP-C15 used $1.8271 metered; MP-C16 used $2.7940 metered. No diagnostic retries or excluded runs were needed in this phase.

### Semantic and MP-C11 hardening phase

This phase began at `2026-08-09T15:50:08Z` with a $7 metered ceiling and $0.75 reserve. The guard stopped an incomplete MP-C08 matrix at $6.3039. The user approved raising the cumulative ceiling to $8.75, and the remaining work finished at $7.8097.

| Measure                            |  Result |
| ---------------------------------- | ------: |
| Recorded subject calls             |     114 |
| Metered calls                      |      79 |
| Metered cost                       | $7.8097 |
| Junie calls with unavailable usage |      35 |

The phase total includes the budget-stopped MP-C08 attempt, the initial MP-C05 and MP-C07 Junie escape runs, and their final replacements. Two unpriced ledger rows produced by deterministic Junie driver tests are excluded from the subject-call table.

### Repository ledger boundary

As of this report, the three active worktree ledgers contain 1,190 non-overlapping recorded calls and $39.1985 of metered cost, including 248 calls with unavailable pricing. That is not the all-project cost. Metering was added after substantial earlier activity, Junie text mode does not expose usage, and costs incurred outside the ledgers cannot be reconstructed from repository evidence. The ledger total therefore must not be presented as complete spend.

## Limitations and open risks

1. **Prompt coverage is narrow.** The contracts test exact task shapes, not a paraphrase suite.
2. **Long-session behavior is unmeasured.** Fresh isolated contexts do not reproduce instruction competition in a long working session.
3. **The suite measures compliance, not answer quality.** In particular, `validate_bundle.py` intentionally validates that the four answers are stated; it does not decide whether answers such as “no” or “blocked” are persuasive.
4. **Junie cost is incomplete.** Its required text-output mode provides no usage.
5. **Raw run artifacts are local and gitignored.** The committed findings preserve run IDs and aggregate results, but reviewers cannot reconstruct every event from the Git repository alone.
6. **No automatic model-drift schedule exists.** Behavioral matrices run on demand; a future CLI or model change can invalidate old evidence until the suite is rerun.

## Reproduction

These commands invoke paid subjects. Set an explicit budget and shared start time before running them. Never run unbounded integration tests through plain `pytest`.

```sh
phase_start="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

python3 -m pytest -q -m 'not integration'
python3 scripts/lint_portable.py

python3 -m eval.run_contracts \
  --max-metered-cost 9.00 \
  --budget-since "$phase_start" \
  --budget-reserve 0.25

python3 -m eval.run_contracts \
  --negative-control --repeat 5 \
  --max-metered-cost 9.00 \
  --budget-since "$phase_start" \
  --budget-reserve 0.25

python3 -m eval.spend "$phase_start"
```

Use `--contract` and `--harness` to qualify one bounded slice instead of spending for the full matrix. The metered guard does not price Junie; count those calls and report them separately.

## Evidence index

### Foundational behavioral harness

- Normal matrix: `20260809T000730Z-541029000`
- Repeated negative-control details: `spikes/ms-004-behavioral-eval/FINDING.md`

### Human-output normal runs

| Contract | Codex                        | Junie and Claude             |
| -------- | ---------------------------- | ---------------------------- |
| MP-C09   | `20260809T044314Z-374577000` | `20260809T045218Z-513752000` |
| MP-C10   | `20260809T044417Z-478154000` | `20260809T045309Z-302516000` |
| MP-C11   | `20260809T044528Z-120479000` | `20260809T045425Z-089260000` |
| MP-C12   | `20260809T044642Z-225328000` | `20260809T045600Z-454105000` |
| MP-C13   | `20260809T044743Z-015329000` | `20260809T045701Z-330235000` |
| MP-C14   | `20260809T044845Z-650793000` | `20260809T045808Z-351491000` |

### Human-output repeated negative controls

| Contract | Run IDs                                                    |
| -------- | ---------------------------------------------------------- |
| MP-C09   | `20260809T033449Z-260543000`; `20260809T034014Z-920973000` |
| MP-C10   | `20260809T034439Z-409022000`                               |
| MP-C11   | `20260809T035657Z-296839000`; final Codex `20260809T175326Z-101952000` |
| MP-C12   | `20260809T041005Z-487095000`                               |
| MP-C13   | `20260809T042033Z-092977000`                               |
| MP-C14   | `20260809T043354Z-604641000`                               |

Supporting interpretation and excluded-run notes are in `spikes/human-output-hardening/FINDING.md` and `spikes/user-story-acceptance/FINDING.md`.

### Semantic repeated negative controls

| Contract | Final run IDs |
| --- | --- |
| MP-C05 | Codex and Claude `20260809T155020Z-391957000`; final Junie `20260809T172332Z-032652000` |
| MP-C06 | `20260809T161838Z-141541000` |
| MP-C07 | Codex and Claude `20260809T164417Z-547987000`; final Junie `20260809T171258Z-809011000` |
| MP-C08 | Codex `20260809T180458Z-071485000`; Junie `20260809T181146Z-068242000`; Claude `20260809T175014Z-564380000` |

The initial MP-C05 Junie 4-of-5 result and MP-C07 Junie 3-of-5 result are retained in their original runs but superseded by the final post-fix cells. Budget-stopped MP-C08 run `20260809T173335Z-105869000` produced no results artifact and is excluded from behavioral claims while remaining in cost totals. MP-C11's final normal Codex verification is `20260809T180243Z-040169000`.

### Continuous-improvement acceptance and repeated negative controls

| Contract | Normal run IDs | Five-run negative-control run |
| --- | --- | --- |
| MP-C15 | `20260809T125850Z-224658000`; `20260809T125851Z-116791000`; `20260809T125850Z-690736000` | `20260809T143303Z-055364000` |
| MP-C16 | `20260809T133354Z-081947000`; `20260809T133354Z-815852000`; `20260809T133354Z-526118000` | `20260809T145716Z-056142000` |

Supporting interpretation and excluded-run notes are in `spikes/ms-005-ms-006-acceptance/FINDING.md`.

## Final assessment

The current skill is ready for prototype or bounded beta use. Its intact behavior passed every recorded normal contract in all three harnesses, and every one of the 16 contracts now has 5-of-5 final mutation detection in every claimed harness. The evidence is not equivalent to universal reliability: broader prompt paraphrases, long-session instruction competition, model drift, and user-success outcomes remain future hardening work.
