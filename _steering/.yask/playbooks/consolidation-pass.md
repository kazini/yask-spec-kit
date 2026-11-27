---
kind: steering
module: core
use_when: "Periodic cleanup or structure review: tidy up, audit, spring clean, find duplicate, stale, contradictory or drifting documents"
description: "Periodic cleanup and structure review: sizes, orphans, duplicates, stale items, lessons. Report, then ask before restructuring."
---
# Consolidation pass

Run every few weeks, or when `ws review` reports a trigger. Tool: `ws review`, `ws check`, `ws dupes`. Manual checks (adjust the shell for your OS):
1. Size: `find docs -name '*.md' -size +25k`. Read what you find by section; split it only if it mixes topics.
2. Orphans: canon documents not linked from a folder `README.md` or the map.
3. Duplicates: repeated headings (`grep -rh '^#' docs | sort | uniq -d`) and the same fact in two places. Keep it in its owner and link from the other.
4. Stale: documents past `review_by`, or untouched for a long time (`git log -1 --format=%cs -- <file>`).
5. Open items older than the threshold in `_steering/.ws/config.yaml`. Decisions with no follow-up task. Requirements with no task.
6. Raw material past its retention period: see `archive-and-retention.md`.
7. Lessons or rules that repeat: turn them into a check instead of prose. Work that sessions keep re-deriving (the same steps or scripts): make it a playbook (`write-playbook.md`) or a tool in `_tools/`.
8. Write the findings as a short report in `_workboard/reports/`. Do not restructure on your own; propose and ask.
