---
kind: steering
module: knowledge
use_when: "Choose structure, register and handling of ambiguity when writing instructions or documents (Part I): how to word instructions or prompts, tone, ambiguity, structure of a new document"
description: "Documentation framework, Part I (Cognition): format as meaning, precision and register, ambiguity as a tool, load, pitfalls."
---
> Part I of the documentation framework. Start at `document-handling.md`.

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
