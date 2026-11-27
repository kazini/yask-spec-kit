---
kind: steering
module: core
use_when: "Archive or retire old material: clean up, move out of the way, expire, delete after its retention period, free space, or a document, folder or raw file is stale, obsolete or no longer needed"
description: "Move retired material to `.archive/`, offload heavy files and apply its retention period."
---
# Archive and retention

Three operations. Do the cheapest one that solves the problem.
- **Archive** (`ws archive <path>`): the item moves to `.archive/` with the same relative path, as a fresh file, and its history is deleted from git. This rewrites history: it needs the preconditions in `purge-history.md` and a person's go-ahead. `ws related <path>` lists what points at it first.
- **Offload** (`ws git offload`): heavy or sensitive files go to cold storage outside git. Record path, `sha256sum`, size, location and retention in `.archive/manifest.md` and leave a stub. History is untouched.
- **Compaction**: `git maintenance start`, or `git gc`. Deletes nothing reachable.

## Archive steps
1. Clean working tree. Tell everyone who shares the repository: they must re-clone after the forced push.
2. `ws archive <path>` (dry run): lists the item, inbound links, the backup and the commands.
3. `ws archive <path> --apply --yes-rewrite-history`: writes a verified bundle of the full history to `_steering/.ws/backups/`, copies the item to `.archive/<path>`, removes the item's history from every branch and tag (`git filter-repo` if installed, else `git filter-branch`), expires reflogs, collects garbage, points citations and links in your documents at the archived copy (`--keep-citations` skips this), and commits the archived copy as new content.
4. Force-push yourself (`git push --force --all`, then `--tags`), and have everyone re-clone. Ask the git host to run garbage collection and clear cached views.
5. Delete the backup bundle once you have verified the result: it still contains the old history.

By hand: copy the item to `.archive/<path>`; `git filter-repo --force --invert-paths --path <path>` (or `git filter-branch --index-filter 'git rm -r --cached --ignore-unmatch <path>' -- --all`); `git reflog expire --expire=now --all && git gc --prune=now`; add and commit `.archive/<path>`.

## Retention
`ws retention` lists raw items past their period and the command for each (it only plans: archiving rewrites history).
`_steering/.ws/retention.yaml` sets, per kind, how long an item stays in the tree, what falls due then (`then:`), when it goes cold, and when a history purge is considered. Set it when the kind is created, from the client's contract. Log each step you take.
`then:` is `review` by default: the item is listed and a person decides between keeping it, offloading it, or archiving it. `offload` plans cold storage and leaves history alone. `archive` plans `ws archive`, which deletes history and makes every collaborator re-clone: choose it only when a contract or law requires the deletion, never because a period has passed. An unknown value is read as `review`.

## Prevent instead of purge
Redact at ingest. Keep heavy raw files out of git from the start. Never cite commit hashes in documents.

## Clone size
Partial or shallow clones (`--filter=blob:none`, `--depth`) give light working copies without destroying anything.
