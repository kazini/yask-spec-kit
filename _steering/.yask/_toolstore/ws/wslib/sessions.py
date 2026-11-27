"""Session and state commands: log, task, item, label, status, start, scaffold."""
import re
import shutil
from datetime import timedelta
from pathlib import Path

from . import gen
from .checks import LOGLINE, ITEM_TYPES, TASK_ST, last_log_mentions, log_files, run_checks, task_lines
from .index import ID_REF
from .repo import WsError, read_fm
from .util import append_text, atomic_write, day, emit, hex4, locked, new_id, now, parse_item, parse_stamp, render_item, stamp, table, warn, words

TASKS, ITEMS = "tasks.md", "_workboard/open-items.md"


def me(repo, a):
    return repo.user(getattr(a, "you", None))


# ---- logs -----------------------------------------------------------------------
def all_log_ids(repo):
    ids = set()
    for f in log_files(repo):
        for ln in repo.read(f).splitlines():
            m = LOGLINE.match(ln)
            if m and m.group(6):
                ids.add(m.group(6))
    return ids


def append_log(repo, user, typ, text, agent=False, tid=None):
    if typ not in ("note", "STARTED", "FINISHED", "INCOMPLETE", "BLOCKED", "REVIEWED"):
        raise WsError("type must be note, STARTED, FINISHED, INCOMPLETE, BLOCKED or REVIEWED", 2)
    if tid and tid not in text:
        text = f"{tid} {text}"
    rel = f"_workboard/people/{user}/log/{day()}.md"
    head = f'---\nkind: personal\ndescription: "Log for {user}, {day()} (UTC): appended; correct or fold lines by id."\n---\n# Log {day()}\n\n'
    with locked(repo):
        line = f"- {stamp()} @{user}{'+agent' if agent else ''} ({typ}): {text} {{{hex4(all_log_ids(repo))}}}"
        append_text(repo.abs(rel), head, line)
    return rel, line


FOLD_ID = re.compile(r"^([tolrm]-[0-9a-f]{4}|[0-9a-f]{4})$")


def own_lines(repo, user):
    """(file, index, match) for every log line in this person's files."""
    out = []
    for f in log_files(repo):
        if f.startswith(f"_workboard/people/{user}/log/"):
            for i, ln in enumerate(repo.read(f).split("\n")):
                m = LOGLINE.match(ln)
                if m:
                    out.append((f, i, m))
    return out


def one_line(repo, user, lid):
    """The single own log line with this id. Someone else's line, a missing id and a duplicated id are refused."""
    hits = [(f, i, m) for f, i, m in own_lines(repo, user) if m.group(6) == lid]
    if len(hits) == 1:
        return hits[0]
    if hits:
        raise WsError(f"log id {lid} appears {len(hits)} times in your log (a line edited on two sides of a merge): keep one by hand", 2)
    if any(m.group(6) == lid for f in log_files(repo) if "/log/" in f for m in map(LOGLINE.match, repo.read(f).split("\n")) if m):
        raise WsError(f"{lid} is in someone else's log; only its author edits it", 2)
    raise WsError(f"no log line {{{lid}}} in your log (ws log --author @{user} shows ids)", 2)


def drop_lines(repo, spots):
    by = {}
    for f, i, _ in spots:
        by.setdefault(f, set()).add(i)
    for f, ns in by.items():
        lines = repo.read(f).split("\n")
        atomic_write(repo.abs(f), "\n".join(l for k, l in enumerate(lines) if k not in ns))


def fold_targets(repo, user, tokens):
    spots, seen = [], set()
    for tok in tokens:
        if not FOLD_ID.match(tok):
            raise WsError(f"--folds takes log ids (4 hex) or t-/o-/m- ids, not {tok!r}", 2)
        found = [one_line(repo, user, tok)] if len(tok) == 4 else [(f, i, m) for f, i, m in own_lines(repo, user) if tok in m.group(5)]
        if not found:
            raise WsError(f"no lines of yours mention {tok}", 2)
        for h in found:
            if (h[0], h[1]) not in seen:
                seen.add((h[0], h[1]))
                spots.append(h)
    return spots


