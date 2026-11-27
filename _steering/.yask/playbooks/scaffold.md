---
kind: steering
module: core
use_when: "Create a folder or enable a module for the first time: set up an area, bootstrap the docs, decisions, lessons or evals folders"
description: Create project folders on demand from a module's starter files, and enable modules without pre-building anything.
---
# Scaffold on demand

Tool: `ws scaffold`. Folders are never pre-created. Create one when you have something to put in it (git does not track empty folders anyway). Manual steps. A module's files are in the shipped `_steering/.yask/modules/<module>/` and, if the project has overridden or added to it, also in `_steering/modules/<module>/`; on a fresh checkout only the shipped folder exists. The commands below read both, the project's first, and never overwrite (`cp -n`).
1. Find the module that owns the folder: `ws where`, or `grep -rn 'path: "<folder>/"' _steering/modules/*/module.yaml _steering/.yask/modules/*/module.yaml 2>/dev/null`.
2. Check the module is in `modules.enabled` in `_steering/.ws/config.yaml`. If not, ask before enabling it (it changes which playbooks and checks apply), then add it and any module it `requires`.
   To switch a module off, ask the same way, then `ws modules disable <module> --apply` (refused for `core` and for one that another enabled module `requires`). Its files stay; only its playbooks, checks and routing stop applying. `ws modules enable <module> --apply` is the same step as `ws scaffold <module> --apply`.
3. Create the folder and copy only that folder's starter files, without overwriting:
   `mkdir -p <folder>; for m in _steering/modules/<module> _steering/.yask/modules/<module>; do cp -n "$m"/scaffold/<folder>/*.md <folder>/ 2>/dev/null; done`
   Starter files are the files directly in that scaffold folder; subfolders are scaffolded when needed. If the parent has its own starter (for example `docs/` before `docs/decisions/`), scaffold the parent first. Without a POSIX shell, copy the files by hand and do not overwrite existing ones.
4. Fill the placeholders in the copied files.
5. Your personal folder: `mkdir -p _workboard/people; for m in _steering/modules/collab _steering/.yask/modules/collab; do cp -n "$m"/scaffold/_workboard/people/README.md _workboard/people/ 2>/dev/null; [ -d _workboard/people/<you> ] || cp -r "$m"/scaffold/_workboard/people/_template _workboard/people/<you> 2>/dev/null; done`.
6. After enabling a module, regenerate the generated blocks in `AGENTS.md` (router and "where a new fact goes"): `ws check --fix-generated`, or run the portable commands in `conventions.md` (`_steering/.yask/conventions.md`, or `_steering/conventions.md` if the project has its own copy) and replace the text between the markers.
7. Add a `note` line to your log.

A module with no `scaffold/` has nothing to copy; its manifest and playbooks are enough. If no module owns a folder, create it directly; no scaffold is required. Register non-default folder behavior with `ws folders add|set`, and a new fact home with a project module `where:` row.
