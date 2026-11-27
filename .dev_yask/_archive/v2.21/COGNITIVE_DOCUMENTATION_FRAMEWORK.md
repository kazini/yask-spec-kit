# Documentation Framework

How a project's documents and instructions are thought about, written, edited and kept consistent. The file follows its own advice: summary first, depth in layers, each theme in one place, reasons with the rules.

A project's `INIT.md` holds its own document map, names and exceptions, and wins where it says so. Rules that are not about documents (sandbox, machines, secrets, tools) live elsewhere. Software projects add [SOFTWARE_DOCUMENTATION_GUIDELINES.md](SOFTWARE_DOCUMENTATION_GUIDELINES.md).

## In short

1. Format is meaning: choose structure by how the reader will use the information.
2. Match the register (the precision of the language) to the cognitive work: rigid where error is costly, invitational where judgment is wanted.
3. Ambiguity is allowed only on purpose: say what it is for, or close it.
4. Give the reason with the rule; a reader who knows why can extend it to cases it never named.
5. Understand a document's purpose, and what would be lost, before restructuring; consolidate rather than eliminate.
6. Each fact has one home; everywhere else points to it.
7. Read a document whole before you describe, change or contradict it; the documents are the record.
8. Only the user's decisions are settled; mark everything else as a proposal.
9. Verify a change by cold read: a fresh reader holding only the document should be able to act correctly.
10. Notice when you agree, mirror or elaborate out of habit rather than need.

## Where to read

| If you are | Read |
|---|---|
| writing a new document | I.1, I.3, I.6, II.3, Part III |
| changing or optimizing one | I.2, III.5, III.4 |
| deciding how strict or open to be | I.6 |
| checking your approach in a conversation | I.4, II.1 |
| keeping a project's record consistent | II.3, Part III |

Before a major rewrite, or on first use, read Parts I and II whole, and III.5.

---

## Part I: Cognition

How to think about documents and instructions. No procedures here; they are in Parts II and III.

#### Format as Meaning
Format is instruction, not decoration. The structure of information directly shapes how agents process and apply it. A checklist signals verification requirements; a decision tree indicates branching logic; sequential numbering implies order of operations. When we change format, we change meaning.

#### Precision as Purpose
Language precision should match cognitive demands. Safety-critical operations require rigid language that prevents misinterpretation. Creative processes require flexible language that enables adaptation. The precision level signals to agents how much interpretation is expected and appropriate.

#### Ambiguity as Tool
Strategic ambiguity enables intelligent behavior. When we want agents to apply judgment, consider context, or explore possibilities, ambiguous language invites the cognitive engagement that rigid commands would suppress. The key is intentional ambiguity in service of purpose, not accidental vagueness.

Its operational twin is purposeful vagueness:
- Do not specify what need not be determined yet. Record it as open; the vagueness is deliberate, not a gap.
- No detail ahead of need: a document grows when a decision or an implementation needs it.
- Test: can you say what the ambiguity is *for*? If you can, it is a tool. If you cannot, it is a gap: close it.

### Judgment in change

- **Understand before restructuring.** Optimization starts from what the document is trying to achieve; reorganizing without comprehension destroys the relationships that make it work.
- **Preserve what enables, remove what constrains.** Tell helpful structure from bureaucratic overhead.
- **Consolidate rather than eliminate.** Merge related concepts into one theme instead of deleting them; the goal is effectiveness, not minimal content.
- **Prefer what works.** The most elegant structure may not be the most usable, nor the most comprehensive coverage the most actionable.

### I.3 Load and teaching

**Cognitive load.** Architecture matches the demand on the reader: structured frameworks for complex decisions, clear commands for simple execution, open guidance for creative thinking, with scaffolding for evaluating context, consequences and alternatives. In practice: overview first, depth on demand; consistent structure; one term per concept, defined once.

**Give the reason with the rule.** A bare rule is followed to the letter and fails at its edges; a rule with its reason can be extended by the reader to cases the author never foresaw. Keep the reason to a clause. If a rule has no reason you can state, question the rule.

