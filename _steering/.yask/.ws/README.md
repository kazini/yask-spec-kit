---
kind: steering
description: "This project's tool settings and stored data. Generated in _steering/.ws/ from the shipped copy the first time ws runs; the tool itself lives in _steering/.yask/_toolstore/."
---
# .ws

Template for the project's `_steering/.ws/`: `ws` copies these files in when missing. The project's copies are in force and are never replaced by an update; new release options reach them only through `update.reconcile` in `_steering/.yask/yask.yaml` (additive only). Generated in the project's copy, ignored by git through `_steering/.gitignore`, created when first needed: `snapshots/`, `cache/`, `reports/`, `backups/` (verified bundles written before archive and purge). `update-notes.md` records what the last update changed in your files.

- `config.yaml`: modules enabled, budgets, thresholds, task and git settings, naming, other workspace defaults.
- `check.yaml`: exceptions to `ws check`, by finding code and path.
- `folders.yaml`: what `map`, `find` and `check` do with each folder (`ws folders`).
- `retention.yaml`: lifecycle per kind of raw material.
- `redaction.yaml`: patterns applied before saving or committing.
