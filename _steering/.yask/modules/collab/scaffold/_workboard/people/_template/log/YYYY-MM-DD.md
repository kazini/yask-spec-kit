---
kind: personal
description: "Append-only log for one person and one UTC day, in the status-line format."
---
# Log YYYY-MM-DD

Format: `- <UTC stamp> @<name>[+agent] (<type>): <text> {<4 hex>}`. Types: note, STARTED, FINISHED, INCOMPLETE, BLOCKED.
When a task finishes, replace its earlier lines with one FINISHED line.

