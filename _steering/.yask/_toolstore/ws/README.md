---
kind: steering
description: "ws: the command that operates the workspace. What it is, how to run it, and the contract of each command."
---
# ws

A Python 3.8+ command. Run through the root launcher: `./ws <command>` or `sh ws <command>`; on Windows run `ws-windows-setup.cmd` once, then `.\ws <command>` (PowerShell) or `ws.cmd <command>` (cmd). Nothing is installed or on `PATH`; the launcher finds the workspace. `yask` is the same tool. Without it: `python3 _steering/.yask/_toolstore/ws/ws.py`. The Windows shim uses `WS_PYTHON` if set, then `python`, `py -3`, `python3`; it assumes `python` is Python 3.8+.

Files: `ws.py`, shims `ws`/`yask` (`.cmd` on Windows), `wslib/` (command groups; help in `ws_help.py`). The root `ws` only points at the shims, so updates never replace it. Conventions: `../README.md`.

Global flags: `--json`, `--you NAME`, `--root PATH`; `WS_USER`, `WS_ROOT`, `WS_NOW` and `YASK_AUTOUPDATE=0`/`CI` come from the environment. `WS_UPDATE_SYNC=1` makes the background update check synchronous. Read commands do not write; state commands write their own files; moving, deleting or rewriting needs `--apply`. Exit codes: 0 clean, 1 warnings, 2 action, 3 could not analyze. First run generates `_steering/.ws/`; its index refreshes on content hash change and narrows in-place markdown edits to markdown rows.

## Automatic lifecycle
At the start of ordinary commands `ws` silently creates git, heals a conflicted merge, closes finished tasks, parks stale `STARTED`, and snapshots uncommitted work (`ws restore`). Config: `lifecycle:`; `YASK_LIFECYCLE=0` pauses. Commit commands (`save`, `squash`, `archive`, `git`, `update`, `sync`, `hooks`, `approve`) skip it.

## Concurrency
Shared-state edits take a short lock, re-read and write once; waiters are told on stderr. Logs append only; stale locks break after 15 s. `.gitattributes` merges state by union; `sweep` and `check` repair merges.

## Find
| Command | Contract |
|---|---|
| `map [path]` | Descriptions from front matter (else first heading); flags missing ones; omits unlisted folders unless asked. |
| `where`, `modules`, `tools` | Fact map, module states, tools in both steering layers and `_tools/`. |
| `playbooks [--check]`, `route "<query>"` | Routed playbooks; `--check` lints `use_when`; `route` ranks by `use_when` and `description`, flags near ties, returns `path`, `score`, `use_when` in JSON. |
| `outline <file>`, `section <file> <heading>`, `brief <topic>` | Heading tree with sizes, one section, or sections for a topic with sizes, token estimate and related files. |
| `find <terms>` | Ranked sections and symbols, accent-insensitive, with glossary aliases; pointers only; `--steering`/`--hidden` widen the search. |
| `related <ref>`, `impact <ref>`, `graph <ref> [--depth N] [--mermaid]` | Both-direction edges, dependents, and a text or Mermaid neighborhood. `ref` = `path`, `path#Heading`, `path:symbol`. |
| `callers <symbol>`, `path <a> <b>` | Callers and shortest call/import path; edges are syntactic and carry confidence. |
| `code map [--write]`, `code purposes` | Programs under `code/`, purpose lines, symbols/imports, and files missing a purpose line. |
| `decisions [--governing]`, `show <doc> --as-of <date>`, `index [--force]` | Decision records, a document as of a date, and a refreshed index. |

## Resume and keep state
| Command | Contract |
|---|---|
| `start`, `status` | Resume brief and state overview: tasks, open items, recent log, git changes, stale `STARTED`, check counts. |
| `task add\|set\|done` | Edit `tasks.md` with random-hex ids; `add --due --prio --ms`, `set st=OPEN\|STARTED\|BLOCKED\|INCOMPLETE`, `done [--outcome path]`. Actions log; `done` condenses. Format: `../../conventions.md`. |
| `item add\|set\|done` | Same for `_workboard/open-items.md`; `--type question\|decision\|risk\|assumption\|waiting`, `--sev`, `--due`. |
| `log [--last N --since --author --task]`, `log add "<text>" [--type --task --agent --folds <ids>]`, `log set <id> "<text>" [--type --agent]`, `log --condense <id> --apply` | Timeline; append, correct by id, fold (`--folds` takes log ids or `t-`/`o-`/`m-` id), condense. Format: `../../conventions.md`. |
| `label set <id> key=value...`, `id <letter>` | Edit a trailing attribute block by id; get an unused id for a hand-written label. |
| `folders [add\|set\|remove <path> key=value] [rename <old> <new> --apply]` | Folder policy from `.ws/folders.yaml`: `listed`, `searched`, `checked`, `generated`, `purpose`; `rename --apply` moves a project folder with `git mv` and fixes links. |
| `sweep [--apply]` | Lists finished tasks, stale or untouched `STARTED`, overdue `due`, status lines naming closed ids; `--apply` closes and parks. |
| `scaffold <folder\|module\|file.md> --apply` | Copies starter files without overwriting, or enables a module and its requirements and regenerates generated blocks. |

