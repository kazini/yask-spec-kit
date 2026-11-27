---
kind: steering
module: collab
use_when: "Commit and push your changes, a file or a docs folder: save work, sync with a remote, or share a branch for review"
description: "Commit only the paths you touched, then push or sync under the project's path policy."
---
# Save and push

Git only keeps the history. `ws` snapshots uncommitted work, settles merges and tracks who must read what while it runs (`collaborate.md`).
1. Save: `ws save [paths] -m "<area>: <what changed>" --apply`. It commits to whatever is checked out, only the paths you name, refuses secrets, and adds `Ws-Task` and attribution trailers (`git.ai_attribution`: `none`, `trailer`, `co-author`; set it from the client's contract, not by habit). Add `--agent` when you are the agent.
2. Share: `ws sync` commits what is left, merges the remote, settles conflicts by rule, and pushes (again, if the remote moved).
3. Never force-push; a history rewrite is only ever `purge-history.md`.

Without `ws`: `git status`; add paths by name, not `-A`; scan the diff for the patterns in `_steering/.ws/redaction.yaml`; commit as above; `git pull --no-rebase`; push; check `git log origin/<branch> -1`.
