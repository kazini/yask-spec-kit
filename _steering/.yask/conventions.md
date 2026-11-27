---
kind: steering
description: "Front matter, kinds, ids, labels, log lines, naming, reading and size, generated lists, git policy and folder creation rules used by every document in this workspace."
---
# Conventions

## Document kinds
| kind | What it is | Writer | Read policy |
|---|---|---|---|
| raw | Immutable evidence: transcripts, exports, reports | ingest step or worker | never whole; search or extract |
| canon | Curated, owned documents and decisions | humans, reviewed | by section, or whole when small |
| working | Open tasks, open items, proposals, state | humans and agents | read at session start |
| personal | One person's log and drafts | that person and their agents | read by that person; digest for others |
| generated | Map, indexes, graphs, reports | tools only | regenerate, never edit |
| steering | Rules, playbooks, templates, manifests | the shipped layer (`_steering/.yask/`) is replaced by `ws update`; the project's own (`_steering/`) is kept | follow; copy a shipped file to change it |
In a module manifest `kind: any` means the path holds mixed kinds (for example `.archive/`). Files in `_workboard/` are `working` unless they sit in `meetings/` or `reports/` (raw) or `people/` (personal).

## Front matter
Every document starts with front matter, except files written for readers elsewhere, such as the GitHub `README.md` and its shipped copy `YASK.md`; a project lists such files under `ignore: front-matter:` in `_steering/.ws/check.yaml`. Required: `kind` and `description` (one line, used to build the map). Quote the value when it contains `: `. Optional:
- `proposed_by`, `decider`: on proposals and decisions only, where who proposed or decided matters. Authorship otherwise comes from git (`git log`, `git blame`) and from the personal folder; do not add `owner` or `author` fields.
- `status`: see "Statuses".
- `label`: a document label from the software standards (`binding`, `aspirational`, `working`, ...). It is separate from `status`.
- `approved_by`: who approved it (required before dependent work starts).
- `supersedes`: the file name (without `.md`) of the document this one replaces.
- `governing`: on a decision, `true` while it governs current work.
- `use_when`: on a playbook, when to use it; the router is generated from it.
- `derived_from`: path (and line) of the raw source.
- `covers`: code path globs the document describes (for example `code/<program>/**`), used to flag drift.
- `cadence`: how fast it changes (`every-session`, `weekly`, `monthly`, `quarterly`, `rarely`).
- `review_by`: a date after which it should be re-checked.
- `retain`: a retention class that overrides the default (see "Retention").
Do not type creation or modification dates. Git records them.

## Dates and times
Record the day and the time (UTC, to the minute) wherever a date is recorded: file names `YYYY-MM-DD-HHMM`, log lines `YYYYMMDDTHHMMZ`, front matter `YYYY-MM-DDTHH:MMZ`. A date alone is only for a deadline such as `review_by`.

## Ids
- Files with ids in their name: `<YYYY-MM-DD-HHMM>-<4 hex>-<slug>.md`. The id is the filename stem; do not repeat it in front matter. The stamp is UTC to the minute, from the clock or the event's start; the hex is random and checked for collisions. Never sequential: two branches creating the next number collide.
- Tasks, open items, lessons and rejected options: `t-xxxx`, `o-xxxx`, `l-xxxx`, `r-xxxx` (4 hex), never reused.
- Requirement and axiom ids follow the software standards playbook (component prefix, never reused, a retired one leaves a stub). They are not date-and-hex ids.

## Statuses
- Decisions: `proposed`, `accepted`, `deferred`, `rejected`, `withdrawn`, `replaced`.
- Proposals: `pending`, `approved`, `edited`, `rejected`.
- Components and stages: `draft`, `approved` (with `approved_by`), `replaced`.
- Tasks: `OPEN`, `STARTED`, `BLOCKED`, `INCOMPLETE` (finished items are deleted).
A status is a claim. Check it against reality when you cite it.

## Labels
A trailing attribute block on list items, task lines and headings (not prose paragraphs):
`- Retry policy is exponential backoff, max 5 {#a1b2 st=decided by=ana src=_workboard/meetings/2026-11-03-0930-b7c2-kickoff/summary.md#L40}`
- Keys: `#id`, `st` (`proposal`, `decided`, `unverified`, `open`, `graduated`), `type` (on open items), `touching` (the path a `STARTED` task edits), `requires` (task ids that must finish first), `due` (`YYYY-MM-DD`), `prio` and `sev` (`high`, `med`, `low`; `sev` is for risks), `ms` (a milestone id, with the `roadmap` module), `by` (who proposed it, only when it matters), `for` (who it is addressed to), `src`, `reason`, `trigger`, `check`.
- Values contain no spaces. Never label authorship in content: git blame already records it.
- Labels are attribution, not authentication. Check important claims against git history.

