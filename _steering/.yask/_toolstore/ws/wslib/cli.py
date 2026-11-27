"""ws command line. Contracts: ../README.md. Exit codes: 0 clean, 1 warnings, 2 action required, 3 could not analyze."""
import argparse
import os
import signal
import sys

from . import __version__, auto, capture, checks, codemap, collab, delegate, folders, gitops, hygiene, orient, retention, review, secrets, sessions, steering, update
from .repo import Repo, WsError
from .util import flag


def common():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--root", help="workspace root (default: found from the current directory or WS_ROOT)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--you", help="your name (default: WS_USER or git user.name)")
    return p


def build():
    ap = argparse.ArgumentParser(prog=os.environ.get("WS_PROG", "ws"), description="Tools that operate the workspace. `ws help` lists the groups; `ws help <topic>` explains one.")
    ap.add_argument("--version", action="version", version=f"{os.environ.get('WS_PROG', 'ws')} {__version__}")
    sub = ap.add_subparsers(dest="cmd", metavar="command")
    C = common()

    def add(name, fn, help_, **kw):
        p = sub.add_parser(name, parents=[C], help=help_, **kw)
        p.set_defaults(func=fn)
        return p

    p = add("map", orient.cmd_map, "folders and files with descriptions"); p.add_argument("path", nargs="?"); p.add_argument("--depth", type=int); p.add_argument("--all", action="store_true", help="list every file even when there are very many")
    p = add("where", orient.cmd_where, "where each kind of fact goes"); p.add_argument("--all", action="store_true")
    p = add("modules", orient.cmd_modules, "modules and whether they are on; `enable|disable NAME [--apply]` switches one")
    p.add_argument("action", nargs="?", choices=["list", "enable", "disable"]); p.add_argument("name", nargs="?"); p.add_argument("--apply", action="store_true")
    add("tools", orient.cmd_tools, "tools in _steering/_toolstore (both steering layers) and _tools")
    p = add("playbooks", orient.cmd_playbooks, "routed playbooks; --check lints use_when"); p.add_argument("--check", action="store_true")
    p = add("route", orient.cmd_route, "rank playbooks against a query"); p.add_argument("query")
    p = add("outline", orient.cmd_outline, "headings with sizes (symbols for code)"); p.add_argument("file")
    p = add("section", orient.cmd_section, "print one section"); p.add_argument("file"); p.add_argument("heading")
    p = add("brief", orient.cmd_brief, "minimal read-set for a topic"); p.add_argument("topic", nargs="+"); p.add_argument("-k", type=int, default=6)
    p = add("index", orient.cmd_index, "build or refresh the section and symbol index"); p.add_argument("--force", action="store_true")
    p = add("find", orient.cmd_find, "ranked sections and symbols"); p.add_argument("terms", nargs="+"); p.add_argument("-k", type=int, default=8); p.add_argument("--steering", action="store_true", help="include steering"); p.add_argument("--hidden", action="store_true", help="include every folder the registry leaves out")
    p = add("related", orient.cmd_related, "explicit edges in both directions"); p.add_argument("ref")
    p = add("impact", orient.cmd_impact, "what depends on it"); p.add_argument("ref")
    p = add("callers", orient.cmd_callers, "callers of a symbol"); p.add_argument("symbol")
    p = add("path", orient.cmd_path, "shortest call/import path"); p.add_argument("a"); p.add_argument("b")
    p = add("decisions", orient.cmd_decisions, "decision records"); p.add_argument("--governing", action="store_true")
    p = add("show", orient.cmd_show, "a document as of a date (git)"); p.add_argument("doc"); p.add_argument("--as-of", required=True)
    p = add("check", checks.cmd_check, "links, citations, ids, labels, decisions, playbooks, secrets"); p.add_argument("--fix-generated", action="store_true"); p.add_argument("--all", action="store_true")
    p = add("review", checks.cmd_review, "structure metrics; is a restructure review due"); p.add_argument("--apply", action="store_true", help="record a snapshot")
    p = add("dupes", checks.cmd_dupes, "near-duplicate paragraphs"); p.add_argument("--threshold", type=float, default=0.6); p.add_argument("--steering", action="store_true", help="include steering"); p.add_argument("--hidden", action="store_true", help="include every folder the registry leaves out")
    add("insight", checks.cmd_insight, "deterministic findings report")
    add("start", sessions.cmd_start, "resume brief")
    add("status", sessions.cmd_status, "tasks by state, ready and blocked, stale, open items")

    p = add("log", sessions.cmd_log, "merged timeline; `log add` appends")
    p.add_argument("--last", type=int, default=20); p.add_argument("--since"); p.add_argument("--author"); p.add_argument("--task")
    p.add_argument("--condense", metavar="ID"); p.add_argument("--apply", action="store_true")
    ls = p.add_subparsers(dest="logcmd")
    q = ls.add_parser("add", help="append a stamped line to today's file")
    q.add_argument("text", nargs="+"); q.add_argument("--type", default="note"); q.add_argument("--task"); q.add_argument("--agent", action="store_true")
    q.add_argument("--folds", metavar="IDS", help="replace these earlier lines (log ids, or a t-/o-/m- id for every line about it) with this one")
    q.add_argument("--json", action="store_true", default=argparse.SUPPRESS); q.add_argument("--you", default=argparse.SUPPRESS)
    q = ls.add_parser("set", help="correct one of your lines in place by its id; keeps stamp and id")
    q.add_argument("id"); q.add_argument("text", nargs="+"); q.add_argument("--type"); q.add_argument("--agent", action="store_true")
    q.add_argument("--json", action="store_true", default=argparse.SUPPRESS); q.add_argument("--you", default=argparse.SUPPRESS)

    for name, fn, word in (("task", sessions.cmd_task, "tcmd"), ("item", sessions.cmd_item, "icmd")):
        p = add(name, fn, "tasks.md" if name == "task" else "_workboard/open-items.md")
        sp = p.add_subparsers(dest=word, required=True)
        q = sp.add_parser("add"); q.add_argument("text", nargs="+"); q.add_argument("--for", dest="for_")
        if name == "task":
            q.add_argument("--touching"); q.add_argument("--requires"); q.add_argument("--due"); q.add_argument("--prio", choices=["high", "med", "low"]); q.add_argument("--ms")
        else:
            q.add_argument("--type", default="question"); q.add_argument("--src"); q.add_argument("--due"); q.add_argument("--sev", choices=["high", "med", "low"])
        q = sp.add_parser("set"); q.add_argument("id"); q.add_argument("kv", nargs="*"); q.add_argument("--text", nargs="+"); q.add_argument("--agent", action="store_true")
        q = sp.add_parser("done"); q.add_argument("id"); q.add_argument("--outcome"); q.add_argument("--agent", action="store_true")
        for qq in sp.choices.values():
            qq.add_argument("--json", action="store_true", default=argparse.SUPPRESS); qq.add_argument("--you", default=argparse.SUPPRESS)
            if not any(x.dest == "agent" for x in qq._actions):
                qq.add_argument("--agent", action="store_true")
    p = add("sweep", hygiene.cmd_sweep, "leftover and stale state; --apply closes finished tasks and parks untouched STARTED ones"); p.add_argument("--apply", action="store_true"); p.add_argument("--agent", action="store_true")
    p = add("id", hygiene.cmd_id, "mint an unused id, e.g. ws id m for a milestone"); p.add_argument("prefix")
    p = add("label", sessions.cmd_label, "edit a trailing attribute block by id"); p.add_argument("action", choices=["set"]); p.add_argument("id"); p.add_argument("kv", nargs="+")
    p = add("scaffold", sessions.cmd_scaffold, "create a folder from starter files, or enable a module"); p.add_argument("target"); p.add_argument("--apply", action="store_true")

    p = add("parse", capture.cmd_parse, "convert a document to markdown"); p.add_argument("file"); p.add_argument("--out")
    p = add("ingest", capture.cmd_ingest, "capture a document as raw evidence"); p.add_argument("file"); p.add_argument("--title"); p.add_argument("--when"); p.add_argument("--apply", action="store_true"); p.add_argument("--allow-flagged", action="store_true")
    p = add("extract", capture.cmd_extract, "worker brief for a raw item; --check validates proposals"); p.add_argument("raw", nargs="?"); p.add_argument("--check", nargs="?", const="", default=None)
    p = add("promote", capture.cmd_promote, "file an approved proposal"); p.add_argument("proposal"); p.add_argument("--apply", action="store_true"); p.add_argument("--type"); p.add_argument("--for", dest="for_")

    p = add("graph", codemap.cmd_graph, "neighborhood of a document, section, file or symbol"); p.add_argument("ref"); p.add_argument("--depth", type=int, default=1); p.add_argument("--max", type=int, default=40); p.add_argument("--mermaid", action="store_true")
    p = add("code", codemap.cmd_code, "code map: programs, files, purposes, symbols; purposes lists files missing one"); p.add_argument("ccmd", choices=["map", "purposes"]); p.add_argument("--write", action="store_true")
    p = add("delegate", delegate.cmd_delegate, "worker contract for a delegated task"); p.add_argument("task", nargs="+"); p.add_argument("--inputs", nargs="*"); p.add_argument("--cap", type=int, default=16384); p.add_argument("--steps", type=int, default=25)
    p = add("report", delegate.cmd_report, "check a worker report"); p.add_argument("action", choices=["check"]); p.add_argument("file"); p.add_argument("--cap", type=int, default=0)
    add("retention", retention.cmd_retention, "raw items past their retention period (plan only)")
    p = add("save", gitops.cmd_save, "commit touched paths under the path policy"); p.add_argument("paths", nargs="*"); p.add_argument("-m", "--message"); p.add_argument("--task", action="append"); p.add_argument("--agent", action="store_true"); p.add_argument("--push", action="store_true"); p.add_argument("--apply", action="store_true")
    p = add("archive", gitops.cmd_archive, "move to .archive/ and delete the item's history"); p.add_argument("paths", nargs="+"); p.add_argument("--apply", action="store_true"); p.add_argument("--yes-rewrite-history", action="store_true"); p.add_argument("--keep-citations", action="store_true", help="do not point citations at the archived copy")
    p = add("folders", folders.cmd_folders, "what the tools do with each folder: list, add, set, remove, rename (project folders)")
    p.set_defaults(fcmd="list")
    fs_ = p.add_subparsers(dest="fcmd")
    fs_.add_parser("list")
    for n_ in ("add", "set"):
        q = fs_.add_parser(n_); q.add_argument("path"); q.add_argument("kv", nargs="*", help="listed|searched|checked|generated=true|false, purpose=word")
    q = fs_.add_parser("remove"); q.add_argument("path")
    q = fs_.add_parser("rename"); q.add_argument("path"); q.add_argument("new"); q.add_argument("--apply", action="store_true")
    for qq in fs_.choices.values():
        qq.add_argument("--json", action="store_true", default=argparse.SUPPRESS); qq.add_argument("--you", default=argparse.SUPPRESS)
    p = add("squash", collab.cmd_squash, "group unpushed commits by task, area and wip/fixup; --apply rewrites them locally, --undo restores"); p.add_argument("--base"); p.add_argument("--apply", action="store_true"); p.add_argument("--undo", action="store_true")
    p = add("restore", auto.cmd_restore, "autosaved snapshots of uncommitted work; give a path to bring a file back (--apply)"); p.add_argument("path", nargs="?"); p.add_argument("--from", dest="src"); p.add_argument("--apply", action="store_true")
    p = add("sync", auto.cmd_sync, "exchange with the shared remote: commit what is uncommitted, merge, settle conflicts by rule, push")
    p = add("approve", review.cmd_approve, "changes to canon and steering by agents that no person has read yet; give paths (or --all) to record that you read them"); p.add_argument("paths", nargs="*"); p.add_argument("--all", action="store_true"); p.add_argument("--agent", action="store_true")
    p = add("hooks", collab.cmd_hooks, "optional git hooks: install, remove, status")
    hs = p.add_subparsers(dest="hcmd", required=True)
    for n_ in ("install", "remove", "status"):
        hs.add_parser(n_)
    q = hs.add_parser("run"); q.add_argument("name", choices=list(collab.HOOKS))
    p = add("secret", secrets.cmd_secret, "secrets: list, get, run, set, move, allow, expand (they live in .secrets files, not in documents)")
    p.set_defaults(scmd="list")
    sc = p.add_subparsers(dest="scmd")
    q = sc.add_parser("list"); q.add_argument("--from", dest="src", help="a folder or file to start from")
    q = sc.add_parser("get"); q.add_argument("key"); q.add_argument("--from", dest="src")
    q = sc.add_parser("run", help="run a command with the secrets in its environment; they are hidden from its output"); q.add_argument("argv", nargs=argparse.REMAINDER); q.add_argument("--from", dest="src")
    q = sc.add_parser("expand", help="print a file with its placeholders replaced by the values"); q.add_argument("target")
    for n_ in ("move", "allow"):
        q = sc.add_parser(n_, help="decide about a possible secret ws reported: move = it is one, allow = it is not"); q.add_argument("target", help="<path>:<line>")
    q = sc.add_parser("set"); q.add_argument("key"); q.add_argument("--generate", nargs="?", const="32", help="a random permanent secret; the value is never shown (optional length in bytes)")
    q.add_argument("--temp", nargs="?", const="default", help="a value you supply, expiring after this many hours (default secrets.temp_hours)"); q.add_argument("--value"); q.add_argument("--in", dest="into")
    for qq in sc.choices.values():
        qq.add_argument("--agent", action="store_true"); qq.add_argument("--json", action="store_true", default=argparse.SUPPRESS); qq.add_argument("--you", default=argparse.SUPPRESS)
    p = add("update", update.cmd_update, "bring _steering/.yask up to the latest release (--apply); your _steering/ is never replaced")
    p.add_argument("--from", dest="src", help="a folder or zip instead of GitHub"); p.add_argument("--repo", help="owner/name instead of update.repo"); p.add_argument("--apply", action="store_true")
    p.add_argument("--notes", action="store_true", help="show what the last update changed in your files"); p.add_argument("--force", action="store_true"); p.add_argument("--commit", action="store_true", help="commit the update onto main (the default; update.commit: false turns it off)")
    p = add("steering", steering.cmd_steering, "the two steering layers as one: list, show, copy, override, restore")
    p.set_defaults(scmd="list")
    ss = p.add_subparsers(dest="scmd")
    q = ss.add_parser("list"); q.add_argument("--all", action="store_true")
    q = ss.add_parser("show"); q.add_argument("path")
    q = ss.add_parser("copy"); q.add_argument("path")
    q = ss.add_parser("diff"); q.add_argument("path"); q.add_argument("--done", action="store_true", help="record that you compared your copy with the current shipped file")
    for n_ in ("override", "restore"):
        q = ss.add_parser(n_); q.add_argument("targets", nargs="+", help="shipped files, folders or globs, relative to _steering/"); q.add_argument("--in", dest="into", help="the steering file that carries the override"); q.add_argument("--why", default="")
    for qq in ss.choices.values():
        qq.add_argument("--json", action="store_true", default=argparse.SUPPRESS); qq.add_argument("--you", default=argparse.SUPPRESS)
    g = add("git", lambda repo, a: a.gfunc(repo, a), "health, maintain, offload, purge")
    gs = g.add_subparsers(dest="gcmd", required=True)
    q = gs.add_parser("health"); q.set_defaults(gfunc=gitops.cmd_health)
    q = gs.add_parser("maintain"); q.set_defaults(gfunc=gitops.cmd_maintain); q.add_argument("--apply", action="store_true"); q.add_argument("--schedule", action="store_true")
    q = gs.add_parser("offload"); q.set_defaults(gfunc=gitops.cmd_offload); q.add_argument("paths", nargs="+"); q.add_argument("--to", required=True); q.add_argument("--retain"); q.add_argument("--apply", action="store_true")
    q = gs.add_parser("purge"); q.set_defaults(gfunc=lambda r, a: gitops.cmd_archive(r, a, purge=True)); q.add_argument("paths", nargs="+"); q.add_argument("--apply", action="store_true"); q.add_argument("--yes-rewrite-history", action="store_true")
    for qq in gs.choices.values():
        qq.add_argument("--json", action="store_true", default=argparse.SUPPRESS); qq.add_argument("--you", default=argparse.SUPPRESS)

    p = sub.add_parser("help", help="groups of commands; `ws help <topic>`"); p.add_argument("topic", nargs="?"); p.set_defaults(func=None)
    return ap