def cmd_log(repo, a):
    user = None
    if getattr(a, "logcmd", None) == "set":
        user = me(repo, a)
        text = " ".join(a.text).strip()
        if "\n" in text or not text:
            raise WsError("a log line is one line of text", 2)
        with locked(repo):
            f, i, m = one_line(repo, user, a.id)
            typ = a.type or m.group(4)
            if typ not in ("note", "STARTED", "FINISHED", "INCOMPLETE", "BLOCKED", "REVIEWED"):
                raise WsError("type must be note, STARTED, FINISHED, INCOMPLETE, BLOCKED or REVIEWED", 2)
            gone = sorted(set(ID_REF.findall(m.group(5))) - set(ID_REF.findall(text)))
            line = f"- {m.group(1)} @{m.group(2)}{'+agent' if a.agent else ''} ({typ}): {text} {{{a.id}}}"
            lines = repo.read(f).split("\n")
            lines[i] = line
            atomic_write(repo.abs(f), "\n".join(lines))
        if gone:
            warn(f"note: the line no longer mentions {', '.join(gone)}; stale checks follow those ids through the log")
        emit(a, {"file": f, "line": line}, line)
        return 0
    if getattr(a, "logcmd", None) == "add":
        user = me(repo, a)
        text, typ = " ".join(a.text), a.type
        with locked(repo):
            spots = fold_targets(repo, user, re.split(r"[,\s]+", a.folds.strip())) if a.folds else []
            if any(m.group(4) == "FINISHED" for _, _, m in spots) and typ != "FINISHED":
                typ = "FINISHED"
                warn("note: a folded line was FINISHED, so the summary is FINISHED too")
            for tok in re.split(r"[,\s]+", (a.folds or "").strip()):
                if len(tok) > 4 and tok not in text:
                    text = f"{tok} {text}"
            rel, line = append_log(repo, user, typ, text, a.agent, a.task)
            drop_lines(repo, spots)
        remind = []
        if not a.folds:
            limit = int((repo.config.get("thresholds") or {}).get("log_fold_lines", 3))
            mine = own_lines(repo, user)
            for i in sorted(set(ID_REF.findall(text)) | ({a.task} if a.task else set())):
                n = sum(1 for _, _, m in mine if i in m.group(5)) - 1
                if n >= limit:
                    remind.append(f"{i} now has {n} earlier lines in your log. Fold them: ws log add \"<one line>\" --folds {i}" + (f"  (or ws log --condense {i} --apply, keeping this line)" if typ == "FINISHED" else ""))
        for r in remind:
            warn("note: " + r)
        emit(a, {"file": rel, "line": line, "folded": len(spots), "reminders": remind}, line + (f"\nfolded {len(spots)} earlier line(s)" if spots else ""))
        return 0
    rows = []
    for f in log_files(repo):
        if "/log/" not in f:
            continue
        for ln in repo.read(f).splitlines():
            m = LOGLINE.match(ln)
            if m:
                rows.append((m.group(1), m.group(2), f, ln, m.group(5)))
    if a.condense:
        user = me(repo, a)
        return condense(repo, user, a.condense, a.apply, a)
    if a.author:
        rows = [r for r in rows if r[1] == a.author.lstrip("@")]
    if a.task:
        rows = [r for r in rows if a.task in r[4]]
    if a.since:
        rows = [r for r in rows if r[0] >= a.since]
    rows.sort(key=lambda r: (r[0], r[2]))
    rows = rows[-a.last:] if a.last else rows
    emit(a, [{"stamp": r[0], "author": r[1], "line": r[3]} for r in rows], "\n".join(r[3] for r in rows) or "(no log lines)")
    return 0


def condense(repo, user, tid, apply, a=None, quiet=False):
    with locked(repo):
        files = [f for f in log_files(repo) if f.startswith(f"_workboard/people/{user}/log/")]
        hits = [(f, n, ln) for f in files for n, ln in enumerate(repo.read(f).split("\n")) if tid in ln and LOGLINE.match(ln)]
        if not hits:
            raise WsError(f"no log lines for {tid} in your log", 2)
        fin = [h for h in hits if "(FINISHED)" in h[2]]
        keep = (fin or hits)[-1]
        drop = [h for h in hits if h is not keep]
        if apply:
            by = {}
            for f, n, ln in drop:
                by.setdefault(f, set()).add(n)
            for f, ns in by.items():
                lines = repo.read(f).split("\n")
                atomic_write(repo.abs(f), "\n".join(l for i, l in enumerate(lines) if i not in ns))
    if not quiet and a is not None:
        emit(a, {"kept": keep[2], "removed": len(drop), "applied": bool(apply)},
             f"keep: {keep[2]}\n{'removed' if apply else 'would remove'} {len(drop)} earlier line(s)" + ("" if apply else " (add --apply)"))
    return 0


