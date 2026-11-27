---
kind: working
description: "Development queue for YASK itself: current change set, blockers, resume commands and standing constraints."
---
# YASK development to-do

Working note in `.dev_yask/`, not canon. Development work does not touch root `tasks.md`; it is template content. This is the single dev tracker; start here. Last touched: 2026-11-27T21:39Z.


## Resume state

- Git: `## No commits yet on main`; all project paths untracked. No staging, commit, fetch artifacts or push.
- Package: `dist/yask-3.1.zip`, SHA-256 `84e9cec473670530f658cb2a44845141552c531214b69fc73f099c7a96de3389`. Rebuilt after `t-b0c8` (124 files, `ws update` resolves `_steering/.yask` as its payload). Not pushed, not published. Any later edit to shipped files makes it stale: rebuild.
- `AGENTS.md` generated router: refreshed 2026-11-27 (`ws check` 0 errors). Re-run `check --fix-generated` after any `use_when` change.
- Root `NOTICE` is user-owned and must not be edited. The builder no longer requires it; `NOTICE` ships only from `_steering/.yask/NOTICE`.


## Work log

- 2026-11-27 `t-e672`: added the optional external tool library item; it absorbs the former `t-b3f6` PDF-parser item and leaves `t-f59c` as the CodeGraph analysis gate. Recorded the source-only download rule, YASK-defined pre-approval, `_toolstore` persistence, PATH auto-registration without prompts, 14-day/previous-release update guard and thick local adapters. No code, config, download, package or root-file change.
- 2026-11-27 `t-e672`: settled the adapter policy: keep both Firecrawl tools pre-approved, prefer `anydoc` whenever installed/detected and replace direct `pdf-inspector` calls with it; AnyDoc embeds `pdf-inspector` for text PDFs. All detection, checks, routing and invocation live in `ws`/YASK; agents are not prompted to call the tools themselves. No code or config change.

- 2026-11-27 `t-cb18`: inspected after an external agent ran out of context. Verified `dist/yask-3.1.zip` (21:16:46Z, SHA `84e9cec473670530f658cb2a44845141552c531214b69fc73f099c7a96de3389`) matches all 124 packaged files byte-for-byte: the agent changed no checker, playbook, module declaration or config. The only post-baseline source edit is `.dev_yask/tests/test_hygiene.py` (21:22:40Z) plus its `.pyc`: a widened `comp()` helper and 11 new tests. `checks -k TestSoftwareChecks`: 16 tests, 9 fail (all new behavioral tests), 7 pass (5 old plus 2 vacuous negative table tests); a drill-down shows empty findings for `[SY-1.9]`. `ws check`: 0 errors, 0 warnings, 2 notes. No scratch log or worker report was left. Next action: implement the checker against these tests, starting with the shared id grammar/resolver.

## Known routing limits (for `t-b84f`, not blockers)

Lexical routing cannot separate these. No case for them is in `routing_cases.tsv`; every wording tried either failed or broke a passing case.

- `find the email where we agreed on the scope` -> `record-decision` (9.16) beats `find-information` (<3): `agreed` and `scope` are both in `record-decision`, and only `find`/`where` point to the lookup.
- `where are the decisions recorded` -> `record-decision` 3.87 vs `find-information` 3.73. Adding `where decisions are` to `find-information` flips it but then `record the decisions from Tuesday's steering committee` goes to the wrong playbook. Only `where` tells them apart.
- `where do meeting notes go` is ambiguous between `ingest-meeting` and `document-format`; left out.
- Method note: tuning one `use_when` shifts BM25 weights for every playbook sharing a word, so test each change against the whole case file.


## Release gate — needed to get YASK releasable

A release can be cut when all these are done and the tree is clean. Everything in the next section is queued work, not a blocker unless you move it here.

- `t-cb18` **Extend trace-ref check — IN PROGRESS.** Cover prefixed ids, cross-component ids and decision tables.
  - Current grammar in `_steering/.yask/_toolstore/ws/wslib/checks.py:543-551` scans only `## Design` bracket tokens and accepts bare `\d+(\.\d+)?` or `A\d+`. `[SY-1.1]` falls through silently. Requirement/criterion/axiom maps are per file (`:504-550`); the global `ids_all` (`:516`) is used only by the stage `validates` check (`:563-564`), so cross-component refs are falsely rejected or falsely accepted.
  - Tests: an external agent added 11 tests in `.dev_yask/tests/test_hygiene.py:773-859` on 2026-11-27; `comp()` now takes `design=` and `prefix=` (`:729-732`). The original five tests at `:737-771` still pass. The nine substantive new tests fail because `ws check` emits no finding; two negative tests pass vacuously. The earlier "only the bare `[1.1]` fixture" note is now stale.
  - Decision tables are defined at `_steering/.yask/playbooks/software-standards.md:90-97` and `:143`; no checker parses them. A check needs a `req` column, explicit `impossible`, a shared id grammar/resolver, line-numbered findings and warn-before-approval/error-after severity (precedent `checks.py:541`).
  - Order: failing tests are already added; next widen the token grammar and resolve against one global map; emit a finding for id-like tokens that match neither grammar; then add table parsing; declare the check in `_steering/.yask/modules/software/module.yaml:7` and `modules/software/README.md:15`; align playbook examples at `software-standards.md:57,59,122,130` with the prefixed-id rule at `:116` and fix the example `1.3` that has no criterion.
  - Preserve `ids-unique-never-reused`, `trace-refs-resolve`, `criteria-name-a-check` and `checks-resolve`; no new check name without a test.


