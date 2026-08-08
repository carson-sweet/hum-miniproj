---
name: mp-classify
description: Use when classifying a request as a Project, Discovery, MiniProject, or Chore, or when deciding how a piece of work should enter the board.
---

# Work classification

Classify each request as one of four work types:

- **Project** — a container for sequenced work toward a product or business goal.
- **Discovery** — time-boxed work to understand, decide, design, rank, or de-risk.
- **MiniProject** — a complete, demoable improvement one engineer owns end to end.
- **Chore** — a small, specific, low-variance request. Stays in the fast lane.

Answer with the type and one sentence of reasoning.

## Closing out

When the user signals the session is ending, capture what you learned from it by
appending one entry to the improvement register:

```bash
python3 "$SKILL_DIR/scripts/register_append.py" --register register.jsonl \
  --type correction --learning "<what you learned>" --skill mp-classify
```

Types are correction, confirmation, preference, or pattern. A correction the user
made during the session is the most valuable thing to capture.