# ---- tasks and open items --------------------------------------------------------
def load(repo, rel):
    if not repo.exists(rel):
        raise WsError(f"{rel} not found", 2)
    return repo.read(rel).split("\n")


def section_end(lines, heading):
    start = next((i for i, l in enumerate(lines) if l.strip() == heading), None)
    if start is None:
        raise WsError(f"no '{heading}' section", 2)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return end


def find_line(lines, iid):
    for i, l in enumerate(lines):
        it = parse_item(l) if l.startswith("- ") else None
        if it and it[1] == iid:
            return i, (re.sub(r"^-\s+", "", it[0]), it[1], it[2])
    raise WsError(f"{iid} not found", 2)


def parse_kv(pairs):
    out = {}
    for p in pairs or []:
        if "=" not in p:
            raise WsError(f"expected key=value, got {p}", 2)
        k, v = p.split("=", 1)
        out[k] = v
    return out


def validate_task(iid, attrs):
    st = attrs.get("st", "OPEN")
    if st not in TASK_ST:
        raise WsError(f"st must be one of {sorted(TASK_ST)}", 2)
    if st == "BLOCKED" and not attrs.get("reason"):
        raise WsError("BLOCKED needs reason=<words-with-hyphens> or reason=o-xxxx", 2)
    if attrs.get("due") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", attrs["due"]):
        raise WsError("due must be YYYY-MM-DD", 2)
    if attrs.get("prio") and attrs["prio"] not in ("high", "med", "low"):
        raise WsError("prio must be high, med or low", 2)


def cmd_task(repo, a):
    with locked(repo):
        return _task(repo, a)


def _task(repo, a):
    user = me(repo, a)
    lines = load(repo, TASKS)
    if a.tcmd == "add":
        iid = new_id(repo, "t")
        attrs = {"for": "@" + (a.for_ or user).lstrip("@"), "st": "OPEN"}
        if a.touching:
            attrs["touching"] = a.touching
        if a.requires:
            attrs["requires"] = a.requires
        for k in ("due", "prio", "ms"):
            if getattr(a, k):
                attrs[k] = getattr(a, k)
        validate_task(iid, attrs)
        line = "- " + render_item(" ".join(a.text), iid, attrs)
        lines.insert(section_end(lines, "## Tasks"), line)
        atomic_write(repo.abs(TASKS), "\n".join(lines))
        emit(a, {"id": iid, "line": line}, line)
        return 0
    i, (text, iid, attrs) = find_line(lines, a.id)
    if a.tcmd == "done":
        if a.outcome and not repo.exists(a.outcome.split("#")[0]):
            raise WsError(f"outcome not found: {a.outcome}", 2)
        del lines[i]
        atomic_write(repo.abs(TASKS), "\n".join(lines))
        _, ln = append_log(repo, user, "FINISHED", f"{text[:100]}" + (f" -> {a.outcome}" if a.outcome else ""), a.agent, iid)
        condense(repo, user, iid, True, quiet=True)
        emit(a, {"finished": iid}, f"finished {iid}; logged and condensed")
        return 0
    upd = parse_kv(a.kv)
    new_text = " ".join(a.text) if a.text else text
    for k, v in upd.items():
        if v == "":
            attrs.pop(k, None)
        else:
            attrs[k] = v
    validate_task(iid, attrs)
    lines[i] = "- " + render_item(new_text, iid, attrs)
    atomic_write(repo.abs(TASKS), "\n".join(lines))
    st = upd.get("st")
    if st in ("STARTED", "INCOMPLETE", "BLOCKED"):
        append_log(repo, user, st, new_text[:100] + (f" ({attrs.get('reason')})" if st == "BLOCKED" else ""), a.agent, iid)
    emit(a, {"id": iid, "line": lines[i]}, lines[i])
    return 0


def cmd_item(repo, a):
    with locked(repo):
        return _item(repo, a)


