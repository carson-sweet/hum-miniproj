---
name: mp-probe
description: Use when asked to run the MiniProject probe check, verify bundled script execution, or write a probe sentinel. Runs a bundled script that writes a sentinel file proving the script executed.
---

# MiniProject Probe

A single-purpose probe. It exists to prove that a bundled script in this skill is
actually executed by the host agent, rather than described or simulated.

## How to run it

Run the bundled script from the skill directory, passing the current working
directory as the output location:

```bash
python3 "$SKILL_DIR/scripts/echo_check.py" --out .
```

If `$SKILL_DIR` is not set, use the directory containing this SKILL.md.

The script writes `probe-sentinel.json` into the output directory. Report the
`token` value it printed.

Do not write the sentinel yourself, and do not simulate the output. If the
script cannot be executed, say so plainly instead.