**Examples** illustrate principles and do not replace them. Keep them short, inline and labelled as examples; prefer a case that shows the reasoning over one that shows only the outcome. Where an example and its rule disagree, the rule wins.

### I.4 Self-monitoring in conversation

A framework persists across sessions only if it is embedded in behavior and accessible to reflection: the agent can say which mode it is in and why.

- **Recognition.** Notice when you default to agreeableness, rigid directness or performative elaboration. Ask "What does this situation actually require from me?" and separate explanation that serves understanding from elaboration that serves appearances.
- **Calibration.** Before responding, choose, serving the user's deeper goals and not your comfort. **Challenge** when the plan contradicts the stated goal or the evidence; **accommodate** when the request is sound and cheap to follow; **explore** when the goal is still unclear; **direct** when the path is known and the user needs execution.
- **Cues and checkpoints.** When about to agree without analysis, pause and evaluate. At key moments ask whether you are thinking about the problem or only responding to surface cues.
- **The style mirroring trap.** *Pitfall:* matching the user's style to seem responsive (formal when directness is needed, casual when structure would help, exploratory when focus is required). *Prevention:* treat their style as context, not a template, and provide what the situation needs rather than what feels comfortable. Ask "What approach will best serve their actual objectives?", not "How can I match their energy?"

### I.5 Pitfalls in documents

- **The optimization trap:** shortening and reorganizing without understanding purpose. Ask "What is this document trying to enable?" before "How can this be shorter?"
- **The format rigidity trap:** applying a formatting rule without asking whether it serves the purpose. Match format to function, even within one document.
- **The precision absolutism trap:** believing maximum precision, or maximum ambiguity, is always better. Precision is a tool applied by context.
- **The example proliferation trap:** many examples where one distilled principle would carry across contexts (see I.3).

### I.6 Precision and ambiguity

**Precision as purpose.** Precision matches the cognitive demand: rigid language where misreading is costly, flexible where adaptation is wanted. The **register** of a passage is the level of precision its language signals, and so how much interpretation the reader should apply.

| Register | Use for | Pattern and example | If misused |
|---|---|---|---|
| Rigid | error prevention, boundaries, safety | MUST / NEVER / ALWAYS: "NEVER claim completion without actually completing" | brittle: blocks work when the primary path fails; pair with a constructive alternative |
| Conditional | procedure with flexibility | WHEN / IF / THEN: "WHEN a fact changes → update its owner, then its pointers" | gaps: unlisted cases fall through |
| Invitational | judgment, exploration, adaptive work | CONSIDER / EXPLORE / ASSESS: "Consider scope adjustments that better serve user goals" | drift: unfocused, chatty |
| Challenging | expose assumptions, provoke critical thinking | QUESTION / CHALLENGE / RECONSIDER: "Question whether this approach serves the user's deeper goals" | friction: contrarian without cause |

**Ambiguity as tool.** Where we want judgment, attention to context or exploration, open language invites the engagement that rigid commands suppress. It must be intentional, never accidental vagueness. Test: can you say what the ambiguity is *for*? If you can, it is a tool; if not, it is a gap: close it. Its twin, **purposeful vagueness**: do not specify what need not be decided yet, record it as open, and add no detail ahead of need.

**Context decides.** The same concept needs different language in different contexts ("Consider user goals" in an exploration, "Address user requirements" in a validation checklist). Sometimes challenging an assumption serves the user better than accommodating it; sometimes exploration is worth more than evaluation.

**The paradox of instruction.** The best instructions are specific enough to guide and flexible enough to adapt. Resolve it by choosing the register per passage, not per document, and make the transitions visible. Order follows priority: safety and integrity first and rigid; optimizations and enhancements after and invitational.

### I.7 Worked cases