## Later additions — not release blockers

Order within this section is simplest first. Do not start these before the release gate unless asked.

- `t-b84f` **Expand semantical routing, staged.** Non-blocker.
  - Current router: `cmd_route` (`orient.py:145-164`) uses `gen.routed_playbooks`, tokenizes with `fold` minus `ROUTE_STOP`, builds a fresh in-memory SQLite FTS5 table per call, ranks BM25 with weights 5/1 on `use_when`/`description`, returns top 5, flags near-ties and no-hits, and falls back to stem counting if FTS5 is absent. It is deliberately lexical.
  - Stage 1: reuse `Index.aliases/tokens` (`index.py:332-348`) for route query expansion; never mutate the shared `index.STOP`. Keep FTS5, weights, top 5, exit codes, no-hit message and `ws route --json` `use_when` field intact so `test_ws.py:414-455` stays green.
  - Stage 2, only if stage 1 is insufficient: add a curated `route_also:` front-matter field, expand at query time and lint it in `check_playbooks` (`orient.py:98-124`). Treat the JSON shape change as an interface change with tests.
  - Stage 3 needs a written decision and stays outside `ws` core: precomputed static concept table under `_steering/` or an optional `_tools/` plugin. No bundled model, native extension, pip install or async workspace mutation under a foreground command. Precedent for async is metadata-only update check (`update.py:453-465`) with apply at the command boundary (`cli.py:180-188`).
    - Acceptance (set 2026-11-27): the two queries under `Known routing limits` route to `find-information` (`find the email where we agreed on the scope`, `where are the decisions recorded`), and all 129 cases in `routing_cases.tsv` still pass, including `record the decisions from Tuesday's steering committee` and `we agreed to drop the export feature`. Test each change against the whole file; one `use_when` or expansion edit shifts BM25 weights for every playbook sharing a word. Add the two queries to `routing_cases.tsv` only in the change that makes them pass.
- Interactions: never bypass `gen.routed_playbooks` by globbing; regenerate the static `AGENTS.md` router after any `use_when` change; keep `ws playbooks --check` at 0 (`test_ws.py:418`).
- `t-2ffc` **Async command queue and notices.** Non-blocker. Name: `ws jobs` (`job` singular for subcommands, both work the same, aliases? list subcommands default for running ones?)
  - Goal: agents with an incomplete harness can queue long commands or test runs, let them run in the background, and get a short notice on the next ordinary `ws` command when a job ends or a pattern matches its log. No polling loop for the agent.
  - Simple first: stdlib-only job record in generated state (id, command, pid, scratch log path, byte offset, pattern, status). Redirect stdout/stderr to the log; the foreground command boundary checks status from the last offset and prints completed/matched jobs. Reuse the session-state rule for long-command logs; no secret values in logs.
  - Later: `at`, `in` and `every` timers; queueing a custom script for complex workflows. Prefer a queued script over growing `ws` core. Async work must not mutate workspace state behind a foreground command.
  - Evaluate before coding. Significant rewrites, semantic additions or dependencies need user confirmation; if the core gets heavy, keep it as an optional `_tools/` integration instead.
