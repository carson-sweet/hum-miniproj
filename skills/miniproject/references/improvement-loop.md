# Improvement loop

Use this workflow only after the register contains live entries. The loop may analyze
evidence, select a recurring pattern, and prepare a reversible diff. It must never apply
that diff. Stop after presenting the proposal and wait for explicit human approval before
recording an approval or measuring a candidate instruction version.

## 1. Analyze the register

Run the deterministic detector. It groups schema-valid entries by learning type and target
instruction, and only reports groups meeting the recurrence threshold.

```bash
python3 <skill-dir>/scripts/analyze_improvements.py \
  --register <register.jsonl> --min-occurrences 2 --output analysis.json
```

Seed entries may validate detector behavior, but at least one live entry must exist before
starting a real improvement cycle. The bundled seed corpus intentionally contains no
cluster labels; its expected clusters live outside the skill in the evaluation suite.

## 2. Prepare a proposal

Choose one pattern. Copy the current instruction to a separate candidate file and edit only
the candidate. Generate a proposal bound to the analysis, pattern, target, base content,
and candidate content:

```bash
python3 <skill-dir>/scripts/propose_improvement.py \
  --analysis analysis.json --pattern-id <pattern-id> --target <logical-target> \
  --instruction <current-file> --candidate <candidate-file> --output proposal.json
```

The proposal contains both forward and reverse diffs. The command does not modify the
instruction. Present the pattern, evidence entry IDs, and exact diff to the human decision
owner. Do not continue merely because the proposal looks safe.

## 3. Record the human decision

Only after the user explicitly approves or rejects that exact proposal, record the decision.
Never supply `--human-confirmed` based on an agent's judgment, an old approval, or approval
of a different diff.

```bash
python3 <skill-dir>/scripts/record_improvement_approval.py \
  --proposal proposal.json --decision approved --approved-by "<human name>" \
  --human-confirmed --output approval.json
```

A rejection ends the cycle. Approval permits evaluation of the candidate; it does not
authorize this workflow to apply the candidate to the current instruction.

## 4. Add and run the targeted contract

Create a new JSON behavioral contract for the selected pattern. It must contain a
`negative_control.mutate` block. If the pattern concerns a production outcome, its
`assert.type` must be `artifact` rather than `response`.

Measure four scores without letting proposal generation read the held-out set:

- targeted contract against the current instruction;
- targeted contract against the candidate;
- held-out contracts against the current instruction;
- the same held-out contracts against the candidate.

The candidate must improve the targeted pass rate. Its held-out pass rate must not fall.

## 5. Record the candidate version

Record the candidate and its predecessor hashes together with all four scores. These hashes,
the reverse diff, and the score record make the version genuinely reversible rather than
merely labeled as reversible.

```bash
python3 <skill-dir>/scripts/record_instruction_version.py \
  --proposal proposal.json --version-id <version-id> \
  --targeted-before 3/5 --targeted-after 5/5 \
  --held-out-before 8/10 --held-out-after 9/10 \
  --output instruction-version.json
```

## 6. Validate the complete cycle

Create `cycle.json` beside the artifacts it names. Paths must be relative and remain inside
the cycle directory.

```json
{
  "schema_version": 1,
  "cycle_id": "cycle-001",
  "proposal": "proposal.json",
  "approval": "approval.json",
  "contract": "target-contract.json",
  "instruction_version": "instruction-version.json",
  "production_outcome": true,
  "scores": {
    "targeted": {
      "before": {"passed": 3, "total": 5},
      "after": {"passed": 5, "total": 5}
    },
    "held_out": {
      "before": {"passed": 8, "total": 10},
      "after": {"passed": 9, "total": 10}
    }
  }
}
```

Run the gate:

```bash
python3 <skill-dir>/scripts/validate_improvement_cycle.py \
  --cycle cycle.json --output cycle-result.json
```

Exit 0 means the proposal, explicit human approval, negative control, artifact requirement,
score improvement, held-out non-regression, and reversible version binding all passed. Exit
1 means the cycle has findings and must not be treated as confirmed. Exit 2 means the cycle
input itself could not be evaluated. A passing cycle is evidence that the candidate is safe
enough to present for a separate human-controlled application step; this loop still does not
apply it.
