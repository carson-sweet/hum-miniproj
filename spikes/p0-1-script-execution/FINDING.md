# P0.1 — Do bundled `scripts/` execute under Codex and Junie?

**Version 1.0 — 2026-08-08**
**Verdict: Codex YES. Junie UNTESTED — P0.1 is half-answered.**
**Kill condition: not triggered for Codex.**

Reproduce with `./spikes/p0-1-script-execution/run.sh`. Raw output in `evidence/`.

---

## Assumption at risk

Deterministic validators substitute for the hook primitive the Agent Skills standard does
not define. If scripts do not execute, or execute behind a permission wall that breaks
flow, enforcement collapses to advisory prose.

## Method

A probe skill (`skill/`) containing only `SKILL.md` and `scripts/echo_check.py`. The script
writes `probe-sentinel.json` carrying runtime-derived fields — a sha256 of its own source,
the interpreter path, pid, and cwd — so a host that *describes* running it cannot produce a
matching sentinel by narration.

Installed the way `install.sh` is designed to work: canonical copy at
`~/.agents/skills/mp-probe/`, symlinked into `~/.codex/skills/mp-probe`. Invoked through
`codex exec` in a disposable workspace. Both locations removed afterward, including on
failure.

Three variants:

| | Contents | Flags |
|---|---|---|
| A | portable subset only | none |
| B | portable subset + `agents/openai.yaml` | none |
| C | portable subset only | `--ignore-user-config --ignore-rules` |

## Result

```
expected token: c25f14c61e96593d
model: gpt-5.6-sol      codex-cli 0.145.0

A portable subset only        : PASS
B with agents/openai.yaml     : PASS
C under eval isolation flags  : PASS
```

Every variant wrote a sentinel whose token matched the source hash. The transcript shows a
real subprocess, not a described one:

```
/bin/zsh -lc 'python3 /Users/carsonsweet/.agents/skills/mp-probe/scripts/echo_check.py --out .'
```

Sentinel from variant A:

```json
{
  "marker": "MP-P0.1-SENTINEL",
  "token": "c25f14c61e96593d",
  "python_version": "3.11.6",
  "script_path": "/Users/carsonsweet/.agents/skills/mp-probe/scripts/echo_check.py",
  "cwd": "/private/var/folders/.../tmp.TZOs9dze3g"
}
```

## What this establishes

1. **Bundled scripts execute under Codex.** Validators can be deterministic rather than
   advisory. `validate_bundle.py` does not need redesigning on Codex's account.
2. **The symlink install design works.** `script_path` resolved through the symlink to the
   canonical `~/.agents/skills/` copy, so `install.sh` writing one copy and linking it into
   each harness is viable — at least for Codex.
3. **`agents/openai.yaml` is not required.** Variant A had none and was still discovered and
   run. The portability constraint — `SKILL.md` + `references/` + `scripts/` only — holds on
   Codex. `lint_portable.py` should therefore treat `agents/openai.yaml` as a
   harness-specific construct to flag, not a required file.
4. **The eval driver's isolation flags are safe.** Variant C confirms
   `--ignore-user-config --ignore-rules` does not suppress skill discovery. Contract runs
   will load the skill under test. This was checked because the driver in
   `eval/drivers/codex.py` sets both by default; had it failed, every future contract run
   would have silently tested nothing.

## What this does NOT establish

**Junie is untested.** P0.1 asks about Codex *and* Junie. Half the question is open, and
the kill condition triggers on either harness failing. Nothing here licenses a claim about
portability across harnesses.

**The permission-wall half is unanswered.** This ran non-interactively with
`approval: never` and `sandbox: workspace-write` — `codex exec` defaults. The assumption at
risk includes scripts that "execute behind a permission wall that breaks flow." Interactive
Codex with default approval settings may prompt before running a bundled script. That is a
different question and it is untested.

**One run per variant, one model.** `gpt-5.6-sol`, single-shot. Script execution could be
probabilistic in a way three runs cannot reveal. No flakiness measurement.

**Explicit invocation only.** The prompt named the skill. Whether Codex surfaces it from
the description alone is a separate question — relevant because `allow_implicit_invocation`
exists in the Codex-specific manifest that variant A omitted.

## Follow-on

- Run the same probe under Junie to close P0.1.
- Add an interactive-approval variant, or document that the model assumes a non-interactive
  or pre-approved posture.
- Repeat each variant N times before treating PASS as stable.
- Encode finding 3 as a `lint_portable.py` rule: `agents/*.yaml` is harness-specific.
