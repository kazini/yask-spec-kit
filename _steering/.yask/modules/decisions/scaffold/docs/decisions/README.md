---
kind: canon
description: How decisions are recorded. One decision per file; statuses, rules and where rejected options go.
---
# Decisions

One decision per file, with a stamped name (see `_steering/.yask/conventions.md`); use `_steering/.yask/templates/decision.md`. Generate the index with `ws decisions` or `ls`; do not maintain one by hand.

- Only a named decider's choice is `accepted`; agent output is `proposed`. Statuses: `proposed`, `accepted`, `deferred`, `rejected`, `withdrawn`, `replaced`.
- A replacement sets `supersedes: <old file name without .md>`; the old decision becomes `replaced`.
- Give each assumption a `revisit_when` trigger so it can be re-asked.
- Put rejected options in `rejected.md` so they are not proposed again.
- Use a weighted-criteria matrix only for contested, costly or irreversible choices.
- Check a status against reality before citing it.