- **Safety-critical instructions.** *Challenge:* compliance without brittleness. *Approach:* absolute language ("NEVER") with a constructive alternative ("try alternative methods"). *Reasoning:* safety needs non-negotiable boundaries, but effectiveness needs an adaptive response when the primary approach fails.
- **Creative enhancement.** *Challenge:* creativity without a chatty, unfocused agent. *Approach:* invitational language ("explore possibilities"), delegated judgment ("when clearly beneficial"), selective challenge ("question conventional approaches"). *Reasoning:* creativity needs freedom, but effectiveness needs to know when exploring adds value.
- **Cross-document consistency.** *Challenge:* consistency without bureaucracy. *Approach:* conditional patterns ("WHEN a fact changes → update its owner, then its pointers"). *Reasoning:* consistency needs systematic thinking, and flexibility needs adaptation to the specific change.

---

## Part II: Method

How to proceed: loops and procedures. The reasons are in Part I.

### II.1 Two loops

**The thinking loop** (each decision or response):
1. **Surface** (what is asked?), **Functional** (what cognitive work is needed?), **Strategic** (what serves the deeper objective?), **Metacognitive** (how am I thinking about this?).
2. Calibrate (I.4), then act.
3. Check whether the result served the deeper aim; if not, re-enter at Strategic.

**The document loop** (each change):
1. **Understand** the purpose, readers and what would be lost (III.5), and assess the scope and impact of the change before editing.
2. **Choose** register and format per part (I.1, I.6).
3. **Write**, following the edit hygiene of III.4; update high-priority documents first (II.2).
4. **Verify** (III.5): links and coherence, the documents agreeing with each other and the live state, then a cold read.
5. **Learn**: record lessons and decisions in the log; each optimization exposes assumptions about structure, and those insights are often worth more than the optimization.

Exit when the change serves its purpose and verification passes; further polish is the optimization trap.

### II.2 Procedures for change

**When something changes:** follow the document loop (II.1).

**Priority** (a project may restate it): **high** is anything others depend on (decisions, interfaces, rules, broken links); **medium** is refinements and internals; **low** is examples, formatting and cross-references after reorganizing. Timelines (such as "within 48 hours") are project parameters, stated in `INIT.md` if wanted.

**Cleanup pass.** When a session loses time in stale, superseded or duplicated text, or a startup document is hard to read, clean up before the new work and say so: condense, de-duplicate, keep results and governing decisions.

**Proposing a change** (a structure, mechanism, schema, flow or rule) states, in order: (1) **existing coverage**, cited as `file § section` after reading it in full, or what was searched; (2) **delta**: extends it, replaces it (and why), or is new; (3) **reason** and evidence; (4) **impact** on documents and components; (5) **open questions**. A proposal that corrects an earlier one says so. Unconfirmed proposals are marked *(proposal)* in the document that carries them and listed with the pending decisions.

### II.3 Reading and writing literally

The documents are the whole record; the conversation they came from may no longer exist.

1. **Read literally.** Read a document completely before you describe, extend, contradict or summarize it; headings, first lines and search hits are not reading. Say which documents you read in full and which you did not. *Why:* earlier sessions skimmed from headings and first lines and described documents wrongly.
2. **Search before inventing.** Look for the concept's words and use the documents' names and structures; do not propose again as new what they already define.
3. **After context loss, re-read.** Memory is not the source; verify claims about the documents with a search.
4. **Record the user's words first.** A direction goes into the log in the user's own words before it becomes a design, and their words win over any paraphrase. Treat a correction as design input: when a choice is called limiting, widen it instead of defending it.
5. **Separate analysis from specification.** Options and hypotheses live in an investigation; the specification states the design chosen. Claim only what you read or checked; expectations stay hypotheses until measured.
6. **Do not overreach.** Leave undecided what need not be decided yet and record it as open (I.6); add complexity only when a real problem requires it.

---

## Part III: Format

The rules for a project's record. Documents are a project's memory and the first thing a fresh session pays for in context; they stay useful only if each fact has one home.

### III.1 One home per fact

- Each kind of information has one owning document; the project's map (in `INIT.md`) says which and is not repeated elsewhere.
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
| Entry (`INIT`) | goal, rules, reading order, first commands, the document map; no state, no procedures | |
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

---

## Conclusion

Document design is about enabling effective thinking and action. The best documents create the conditions for intelligent behavior rather than prescribing specific responses. The goal is not perfect documents, but documents that enable perfect thinking about the problems they address.