def main(argv=None):
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    ap = build()
    a = ap.parse_args(argv)
    if a.cmd is None:
        ap.print_help()
        return 0
    if a.cmd == "help":
        from . import ws_help
        print(ws_help.text(a.topic))
        return 0
    for k in ("json", "you", "root"):
        if not hasattr(a, k):
            setattr(a, k, None if k != "json" else False)
    try:
        repo = Repo(a.root)
        if a.cmd != "update" and not (a.cmd == "hooks" and getattr(a, "hcmd", "") == "run"):
            is_git = None
            if flag("YASK_LIFECYCLE"):
                is_git = repo.is_git()
                is_git = auto.ensure_git(repo, is_git=is_git) or is_git   # git keeps the history: create it when missing
            update.schedule_check(repo)     # network check off the command path; apply happens at the boundary below
            if update.auto_update(repo):    # tool code changed: run this command again on the new code
                if not os.environ.get("WS_NO_REEXEC"):
                    os.environ["WS_UPDATED"] = "1"
                    os.execv(sys.executable, [sys.executable] + sys.argv)
            if getattr(repo, "_update_applied", False):
                repo = Repo(a.root)         # shipped files or .ws settings changed without a re-exec
            auto.run(repo, a.cmd, is_git=is_git)   # heal, close leftovers, snapshot work: silent unless it acts
        return a.func(repo, a) or 0
    except WsError as e:
        print(f"ws: {e}", file=sys.stderr)
        return e.code
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
