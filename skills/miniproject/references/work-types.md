# Work types

Classify before estimating or splitting. The four types have different outputs
and should not share one lifecycle.

| Type | Use it for | Required result |
|---|---|---|
| Project | A larger product or business goal that needs sequencing | A shaped sequence of Discovery and delivery work |
| Discovery | A bounded effort to reduce uncertainty before building | A decision artifact and explicit terminal outcome |
| MiniProject | A complete improvement one owner can carry through release | A demoable, launch-ready behavior change |
| Chore | A small, specific, low-variance request | The requested correction or maintenance result |

## Classification cues

- Choose **Chore** when the request is already specific, has little coordination
  risk, and does not need product shaping.
- Choose **Discovery** when a question must be answered before a responsible
  delivery boundary or approach can be chosen.
- Choose **MiniProject** when the improvement is clear enough to answer all four
  bundle criteria and one owner can carry it end to end.
- Choose **Project** when the goal contains multiple improvements or unresolved
  sequencing decisions.

Do not classify a frontend, backend, database, infrastructure, or test-only slice
as a MiniProject merely because it is technically coherent. A MiniProject boundary
describes the improvement that can be demonstrated and made safe to release.

## Discovery contract

Discovery is a first-class, time-boxed work item. Record:

- the **question** it must answer;
- the **owner** responsible for producing the answer;
- the **time box** controlling the investment;
- the **decision artifact** that makes the result inspectable; and
- one terminal outcome.

The terminal outcome is exactly one of:

1. **Ready to shape** as a MiniProject or Chore.
2. **More Discovery** is required, with the next question stated.
3. **Stop**, with the reason recorded.

Do not estimate Discovery as implementation and do not force it through a
delivery lifecycle. Its completion evidence is the decision artifact and terminal
outcome, not shipped code.
