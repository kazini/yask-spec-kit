---
kind: steering
module: knowledge
use_when: "Decide which document rule applies: writing, wording, changing or finding a document's owner"
description: "Entry point for the document modules: which playbook to use for each documentation task."
---
# Document handling

Use this to pick a module, not as a rulebook. A project's `AGENTS.md` names owners and wins where it says so; rules that are not about documents live elsewhere. Software projects add `software-standards.md`. Adaptations are in `_steering/.yask/modules/knowledge/README.md`.

| Need | Module |
|---|---|
| Write, place, shorten, edit cleanly, check links and cites | `document-format.md` |
| Choose structure, register, intentional ambiguity or tone | `document-thinking.md` |
| Change or review, assess impact, propose, read literally | `document-method.md` |

Start with `document-format.md` for any new document or README. Open another module only for its named need; none has to be read in order.

## Section map
Use `ws outline <file>` to see headings and `ws section <file> '<heading>'` for a refresher. Read the whole document before changing or restructuring it.

| Document | Sections |
|---|---|
| `document-format.md` | `One home per fact` — ownership, conflicts, status marks; `Short writing` — compression baseline; `Roles and where a fact goes` — fact destinations; `History and dates` — dates and rewrites; `Edit hygiene` — per-edit checks and curation; `Writing and optimizing` — audience, new and existing documents, format choice; `Links, cites and names` — links, stable ids, traces and file names. |
| `document-thinking.md` | `Format as meaning` — what structure signals; `Register and ambiguity` — precision, open language and purposeful vagueness; `Judgment in change` — what to preserve or consolidate; `Load and examples` — reader demand, reasons and short examples; `Self-monitoring in conversation` — conduct calibration; `Pitfalls` — common traps; `Worked cases` — safety, creativity and cross-document consistency. |
| `document-method.md` | `Two loops` — thinking and document loops; `Change priorities` — impact tiers and cleanup triggers; `Proposing a change` — coverage, delta, evidence, impact and open questions; `Reading literally` — full reads, source words, user words and scope discipline. |
| `AGENTS.md` | `Hard rules`, `Stop and ask before` — non-negotiables and consent gates; `Session protocol`, `Finding things` — state and lookup order; `Router`, `Where a new fact goes` — generated maps for playbooks and fact owners; `Folders and tools`, `Reading policy`, `Conventions`, `Modules` — workspace layout and reading limits. |
| `software-standards.md` | `1. Files to create` — component layout and when to split; `2. The component document` — fused skeleton, order and gates; `3. Requirements` — EARS, predicates, axioms and criteria; `4. Design` — boundaries, contracts, flow and decisions; `5. Worked cases` — examples of requirement judgment; `6. Tests, traceability and checkpoints` — checks and review gates; `7. Aspirational and practical` — architecture versus staged builds; `8. Defaults a project may replace` — default labels and overrides. |
| `_steering/.yask/modules/knowledge/README.md` | Single page: workspace adaptations, priority settings, reader guides and numbering. No subsections. |
