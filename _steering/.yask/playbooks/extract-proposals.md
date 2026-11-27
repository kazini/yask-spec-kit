---
kind: steering
module: meetings
use_when: "Turn raw material into proposals: pull action items, open questions or decisions out of it, mine meeting notes, transcripts, emails, chats or reports in a fresh context"
description: "Write evidence-backed proposals from one raw item without editing canon. `ws extract` automates it."
---
# Extract proposals

Tool: `ws extract`. Run this in a fresh-context worker or a separate session so the main session never loads the transcript (see `delegate-to-subagent.md`).
1. Input: one raw item (a meeting folder or a report). Read the summary first, then search the transcript for specifics. Read the transcript in chunks only if needed.
2. For each decision, open item, task or state change you find, write a file in `_workboard/proposals/` from `_steering/.yask/templates/proposal.md`. Give it a stamped name (`conventions.md`, Ids).
3. Every proposal cites its evidence as `path#Lnn` and has a `Not found` section. Check that each anchor exists and contains what you cite.
4. Mark confidence. Mark anything uncertain `low`. Do not fill gaps by guessing.
5. Never edit canon, `status_log.md` or `tasks.md`. Extraction only proposes.
6. Return a list of the proposals you wrote, with their paths and one line each.
