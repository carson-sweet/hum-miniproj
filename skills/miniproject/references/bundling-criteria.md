# Bundling criteria

A MiniProject needs a stated answer for all four criteria. Use the answers to
shape the work; use the bundled validator to check that none are missing.

## Complete

Name the whole improvement rather than one technical layer. Describe the behavior
or operational result that exists when the work is finished.

Question: What complete improvement will be delivered?

## Demoable

Describe the observable proof. A stakeholder or teammate should be able to see a
real behavior, result, or operational change rather than a list of internal tasks.

Question: How will someone see the improvement work?

## Owned

Name one owner for the end-to-end result. The owner may coordinate reviews and
specialist input, but responsibility does not fragment by technical layer.
Contributors may implement or review parts of the work, but they do not own
technical-layer slices inside the MiniProject. The one owner remains accountable
for integration, verification, and release readiness.

Question: Who carries the improvement through implementation, verification, and
release readiness?

## Launch-ready

State what makes the result safe to release, even if release is intentionally held.
Include the relevant verification, rollout, observability, rollback, or migration
considerations without turning them into separate board items.

Question: What must be true for this improvement to be safe to launch?

## Splitting rule

Split oversized work along independently useful improvement boundaries. Each
resulting MiniProject must answer all four criteria on its own, and at least one
piece should be releasable without waiting for every sibling.

Do not split into frontend, backend, data, infrastructure, and testing cards. Those
are implementation concerns inside the owner's plan.

## Validator boundary

`validate_bundle.py` is intentionally mechanical. It reports missing or blank
answers in a stable JSON shape. It does not decide whether an answer is persuasive,
whether the scope is too large, or whether the work is genuinely complete. Apply
human or agent judgment after the presence check.
