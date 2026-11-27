"""Hygiene: leftovers and stale state, unfilled placeholders, conflict markers, drift in docs, milestones.

Checks only report. `ws sweep --apply` does the mechanical part (close what the log says is finished, park what
nobody touched) and leaves judgment calls to a person."""
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

from .checks import LOGLINE, finding, last_log_mentions, log_files
from .index import ID_REF
from .repo import WsError
from .util import atomic_write, day, emit, locked, new_id, now, parse_item, render_item

TASKS, ITEMS, ROADMAP = "tasks.md", "_workboard/open-items.md", "docs/roadmap.md"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LEVEL = {"high", "med", "low"}
MS_ST = {"OPEN", "DONE", "SLIPPED"}
HTML = {"br", "p", "b", "i", "a", "img", "kbd", "code", "details", "summary", "sub", "sup", "ul", "li", "ol", "table", "tr", "td", "th", "div", "span", "hr", "h1", "h2", "h3"}
PH = re.compile(r"<([A-Za-z][^<>\n]{2,60})>")
TOOL_MADE = {"summary.md", "transcript.md", "local-changes.md", "manifest.md", "rejected.md", "module.yaml", ".offloaded.md", "design.md", "sync.md", "requirements.md", "overrides.md", "update-notes.md"}   # created per project or by a tool
STATE_FILES = (TASKS, ITEMS, "status_log.md")
HISTORY_VERSION = 1
COMMIT_LINE = re.compile(r"^([0-9a-f]{40}) (\d+)$")


def th(repo, key, default):
    return float((repo.config.get("thresholds") or {}).get(key, default))


# ---- state -----------------------------------------------------------------------------
def entries(repo, rel, prefix):
    out = []
    if repo.exists(rel):
        for n, ln in enumerate(repo.read(rel).split("\n"), 1):
            it = parse_item(ln) if ln.startswith("- ") and "{#" in ln else None
            if it and it[1].startswith(prefix) and not it[1].endswith("-0000"):
                out.append({"id": it[1], "text": it[0][2:].strip(), "line": n, **it[2]})
    return out


def finished_ids(repo):
    out = set()
    for f in log_files(repo):
        if "/log/" in f:
            for ln in repo.read(f).splitlines():
                m = LOGLINE.match(ln)
                if m and m.group(4) == "FINISHED":
                    out.update(ID_REF.findall(m.group(5)))
    return out


def history_limits(repo):
    """Lookback window in days and the most commits one bounded history pass may read."""
    t = repo.config.get("thresholds") or {}
    days = max(th(repo, "task_stale_days", 30), th(repo, "open_item_stale_days", 30), th(repo, "status_stale_days", 21))
    return int(max(60, days + 30)), int(max(50, min(500, th(repo, "history_scan_commits", 200))))


def history_key(repo, window, cap):
    rc, out, _ = repo.git("rev-parse", "--verify", "-q", "HEAD")
    t = repo.config.get("thresholds") or {}
    files = []
    for rel in STATE_FILES:
        p = repo.abs(rel)
        st = p.stat() if p.exists() else None
        files.append([rel, st.st_mtime_ns if st else 0, st.st_size if st else 0])
    return {"v": HISTORY_VERSION, "head": out.strip() if rc == 0 else "", "window": window, "cap": cap, "files": files,
            "limits": [t.get(k) for k in ("task_stale_days", "open_item_stale_days", "status_stale_days", "status_stale_commits")]}


def history_range(repo, cap):
    """Bound commit traversal as well as output: an old file must not make git walk years of history."""
    rc, base, _ = repo.git("rev-parse", "--verify", "-q", f"HEAD~{cap}^{{commit}}")
    return f"{base.strip()}..HEAD" if rc == 0 and base.strip() else "HEAD"


