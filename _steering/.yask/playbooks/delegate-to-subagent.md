---
kind: steering
module: core
use_when: "Hand a large read or exploration to a fresh-context worker, or split work across subagents: too much to read yourself, a long document, PDF or report to summarize or summarise, parallel workers, offload research"
description: "When and how to hand a large read to a fresh-context worker: a fixed contract, a report file, and checks the parent runs."
---
# Delegate to a subagent

## When
Delegate when the input is large and the output small: transcript extraction, codebase exploration, test-failure summaries, shortlists of duplicates. Do not delegate when judgment needs the main conversation's context, when the task is small enough that overhead exceeds the saving, or when a summary would lose needed detail. Delegation protects the main context but adds total cost.

## Report shape
A report is dense evidence, not a transcript: one bullet per finding with claim, `path:line`, short quote and confidence; keep `Not found` and `Limits`. Length follows the task; do not pad to a byte target. Use the cap the parent sets; raise it only with a reason in `Limits`, up to 24 KB, and split above that. Split only along topic boundaries: one general report links to detail reports, each using the template and fixed sections; do not duplicate findings. Apply `document-format.md` short writing to report prose.

## Steps
1. `ws delegate "<task>" --inputs <paths> --cap <bytes> --steps <n>` prints the worker contract and allocates the report path. Give the worker all of it. Without the tool, state the same: exact inputs, one output file in `_workboard/reports/` from `_steering/.yask/templates/report.md`, findings with `path:line` evidence and a short quote in double quotes, a Not found section, a length cap, a step budget, read-only elsewhere.
2. The worker logs milestones with `ws log add --agent --task <id> "<text>"`, so you read progress instead of polling.
3. When it returns, run `ws report check <report> --cap <bytes>`. It verifies the sections, the length, that every cited file and line exists, that each quote is on its cited line, and that nothing changed outside the report. Without the tool, spot-check three citations and run `git status`.
4. Treat the report as evidence, not canon. Verify a sample before acting on it.

## Parallel workers
Each worker gets its own report file, so nothing collides. If the tool has no subagents, run the same contract in a separate session and hand back the report file.
