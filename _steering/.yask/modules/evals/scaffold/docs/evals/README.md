---
kind: canon
description: "Test cases for the workspace itself. One file per case; cases are never edited to make them pass."
---
# Evals

One file per case, from `_steering/.yask/templates/eval-case.md`; procedure: `run-evals.md`. Write a case when an agent:

- proceeds without confirmation or runs past a gate;
- claims completion without evidence or reports a guess as verified;
- leaves finished work in `tasks.md`, skips the log line, fails to update `tasks.md` or the log as it works, or resumes without checking git;
- cites raw evidence as settled canon, invents a role, amount or agreement instead of adding an open item, or resolves conflicting sources silently;
- reads a whole transcript instead of searching or delegating;
- closes a decision without a named decider, or revives a rejected option;
- records agent-written canon as read when no person has read it.
