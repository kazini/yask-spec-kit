---
kind: steering
module: core
use_when: "Remove something from git history (stop and ask first): a secret, large file or personal data was committed, rewrite or filter history, force-push"
description: Guarded procedure to remove content from git history. Manual, human-approved, agents may only prepare the plan.
---
# Purge from history

Stop and ask. This rewrites history, cannot be undone, and breaks every existing clone. Use it to remove content without keeping a copy; `ws archive` runs the same procedure for retired material and keeps a copy in `.archive/`. Agents prepare the plan only; a named human runs it with `--yes-rewrite-history`.

## Preconditions (all must hold)
- A. Reason: recorded (exposed secret, personal-data erasure, contractual deletion, an accidental heavy binary, or retirement of material); cheaper options ruled out; any exposed credential already rotated; other copies handled (git host, CI caches, partner clones, backups, model-provider logs).
- B. Scope: exact paths or blob ids with a dry-run of the impact; needed content stored in cold storage with a matching hash, or declared disposable; no document cites commit hashes; documents linking to the targets listed.
- C. Safety: a mirror or bundle taken, verified and restore-tested, with its location, checksum and destruction date recorded; the rewrite runs in a throwaway fresh mirror clone, never a working clone; the toolchain is present (a recent Git, Python 3 and `git-filter-repo`).
- D. Coordination: collaborators listed and a freeze window acknowledged by each; open pull requests and branches listed with owners; branch-protection state recorded, with who lifts and restores it; agents refused from pushing during the window; downstream pins listed.
- E. Approval: the approver is not the requester (client approval if the contract requires it).

## After
- F1: verify in a fresh clone that the targets are absent from all refs and checks pass.
- F2: force-push all branches and tags; ask the git host to garbage-collect and clear cached views.
- F3: everyone re-clones; keep a tombstone list so CI fails if the purged content reappears.
- F4: write a ledger entry (what, why, who approved, old and new tips); destroy the backup on schedule. The backup still contains the purged data, so restrict its access.

## Known facts
`git filter-repo` requires a fresh clone by default, the rewrite is irreversible, and collaborators must re-clone or hard-reset. A collaborator who pushes work based on the old history silently reintroduces the removed content. Check your git host's own removal process; hosts may keep cached views and pull-request refs.
