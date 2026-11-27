"""Help text, loaded only when `ws help` is run."""
GROUPS = """YASK Workspace Suite (ws, or yask): tools that operate the workspace. Reading never writes; state commands (task, item, log) write their own files; moving, deleting or rewriting needs --apply. Exit codes: 0 clean, 1 warnings, 2 action required, 3 could not analyze.

Find      map, where, folders, modules, playbooks, route, tools, outline, section, brief, find, related, impact, callers, path, graph, code, decisions, show
Resume    start, status, log (log add), task (add set done), item (add set done), label, sweep, id, log set, sync, approve, restore, secret, secret
Check     check (--fix-generated), review, dupes, insight, index, retention
Capture   parse, ingest, extract, promote, scaffold, delegate, report check
Git       save, archive, git health|maintain|offload|purge, squash, hooks, update

Topics: ws help workflow | paths | labels | history"""
TOPICS = {
    "workflow": "Resume: ws start. Work: ws task add/set/done, ws item add/done and ws log add keep tasks.md, open-items.md and your log current; ws save commits under the path policy. Capture: ws ingest FILE --apply, hand ws extract RAW to a worker, ws extract --check, a person approves, ws promote FILE --apply. Find: ws find TERMS, ws brief TOPIC, ws outline FILE, ws section FILE HEADING, ws related/impact REF.",
    "paths": "Paths are relative to the workspace root, with / separators. A section is path#Heading; a code symbol is path:symbol. The root is found from the current directory (or WS_ROOT, or --root). Your name comes from --you, WS_USER or git user.name. WS_NOW=YYYYMMDDTHHMMZ pins the clock.",
    "labels": "Items end with {#id key=value ...}. Tasks t-xxxx: for, st (OPEN STARTED BLOCKED INCOMPLETE), reason, touching, requires, due (YYYY-MM-DD), prio (high med low), ms (milestone m-xxxx). Open items o-xxxx: type (question decision risk assumption waiting), for, src. Edit them with ws task/item/label so ids and syntax stay valid.",
    "history": "ws archive PATH moves an item to .archive/ and deletes its history from every branch and tag. ws git purge PATH does the same without keeping a copy. Both: dry run by default; --apply --yes-rewrite-history after a person agrees; a verified bundle is written to _steering/.ws/backups/ first; the tool never pushes. Afterwards force-push yourself, have everyone re-clone, and delete the bundle.",
}


def text(topic=None):
    if not topic:
        return GROUPS
    return TOPICS.get(topic, f"no topic {topic!r}; topics: {', '.join(TOPICS)}")
