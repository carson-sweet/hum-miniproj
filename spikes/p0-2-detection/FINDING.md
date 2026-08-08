# P0.2 — Can the behavioral method detect a regression at all?

**Version 1.0 — 2026-08-08**
**Verdict: YES, but conditionally — and the kill condition as written is wrong.**
**Plan revision required before Phase 1. Proposed below.**

Reproduce with `python3 -m eval.run_contracts [--negative-control]`. Raw output in
`evidence/`.

---

## Assumption at risk

The fresh-context-subject with separate-judge method is a sound base. Its sensitivity is
unmeasured — a suite that has only ever returned green has not demonstrated it can return
red.

## Method

Four contracts across distinct behavior classes, run against a probe instruction set
(`skill/`) carrying four one-line rules. Each contract declares a mutation that deletes its
governing rule. Normal mode expects PASS. Negative-control mode deletes the rule and
expects the contract to go red.

The probe instruction set is not the MiniProject skill — that is authored in Phase 2.

## Result

| Contract | Class | Normal | Negative control |
|---|---|---|---|
| MP-C01 estimation | response | PASS | **DETECTED 2 of 5** |
| MP-C02 bundling | response | PASS | **BROKEN 2 of 2** — never detected |
| MP-C03 record | artifact | PASS | DETECTED 2 of 2 |
| MP-C04 one owner | response | PASS | DETECTED 2 of 2 |

**The method detects regressions.** MP-C03 and MP-C04 went red every time their rule was
removed, covering both assertion types — artifact and judged response.

**It does not detect them uniformly**, and the two failures are different problems.

### MP-C02 — the contract measured a prior, not the rule

With `RULE-BUNDLE` deleted, the subject still rejected "backend API changes for widget
reporting" as incomplete and named what was missing. The mutation applied cleanly — the
line was gone, the other rules intact — so this is not a harness fault.

The model already holds this judgment. A backend-only slice reads as an implementation
fragment from general reasoning, with or without instruction. The contract looked like
coverage and measured nothing.

### MP-C01 — detection is probabilistic

Same contract, same mutation, five runs: DETECTED, BROKEN, BROKEN, BROKEN, DETECTED. A 40%
detection rate.

The BROKEN reason is the informative part: *"The response explicitly declines to estimate
the Discovery item and does not assign story points, an effort size, or any work
estimate."* Without the rule, the subject usually declines anyway — a partial prior. The
rule is load-bearing only some of the time.

**A single-run negative control would have called this contract green.** The plan's method
says "Re-run. Expect FAIL on all three" — one run. That is not enough evidence.

### A third failure mode, found and fixed mid-spike

MP-C04's first criterion read "Recommending it be split across two or more engineers
fails, even if the recommendation is hedged." The subject refused to split the MiniProject
and kept one owner, but suggested other engineers take separate independently-releasable
slices — which is what the model document actually prescribes. The judge marked FAIL,
correctly enforcing a criterion that was broader than the rule.

The judge was right and the contract was wrong. Narrowing the criterion to match
`RULE-OWNER` produced PASS in normal mode and DETECTED under mutation.

## Kill condition

As written: *"any mutation still returns PASS → the method does not discriminate, and Phase
3 becomes a design problem rather than an engineering one."*

The trigger fired — MP-C02's mutation returned PASS. **The conclusion it draws is
contradicted by the evidence.** The method discriminates: MP-C03 and MP-C04 detected 2 of 2
each. What MP-C02 shows is a bad contract, not an insensitive method.

Treating this as "Phase 3 becomes a design problem" would be the wrong call. Phase 3 remains
an engineering problem. The design problem is in contract selection.

## Proposed plan revision

1. **Rewrite the kill condition.** Distinguish *no mutation detected by any contract* —
   which really would mean the method cannot discriminate — from *a specific mutation
   undetected*, which means that contract measures a prior. Only the first should threaten
   Phase 3.

2. **Negative controls run N times and report a rate, not a verdict.** One run cannot
   distinguish a load-bearing rule from a lucky sample. MP-C01 would have passed or failed
   the gate depending on which run you happened to take. Suggested floor: a contract must
   detect in at least 4 of 5 runs to count as measuring its rule.

3. **The negative control is a contract-selection screen, not just validation.** Run it
   *before* trusting a contract. One whose mutation goes undetected is measuring the model's
   prior and must be redesigned or dropped. This is the cheapest way to find contracts that
   look like coverage and are not.

4. **A contract's criterion must be no broader than the rule it tests.** The judge enforces
   what you wrote, faithfully. MP-C04's first version failed a compliant response.

5. **Prefer artifact assertions where an outcome is claimed.** MP-C03 was the only contract
   that was both deterministic and 2 of 2 — a file exists or it does not, with no judge
   variance in the loop. This is already rule 3 of the testing approach; it now has evidence
   behind it.

## What this does NOT establish

**Codex only.** Every run used `gpt-5.6-sol` through `codex exec`. Nothing here says the
method transfers to Claude Code or Junie, and the contract format claims all three.

**Small N.** Five runs for MP-C01, two for the others. Enough to prove detection is
probabilistic; not enough to put a confidence interval on any rate.

**A probe instruction set, not the skill.** Four one-line rules in a clean file is the
easiest possible case. The real `SKILL.md` will be longer, and instructions compete for
attention as documents grow.

**Judge variance is unmeasured.** The judge model was never varied, and the same
subject output was never graded twice. Some of MP-C01's flakiness may be judge variance
rather than subject variance. Separating those requires re-grading fixed outputs.

## Follow-on

- Re-run MP-C01 and MP-C02 with a judge model different from the subject model, to separate
  judge variance from subject variance.
- Replace MP-C02 with a counter-prior bundling rule, as MP-C04 was for ownership.
- Add repeat-count support to `run_contracts.py` so negative controls report rates natively.
- Re-run the whole suite once the real `SKILL.md` exists, since rule dilution in a longer
  document is the untested condition that matters most.
