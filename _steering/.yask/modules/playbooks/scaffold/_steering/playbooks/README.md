---
kind: steering
description: "Playbooks for procedures specific to this project. Routed from AGENTS.md through their use_when line."
---
# Project playbooks

One file per procedure, from `_steering/.yask/templates/playbook.md`, written and improved with `write-playbook.md`. Front matter follows `_steering/.yask/conventions.md` (`kind: steering`, `use_when`, `description`). `AGENTS.md` routes them with the shipped playbooks. A copy of a shipped playbook here (same file name) supersedes it; `override:` on top switches others off.