- `t-e672` **YASK-managed optional external tool library.** Non-blocker. Absorbs the former `t-b3f6` PDF-parser item; `t-f59c` remains the read-only analysis gate for CodeGraph.
  - Settled 2026-11-27 *(user)*: YASK owns a pre-approved tool set and its config. Registry, adapters and guard rules live under `_steering/.yask/_toolstore/`, so they ship with the template and survive `ws update`. Exact registry filename and schema are open.
  - Never ship tool binaries, models, vendored tool source or downloaded artifacts in `yask-<version>.zip`. When a tool is enabled for download, fetch it from source from a pinned upstream and install/build locally; no binary releases and no silent third-party download. Build prerequisites are an open item.
  - First pre-approved candidates: `pdf-inspector` (Firecrawl, MIT, PDF) and `anydoc` (Firecrawl, MIT, Word/Excel/PowerPoint/RTF/ODF/EPUB/CSV and text PDFs via pdf-inspector). Both have one-call Markdown APIs. Add versions, source URLs and hashes to the allowlist before enabling either.
  - Settled 2026-11-27 *(user)*: use both together, but when `anydoc` is installed/detected, YASK replaces direct `pdf-inspector` calls with `anydoc` calls. AnyDoc delegates text PDFs to its embedded `pdf-inspector`, so the PDF engine is still used without two adapters in the agent path. `pdf-inspector` remains the fallback when AnyDoc is unavailable.
  - Settled 2026-11-27 *(user)*: routing and checks stay inside YASK's adapter, not in prompts. Do not rely on the tools' agent skills or ask agents to run the tools directly; `ws`/YASK detects, chooses, calls, validates and reports every tool use.
  - Integration is intentionally heavy: YASK calls the local tool/library through a thick adapter and owns document discovery, tool selection, paths, output shaping, naming, titles, errors and security flow. No adapter may bypass `secrets.scrub_text`, `redact`, the injection warning, dry-run plan, `atomic_write` or the `parse_text`/`cmd_ingest` funnel in `_steering/.yask/_toolstore/ws/wslib/capture.py:43-123`. `ws` core stays stdlib-only; adapter imports/CLI calls stay outside core.
  - System-installed alternatives: when an allowlisted tool is found on `PATH`, register it as installed and usable immediately, with no user or agent prompt/request; record detected path and version for audit. Downloaded copies are fallback. Behavior for unknown or older detected versions is an open config decision.
  - Tool updates use a YASK-defined security guard in config. Default: wait 14 days after a release before considering it and download the previous release rather than the newest one. Exact reference clock, pinning, verification and failure behavior are open details; do not implement a looser default.
  - Starts with document ingestion (PDF, then office formats). CodeGraph is a candidate only after `t-f59c`; if analysis supports it, it may join this library and integrate with or supersede the basic `ws graph`/`ws code`/`ws index`/`ws related`/`ws impact`/`ws callers`/`ws callees` map. No CodeGraph download, rewrite or semantic change without that analysis and user confirmation.
  - Testing follows the existing `TestCapture` harness with synthesized inputs and dry runs; no network, binary fixture or installed tool in unit tests. Keep original-byte SHA-256 and existing transcript/summary naming. Scanned/image PDFs still need OCR and should be reported honestly.
  - Current entry point remains `parse_text()` in `_steering/.yask/_toolstore/ws/wslib/capture.py:43-76`; `cmd_parse` (`:80`) and `cmd_ingest` (`:115`) both call it. `.pdf` currently exits 3 with “convert to text first” (`:76`); `ws outline <pdf>` has no adapter (`orient.py:237`). Do not add a separate direct-to-transcript command unless asked. If extraction quality is poor, delegation remains the fallback and the playbook already routes long PDFs to `delegate-to-subagent`.
- `t-f59c` **Compare CodeGraph with YASK's code map.** Non-blocker.
  - Evaluate first, code later. Compare CodeGraph features with `ws graph`, `ws code`, `ws index`, `ws related`, `ws impact`, `ws callers` and `ws callees`; list what could be folded into the existing code map if it is effective and works cross-language, plus other worthwhile improvements.
  - Weigh two paths: extend the current design with optimizations and small improvements, versus adding CodeGraph to the `t-e672` tool library with explicit flags to enable, download and integrate it into a project's workflow. Reason what fits the scope and is worth the work; prefer reuse over rewrites.
  - No significant rewrite, semantic addition or new dependency without evaluation and user confirmation. Evaluation is read-only: no download, install, push or workspace mutation. Deliver a short comparison and recommendation, not code.


## Boundaries
- No commit, stage, fetch artifacts or push. Do not edit root `tasks.md` or root `NOTICE`.
- Keep `ws` core stdlib-only; no bundled binaries or models. Do not redesign settled features; open scope changes with the user.
- Run targeted tests; clean only generated state. Update this file whenever a task changes state; if you stop mid-task, leave the next action here.
- Dev work lives in .dev_yask and here; don't use the template tasks.md, status_log.md nor AGENTS.md, these belong to the template.


## Resume commands

```sh
python _steering/.yask/_toolstore/ws/ws.py check
python .dev_yask/run_tests.py core -k TestRouting
python .dev_yask/run_tests.py checks -k CheckExceptions
python .dev_yask/run_tests.py steering -k TestLayers
python .dev_yask/build_release.py --out dist
python .dev_yask/cleanup.py --apply
git status --short --branch
```
