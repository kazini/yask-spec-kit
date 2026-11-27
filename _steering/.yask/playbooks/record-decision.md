---
kind: steering
module: decisions
use_when: "Record or change a decision someone with authority made: agreed, chosen, approved, dropped or reversed; an agreed change to scope, a budget, or a deadline or launch date (postpone, push back, move), or to an approved requirement"
description: "Write a decision with its decider, status, options and assumptions; an agent never accepts one on its own."
---
# Record a decision

1. Copy `_steering/.yask/templates/decision.md` (or `_steering/templates/decision.md` if the project has its own copy) to `docs/decisions/<stamped name>.md` (`conventions.md`, Ids). The file name is the id. Set `description`, `proposed_by` (if it matters) and `derived_from`.
2. Fill Context, Options, Consequences and Assumptions. Each assumption gets a `revisit_when` trigger.
3. Leave `status: proposed` until the named decider confirms. Then set `status: accepted` and `decider: <name>`. An agent never sets `accepted` on its own.
4. If it replaces an earlier decision, set `supersedes: <old file name without .md>` and set the old decision's `status: replaced`.
5. Copy each rejected option to `docs/decisions/rejected.md`.
6. If it governs current work, set `governing: true` in its front matter (and `false` when it stops). Do not list it anywhere else; `ws decisions --governing` derives the list.
7. Use a weighted-criteria matrix only for contested, costly or irreversible choices.
8. Check every status against reality when you cite it.