def build_history(repo, key, window, cap):
    """One bounded pass for first-seen ids and the last status_log change; no per-id history walks."""
    snap = {"key": key, "window": window, "first": {}, "touched": {}, "head_ids": {TASKS: [], ITEMS: []}, "status": {}, "dirty": []}
    if not key["head"]:
        return snap
    span = history_range(repo, cap)
    _, count, _ = repo.git("rev-list", "--count", "--first-parent", span)
    since = (now() - timedelta(days=window)).strftime("%Y-%m-%d")
    rc, out, _ = repo.git("log", "--reverse", "--first-parent", "-m", "--no-renames", f"--max-count={cap}", f"--since={since}", "--format=%H %ct", "-p", "--unified=0", span, "--", *STATE_FILES)
    touched, status, sha, ct, rel = set(), {}, None, None, ""
    if rc == 0:
        for ln in out.splitlines():
            m = COMMIT_LINE.match(ln)
            if m:
                sha, ct = m.group(1), int(m.group(2))
                continue
            if ln.startswith("diff --git "):
                hit = re.search(r" b/(.+)$", ln)
                rel = hit.group(1) if hit else ""
                if rel in STATE_FILES:
                    touched.add(rel)
                if rel == "status_log.md" and sha and ct:
                    status = {"sha": sha, "ct": ct}
                continue
            if rel in (TASKS, ITEMS) and ct and ln.startswith("+") and not ln.startswith("+++"):
                for iid in ID_REF.findall(ln):
                    if iid.startswith(("t-", "o-")):
                        snap["first"].setdefault(iid, ct)
    snap["touched"] = sorted(touched)                 # presence is enough: the fallback is the whole bounded window
    for rel, prefix in ((TASKS, "t-"), (ITEMS, "o-")):
        rc, text, _ = repo.git("show", f"HEAD:{rel}")
        if rc == 0:
            live = {e["id"] for e in entries(repo, rel, prefix)}
            snap["head_ids"][rel] = sorted(i for i in set(ID_REF.findall(text)) & live if i.startswith(prefix))
    if status:
        rc, n, _ = repo.git("rev-list", "--count", "--first-parent", f"{status['sha']}..HEAD")
        status["n"] = int(n.strip() or 0) if rc == 0 else 0
    else:
        # No status change inside the window: it is at least that old, with the commit count bounded too.
        status = {"sha": "", "ct": 0, "n": int(count.strip() or 0)}
    snap["status"] = status
    rc, out, _ = repo.git("status", "--porcelain", "--", *STATE_FILES)
    snap["dirty"] = [ln[3:].strip() for ln in out.splitlines() if ln.strip()] if rc == 0 else []
    return snap


def history_snapshot(repo):
    """Cached, scoped view of state history. Invalidated by HEAD, state-file signatures or thresholds."""
    window, cap = history_limits(repo)
    key = history_key(repo, window, cap)
    memo = getattr(repo, "_history_snapshot", None)
    if memo and memo.get("key") == key:        # a command may merge or commit; HEAD and state signatures catch that
        return memo
    path = repo.ws / "cache" / "hygiene-history.json"
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("key") == key:
            repo._history_snapshot = cached
            return cached
    except (OSError, ValueError, TypeError):
        pass
    snap = build_history(repo, key, window, cap)
    try:
        with locked(repo):
            atomic_write(path, json.dumps(snap))
    except (OSError, WsError):
        pass
    repo._history_snapshot = snap
    return snap