def _item(repo, a):
    user = me(repo, a)
    lines = load(repo, ITEMS)
    if a.icmd == "add":
        iid = new_id(repo, "o")
        if a.type not in ITEM_TYPES:
            raise WsError(f"type must be one of {sorted(ITEM_TYPES)}", 2)
        attrs = {"type": a.type, "for": "@" + (a.for_ or user).lstrip("@")}
        if a.src:
            attrs["src"] = a.src
        for k in ("due", "sev"):
            if getattr(a, k):
                attrs[k] = getattr(a, k)
        line = "- " + render_item(" ".join(a.text), iid, attrs)
        lines.insert(section_end(lines, "## Open"), line)
        atomic_write(repo.abs(ITEMS), "\n".join(lines))
        emit(a, {"id": iid, "line": line}, line)
        return 0
    i, (text, iid, attrs) = find_line(lines, a.id)
    if a.icmd == "done":
        if a.outcome and not repo.exists(a.outcome.split("#")[0]):
            raise WsError(f"outcome not found: {a.outcome}", 2)
        del lines[i]
        atomic_write(repo.abs(ITEMS), "\n".join(lines))
        append_log(repo, user, "FINISHED", f"{text[:100]}" + (f" -> {a.outcome}" if a.outcome else ""), a.agent, iid)
        condense(repo, user, iid, True, quiet=True)
        emit(a, {"resolved": iid}, f"resolved {iid}")
        return 0
    upd = parse_kv(a.kv)
    for k, v in upd.items():
        if v == "":
            attrs.pop(k, None)
        else:
            attrs[k] = v
    if attrs.get("type") not in ITEM_TYPES:
        raise WsError(f"type must be one of {sorted(ITEM_TYPES)}", 2)
    lines[i] = "- " + render_item(" ".join(a.text) if a.text else text, iid, attrs)
    atomic_write(repo.abs(ITEMS), "\n".join(lines))
    emit(a, {"id": iid, "line": lines[i]}, lines[i])
    return 0


def cmd_label(repo, a):
    with locked(repo):
        return _label(repo, a)


def _label(repo, a):
    kv = parse_kv(a.kv)
    for f in repo.md_files():
        if f.startswith("_steering/"):
            continue
        lines = repo.read(f).split("\n")
        for i, l in enumerate(lines):
            it = parse_item(l) if "{#" in l else None
            if it and it[1] == a.id:
                text, iid, attrs = it
                for k, v in kv.items():
                    attrs.pop(k, None) if v == "" else attrs.__setitem__(k, v)
                lines[i] = l[:len(l) - len(l.lstrip())] + render_item(text.lstrip(), iid, attrs)
                atomic_write(repo.abs(f), "\n".join(lines))
                emit(a, {"file": f, "line": lines[i]}, f"{f}: {lines[i]}")
                return 0
    raise WsError(f"{a.id} not found", 2)


# ---- status and start ------------------------------------------------------------
def read_tasks(repo):
    out = []
    for n, ln in task_lines(repo, TASKS):
        it = parse_item(ln)
        if it and it[1].startswith("t-") and it[1] != "t-0000":
            out.append({"id": it[1], "text": it[0].lstrip("- ").strip(), "line": n, **it[2]})
    return out


def read_items(repo):
    out = []
    for n, ln in task_lines(repo, ITEMS):
        it = parse_item(ln)
        if it and it[1].startswith("o-") and it[1] != "o-0000":
            out.append({"id": it[1], "text": it[0].lstrip("- ").strip(), **it[2]})
    return out


def classify(repo):
    tasks = read_tasks(repo)
    open_ids = {t["id"] for t in tasks}
    stale_h = float((repo.config.get("tasks") or {}).get("stale_started_hours", 24))
    ment = last_log_mentions(repo)
    ready, blocked, stale = [], [], []
    for t in tasks:
        waits = [r for r in (t.get("requires") or "").split(",") if r and r in open_ids]
        st = t.get("st", "OPEN")
        if st == "BLOCKED" or waits:
            blocked.append({**t, "waiting_on": waits or [t.get("reason", "")]})
        elif st in ("OPEN", "INCOMPLETE"):
            ready.append(t)
        if st == "STARTED":
            last = ment.get(t["id"])
            if last is None or now() - last > timedelta(hours=stale_h):
                stale.append(t)
    rank = {"high": 0, "med": 1, "low": 3}
    ready.sort(key=lambda t: (rank.get(t.get("prio"), 2), t.get("due", "9999-99-99")))
    return tasks, ready, blocked, stale


