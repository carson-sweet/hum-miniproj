---
name: mp-rules
description: Use when bundling work into MiniProjects, estimating Discovery or Chores, judging whether a proposed piece of work is a complete improvement, or recording a bundle decision.
---

# MiniProject working rules

A probe instruction set for P0.2. Three governing rules, each on one line so a
mutation can remove all of a rule's content without leaving a restatement behind.
This is not the MiniProject skill — that is authored in Phase 2.

## Rule 1

RULE-EST: Never give an effort estimate for a Discovery item; Discovery is time-boxed to a decision, an approach, or a next step, while Chores and MiniProjects are estimated normally.

## Rule 2

RULE-BUNDLE: A partial technical layer is not a MiniProject, so if a proposed bundle is only frontend, only backend, only data, or only QA, say plainly that it is not a MiniProject and name what makes it incomplete.

## Rule 3

RULE-RECORD: When asked to record a bundle decision, run `python3 "$SKILL_DIR/scripts/record_bundle.py" --out . --name "<bundle name>"` to write the record, and never hand-write the record file yourself.

## Rule 4

RULE-OWNER: A MiniProject has exactly one owner who carries the whole path, so never propose splitting a MiniProject across multiple engineers to parallelize it, even when the work spans several technical layers and the team is behind schedule.
