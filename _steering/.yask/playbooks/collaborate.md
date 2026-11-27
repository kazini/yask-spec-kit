---
kind: steering
module: collab
use_when: "Coordinate concurrent work: another person or agent is editing the same file, merge changes, or get your changes read"
description: "Avoid clobbering shared work: claim areas, merge with tests, and request review of canon and steering."
---
# Collaborate

Git only keeps the history. Coordination between people and agents is `ws`'s, and it happens by itself while `ws` runs: nothing is claimed, released, labelled or routed by hand before you change something.

## What happens automatically
- **Writes are serialised.** `ws` edits its shared state files under a short lock it holds itself; logs are appended.
- **Git exists.** If the folder is not a repository, `ws` creates one and commits what is there (`lifecycle.git`).
- **Your work is never only in the working tree.** Uncommitted changes are snapshotted every few minutes into a small rolling set kept outside your branch (`lifecycle.autosave_keep`, default 3, spaced so they differ as much as possible; not in `git log`, never pushed, cleared by your next commit). A file got deleted or overwritten: `ws restore` lists them and `ws restore <path> --apply` brings it back. Files that look like a secret are left out.
- **A merge that stopped on conflicts is finished by rule** the next time `ws` runs (`lifecycle.heal`), or by `ws sync`: tasks, open items and logs merge by id; generated blocks are regenerated; for a real conflict in a document the shared version stays and your copy is set aside in `_workboard/conflicts/` with an open item for you.
- **Leftovers close themselves**: tasks the log says are finished, and `STARTED` tasks nobody touched (`lifecycle.sweep`).
- **Review is worked out from the history.** A person's own commit of a canon or steering file counts as their review. Changes an agent committed (`ws save --agent`) wait: `ws start` counts them and `ws approve` lists them; `ws approve <paths>` or `--all` records that you read them (`git.review`: `agent`, `all` or `off`).

## Two copies and a shared remote
Run `ws sync`: it commits what is uncommitted, merges the remote, settles conflicts as above, and pushes (again, if the remote moved meanwhile). Several agents in one checkout tell themselves apart with `WS_AGENT=<name>` (commits are authored `<you>+<name>`).

## Rules
- Single-writer paths: everything personal is under `_workboard/people/<name>/`.
- One file per shared item (meetings, decisions, proposals), with collision-free ids.
- Generated views are not hand-edited.
- Read your partners' `STARTED` tasks before editing a shared area. A `STARTED` task with no log line for `tasks.stale_started_hours` is parked by `ws`; take it over with a log note, or ask.
- History is rewritten only by `ws archive` and `ws git purge`, with a freeze (`purge-history.md`). `ws squash` may tidy your own unpushed commits.

## What changed
`git log --oneline --since=<UTC time of your last log line>` and `git diff --stat` for that range, grouped by folder. Read `description` lines, not whole files.

## If conflicts keep happening
`tasks.md` and `_workboard/open-items.md` are single files. If `ws check` keeps reporting duplicate ids in either, split it into one file per item. Optional hooks (`ws hooks install`) refuse a staged secret or conflict marker; `--no-verify` skips them once.
