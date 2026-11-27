---
kind: steering
description: "Tools that operate this workspace: conventions every tool follows and how to add one. The list of tools is generated."
---
# Toolstore

Tools that operate the workspace (`ws` and helpers), shipped with the steering and updated with it. A workspace tool of your own goes in `_steering/_toolstore/`, beside the shipped layer; tools for the project's own work go in `_tools/`, never here (both follow these conventions). `ws/README.md` holds the `ws` contracts, including the root launcher and Windows setup. Tools do the deterministic work (parse, index, lint, diff, archive) so agents spend context on judgment. List them with `ws map _steering/_toolstore/`.

## Conventions
- Tools are Python or Node.js; each documents its runtime and install and works on Windows, macOS and Linux.
- Each tool keeps its command shim in its own folder (a few lines of `sh`, plus a `.cmd` for Windows); each layer's `_shims/` holds a copy of every shim, which works from either place. Nothing is installed and nothing goes on the `PATH`; run your own tool by its shim path.
- A tool finds the workspace from the current directory (or `WS_ROOT`) and its own files from its own location. Everything it creates for a project lives in `_steering/.ws/`, never next to the tool.
- A large tool keeps its help text in `<tool>_help` next to it, loaded only when help is asked for. A tool's README stays short: what it is, `--help`, its files, how to run it.
- Output is short and token-lean: say what answers the question or needs action, nothing else. Background steps that work or fail quietly say nothing (an update that cannot reach the network is silent). A command's help is basic; the detail of a parameter appears only where that parameter is described. The tool does the lifecycle work so neither the person nor the agent has to remember it.
- Project-independent: inputs by parameter, nothing hard-coded to one project. Settings come from `_steering/.ws/config.yaml` and the module manifests.
- Self-documenting: `--help` and `--help TOPIC`; error messages say what to do.
- Read-only by default. Changes need `--apply`; destructive operations are dry-run first.
- `--json` on every command. Exit codes: 0 clean, 1 warnings, 2 action required, 3 could not analyze.
- Time from the clock, ids from random hex, atomic writes. Shared files are edited under a short lock the tool holds and releases itself (`ws/README.md`, Concurrency).

## Adding a tool
Create `_steering/_toolstore/<tool>/` with `README.md` (front matter `kind`, `description`) and the code; add its command shim in the tool's folder and a copy in `_steering/_toolstore/_shims/`; add its checks, if any, to the module manifest. `_shims/` appears with the first tool.
