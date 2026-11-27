---
kind: working
description: "Open items that are not tasks: questions, pending decisions, risks, assumptions to verify and things waiting on someone."
---
# Open items

One line per item, with a trailing attribute block: `- <text> {#o-<4 hex> type=question|decision|risk|assumption|waiting for=@name src=<path#Lnn>}`. Optional: `sev=high|med|low` (risks), `due=YYYY-MM-DD`.
- `type`: `question` needs an answer; `decision` needs a named decider; `risk` may hurt the project; `assumption` is to be verified before relying on it; `waiting` is blocked on someone outside the team.
- `for` is who it is addressed to. Add `by=@name` only when who raised it matters. `src` points at the evidence.
- Agents add an item instead of guessing (the no-invention rule in `AGENTS.md`).
- Resolved: record the outcome in its owning document (a decision becomes a record in `docs/decisions/`), then delete the line here and add a FINISHED line to your log. If something needs doing, add a task in `tasks.md` instead.
- Ids: 4 random hex characters, unused (`grep -r "o-abcd" .`).

## Open
- Example: who approves scope changes on the client side? {#o-0000 type=question for=@name}
