---
kind: steering
module: knowledge
use_when: "Place a fact, keep history, edit cleanly, or check links and cites (Part III): where does this go, front matter, formatting, broken links, citations, naming a file"
description: "Documentation framework, Part III (Format): one home per fact, roles, history and dates, edit hygiene, writing and optimizing documents."
---
> Part III of the documentation framework. Start at `document-handling.md`.

## Part III: Format

The rules for a project's record. Documents are a project's memory and the first thing a fresh session pays for in context; they stay useful only if each fact has one home.

### III.1 One home per fact

- Each kind of information has one owning document; the project's map (in `AGENTS.md`) says which and is not repeated elsewhere.
- A fact that fits two homes goes in the first named and is pointed to from the other.
- Where two documents disagree, cite both, settle it in the owner, leave a one-line pointer in the other, and record the conflict where open items live until settled. Say which one you followed.
- At the end of a session, check overlap: a duplicated fact stays in its owner and becomes a pointer; documents that disagree about the live state are settled against it; the state document wins over notes on run state.

*Why:* two homes drift apart, and the reader cannot tell which is current.

**Status marks.** A statement says what kind of claim it makes. Default set:
- *(user)*: a settled decision of the user. Only the user's decisions are settled.
- *(proposal)*: anything else that is a design choice. On confirmation: remove the marker, log it, drop it from the pending list.
- **open**: analysis, options, hypotheses; not a decision.
- **reference**: informs, does not bind.

A project may add labels (for example *binding*, *aspirational*, *working*, *steering*, *state*, *navigation*) and lists them in its map.

### III.2 Roles and where a fact goes

Avoid unnecessary documents; a project omits the roles it does not need. A new fact goes to the role that receives it; one that fits two follows III.1.

| Role | Holds | Receives |
|---|---|---|
| Entry (`AGENTS`) | goal, rules, reading order, first commands, the document map; no state, no procedures | |
| State | stage, latest results, governing decisions (facts, not diary); then the dated log | user decisions and rules that govern the work; one line for a result that governs the next step |
| Handoff | where the last session stopped (one, replaced each session), resume commands | procedures and lessons |
| Tasks | open tasks and pending user decisions only | every new task or open question |
| Report | consolidated results with their sources | results |
| Notes or spec | design, reasoning, definition of success | design reasons |
| Glossary | the goal in plain words; wording rules | |
| Tool readme | how a shared tool works | that tool's procedures and lessons |
| Archive | verbatim history; never read at startup | |

A cross-project directive goes in the shared steering document.

*Why:* a fixed home makes a fact findable by a fresh session with no memory of where you put it.

### III.3 History and dates

- Dates and times appear only in the log, in the project's format, taken from the system clock and never typed by hand.
- Other documents carry no dates, no "rewritten", "condensed" or "replaces the earlier" banners, and no status narration.
- With version control, it is the history and the tree keeps no copies of superseded documents; commit before a large rewrite, and commit documentation with related changes under descriptive messages. Without it, archive verbatim (`<archive>/<what>_<timestamp>.md`), add an index line in the log, and leave a stub where the text stood if anything cites its section.

*Why:* stale duplicates and dated banners mislead agents into treating old text as current.

### III.4 Edit hygiene

Length has no cap; hygiene is the standard: one home per fact, no stale or duplicated text, the right placement. Every time you edit a document:
- [ ] Check who else is editing; keep a backup (version control or a backup folder); change the document in one read-modify-write step; do not restructure a document another session is editing.
- [ ] **Curate as you add:** check whether older text is now superseded, finished or redundant, and remove or archive it in the same edit.
- [ ] **Replace, don't append** for handoffs, stage and active-run lines, and any status a later fact supersedes; compare a status text with the live state before trusting it.
- [ ] **Finished work leaves the document:** delete a finished task at once (no "done" list); its outcome lives in the report, specification or log.
- [ ] **Placement and size:** startup documents (entry, state, tasks) stay short; large specifications are read on demand, one part at a time.
- [ ] **Suggestions** (candidate tools, options) get a brief mention with the reason they might help, and are not evaluated until needed.
- [ ] **Never write** a hand-typed timestamp, diary narration, tooling or documentation work in a run log, or a secret.

### III.5 Writing and optimizing documents

**Purpose analysis.** Before writing or changing anything, understand:
- **Reader and moment:** who reads it, and when (startup, on demand, once).
- **What cognitive work** does the document enable, and **what decision or action** does it support?
- **What behaviors** does it encourage or constrain?
- **What would be lost** if specific elements were changed (an existing document)?

**A new document:**
- [ ] **Existing coverage:** searched for a document that already owns this (II.3).
- [ ] **Owner:** which facts live here, which are pointers (III.1).
- [ ] **Register, format and open items** chosen per part, each open item with its reason (I.1, I.6).
- [ ] **Reasons** attached to non-obvious rules; one short labelled example where a rule would be misread (I.3).
- [ ] **Placement and size:** startup or on-demand (III.4).

**An existing document:**
1. **System analysis:** map the document ecosystem, where information is distributed, and cross-document coherence.
2. **Document analysis:** role, content types and formats, the format-meaning relationship.
3. **Gentle optimization:** consolidate rather than eliminate; streamline while preserving structure; keep the essential examples and validation mechanisms.
4. **Verification:** a cold read (hand the document alone to a fresh reader and check that they can act correctly); re-ask the purpose-analysis questions; compare one real task before and after.

| Content type | Best format | Reading before a change |
|---|---|---|
| Direct instructions (rules, safety measures, format requirements) | bullets, numbered lists, checkboxes | bounded change: the item, its section, a search for every other mention |
| Thinking patterns (strategies, conceptual guidance, problem-solving frameworks) | structured explanation, conditional logic, hierarchy | the whole document and its dependencies |
| Reference information (templates, patterns, examples, specifications) | complete examples, templates, catalogs | lookup: targeted; updating interconnected elements: full review |

Whatever the type, read the whole document before you restructure, describe, summarize, extend or contradict it (II.3).

**Links, cites and names**, for any document:
- Use descriptive link text and relative paths.
- Validate links at every documentation change; a broken link is a high-priority fix. Check mechanically: every link resolves, every cited `file § section` exists as a heading, tables and lists are well formed.
- Cite by stable id or named section, never by position. Identifiers are unique and never reused; a retired item leaves a stub that keeps its number.
- After moving, renaming or merging documents, update the map, any index and every cite before committing.
- Where things must trace to each other (requirements to design to tests, claims to sources), keep the trace in both directions.
- Names are specific, never generic; a file name says what it owns.