## Log lines
Per-person, in `_workboard/people/<name>/log/YYYY-MM-DD.md` (one file per UTC day). Lines are appended; your own can be corrected or folded by id, so the log stays a short, true account rather than a pile:
`- 20261115T1740Z @ana (note): confirmed webhook retries are idempotent {4f2a}`
- Time is UTC from the clock. Linux and macOS: `date -u +%Y%m%dT%H%MZ`. PowerShell: `(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmZ')`.
- Agent-written lines use `@name+agent`. Types: `note`, `STARTED`, `FINISHED`, `INCOMPLETE`, `BLOCKED`. Each line ends with a 4-hex id.
- `ws log set <id> "text"` corrects a line in place (stamp and id stay). `ws log add "summary" --folds <ids>` replaces earlier lines with one: give log ids, or a `t-`/`o-`/`m-` id for every line about it. Finishing a task or item condenses its lines itself. Only the author edits a line. When a new line is about an id that already has several earlier lines, `ws` says so; folding is your call.
- A shared timeline is built by merging everyone's shards by timestamp. Do not keep one shared committed log.

## Naming and language
- Files and folders are English, lowercase ASCII words joined by hyphens, with a lowercase `.md`. Front matter, config and label keys are snake_case; `ws` commands are hyphenated. Conventional names stay as they are (`README.md`, `AGENTS.md`, `LICENSE`, `NOTICE`) and so does `status_log.md`, the one exception. `ws check` warns about the rest under the root, `docs/` and `_workboard/` (`naming:` in `config.yaml` takes `ignore:` paths and `allow:` names).
- A leading underscore sets a folder apart and keeps it visible (`_workboard`, `_steering`). A leading dot keeps it out of the way. These are cues for people; what the tools actually do with each folder is written in `_steering/.ws/folders.yaml` (`ws folders`): whether it is listed by `map`, returned by `find`, checked by `check`. A folder with no entry is content, or out of the way if a name in its path starts with a dot. Asking for a folder by path always works. A folder your project created can be renamed with `ws folders rename`, which fixes the links; folders the shipped steering names stay as they are (change their behaviour, not their names).
- Prose follows the language set in `AGENTS.md`. Steering text is English.
- Avoid accented and unaccented spellings of the same term in identifiers.
- A folder `README.md` describes the folder in one page or less.

## Writing
- Avoid numbering sections and lists unless a number is required or pertinent. Leave it out where the order is self-evident or does not matter, above all in general sections and in replies. Keep it where a specific case justifies it: the steps of a procedure, and items other text cites by number (requirements and axioms keep their stable ids). Refer to a section by its heading name (`path#Heading`), so reordering never breaks a reference; a number in a heading ties every reference to that number.
- A fact has one home; elsewhere, link to it. Replace text when it changes instead of appending beside it.
- Say what it is and what to do, directly. No history of how it used to be, and no open questions inside instructions: unresolved items go in `_workboard/open-items.md`.

## Reading and size
| Item | Limit |
|---|---|
| `AGENTS.md` | under 150 lines |
| `status_log.md`, meeting summary | one page |

No other size limit for project documents. A document up to about 25 KB may be read whole when the task needs most of it; playbooks are short and single-purpose, so read them whole when triggered. Above that, or when the task needs one part, read the headings first (`ws outline`, or `grep '^#'`), then only the sections you need. About 25 KB is a nudge to choose deliberately, not a ceiling. Split a document when it mixes topics, not because of its size.

Delegated reports follow the cap and split rule in `delegate-to-subagent.md`.

Style for playbooks and other short documents: dense and imperative, one purpose per file, no filler. `document-format.md` owns the compression baseline; numbering is set in `Writing` above. A long reference document opens with a short summary and keeps stable headings so sections can be loaded alone.

## Folder roles
| Folder | Role |
|---|---|
| root files | `AGENTS.md` (entry and rules), `README.md`, `status_log.md` (current status), `tasks.md` (open tasks) |
| `_steering/` | This project's own steering: playbooks, templates, rules, modules it adds or changes. Read first; it supersedes the shipped layer by path |
| `_steering/.yask/` | The shipped steering (rules, playbooks, templates, modules, tools), replaced by `ws update`; never edited |
| `_steering/_toolstore/` | Tools that operate this workspace (`ws` and its helpers); they come with the steering |
| `_steering/.ws/` | This project's tool settings (config, retention, redaction, folders), generated from `_steering/.yask/.ws/` the first time `ws` runs; snapshots, cache, reports and backups are generated |
| `_workboard/` | Planning and organizing: files in progress, open items, proposals, raw material, stages, `people/`. Distilled into established folders when settled |
| `docs/` | The project's documentation: context, product, architecture, specs, decisions, lessons, evals |
| `code/` | The product's code: one subfolder per program or module. Documented in `docs/architecture/`; the `code` module owns it |
| `_tools/` | Tools made for the project's own work (not for running this workspace) |
| `.archive/` | Retired material, kept in git, skipped by default searches |