## Capture
| Command | Contract |
|---|---|
| `parse <file> [--out]` | Markdown from `.md`, `.txt`, `.vtt`, `.srt`, `.html`, `.docx`; other formats need an adapter. |
| `ingest <file> --title T [--when YYYY-MM-DD-HHMM] --apply` | Parse, redact (`.ws/redaction.yaml`), hash, write `_workboard/meetings/<stamp>-<id>-<slug>/`; refuses flagged secrets unless `--allow-flagged`. |
| `extract <raw>`, `extract --check [path]` | Worker brief for a raw item; validates proposals (type, source anchor, confidence, sections, quote on cited line). |
| `promote <proposal> --apply [--type --for]` | After approval: open item, task or decision record with source cited and decider blank; marks proposal `promoted_to`. State changes by hand. |
| `delegate "<task>" [--inputs --cap --steps]`, `report check <file> [--cap]` | Worker contract and parent's monitor (sections, cap, citations, quotes, dirty state). Defaults `--cap 16384`, `--steps 25`; `report check` checks length only with `--cap`. Shape: `../../playbooks/delegate-to-subagent.md`. |

## Check and review
| Command | Contract |
|---|---|
| `check [--fix-generated] [--all]` | Checks front matter, generated blocks, links/cites, ids, tasks/items, logs, routing, secrets, names, stale state and module rules; `--fix-generated`, `--all`/`--json` show set-aside findings. Exit 0/1/2. Details below. |
| `review [--apply]`, `dupes [--threshold] [--steering]`, `insight`, `retention` | Structure metrics, near-duplicate paragraphs (never merged), stale items/decisions, past `review_by`, raw items past `.ws/retention.yaml`. |

## Git
| Command | Contract |
|---|---|
| `save [paths] -m "<msg>" [--task t-xxxx --agent --push] --apply` | Commits touched paths to whatever is checked out; refuses secrets; adds `Ws-Task` and attribution trailers; never forces. |
| `archive <paths> --apply --yes-rewrite-history` | Moves to `.archive/<path>` and rewrites history away from every branch and tag. Dry run; verified bundle first, citations updated, rollback on failure; never pushes. Policy: `../../playbooks/archive-and-retention.md`. |
| `squash [--base rev] [--apply\|--undo]` | Plans unpushed commits by same author/task, area gap or wip/fixup; decision records stay alone. `--apply` rewrites locally with a backup ref; refuses pushed commits and merges. |
| `restore [path] [--from N] [--apply]` | Shows autosave snapshots; with a path and `--apply` restores that file from snapshot N. A commit clears the snapshots. |
| `secret [list\|get KEY\|run -- cmd\|expand file\|move path:line\|allow path:line\|set KEY --generate\|--temp]` | Secrets in `.secrets`, documents hold `{{secret:KEY}}`; `run` hides values. Policy and `secrets.agent_read`: `../../playbooks/handle-secrets.md`. |
| `sync` | Commits local work, merges remote, settles conflicts by rule (state by id, generated blocks regenerated, document conflicts set aside), pushes, retries. |
| `approve [paths\|--all]` | Records a person's review of canon and steering changes agents committed (`git.review`: `agent`, `all`, `off`); a person's own commit already counts. |
| `hooks install\|remove\|status` | Optional `pre-commit` (staged secrets, conflict markers) and `post-merge` (reports leftovers); never overwrites another hook. |
| `update [--apply] [--from folder-or-zip] [--repo owner/name] [--notes]` | Mirrors `_steering/.yask/` from the latest release, applies additive `update.reconcile`, commits as "Updated YASK" when configured; transactional via `_steering/.yask_cache/`. Background check on `update.interval_hours`, apply at the next command boundary; `auto` and `repo` must be set. Settings: `../../yask.yaml`. |
| `steering [list [--all]\|show <path>\|copy <path>\|override <paths> [--in file] [--why text]\|restore <paths>]` | Layers as one: superseded, added and switched-off paths; file in force; editable copy; `override:` entries in `_steering/overrides.md`. |
| `git health`, `git maintain [--schedule] --apply` | Size, heaviest blobs and whether at HEAD, bytes by folder, secret patterns, maintenance, stale branches; findings carry evidence, confidence and blast radius. |
| `git offload <paths> --to <dir> --apply`, `git purge <paths> --apply --yes-rewrite-history` | Copies to `<dir>`, verifies sha256, deletes original, leaves stub and manifest line; `purge` keeps no copy. |

## Check findings
`ws check` reports:

- Front matter; `AGENTS.md` budget; generated blocks fresh.
- Links, anchors, citations and `covers`; decision records; docs naming a `ws` command or file that does not exist.
- Unique ids and label syntax; `due`, `prio`, `sev`, milestone attributes; `residue:` terms from `config.yaml`.
- Tasks (state, reasons, stale `STARTED`), open-item types and log format. Recent log lines settle activity first; otherwise one bounded git pass (threshold window, at most `thresholds.history_scan_commits` commits) builds a cache under `_steering/.ws/cache/`, keyed by HEAD, state-file signatures and thresholds.
- Playbook `use_when`; unfilled `<placeholders>` (an error in an accepted decision).
- Secrets (every match; a harmless sample takes `ws:allow`); leftovers and stale state as `sweep`.
- Names: lowercase ASCII words and hyphens under the root, `docs/` and `_workboard/`; stamped meeting and proposal names; case or accent twins.
- Merge-conflict markers.
- Per enabled module: software ids, trace references, invariants, approval gates, lessons, evals and code purposes.

Exceptions in `_steering/.ws/check.yaml` under `ignore:` map a finding code (`*` for all) to paths. Secret findings cannot be listed (`ws secret allow`); name exceptions use `naming:`. `--all`/`--json` show set-aside findings. Updates add codes without changing paths.
