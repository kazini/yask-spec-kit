# Software Documentation Guidelines

This file adds conventions for application projects that specify before they build. Technical components are documented in an `architecture/` folder. A project opts in through its `INIT.md`, which wins where it overrides anything here. Research and ML pipelines (pre-registered evaluations, thresholds, hypotheses) are not covered.

## 1. Files to create

**Default: one fused document per component, requirements first, design after, in `architecture/`.** Create a file when a component, a cross-component topic or a stage of the build needs one; a document grows when a decision needs it, not before.

Example:
```
architecture/
  README.md          index: one line per component, with its status (navigation only)
  sync.md            a component: requirements, then design, then open questions
  storage/           a component that outgrew one file (the exception)
    storage-requirements.md
    storage-design.md
  security.md        a cross-component topic, beside the components
```

- **Split only when needed:** design churn buries the requirements, a reader needs only one half, or the file is too large to read in one go. A split component becomes a folder; its files keep the component name as prefix.
- **Cross-component topics** (security, data model, protocols) sit beside the component files.
- **Investigations** are folded into the owning component once their question is decided or reduced to a few open options; they do not stay as separate files.
- **Tasks and plan** live in the project's task and state documents; no per-component task or map files.
- **Names** are component-specific, never generic (`sync.md`, not `design.md`). A changed requirement prefix is noted in the file that carries it.
- **Reading:** open `architecture/` when implementing a component, planning integration, needing a technical reference, or working across components. Read one component at a time.
- **Upkeep:** keep responsibilities cleanly separated, keep how components communicate and share data accurate, and keep cross-references between related components current.

## 2. The component document

Example skeleton:
```markdown
# <Component>
Position in the system: <one line>.

## Requirements
Terms (optional)
  online := link.up and since(last_ack) < 30 s
  full(q) := len(q) >= 1000
Axioms
  A1 invariant: for all i < j in queue: saved_at(i) <= saved_at(j) → p_replay_order

### SY-1 <Title>
Acceptance criteria (the system SHALL)
1. WHILE online and not full(queue): enqueue the change and flush within 5 s (target) → t_flush
2. IF full(queue): reject the write with E_FULL → t_queue_full

## Design
Boundaries: <what this component owns and does not own>
Contracts: enqueue(c) → id | E_FULL; E_FULL iff full(queue); post: tail(queue) = c [1.1, A1]
Flow: edit → store.write → queue.enqueue → queue.flush → remote
Decisions: D1: <choice>, over <alternative>; <reason> [1.1]
Tests: <which test file covers which requirement or axiom>

## Open
- <question, listed rather than guessed>
```

- **Order:** Requirements (its terms, axioms and criteria), then Design, then Open. Tiny components may need only Requirements.
- **Status:** Requirements are **binding** once the user approves them; Design is **working**; Open holds questions, not decisions. Architecture specifications are **aspirational**: the intended end state, listings illustrative. Every agent suggestion is marked *(proposal)*, every user decision *(user)*.
- **Gates survive the fusion:** approve Requirements, then Design, then the task breakdown. Do not start a later gate on an unapproved earlier one unless directed to work unattended.

## 3. Requirements

EARS (Easy Approach to Requirements Syntax) gives each requirement one behaviour of the system in a fixed shape. The fixed shape is deliberate: this is where precision matters.

| Pattern | Template | Use for |
|---|---|---|
| Ubiquitous | The system SHALL <response> | always-true behaviour (or an axiom) |
| Event-driven | WHEN <trigger>: <response> | reactions; the default |
| State-driven | WHILE <state>: <response> | behaviour during a condition |
| Unwanted behaviour | IF <condition>: <recovery> | errors, failures, bad input |
| Optional feature | WHERE <feature>: <response> | configuration-dependent |
| Complex | combinations | only when predicates cannot say it |

**Grouping.** Group requirements by component. Within a group, fold criteria that begin the same way under one lead line (`Acceptance criteria (the system SHALL)`) and list criteria that share a trigger or state as bullets under it. A criterion with another subject names it.

**Extending EARS with predicates.** A predicate is a named, observable condition defined once under *Terms* and used by name inside the EARS shapes. It extends the shape; it does not replace it.
1. Define one when a condition recurs or its plain word is ambiguous ("online", "valid", "stale"). Otherwise leave the prose.
2. It must be observable: a field, count or duration a test or reader can check, never a judgment ("healthy").
3. Defined once, in the owning component; other components cite it. One term per concept.
4. Combine with `and`, `or`, `not` and comparisons; this usually removes the need for the Complex pattern. Use `for all` / `exists` only in axioms and contracts, one level deep, where prose is ambiguous.
5. **Completeness check.** When two or more predicates govern one response, list their combinations in a table and confirm each row has a requirement or is marked impossible:

| online | full(queue) | response | req |
|---|---|---|---|
| yes | no | enqueue and flush | 1.1 |
| yes | yes | reject E_FULL | 1.2 |
| no | no | enqueue | 1.3 |
| no | yes | reject E_FULL | 1.2 |

6. Trace each predicate to the check or code symbol that implements it, so definition and implementation cannot drift apart silently.
7. Formality is a tool, not a goal: no proofs, no formal-method tooling assumed, prose wherever it is already clear.

