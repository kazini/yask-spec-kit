---
kind: steering
module: collab
use_when: "Start, resume, work through or hand off a session, or pick up where the last one left off: keep status, tasks, open items and the log current so any session can stop or continue"
description: "Session lifecycle: resume from files on disk, record state as events happen and leave a fresh session able to continue."
---
# Session state

Tool: `ws start` prints the resume state. Manual steps:

## Start or resume

- `git fetch`, then `git status`. If behind, `git pull --no-rebase` before editing; never rebase shared work. Scaffold `_workboard/people/<you>/` if absent.
- Read `status_log.md`, `tasks.md` (your items and any `STARTED` first) and `_workboard/open-items.md`. Check `docs/decisions/rejected.md` before proposing alternatives.
- Read the last log lines (`ws log --last 20`, or the newest files in `_workboard/people/*/log/`). See what changed since your last log line; read changed documents' descriptions, not whole files.
- Verify each `STARTED` item of yours against its `touching` path and git changes. Run `ws sweep` if `ws start` lists leftovers. A `STARTED` item with no log line within `tasks.stale_started_hours` (`_steering/.ws/config.yaml`) is stale: continue it or mark it `INCOMPLETE` with a note.
- Before editing an area a partner's `STARTED` task touches, ask or coordinate.
- Say in one short paragraph what changed, what is yours and what is stale. Ask only about what blocks you.

## Keep state current

Tools: `ws task`, `ws item`, `ws log add`, `ws save`. Update when the event happens, not later.

| When | Do |
|---|---|
| You start a task | `tasks.md`: `st=STARTED`, `for=@you`, and `touching=<path>` if others may edit that area; log `STARTED` |
| You learn the next step, or stop midway | `tasks.md`: next action in the text, `st=INCOMPLETE` if you stop |
| You are blocked | `st=BLOCKED reason=<words>` (or `reason=o-xxxx` with an open item); log `BLOCKED` |
| A question, risk or assumption appears | `_workboard/open-items.md` with a `type` |
| Something is decided | the decision record (`record-decision.md`); `status_log.md` if status or a standing direction changed |
| A result exists | the owning document; then finish the task: delete the line, log `FINISHED` with the outcome path |
| Work for someone else appears | a task or open item with `for=@them` |
| Anything else a fresh session should know | a log `note` line |
| A log line is wrong, or several lines say one thing | `ws log set <id> "..."`, or `ws log add "..." --folds <ids or t-xxxx>`; never add a line that contradicts an earlier one |

Long commands (tests, builds, scans) expected to run more than a moment write stdout/stderr to a scratch `.log` path and record that path with the exit code in the session note; the command can then run in the background with only a console. The log is evidence for the next session, not canon: scrub secrets and delete it when done.

Commit as you go (`save-and-push.md`): uncommitted work is invisible to a session on another machine.

Test: from `status_log.md`, `tasks.md`, `_workboard/open-items.md` and the last log lines alone, could a fresh session continue exactly here?