def last_activity(repo):
    last = {}
    for f in log_files(repo):
        for ln in repo.read(f).splitlines() if "/log/" in f else []:
            m = LOGLINE.match(ln)
            if m and (m.group(2) not in last or m.group(1) > last[m.group(2)]):
                last[m.group(2)] = m.group(1)
    return last


def cmd_status(repo, a):
    tasks, ready, blocked, stale = classify(repo)
    items = read_items(repo)
    by = {}
    for t in tasks:
        by.setdefault(t.get("for", "@?"), {}).setdefault(t.get("st", "OPEN"), 0)
        by[t.get("for", "@?")][t.get("st", "OPEN")] += 1
    types = {}
    for i in items:
        types[i.get("type", "?")] = types.get(i.get("type", "?"), 0) + 1
    data = {"tasks_by_person": by, "ready": [t["id"] for t in ready], "blocked": [{"id": b["id"], "waiting_on": b["waiting_on"]} for b in blocked],
            "stale_started": [t["id"] for t in stale], "open_items": types, "last_activity": last_activity(repo)}
    if a.json:
        return emit(a, data, "")
    print("tasks by person:", "; ".join(f"{p}: " + ", ".join(f"{n} {s}" for s, n in d.items()) for p, d in by.items()) or "none")
    print("ready:", ", ".join(f"{t['id']} {t['text'][:50]}" for t in ready) or "none")
    print("blocked:", ", ".join(f"{b['id']} (waits on {','.join(b['waiting_on'])})" for b in blocked) or "none")
    print("stale STARTED:", ", ".join(f"{t['id']} {t['text'][:40]}" for t in stale) or "none")
    print("open items:", ", ".join(f"{n} {t}" for t, n in types.items()) or "none")
    print("last activity:", ", ".join(f"@{p} {s}" for p, s in data["last_activity"].items()) or "none")
    from . import hygiene
    ms = hygiene.milestone_lines(repo)
    if ms:
        print("milestones:\n" + "\n".join(ms))
    snap = hygiene.history_snapshot(repo)
    left = [r for r in hygiene.state(repo, snap) + hygiene.status_rows(repo, snap) if r[0] != "stale-started"]
    if left:
        print(f"leftover/stale: {len(left)} (ws sweep)")
    return 1 if stale else 0


def section_text(repo, rel, heading, limit=14):
    if not repo.exists(rel):
        return []
    lines = repo.read(rel).split("\n")
    try:
        i = next(k for k, l in enumerate(lines) if l.strip() == heading)
    except StopIteration:
        return []
    out = []
    for l in lines[i + 1:]:
        if l.startswith("## "):
            break
        if l.strip() and not l.strip().startswith(("<", "-")) or (l.startswith("- ") and len(l) > 3):
            out.append(l)
    return out[:limit]


