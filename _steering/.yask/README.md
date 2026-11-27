---
kind: steering
description: "How shipped and project steering combine, update, and when to enable modules and tools."
---
# Steering

Shipped steering (`_steering/.yask/`) is replaced by releases; project steering (`_steering/`) is yours. Folder roles and front matter are in `conventions.md`; playbooks, templates and modules describe themselves (`ws playbooks`, `ws modules`, `ws map _steering/`).

## Layers
A path in `_steering/` wins; a missing path falls through to `.yask/`. `ws steering` and `ws map _steering/` show the merge; `AGENTS.md` lists the file in force. Only the tool merges, not a shell command.

- Write project files under `_steering/`: playbooks in `playbooks/` (routed automatically), plus templates, rules and `modules/`. `ws steering copy <path>` copies a shipped file into `_steering/`, where it supersedes the original.
- `override:` in front matter or yaml switches off shipped paths relative to `_steering/`; `ws steering override` and `ws steering restore` record and reverse it. Tool code is not overridden; add your own under `_steering/_toolstore/`.
- Git rules stay with what they govern; see `conventions.md`.

## Playbooks and templates
Front matter and `use_when` follow `conventions.md` and `playbooks/write-playbook.md`. Manual steps work without `ws`; disabled modules are not routed. Templates are copied, filled in and keep their front matter.

## Modules
`modules/<name>/` holds `module.yaml`, an optional `README.md` and `scaffold/` (starter files copied when a folder is first needed). `modules.enabled` in `.ws/config.yaml` decides which modules apply. A project module goes in `_steering/modules/<name>/` with the same shape; see `modules/core/module.yaml` and `playbooks/scaffold.md`.

## When to enable
Add structure when the project shows the need.

| Enable | When |
|---|---|
| `meetings` | meetings or other raw material arrive regularly |
| `lessons` | the same mistake repeats |
| `software` | the project must be specified before it is built |
| `evals` | rules or playbooks change often, or weaker models are used |
| `code` | the product has code worth mapping |
| `effort` | a client needs time tracking |
| `playbooks` | a procedure keeps repeating in this project (needs `evals`) |

Start with `map`, `check`, `start`, `task` and `log` when manual steps become error-prone; add `ingest`, `extract`, `promote` for regular raw material, `index`, `find`, `related`, `impact` for many documents, `review`, `dupes` for repeated check findings, and `git health`/offload for size or retention terms. Split `tasks.md` and `_workboard/open-items.md` only when they conflict repeatedly.
