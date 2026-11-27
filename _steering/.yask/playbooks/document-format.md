---
kind: steering
module: knowledge
use_when: "Write a document or decide where a fact belongs: which folder or file holds a glossary, background or notes; placement, short writing, shorten, condense or make a document shorter, edit hygiene, links and cites, file names"
description: "Document format: one home per fact, compressed writing, status marks, dates, edit hygiene and stable names."
---
# Document format

Use this when writing a document or deciding what goes where. `document-handling.md` routes the other document modules; `document-thinking.md` covers register and ambiguity, `document-method.md` covers change and review.

## One home per fact

- Each kind of fact has one owner; `AGENTS.md` maps owners and is not repeated elsewhere. A fact that fits two homes goes in the first named and is pointed to from the other.
- Where documents disagree, cite both and say which you followed; settle in the owner, leave a one-line pointer elsewhere, and record the conflict with open items until closed.
- At a session's end, turn duplicated facts into pointers and settle live-state conflicts against the state document.
- Why: two homes drift apart and the reader cannot tell which is current.

Status marks say what a claim is:

- *(user)*: a settled decision of the user; only the user's decisions are settled.
- *(proposal)*: every other design choice. On confirmation, drop the marker, log it and remove it from the pending list.
- **open**: analysis, options or hypotheses, not a decision.
- **reference**: informs, does not bind.

A project may add labels (*binding*, *aspirational*, *working*, *steering*, *state*, *navigation*) and lists them in `AGENTS.md`.

## Short writing

These rules apply to playbooks, READMEs, specs and guides; a project rule may narrow them.

- Compress, don't merely cut: keep the decision, the reason and the next action; drop restatement, edit history, hedging and examples that repeat the rule.
- Summary first, depth on demand. One fact, one home; link instead of repeating.
- Prefer prose or bullets. Number only steps whose order matters and items other text cites by number: stable ids, or a playbook's sections when other files cite them by number. Avoid numbered sections and long numbered lists otherwise (`conventions.md`), and skip them where the order is self-evident or irrelevant.
- Use imperative voice. Give the reason for a non-obvious rule in a short clause so a reader can extend it.
- One term per concept, defined once. No "as above", dated banners or narration of the edit.
- A folder `README.md` is one page: what the folder is for, who owns its facts, and where to look next.
- Test: a fresh reader can act from the shorter text without opening the old one.

## Roles and where a fact goes

A project omits roles it does not need. A new fact goes to the role that receives it; one that fits two follows one-home-per-fact.

| Role | Holds | Receives |
|---|---|---|
| Entry (`AGENTS.md`) | goal, rules, reading order, first commands, document map; no state or procedures | |
| State (`status_log.md`) | current stage, standing directions, focus; then the dated log | user decisions and results governing the next step |
| Handoff | where the last session stopped (one, replaced each session), resume commands | procedures and lessons |
| Tasks | open tasks and pending user decisions only | every new task or open question |
| Report | consolidated results with sources | results |
| Notes or spec | design, reasoning, definition of success | design reasons |
| Glossary | the goal in plain words; wording rules | |
| Tool readme | how a shared tool works | that tool's procedures and lessons |
| Archive | verbatim history; never read at startup | |

A cross-project directive goes in shared steering.

## History and dates

- Dates and times appear only in the log, in the project's format, taken from the system clock and never typed by hand.
- Other documents carry no dates, no "rewritten", "condensed" or "replaces the earlier" banners, and no status narration.
- With version control, commit before a large rewrite and commit documentation with related changes under descriptive messages. Without it, archive verbatim (`<archive>/<what>_<timestamp>.md`), add an index line in the log, and leave a stub where the text stood if anything cites its section.

## Edit hygiene

Every edit:

- Check who else is editing, keep a backup, change the document in one read-modify-write step, and do not restructure a document another session is editing.
- Curate as you add: remove superseded, finished or redundant text in the same edit.
- Replace status that a later fact supersedes; compare a status text with the live state before trusting it.
- Finished work leaves status and tasks; its outcome lives in the owning document or log.
- Keep startup documents short; read large specifications on demand.
- Give a suggestion a brief mention with the reason it might help; do not evaluate it until needed.
- Never write a hand-typed timestamp, diary narration about tooling or documentation work in a run log, or a secret.

## Writing and optimizing

Before writing or changing, ask who reads it and when, what decision or action it supports, what behavior it encourages or constrains, and what would be lost if specific elements changed.

A new document states its existing coverage, owner, register and open items, with reasons attached to non-obvious rules and one short labelled example where a rule would be misread. `document-method.md` handles the change process.

An existing document is optimized by mapping its ecosystem and role, consolidating rather than eliminating, keeping the essential examples and validation mechanisms, then verifying by cold read and one real task.

| Content type | Best format |
|---|---|
| Direct instructions (rules, safety measures, format requirements) | bullets, numbered steps, checkboxes |
| Thinking patterns (strategies, conceptual guidance, frameworks) | structured explanation, conditional logic, hierarchy |
| Reference information (templates, patterns, examples, specifications) | complete examples, templates, catalogs |

Read the whole document before you restructure, summarize, extend or contradict it (`document-method.md`).

## Links, cites and names

- Use descriptive link text and relative paths. Validate every link at each documentation change; a broken link is a high-priority fix.
- Cite by stable id or named section, never by position. Identifiers are unique and never reused; a retired item leaves a stub that keeps its id.
- After moving, renaming or merging documents, update the map, any index and every cite before committing.
- Where things must trace to each other (requirements to design to tests, claims to sources), keep the trace in both directions.
- Names are specific, never generic; a file name says what it owns.
