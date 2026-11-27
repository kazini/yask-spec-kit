---
kind: steering
module: meetings
use_when: "Approve and file a proposal: accept, edit or reject an extracted proposal and put it in its owning document"
description: "File a human-approved proposal with provenance; record rejected options. `ws promote` automates it."
---
# Promote a proposal

Tool: `ws promote`. A human approves, edits or rejects each proposal first.
1. Approved decision: follow `record-decision.md`.
2. Approved open item (question, pending decision, risk, assumption, waiting): add a line to `_workboard/open-items.md` with `type`, `for=@name` and `src`.
3. Approved task: add a line to `tasks.md` with `for=@name` and an id.
4. Approved knowledge or state change: write it into the owning canon document (or `status_log.md`, replacing the old text). Add `derived_from` or an `src=` label pointing at the raw source. Replace outdated text rather than appending beside it.
5. Set the proposal's `status` to `approved`, `edited` or `rejected`. Record a rejected option in `docs/decisions/rejected.md` if it is a rejected alternative.
6. A canon edit an agent committed waits for a person to read it: `ws approve` lists it, and your own commit of the file counts (see `collaborate.md`).
7. Leave the proposal in place; it is moved to `.archive/` after the retention period.