**Axioms.** Statements the criteria lean on, stated once under *Axioms* and cited by id. They are the ubiquitous pattern given a name. Two kinds, in two registers:

| Kind | Holds | Register | Guarded by |
|---|---|---|---|
| Invariant | always true, whatever the behaviour | rigid (SHALL / NEVER) | a named test or property check |
| Principle | guides choices where judgment is needed | invitational (prefer, consider) | review, not a test |

Few, one statement each, numbered `A1`... and never reused. Every invariant names its check; one with no possible check is a principle. If a requirement contradicts an axiom, one of them is wrong: record the conflict and let the user decide. An axiom is *(user)* or *(proposal)*; changing an approved one is a user decision, logged in the user's words.

**Rules for criteria.**
1. One requirement, one behaviour; "and" between two responses means split.
2. State the response, not the implementation.
3. Make it measurable; where a number is a target and not an acceptance bar, say so.
4. Use SHALL for obligations; avoid "should", "may", "etc.".
5. Number uniquely with a component prefix and never reuse (`SY-1.2`, or `Requirement N.criterion`); a retired requirement leaves a stub that keeps its number.
6. Put the check on the same line (`→ t_name`). Negative requirements ("SHALL NOT ...") say how a violation is detected.
7. Skip user stories. Add one line `Why:` only where the reason is not evident.

## 4. Design

In this order, each item citing the requirement or axiom it serves (`[1.2, A1]`):
1. Purpose and position in the system.
2. Boundaries and responsibilities.
3. Contracts, one line each: `name(in) → out | errors; pre; post; invariant`. Language-neutral.
4. Data flow as an arrow chain, including integration with neighbouring components.
5. Error handling and recovery.
6. Performance considerations with the targets they serve.
7. Test strategy: which requirement and axiom each test file covers.
8. Decisions, one line each: `D1: choice, over alternative; reason [ids]`.
9. Open questions: listed, not guessed.

Code listings are illustrative; where one disagrees with a requirement or the design, the listing is wrong. None until the data schema and operators are decided. Where a schema or type can state a contract so a tool can check it, prefer that to prose.

## 5. Worked cases

**Vague requirement.** Challenge: "The sync should be fast." Approach: replace with an observable, `WHILE online: flush within 5 s (target)`. Reasoning: a test can fail it, and the "target" tag keeps a hope from becoming an acceptance bar. This does not mean that all requirements that are broad in focus must be reduced to specifics, "The sync should aim to be efficient:" followed by a list of targets or observations that can be reworked is also valid.

**Implementation hiding in a requirement.** Challenge: "Use an atomic rename when saving." Approach: `WHEN a change is saved: persist it before reporting success`, with the rename moved to a design decision `D1`. Reasoning: requirements bind WHAT; the design may change HOW without touching the requirement.

**Conflict with an axiom.** Challenge: a requirement lets a retry skip ahead of older queued items, against A1. Approach: do not resolve it silently; record the conflict and ask. Reasoning: either the requirement or the axiom is wrong, and only the user decides which.

**Missing combination.** Challenge: requirements cover "online" and "full" separately. Approach: the decision table shows a row (not online and full) with no requirement; add it or mark it impossible. Reasoning: gaps hide between conditions; a table makes them visible.

## 6. Tests, traceability and checkpoints

- Where a check is useful, a requirement or invariant is traced to it by id on its own line, and each test names what it checks; not all wording needs to be testable *(user)*. Invariants suit property-based checks.
- Acceptance checks are not edited to make them pass. A changed check is a new version and a user decision. If a test fails, fix the implementation or raise the requirement.
- Review checkpoints: **before building a stage** (its specification matches the architecture); **after a stage** (architecture updated with validated learnings, lessons logged); **before implementation** (specifications current and complete); **after a milestone** (all affected documents reviewed).
- When something changes: update axioms and requirements first, then architecture and interfaces, then implementation notes. Timelines are project parameters.

## 7. Aspirational and practical

Where a project builds in stages (prototypes, milestones) against an architecture, these principles apply *(user)*:

1. **Separation of Concerns**: Master architecture and prototype specifications serve different purposes and should not be conflated
2. **Aspirational Preservation**: The master architecture documents represent the desired end state and should remain comprehensive
3. **Incremental Validation**: Each prototype validates specific aspects of the master architecture through working implementations
4. **Practical Focus**: Prototypes use practical, descriptive terms rather than complex theoretical concepts
5. **Iterative Refinement**: Development proceeds through working prototypes that gradually incorporate more architectural complexity

In practice: the architecture folder stays comprehensive and is not simplified to match what a stage builds. A stage gets its own fused `{stage-id}.md`, written when it starts, in practical language, naming the architecture requirement each of its requirements validates and carrying the success criteria that gate moving on. Validated learnings flow back into the architecture after the stage; otherwise the two develop independently.

## 8. Defaults a project may replace

- **Status labels** for the project's map: **binding**, **aspirational**, **working**, **open**, **reference**, **steering**, **state**, **navigation**.
- **Coherence:** one term per concept across documents, accurate links, explicit dependencies.
- **Overrides:** names, labels, layout, test framework, update timelines, when to split, how many axioms are too many, whether to use predicates at all. Anything not stated in `INIT.md` follows this file.
- The token savings of the fused layout, one-line contracts, inline traces and predicates are hypotheses until measured on a real component.
