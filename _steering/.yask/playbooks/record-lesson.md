---
kind: steering
module: lessons
use_when: "Record a lesson learned, or turn a repeated lesson into a check: retrospective, postmortem, a mistake or what went wrong, so it does not happen again"
description: "Record lessons per area, and graduate repeated ones into checks instead of prose."
---
# Record a lesson

1. Scaffold `docs/lessons/` if it does not exist (`scaffold.md`). Keep one file per area: `docs/lessons/<area>.md`, from `_steering/.yask/templates/lesson.md`.
2. Add one line: what happened and what to do instead, with `{#l-<4 hex> trigger=<when-it-applies> check=none st=open}`.
3. If the same lesson recurs, or it cost something real, graduate it: improve the playbook it belongs to (`write-playbook.md`) or add a check (a lint rule, hook, test or template line), then set `check=<path>` and `st=graduated`. Keep graduated lines short.
4. In `consolidation-pass.md`, prune: remove lessons that are no longer true and merge duplicates. A human decides.
5. A lesson is a claim, not a rule. If it must bind, record it as a decision.