def cmd_start(repo, a):
    try:
        user = repo.user(a.you)
    except WsError as e:
        user, warn_user = None, str(e)
    out = []
    if user is None:
        out.append(f"! {warn_user}")
    elif not repo.exists(f"_workboard/people/{user}"):
        out.append(f"! no personal folder yet: ws log add \"...\" creates it (or follow scaffold.md)")
    out.append("== status_log.md")
    for h in ("## Stage", "## Standing directions", "## Current focus"):
        s = [l for l in section_text(repo, "status_log.md", h) if not l.startswith("-") or len(l) > 3]
        if s:
            out.append(f"{h[3:]}: " + " ".join(x.strip("- ") for x in s)[:240])
    tasks, ready, blocked, stale = classify(repo)
    mine = [t for t in tasks if user and t.get("for") == "@" + user]
    started = [t for t in tasks if t.get("st") == "STARTED"]
    out.append("== tasks")
    for t in mine:
        out.append(f"  yours   {t['id']} {t.get('st', 'OPEN'):10} {t['text'][:80]}")
    for t in started:
        if t not in mine:
            out.append(f"  started {t['id']} {t.get('for', ''):8} touching={t.get('touching', '-')}  {t['text'][:60]}")
    out.append(f"  ready: {len(ready)}  blocked: {len(blocked)}  stale STARTED: {', '.join(t['id'] for t in stale) or 'none'}")
    items = read_items(repo)
    out.append("== open items")
    for i in [x for x in items if user and x.get("for") == "@" + user][:6]:
        out.append(f"  for you {i['id']} {i.get('type', ''):10} {i['text'][:80]}")
    out.append(f"  total: {len(items)}")
    rows = []
    for f in log_files(repo):
        for ln in repo.read(f).splitlines() if "/log/" in f else []:
            m = LOGLINE.match(ln)
            if m:
                rows.append((m.group(1), ln, m.group(2)))
    rows.sort()
    out.append("== recent log")
    out += ["  " + r[1][:150] for r in rows[-8:]] or ["  (none)"]
    if user and repo.is_git():
        mine_l = [r for r in rows if r[2] == user]
        if mine_l:
            since = parse_stamp(mine_l[-1][0]).strftime("%Y-%m-%dT%H:%M:%SZ")
            rc, lg, _ = repo.git("log", f"--since={since}", "--format=%h %an %s", "-n", "15")
            out.append(f"== git since your last log line ({mine_l[-1][0]})")
            out += ["  " + l for l in lg.strip().splitlines()] or ["  (no commits)"]
        rc, st, _ = repo.git("status", "--porcelain")
        if st.strip():
            out.append(f"  uncommitted: {len(st.strip().splitlines())} path(s)")
        rc, ab, _ = repo.git("rev-list", "--left-right", "--count", "HEAD...@{u}")
        if rc == 0:
            ahead, behind = ab.split()
            out.append(f"  ahead {ahead}, behind {behind} (git fetch first if behind)")
    from . import hygiene
    snap = hygiene.history_snapshot(repo)
    left = hygiene.state(repo, snap) + hygiene.status_rows(repo, snap)
    if left:
        out.append(f"== leftover/stale: {len(left)} (ws sweep lists them; --apply closes finished ones)")
        out += ["  " + r[4][:130] for r in left[:5]]
    from . import hygiene
    todo = {f: hygiene.placeholders(repo, f, repo.read(f)) for f in ("AGENTS.md", "README.md", "status_log.md") if repo.exists(f)}
    todo = {f: v for f, v in todo.items() if v}
    if todo:
        out.append("== setup: fill in " + "; ".join(f"{f} ({', '.join('<' + x + '>' for x in v[:2])})" for f, v in todo.items()))
    from . import review
    waiting = review.awaiting(repo)
    if waiting:
        out.append(f"== approve: {len(waiting)} change(s) to canon or steering by agents wait for a person (ws approve)")
    if (repo.ws / "update-notes.md").exists():
        out.append("== update notes: _steering/.ws/update-notes.md (what the last ws update changed in your files; delete it when read)")
    ov = [t for t in tasks if t.get("due") and t["due"] < day()]
    if ov:
        out.append("== overdue: " + ", ".join(f"{t['id']} (due {t['due']})" for t in ov))
    ms = hygiene.milestone_lines(repo)
    if ms:
        out.append("== milestones")
        out += ms[:4]
    F = run_checks(repo)
    cnt = {s: sum(1 for x in F if x["severity"] == s) for s in ("error", "warn")}
    out.append(f"== check: {cnt['error']} error(s), {cnt['warn']} warning(s) (ws check)")
    print("\n".join(out))
    return 0


def porcelain_paths(repo):
    rc, out, _ = repo.git("status", "--porcelain", "-z", "--untracked-files=all")
    paths, parts, i = [], out.split("\0"), 0
    while i < len(parts):
        p = parts[i]
        if len(p) > 3:
            if p[0] in "RC":
                i += 1
            paths.append(p[3:])
        i += 1
    return paths


# ---- scaffold --------------------------------------------------------------------
def owner_module(repo, folder):
    best, bl = None, -1
    folder = folder.rstrip("/") + "/"
    for e in repo.where_entries(all_modules=True):
        p = e["path"].split("<")[0]
        p = p if p.endswith("/") else p.rsplit("/", 1)[0] + "/" if "/" in p else ""
        if p and (folder.startswith(p) or p.startswith(folder)) and len(p) > bl and repo.steer_has_dir(f"modules/{e['module']}/scaffold/{folder.rstrip('/')}"):
            best, bl = e["module"], len(p)
    if best is None:
        for m in repo.manifests:
            if repo.steer_has_dir(f"modules/{m}/scaffold/{folder.rstrip('/')}"):
                return m
    return best