- **Steering is not documentation.** Steering says how to work; `docs/` says what this project is. A fact about the project never goes in `_steering/`, only a rule for how to work on it.
- **Planning vs work.** `_workboard/` is for planning and organizing. Established work lives in its own folder in the main project folder, defined by the module that owns it (for software, the architecture folder); other kinds of project add their own work folders the same way. Established things that could pass for planning (decisions, specs) still get their own folder.
- **Settled material may be created directly in its folder.** `_workboard/` is where planning happens first; it is not a required stop.
- **Two toolboxes.** A tool that operates the workspace goes in `_steering/_toolstore/`; a tool for the project's own work goes in `_tools/`. Never mix them. `_tools/` follows the same conventions as `_steering/_toolstore/` (see its README).
- **Update** with `ws update`, which mirrors `_steering/.yask/` from the release and never touches `_steering/`; `_steering/.yask/VERSION` holds the version.

## Folders appear when needed
Do not pre-create folders. Create one when there is something to put in it, copying that folder's starter files from its module's `scaffold/` (`scaffold.md`). Day one has only `_steering/.yask/`, the root files and `_workboard/` (its README and `open-items.md`).

These are defaults, not a fixed set. Create a project-specific folder when a need or user convention requires one, following `Naming and language`, `AGENTS.md` and the folder's own `README.md`. If no module scaffold owns it, create it directly; do not add a module just to imitate the examples. Register non-default tool behavior with `ws folders add|set`; if the folder owns a new kind of fact, add a `where:` row to a project module manifest, enable it and regenerate the generated blocks in `AGENTS.md`. Never create empty placeholders or indexes.

## Lists are generated, not written
Never hand-write an index, map, or list of documents, folders, modules, playbooks, templates or decisions. The source of truth is each file's front matter and each module manifest. Get a list one of two ways:
- Ask a tool (preferred): `ws map [path]`, `ws where`, `ws playbooks`, `ws modules`, `ws decisions [--governing]`.
- Run a portable command (no tool needed):
```
# map of documents with descriptions (GNU or BSD grep; skips .git and archive)
grep -rH -m1 --include='*.md' --exclude-dir=.git --exclude-dir=.archive '^description:' .
# the same with ripgrep (respects .ignore, so .archive/ is skipped)
rg -m1 '^description:' -g '*.md'
# playbooks and when to use them (lists every file of both layers, including playbooks switched off and modules not enabled; the router in AGENTS.md is the one in force)
grep -H '^use_when:' _steering/playbooks/*.md _steering/.yask/playbooks/*.md
# modules, and where each kind of fact goes
grep -H -E '^(name|description|default):' _steering/modules/*/module.yaml _steering/.yask/modules/*/module.yaml
grep -H 'holds:' _steering/modules/*/module.yaml _steering/.yask/modules/*/module.yaml
# decisions that govern now
grep -l '^governing: true' docs/decisions/*.md
```
PowerShell (not tested here): `Get-ChildItem -Recurse -Filter *.md | Where-Object { $_.FullName -notmatch '[\\/](\.git|archive)[\\/]' } | Select-String '^description:'`

### Generated blocks inside a file (use sparingly)
Where a file is loaded in full and should be self-contained (today the router and the "where a new fact goes" table in `AGENTS.md`), a tool may write a list between marker comments: `<!-- ws:generated:<name> start -->` ... `<!-- ws:generated:<name> end -->`.
- Never edit between the markers by hand. Regenerate with the tool, or by running the portable commands and replacing the block. Only modules listed in `modules.enabled` contribute rows.
- `ws check` compares each block with its source and flags a stale one.
- If two branches both change a block, do not merge it: regenerate it. Generated blocks are a merge-conflict risk, so keep them to a minimum.

## Retention
A document's retention class is the `retention` key of the module manifest that owns its path (`_steering/.ws/retention.yaml`). A `retain:` value in its front matter overrides it. Set retention from the client's contract when the kind is first created.

## Git and commits
Settings are in `_steering/.ws/config.yaml` under `git`.
- Git rules live with what they govern: generated-state ignores in `_steering/.yask/.gitignore`, project ws state in `_steering/.gitignore`, the root `.gitignore` for the user's own files, template line endings in the root `.gitattributes`, and YASK launchers in `_steering/.yask/.gitattributes`. A release can be dropped onto a project that already has root git files.
- Git keeps the history and nothing else: no branch is required, and `ws save` commits to whatever is checked out. Who must read what is `ws`'s job (`ws approve`, `git.review`); uncommitted work is snapshotted by itself outside the branch (`lifecycle.autosave`, `ws restore`); a stopped merge is settled by rule (`lifecycle.heal`, `ws sync`).
- Commit messages: `<area>: <what changed>`, with `Ws-Task: t-xxxx` trailers.
- AI attribution (`git.ai_attribution`: `none`, `trailer` or `co-author`) is set per client contract. With `--agent`, the commit author is `<you>+agent` (or `<you>+<WS_AGENT>` when several agents work) and you stay the committer, so merges and squashes land under your ID (`git.agent_author: false` turns it off).
- `ws squash` tidies unpushed commits only (same author and task, or area within a short gap, or wip/fixup); a backup ref is kept and `--undo` restores it. It is not a history rewrite in the sense below.
- Never force-push from a tool or unprompted. History is rewritten only by `ws archive` and `ws git purge`; each needs `--yes-rewrite-history` and a person's go-ahead, and pushing the result is manual.
