---
kind: steering
description: "How the software standards playbook applies in this workspace, and the checks it implies."
---
# Software module notes

Workspace adaptations of `software-standards.md`; a project may override them in `AGENTS.md`. Folder roles, front matter, status markers and generated lists are owned by `AGENTS.md`, `conventions.md` and `document-format.md`.

- **Folder.** Components go in `docs/architecture/`; `docs/specs/` is only for non-component specifications.
- **On by default.** A project that builds no software runs `ws modules disable software --apply` (ask a person first); `ws modules enable software --apply` turns it back on. Dependencies are in `module.yaml`.
- **Labels and approval.** Map labels live in front matter `label`, separate from `status: draft | approved` and `approved_by`; requirements bind once `approved_by` is set.
- **Decisions.** One-line `D` decisions stay in the component; a cross-cutting or contested one also gets a record in `docs/decisions/`, cited by the `D` line.
- **Work.** Investigations start in `_workboard/` and fold into the owning component once decided or reduced to a few open options; stage documents live in `_workboard/stages/`, created when the first stage starts.
- **Reviews.** Checkpoints run through `consolidation-pass.md`; after a stage, log lessons (`lessons` module) and archive the stage document.
- **Checks.** `ws check` applies the rules listed in `module.yaml`. `predicates-defined`: a term is defined once, is observable (a field, count or duration, or other terms) and is used somewhere. `criteria-name-a-check`: each numbered criterion has a `→ name` (an error once the component is approved, a warning before). `checks-resolve`: once there is code under the code folder, each named check must appear in it; with no code yet nothing is checked.
