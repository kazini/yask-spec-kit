---
kind: canon
description: Milestones in date order. One line each; tasks reference them with ms=m-xxxx. Outcomes, not activities.
---
# Roadmap

One line per milestone: `- <outcome> {#m-xxxx due=YYYY-MM-DD st=OPEN}`. New id: `ws id m`. Create this file with `ws scaffold docs/roadmap.md --apply`. `st` is `OPEN`, `DONE` or `SLIPPED`; change it with `ws label set m-xxxx st=DONE`. Tasks join a milestone with `ws task add "..." --ms m-xxxx`. `ws status` shows each open milestone, its open tasks and whether it is overdue.

If a milestone moves, say why in `status_log.md` or a decision record; this file holds only where things stand.

## Milestones
