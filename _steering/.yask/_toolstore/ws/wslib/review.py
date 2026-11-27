"""ws approve: changes to canon and steering that no person has looked at yet.

Nothing has to be declared beforehand. It is worked out from the history: a person's own commit of a file counts as having
looked at it, so only a change an agent committed (or, with review: all, anyone's change nobody else read) waits. `ws approve`
is for "I read it and it is fine"; it appends a REVIEWED line to your own log. Git is not asked to hold the gate."""
import hashlib

from .checks import LOGLINE, log_files
from .repo import WsError
from .util import emit, table
from . import sessions

CAP = 300


def mode(repo):
    m = str((repo.config.get("git") or {}).get("review", "agent"))
    return m if m in ("off", "agent", "all") else "agent"


def watched(repo):
    out = []
    for f in repo.md_files():
        if f.startswith("_steering/.yask/") or f.startswith("_steering/.ws/") or "/log/" in f:
            continue
        if f.startswith("_steering/") or repo.fm(f).get("kind") == "canon":
            out.append(f)
    return out[:CAP]


def digest(repo, rel):
    return hashlib.sha1(repo.abs(rel).read_bytes()).hexdigest()[:12]


def reviews(repo):
    """{(path, hash): {reviewer, ...}} from the REVIEWED lines in everyone's logs."""
    out = {}
    for f in log_files(repo):
        if "/log/" in f:
            for ln in repo.read(f).split("\n"):
                m = LOGLINE.match(ln)
                if m and m.group(4) == "REVIEWED" and "@" in m.group(5):
                    p, _, h = m.group(5).rpartition("@")
                    out.setdefault((p.strip(), h.strip()), set()).add(m.group(2))
    return out


def awaiting(repo):
    """[(path, author, hash)] for changes waiting for a person."""
    m = mode(repo)
    if m == "off" or not repo.is_git():
        return []
    seen, rows = reviews(repo), []
    for f in watched(repo):
        if repo.git("status", "--porcelain", "--", f)[1].strip():
            continue                                    # uncommitted: not yet a change anyone saved
        rc, out, _ = repo.git("log", "-1", "--format=%an", "--", f)
        who = out.strip()
        if rc or not who:
            continue
        agent = "+" in who or who.startswith("ws ")
        if m == "agent" and not agent:
            continue                                    # a person's own commit is their review
        base = who.split("+")[0]
        h = digest(repo, f)
        if seen.get((f, h), set()) - {base} if m == "all" else seen.get((f, h)):
            continue
        rows.append((f, who, h))
    return rows


def cmd_approve(repo, a):
    rows = awaiting(repo)
    if a.paths or a.all:
        if a.agent:
            raise WsError("a person approves; run it without --agent", 2)
        user = sessions.me(repo, a)
        pick = rows if a.all else [r for r in rows if any(r[0] == p or r[0].startswith(p.rstrip("/") + "/") for p in a.paths)]
        for f, _, h in pick:
            sessions.append_log(repo, user, "REVIEWED", f"{f}@{h}", False)
        emit(a, {"approved": [r[0] for r in pick]}, f"recorded your review of {len(pick)} file(s)" if pick else "nothing was waiting for you there")
        return 0
    emit(a, [{"path": f, "by": w} for f, w, _ in rows],
         table([(f, w) for f, w, _ in rows], ["changed by agents, not yet read", "author"]) + "\nws approve <paths>  (or --all) when you have read them" if rows else "nothing waits for you")
    return 0