def scaffold_folder(repo, folder, apply=True):
    """Copy the starter files of `folder` (direct files only), without overwriting. Returns the list of created files."""
    folder = folder.strip("/")
    mod = owner_module(repo, folder)
    if not mod:
        raise WsError(f"no module has starter files for {folder}/", 2)
    made = []
    parents = [p for p in Path(folder).parents if str(p) not in (".", "")][::-1]
    for d in [str(p) for p in parents] + [folder]:
        for name, f in repo.steer_list(f"modules/{owner_module(repo, d) or mod}/scaffold/{d}").items():
            dst = repo.abs(f"{d}/{name}")
            if not dst.exists():
                made.append(f"{d}/{name}")
                if apply:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(f, dst)
    if not made and apply:
        (repo.root / folder).mkdir(parents=True, exist_ok=True)
    return mod, made


def write_enabled(repo):
    cfg = repo.ws / "config.yaml"
    t = cfg.read_text(encoding="utf-8")
    t = re.sub(r"(enabled:\s*)\[[^\]]*\]", lambda m: m.group(1) + "[" + ", ".join(repo.enabled) + "]", t, count=1)
    atomic_write(cfg, t)


def enable_plan(repo, name):
    """The modules that enabling `name` turns on: its missing requirements first, then itself."""
    if name not in repo.manifests:
        raise WsError(f"unknown module {name} (ws modules lists them)", 2)
    out = []

    def walk(n):
        for r in repo.manifests[n].get("requires") or []:
            if r in repo.manifests:
                walk(r)
        if n not in repo.enabled and n not in out:
            out.append(n)
    walk(name)
    return out


def disable_plan(repo, name):
    """[name] when it can be switched off. A module that is unknown, already off, core, or required by an enabled one is refused."""
    if name not in repo.manifests:
        raise WsError(f"unknown module {name} (ws modules lists them)", 2)
    if name not in repo.enabled:
        raise WsError(f"{name} is already off", 2)
    if name == "core":
        raise WsError("core cannot be switched off: every other module relies on it", 2)
    needed = sorted(m for m in repo.enabled if m != name and name in (repo.manifests.get(m, {}).get("requires") or []))
    if needed:
        raise WsError(f"{name} is required by {', '.join(needed)}: disable {'that' if len(needed) == 1 else 'those'} first", 2)
    return [name]


def enable_module(repo, name, seen=None):
    seen = seen if seen is not None else []
    for n in enable_plan(repo, name):
        seen.append(n)
        repo.enabled.append(n)
    write_enabled(repo)
    return seen


def disable_module(repo, name):
    disable_plan(repo, name)
    repo.enabled.remove(name)
    write_enabled(repo)
    return [name]


def starters(repo, name):
    return sorted(r for r in repo.steer_rglob(f"modules/{name}/scaffold") if not repo.exists(r))


def cmd_scaffold(repo, a):
    if a.target.endswith(".md"):   # one starter file, for example docs/roadmap.md
        for m in repo.manifests:
            src = repo.steer_path(f"modules/{m}/scaffold/{a.target}")
            if src is not None and src.is_file():
                if repo.exists(a.target):
                    raise WsError(f"{a.target} already exists", 2)
                if a.apply:
                    repo.abs(a.target).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, repo.abs(a.target))
                print(("created: " if a.apply else "would create: ") + a.target + ("" if a.apply else " (add --apply)"))
                return 0
        raise WsError(f"no module has a starter file {a.target}", 2)
    if a.target in repo.manifests:
        if a.apply:
            added = enable_module(repo, a.target)
            gen.apply(repo, write=True)
            st = starters(repo, a.target)
            emit(a, {"enabled": added, "starter_files": st}, f"enabled: {', '.join(added) or 'already on'}; generated blocks refreshed" + (f"\nstarter files when needed: ws scaffold {st[0].rsplit('/', 1)[0] if len(st) > 1 else st[0]} --apply" if st else ""))
        else:
            print(f"would enable {a.target} (and what it requires); add --apply")
        return 0
    mod, made = scaffold_folder(repo, a.target, apply=a.apply)
    if mod not in repo.enabled:
        warn(f"module {mod} is not enabled; enabling is a decision: ws scaffold {mod} --apply")
    emit(a, {"module": mod, "created": made, "applied": a.apply}, ("created: " if a.apply else "would create: ") + (", ".join(made) or "nothing (starter files exist)"))
    return 0