def age_days(repo, rel, iid, snap=None):
    """Days since iid first appeared in bounded history. None when it cannot be dated safely."""
    snap = snap or history_snapshot(repo)
    if not snap.get("key", {}).get("head"):
        return None
    ts = snap.get("first", {}).get(iid)
    if ts:
        return max(0, int((now().timestamp() - ts) // 86400))
    if iid in snap.get("head_ids", {}).get(rel, []):
        return int(snap.get("window", 0))   # committed at HEAD but not added in the window: at least that old
    return None                            # new or uncommitted: too young to call stale


def state(repo, snap=None, mentions=None):
    """Everything that looks left over. Each row: (code, id, file, line, message, sweepable)."""
    snap = snap or history_snapshot(repo)
    rows, fin = [], finished_ids(repo)
    ment = mentions if mentions is not None else last_log_mentions(repo)
    stale_h, today = float((repo.config.get("tasks") or {}).get("stale_started_hours", 24)), day()
    cap = [0]

    def quiet_days(rel, e, limit):
        cap[0] += 1
        if cap[0] > 80 or not snap.get("key", {}).get("head"):
            return 0
        m = ment.get(e["id"])
        since = (now() - m).days if m else None
        if since is not None and since < limit:
            return since                # min(age, since) is already below the threshold: no history fallback needed
        a = age_days(repo, rel, e["id"], snap)
        return min(x for x in (a, since) if x is not None) if (a is not None or since is not None) else 0

    for rel, prefix, limit in ((TASKS, "t-", th(repo, "task_stale_days", 30)), (ITEMS, "o-", th(repo, "open_item_stale_days", 30))):
        for e in entries(repo, rel, prefix):
            if e["id"] in fin:
                rows.append(("leftover-done", e["id"], rel, e["line"], f"{e['id']} has a FINISHED log line but is still listed", True))
                continue
            if e.get("due") and DATE.match(e["due"]) and valid_date(e["due"]) and e["due"] < today:
                rows.append(("overdue", e["id"], rel, e["line"], f"{e['id']} was due {e['due']}: {e['text'][:50]}", False))
            if e.get("st") == "STARTED":
                t = ment.get(e["id"])
                if t is None or now() - t > timedelta(hours=stale_h):
                    rows.append(("stale-started", e["id"], rel, e["line"], f"{e['id']} STARTED with no log line for {int(stale_h)}h", True))
            elif e.get("st", "OPEN") in ("OPEN", "INCOMPLETE") or prefix == "o-":
                d = quiet_days(rel, e, limit)
                if d >= limit:
                    rows.append(("stale-item", e["id"], rel, e["line"], f"{e['id']} untouched for {d} days: finish it, close it, or say why it waits: {e['text'][:50]}", False))
    return rows


def status_rows(repo, snap=None):
    """status_log.md: stale, still holding placeholders, or naming ids that no longer exist."""
    rows = []
    if not repo.exists("status_log.md"):
        return rows
    text = repo.read("status_log.md")
    live = {e["id"] for e in entries(repo, TASKS, "t-")} | {e["id"] for e in entries(repo, ITEMS, "o-")}
    for i in sorted(set(ID_REF.findall(re.sub(r"(?s)`[^`]*`", "", text))) - live):
        if i[0] in "to" and not i.endswith("-0000"):
            rows.append(("status-ref", i, "status_log.md", None, f"status_log.md mentions {i}, which is no longer open: update or remove the line", False))
    snap = snap or history_snapshot(repo)
    if snap.get("key", {}).get("head") and "status_log.md" not in snap.get("dirty", []):
        st = snap.get("status") or {}
        n, ct = int(st.get("n", 0) or 0), int(st.get("ct", 0) or 0)
        if not ct:
            ct = int((now() - timedelta(days=int(snap.get("window", 0)))).timestamp())
        days = max(0, int((now().timestamp() - ct) // 86400))
        if n >= th(repo, "status_stale_commits", 20) or (days >= th(repo, "status_stale_days", 21) and n >= 5):
            rows.append(("status-stale", "", "status_log.md", None, f"status_log.md unchanged for {n} commits / {days} days: is Stage, Standing directions and Current focus still true?", False))
    return rows


# ---- text hygiene ----------------------------------------------------------------------------
def strip_code(text):
    text = re.sub(r"(?s)```.*?```", "", text)
    return re.sub(r"`[^`\n]*`", "", text)


def placeholders(repo, rel, text):
    body = strip_code(text)
    return sorted({m for m in PH.findall(body) if m.split()[0].lower() not in HTML and "://" not in m and "@" not in m})


def text_findings(repo, md):
    F = []
    base = {x for x in repo.walk((".md", ".yaml", ".py", ".sh"), include_archive=False, under="_steering")} if repo.exists("_steering") else set()
    names = {Path(x).name for x in base} | {Path(x).name for x in repo.walk((".md", ".yaml"))} | {f.name for f in repo.base.rglob("*") if f.is_file()}   # switched-off shipped files still exist
    scaffold = {x.split("/scaffold/", 1)[1] for x in base if "/scaffold/" in x}
    cmds = commands()
    residue = repo.config.get("residue") or []
    for f in md:
        if f.startswith(".archive/") or f.startswith("_workboard/meetings/") or "/log/" in f:
            continue
        text = repo.read(f)
        lines = text.split("\n")
        if any(l.startswith("<<<<<<< ") for l in lines) and any(l.startswith(">>>>>>> ") for l in lines):
            F.append(finding("error", "conflict-marker", f, "unresolved merge conflict markers", next(i for i, l in enumerate(lines, 1) if l.startswith("<<<<<<< "))))
        steer = f.startswith("_steering/")
        # unfilled placeholders in live project documents (steering prose and templates legitimately contain them)
        if not steer and not f.startswith("_workboard/") and f not in (TASKS,):
            ph = placeholders(repo, f, text)
            if ph:
                fm = repo.fm(f)
                if f.startswith("docs/decisions/") and fm.get("status") == "accepted":
                    sev = "error"
                elif f.startswith("docs/") and not f.endswith("README.md") and f != "docs/decisions/README.md":
                    sev = "info" if f.startswith("docs/decisions/") else "warn"
                else:
                    sev = "info"
                F.append(finding(sev, "placeholder", f, f"unfilled placeholder(s): {', '.join('<' + x + '>' for x in ph[:3])}" + (" ..." if len(ph) > 3 else "")))
        # drift in the docs themselves: commands and files they name that do not exist
        if steer or f in ("AGENTS.md", "README.md"):
            if "/scaffold/" in f or "/templates/" in f:
                continue
            for tok in re.findall(r"`([^`\n]+)`", text):
                m = re.match(r"^ws ([a-z][a-z-]*)\b", tok)
                if m and cmds and m.group(1) not in cmds and m.group(1) not in ("help",):
                    F.append(finding("warn", "stale-command", f, f"`{tok[:40]}`: ws has no command {m.group(1)!r}"))
                elif re.match(r"^[\w./-]+\.(md|yaml|py)$", tok) and not re.search(r"YYYY|[<*]", tok):
                    if Path(tok).name not in TOOL_MADE and not repo.exists(tok) and Path(tok).name not in names and tok not in scaffold \
                            and not any(tok.endswith(s) for s in scaffold) and not tok.startswith(("docs/", "_workboard/", "code/", ".archive/", "_tools/")):
                        F.append(finding("warn", "stale-reference", f, f"`{tok}` does not exist (renamed or removed?)"))
        elif residue:
            for r in residue:
                for n, ln in enumerate(lines, 1):
                    if str(r.get("term", "")) and str(r["term"]).lower() in ln.lower():
                        F.append(finding("warn", "residue", f, f"old term {r['term']!r}" + (f": use {r['use']!r}" if r.get("use") else ""), n))
    return F


# ---- names ------------------------------------------------------------------------------------------------
STAMPED = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}-[0-9a-f]{4}-[a-z0-9]+(-[a-z0-9]+)*$")
STAMPED_IN = (("_workboard/meetings", "dir"), ("_workboard/proposals", "file"))
SKIP_TOP = {"_steering", "docs", "_workboard", ".git"}   # these are walked separately
NAME_OK = {"README.md", "AGENTS.md", "LICENSE", "NOTICE", "CHANGELOG.md", "CONTRIBUTING.md", "status_log.md"}


def fold_name(n):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", n) if not unicodedata.combining(c)).lower()


def bad_name(n, is_dir):
    core = n.lstrip("_")
    ext = Path(n).suffix
    why = []
    if ext.lower() == ".md" and ext != ".md":
        why.append("extension should be lowercase .md")
    if not n.isascii():
        why.append("non-ASCII characters")
    if " " in n:
        why.append("spaces")
    stem = core if is_dir else Path(core).stem
    if stem != stem.lower():
        why.append("uppercase")
    if "_" in stem:
        why.append("underscores (hyphens separate words)")
    return why


def name_findings(repo):
    """Names under the workspace's own folders (root, docs/, _workboard/): lowercase ASCII words joined by hyphens, stamped
    names where the folder says so. Warnings only; `naming:` in config.yaml has `ignore:` (paths) and `allow:` (names)."""
    cfg = repo.config.get("naming") or {}
    ignore = [str(x).strip("/") for x in cfg.get("ignore") or []]
    allow = NAME_OK | {str(x) for x in cfg.get("allow") or []}
    F = []

    def ignored(rel):
        return any(rel == i or rel.startswith(i + "/") for i in ignore)

    def check_dir(rd, entries):
        """entries: (name, is_dir) directly inside rd."""
        seen = {}
        for n, is_dir in entries:
            rel = (rd + "/" + n).lstrip("/")
            if n.startswith(".") or n in allow or ignored(rel):
                continue
            why = bad_name(n, is_dir)
            if why:
                F.append(finding("warn", "naming", rel, ", ".join(why) + ": rename it (ws folders rename for a folder), or list it under naming.ignore in config.yaml"))
            seen.setdefault(fold_name(n), []).append(n)
        for v in seen.values():
            if len(set(v)) > 1:
                F.append(finding("warn", "naming", (rd + "/" + v[0]).lstrip("/"), f"{', '.join(v)} differ only by case or accents: keep one"))

    root = sorted((n, (repo.root / n).is_dir()) for n in os.listdir(repo.root) if n not in SKIP_TOP and not repo.skip(n))
    check_dir("", root)
    for top in ("docs", "_workboard", "_steering"):
        if not (repo.root / top).is_dir():
            continue
        for d, dirs, files in os.walk(repo.root / top):
            rd = Path(d).relative_to(repo.root).as_posix()
            dirs[:] = sorted(x for x in dirs if not x.startswith(".") and not repo.skip((rd + "/" + x)) and not ignored(rd + "/" + x))
            check_dir(rd, [(x, True) for x in dirs] + [(x, False) for x in sorted(files) if not repo.skip(rd + "/" + x)])
    for folder, kind in STAMPED_IN:
        if (repo.root / folder).is_dir():
            for n in sorted(os.listdir(repo.root / folder)):
                stem = n[:-3] if n.endswith(".md") else n
                if n in allow or n.startswith(".") or ignored(f"{folder}/{n}") or (kind == "dir") != (repo.root / folder / n).is_dir():
                    continue
                if not STAMPED.match(stem):
                    F.append(finding("warn", "naming", f"{folder}/{n}", "stamped name expected: YYYY-MM-DD-HHMM-<4 hex>-<slug> (conventions.md, Ids)"))
    return F


def commands():
    try:
        from .cli import build
        sp = next(a for a in build()._actions if a.__class__.__name__ == "_SubParsersAction")
        return set(sp.choices)
    except Exception:
        return set()


# ---- plan: due, priority, milestones -------------------------------------------------------------
def valid_date(s):
    try:
        datetime.strptime(str(s), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def ignored_findings(repo, md):
    """Documents git ignores are never saved, and nothing says so: name them."""
    if not repo.is_git():
        return []
    cands = [f for f in md if f.startswith(("docs/", "_workboard/", "_steering/")) and not f.startswith("_steering/.yask/")]
    out = []
    for i in range(0, len(cands), 200):
        rc, o, _ = repo.git("check-ignore", "--", *cands[i:i + 200])
        out += [x.strip() for x in o.split("\n") if x.strip()] if rc == 0 else []
    return [finding("warn", "ignored", f, "git ignores this file, so it is never saved or shared: rename it, or narrow the .gitignore pattern") for f in out]


def attr_findings(repo):
    F = []
    logtext = "\n".join(repo.read(f) for f in log_files(repo) if "/log/" in f)
    known = {e["id"] for e in entries(repo, TASKS, "t-")} | set(ID_REF.findall(logtext))
    for e in entries(repo, TASKS, "t-"):
        for rid in [x for x in str(e.get("requires", "")).split(",") if x.strip()]:
            if rid.strip() not in known:
                F.append(finding("warn", "attribute", TASKS, f"{e['id']}: requires {rid.strip()}, which exists nowhere (a typo?); a finished task's id would be in the log", e["line"]))
    for rel, prefix in ((TASKS, "t-"), (ITEMS, "o-"), (ROADMAP, "m-")):
        for e in entries(repo, rel, prefix):
            if e.get("due") and not (DATE.match(e["due"]) and valid_date(e["due"])):
                F.append(finding("warn", "attribute", rel, f"{e['id']}: due must be a real date, YYYY-MM-DD", e["line"]))
            for k in ("prio", "sev"):
                if e.get(k) and e[k] not in LEVEL:
                    F.append(finding("warn", "attribute", rel, f"{e['id']}: {k} must be high, med or low", e["line"]))
            if prefix == "m-" and e.get("st", "OPEN") not in MS_ST:
                F.append(finding("error", "milestone", rel, f"{e['id']}: st must be one of {sorted(MS_ST)}", e["line"]))
    ms = {e["id"] for e in entries(repo, ROADMAP, "m-")}
    for e in entries(repo, TASKS, "t-"):
        if e.get("ms") and e["ms"] not in ms:
            F.append(finding("warn", "attribute", TASKS, f"{e['id']}: ms={e['ms']} is not a milestone in {ROADMAP}", e["line"]))
    return F


def findings(repo, md):
    F = text_findings(repo, md) + attr_findings(repo) + name_findings(repo) + ignored_findings(repo, md)
    snap = history_snapshot(repo)
    for code, iid, rel, line, msg, _ in state(repo, snap) + status_rows(repo, snap):
        if code == "stale-started":  # run_checks already reports this one
            continue
        F.append(finding("warn", code, rel, msg, line))
    return F


def milestone_lines(repo):
    ms = [m for m in entries(repo, ROADMAP, "m-") if m.get("st", "OPEN") != "DONE"]
    tasks = entries(repo, TASKS, "t-")
    out = []
    for m in sorted(ms, key=lambda x: x.get("due", "9999")):
        n = sum(1 for t in tasks if t.get("ms") == m["id"])
        flag = " OVERDUE" if m.get("due") and m["due"] < day() else ""
        out.append(f"  {m['id']} {m.get('due', 'no date'):10} {m.get('st', 'OPEN'):7} {n} open task(s){flag}  {m['text'][:60]}")
    return out


# ---- commands ----------------------------------------------------------------------------------------
def apply_fixes(repo, rows, user, agent=False):
    """The mechanical part of a sweep: drop what the log says is finished, park STARTED tasks nobody touched."""
    from . import sessions
    done = []
    with locked(repo):
        for code, iid, rel, _, msg, _ in rows:
            lines = repo.read(rel).split("\n")
            try:
                i, (text, _, attrs) = sessions.find_line(lines, iid)
            except WsError:
                continue
            if code == "leftover-done":
                del lines[i]
            else:
                attrs["st"] = "INCOMPLETE"
                lines[i] = "- " + render_item(text, iid, attrs)
                sessions.append_log(repo, user, "INCOMPLETE", f"{text[:90]} (parked by ws sweep)", agent, iid)
            atomic_write(repo.abs(rel), "\n".join(lines))
            done.append((code, iid))
    return done


def cmd_sweep(repo, a):
    """Close what the log says is finished and park what nobody touched. Everything else is only listed.
    ws also does the mechanical part by itself while it runs (auto.sweep in config.yaml)."""
    from . import sessions
    snap = history_snapshot(repo)
    rows = state(repo, snap) + status_rows(repo, snap)
    auto = [r for r in rows if r[5]]
    manual = [r for r in rows if not r[5]]
    done = apply_fixes(repo, auto, sessions.me(repo, a), getattr(a, "agent", False)) if a.apply and auto else []
    txt = []
    for code, iid, rel, line, msg, sw in auto:
        txt.append(f"{'fixed' if (code, iid) in done else 'would fix'}  {code:14} {msg}")
    for code, iid, rel, line, msg, sw in manual:
        txt.append(f"person     {code:14} {msg}")
    emit(a, {"fixed": [{"code": c, "id": i} for c, i in done], "needs_a_person": [{"code": r[0], "id": r[1], "message": r[4]} for r in manual],
             "would_fix": [{"code": r[0], "id": r[1]} for r in auto if (r[0], r[1]) not in done]},
         "\n".join(txt) + ("" if not auto or a.apply else "\n(add --apply to fix the first group)") if txt else "nothing left over")
    return 1 if manual else 0


def cmd_id(repo, a):
    if not re.fullmatch(r"[a-z]", a.prefix):
        raise WsError("prefix is one lowercase letter, for example m", 2)
    with locked(repo):
        print(new_id(repo, a.prefix))
    return 0
