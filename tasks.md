---
kind: working
description: "Open tasks. Open items only; finished tasks are deleted and their outcome recorded elsewhere."
cadence: every-session
---
# Tasks

One line per task, with a trailing attribute block: `- <text> {#t-<4 hex> for=@name st=OPEN|STARTED|BLOCKED|INCOMPLETE touching=<path> requires=t-<4 hex>}`. Optional: `due=YYYY-MM-DD prio=high|med|low ms=m-<4 hex>`.
- `for` is who it is addressed to. Add `by=@name` only when who proposed it matters. `touching` names the area a `STARTED` task edits, so others avoid it. `requires` lists task ids that must finish first (finished tasks leave the file); `ws status` shows which tasks are ready. Keep the line current as you work (`session-state.md`).
- `BLOCKED` needs `reason=<words-joined-with-hyphens>`, or `reason=o-xxxx` when it waits on an open item (`_workboard/open-items.md`). `INCOMPLETE` needs the next action in the text.
- Finished: record the outcome in its owning document, then delete the line here and add a FINISHED line to your log.
- Ids: 4 random hex characters, unused (`grep -r "t-abcd" .`).
- Questions, pending decisions, risks and assumptions are not tasks; they go in `_workboard/open-items.md`.

## Tasks
- Example: write the kickoff summary {#t-0000 for=@name st=OPEN}
