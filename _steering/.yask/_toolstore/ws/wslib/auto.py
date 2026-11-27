"""The automatic lifecycle. It runs at the start of ordinary ws commands, is silent unless it acts, and never asks anyone to
declare anything beforehand: it looks at the working tree and the history. Git only keeps history (it is created when missing);
the rules for several people and agents are ours.

  git       create the repository that keeps the workspace's history when there is none, with a baseline commit
  heal      finish a merge that stopped on conflicts: state files merged by id, generated blocks regenerated, a real
            conflict in a document keeps the shared version and sets your copy aside with an open item
  sweep     close tasks the log says are finished, park STARTED tasks nobody touched
  autosave  keep a few rolling snapshots of uncommitted work outside the branch (`ws restore`); a commit clears them
`ws sync` is the one explicit exchange with a shared remote."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .checks import secret_hits
from .repo import WsError, slug
from .util import atomic_write, flag, hex4, locked, stamp, warn

OWN_COMMITS = {"save", "squash", "archive", "git", "update", "sync", "hooks", "help", "approve"}   # commands that manage commits themselves
STATE = ("tasks.md", "_workboard/open-items.md")
LOGGLOB = re.compile(r"^_workboard/people/[^/]+/log/[^/]+\.md$")
ID_ITEM = re.compile(r"\{#([tolrm]-[0-9a-f]{4})\b")
ID_LOG = re.compile(r" \{([0-9a-f]{4})\}$")


def settings(repo):
    c = repo.config.get("lifecycle") or {}
    on = lambda k: c.get(k, True) is not False   # noqa: E731
    return {"git": on("git"), "heal": on("heal"), "sweep": on("sweep"), "autosave": on("autosave"),
            "sweep_hours": float(c.get("sweep_hours", 1)), "autosave_minutes": float(c.get("autosave_minutes", 10)),
            "autosave_keep": int(c.get("autosave_keep", 3))}


def state_file(repo):
    return repo.ws / "cache" / "auto.json"


def load_state(repo):
    try:
        return json.loads(state_file(repo).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(repo, st):
    try:
        with locked(repo):
            atomic_write(state_file(repo), json.dumps(st))
    except (OSError, WsError):
        pass


def gitpath(repo, name):
    rc, out, _ = repo.git("rev-parse", "--git-path", name)
    if rc or not out.strip():
        return None
    p = Path(out.strip())
    return p if p.is_absolute() else repo.root / p


def git_paths(repo, *names):
    """Resolve the usual in-worktree git paths with one subprocess instead of one per name."""
    d = getattr(repo, "_gitdir", None)
    if d is None:
        rc, out, _ = repo.git("rev-parse", "--absolute-git-dir")
        d = Path(out.strip()) if rc == 0 and out.strip() else False
        repo._gitdir = d
    if not d:
        return {n: gitpath(repo, n) for n in names}
    return {n: d / n for n in names}


def exists(repo, name, paths=None):
    p = paths.get(name) if paths is not None else gitpath(repo, name)
    return p is not None and p.exists()


def merging(repo, paths=None):
    return exists(repo, "MERGE_HEAD", paths)


def rebasing(repo, paths=None):
    return exists(repo, "rebase-merge", paths) or exists(repo, "rebase-apply", paths)


def author(name):
    return {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": f"{slug(name) or 'ws'}@localhost"}


def changed(repo):
    """Paths with uncommitted changes, ignored files excluded."""
    rc, out, _ = repo.git("status", "--porcelain", "-uall", "-z")
    paths = []
    parts = out.split("\0")
    i = 0
    while i < len(parts) and parts[i]:
        entry = parts[i]
        paths.append(entry[3:])
        i += 2 if entry[0] in "RC" else 1   # a rename lists its old name as the next field
    return paths


def scan(repo, paths):
    """Secrets and unresolved conflict markers in files about to be committed: {path: "line why"}. Those files are held back;
    the rest of the history still gets written."""
    out = {}
    for p in paths:
        f = repo.abs(p)
        if p.startswith(("_steering/.yask/", ".dev_yask/")) or not f.is_file() or f.stat().st_size > 2_000_000:   # shipped and development files are not project content
            continue
        try:
            t = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = [f"{p}:{n} {name}" for n, name, _ in secret_hits(repo, t)]
        if p.endswith(".md") and re.search(r"(?m)^<<<<<<< ", t) and re.search(r"(?m)^>>>>>>> ", t):
            hits.append(f"{p}: unresolved merge conflict markers")
        if hits:
            out[p] = hits[0]
    return out


# ---- git -----------------------------------------------------------------------------
def ensure_git(repo, is_git=None):
    """Git keeps the history of the workspace. If there is no repository, create one and commit what is there. Returns True when created."""
    known = is_git if is_git is not None else repo.is_git()
    if not settings(repo)["git"] or known or shutil.which("git") is None:
        return False
    main = (repo.config.get("git") or {}).get("main_branch", "main")
    if repo.git("init", "-q", "-b", main)[0]:
        repo.git("init", "-q")
        repo.git("symbolic-ref", "HEAD", f"refs/heads/{main}")
    user = repo.user(None)
    for k, v in (("user.name", user), ("user.email", f"{user}@localhost")):
        if not repo.git("config", "--get", k)[1].strip():
            repo.git("config", k, v)
    note = "created the git repository that keeps this workspace's history"
    paths = changed(repo)
    from . import secrets
    for p in paths:
        secrets.scrub_file(repo, p)      # certain secrets move to .secrets, leaving placeholders
    held = scan(repo, paths)
    if paths:
        repo.git("add", "-A")
        if held:
            repo.git("reset", "-q", "--", *held)
        if repo.git("diff", "--cached", "--quiet")[0] == 1:
            repo.git("commit", "-q", "-m", "Initialized YASK workspace history", env=author("ws"))
            note += " and committed what was there"
    if held:
        first = next(iter(held.values()))
        note += f"; held back {len(held)} file(s) that look like secrets or conflicts ({first}): fix them, then ws save"
    warn(f"note: {note}")
    return True


# ---- heal: finish a merge that stopped on conflicts ----------------------------------------
def stage(repo, n, path):
    rc, out, _ = repo.git("show", f":{n}:{path}")
    return out if rc == 0 else None


def merge_text(repo, path):
    """Union of both sides' lines (git merge-file --union), then one line per id, preferring the shared (theirs) one."""
    ours, base, theirs = (stage(repo, n, path) or "" for n in (2, 1, 3))
    with tempfile.TemporaryDirectory() as d:
        files = []
        for name, t in (("ours", ours), ("base", base), ("theirs", theirs)):
            f = Path(d) / name
            f.write_text(t, encoding="utf-8", newline="\n")
            files.append(str(f))
        r = subprocess.run(["git", "merge-file", "-p", "--union", *files], capture_output=True, text=True, encoding="utf-8", cwd=repo.root)
    lines = r.stdout.split("\n")
    key = ID_LOG if LOGGLOB.match(path) else ID_ITEM
    shared = set(theirs.split("\n"))
    first, keep = {}, []
    for i, ln in enumerate(lines):
        m = key.search(ln) if ln.startswith("- ") else None
        if m:
            k = m.group(1)
            if k in first:
                if ln in shared and lines[first[k]] not in shared:
                    keep[first[k]] = False
                    first[k] = i
                    keep.append(True)
                else:
                    keep.append(False)
                continue
            first[k] = i
        keep.append(True)
    out = [ln for ln, k in zip(lines, keep) if k]
    deduped, seen = [], set()
    for ln in out:   # identical lines twice (both sides added the same thing)
        if ln.startswith("- ") and ln in seen:
            continue
        seen.add(ln)
        deduped.append(ln)
    return "\n".join(deduped)


def set_aside(repo, path, text, user):
    """Our side of a conflict in a document the shared version replaced: a copy, and an open item for a person."""
    from . import sessions
    from .util import render_item, new_id
    rel = f"_workboard/conflicts/{stamp()}-{hex4()}-{slug(path)[:40]}.txt"
    repo.abs(rel).parent.mkdir(parents=True, exist_ok=True)
    repo.abs(rel).write_text(text, encoding="utf-8", newline="\n")
    with locked(repo):
        lines = sessions.load(repo, sessions.ITEMS)
        iid = new_id(repo, "o")
        lines.insert(sessions.section_end(lines, "## Open"), "- " + render_item(f"Conflict in {path}: the shared version was kept; your copy is {rel}. Merge what you want from it, then delete the copy", iid, {"type": "question", "for": f"@{user}"}))
        atomic_write(repo.abs(sessions.ITEMS), "\n".join(lines))
    return rel


def heal(repo, user=None, paths=None):
    """Resolve a stopped merge by rule. Returns notes about what it did (empty when there was nothing to heal)."""
    if not merging(repo, paths):
        return []
    rc, out, _ = repo.git("diff", "--name-only", "--diff-filter=U")
    notes, user = [], user or repo.user(None)
    for p in [x for x in out.split("\n") if x.strip()]:
        if p in STATE or LOGGLOB.match(p):
            atomic_write(repo.abs(p), merge_text(repo, p))
            notes.append(f"{p}: merged by id")
        elif p == "AGENTS.md" or p.startswith("_steering/.yask/") or p.startswith("_steering/.ws/"):
            repo.git("checkout", "--theirs", "--", p)
            notes.append(f"{p}: took the shared version")
        else:
            theirs, ours = stage(repo, 3, p), stage(repo, 2, p)
            if theirs is None:
                repo.git("checkout", "--ours", "--", p)
                notes.append(f"{p}: you kept it, the shared side deleted it")
            else:
                if ours is not None and ours != theirs:
                    notes.append(f"{p}: the shared version was kept; your copy is {set_aside(repo, p, ours, user)} (open item added)")
                else:
                    notes.append(f"{p}: took the shared version")
                repo.git("checkout", "--theirs", "--", p)
        repo.git("add", "--", p)
    from . import gen
    gen.apply(repo, write=True)
    repo.git("add", "--", "AGENTS.md")
    rc, left, _ = repo.git("diff", "--name-only", "--diff-filter=U")
    if not left.strip():
        repo.git("add", "-A", "--", "tasks.md", "_workboard")
        rc, _, err = repo.git("commit", "--no-edit", "-q", env=author("ws"))
        notes.append("merge committed" if rc == 0 else f"merge not committed: {err.strip()[:100]}")
        done = sweep(repo, user)
        if done:
            notes.append(f"closed {len(done)} leftover task(s) the merge brought back")
    return notes


# ---- sweep and autosave ----------------------------------------------------------------------------
def sweep(repo, user):
    from . import hygiene
    snap = hygiene.history_snapshot(repo)
    rows = [r for r in hygiene.state(repo, snap) + hygiene.status_rows(repo, snap) if r[5]]
    return hygiene.apply_fixes(repo, rows, user) if rows else []


REF = "refs/yask/autosave/"


def snapshots(repo, head=None):
    """[(ref, sha, ts, tree)] oldest first. Only snapshots taken on top of the current HEAD count: a commit since then
    (made by anything) turns them into history, so they are dropped."""
    rc, out, _ = repo.git("for-each-ref", "--sort=refname", "--format=%(refname)|%(objectname)|%(parent)|%(creatordate:unix)|%(tree)", REF)
    rows = []
    for ln in out.split("\n"):
        if ln.count("|") == 4:
            ref, sha, parent, ts, tree = ln.split("|")
            rows.append((ref, sha, int(ts), tree, parent.strip()))
    if not rows:
        return []
    head = head.strip() if head is not None else repo.git("rev-parse", "--verify", "-q", "HEAD")[1].strip()
    live = []
    for ref, sha, ts, tree, parent in rows:
        if parent != head:
            repo.git("update-ref", "-d", ref)
        else:
            live.append((ref, sha, ts, tree))
    return live


def dist(repo, a, b):
    t = 0
    for ln in repo.git("diff", "--numstat", a, b)[1].split("\n"):
        p = ln.split("\t")
        if len(p) >= 2:
            t += sum(int(x) for x in p[:2] if x.isdigit()) or 1
    return t


def prune(repo, rows, keep, base_tree):
    """Keep `keep` snapshots as different from each other as possible: drop the one whose removal loses the least."""
    while len(rows) > max(keep, 1):
        best = None
        for i in range(len(rows) - 1):                 # never the newest
            prev = rows[i - 1][3] if i else base_tree
            loss = dist(repo, prev, rows[i][3]) + dist(repo, rows[i][3], rows[i + 1][3]) - dist(repo, prev, rows[i + 1][3])
            if best is None or loss < best[0]:
                best = (loss, i)
        repo.git("update-ref", "-d", rows.pop(best[1])[0])
    return rows


def take(repo, held):
    """The working tree as a tree object, built in a temporary index so the person's staged work is never touched."""
    with tempfile.TemporaryDirectory() as d:
        env = {"GIT_INDEX_FILE": str(Path(d) / "index")}
        repo.git("read-tree", "HEAD", env=env)
        repo.git("add", "-A", env=env)
        if held:
            repo.git("reset", "-q", "--", *held, env=env)
        return repo.git("write-tree", env=env)[1].strip()


def autosave(repo, gpaths=None, is_git=None, files=None):
    """Keep a rolling set of snapshots of uncommitted work (lifecycle.autosave_keep, spaced by what changed), outside the
    branch: nothing shows in git log or is pushed, and a commit clears them. Silent, except when a secret is held back."""
    c = settings(repo)
    git_ok = is_git if is_git is not None else repo.is_git()
    if not c["autosave"] or not git_ok or merging(repo, gpaths) or rebasing(repo, gpaths):
        return None
    files = files if files is not None else changed(repo)
    if not files:
        snapshots(repo)     # a commit since the last snapshot clears it even with no new work
        return None
    rc, head, _ = repo.git("rev-parse", "--verify", "-q", "HEAD")
    if rc:
        return None
    base_tree = repo.git("rev-parse", "HEAD^{tree}")[1].strip()
    rows = snapshots(repo, head=head)
    if rows and time.time() - rows[-1][2] < c["autosave_minutes"] * 60:
        return None
    from . import secrets
    for p in files:
        secrets.scrub_file(repo, p)
    held = scan(repo, files)
    if held:
        st = load_state(repo)
        sig = ";".join(sorted(held.values()))
        if st.get("held") != sig:
            warn(f"note: autosave leaves out {len(held)} file(s): {next(iter(held.values()))}; decide: ws secret move <path>:<line> (it is a secret) or ws secret allow <path>:<line> (it is not)")
            st["held"] = sig
            save_state(repo, st)
    tree = take(repo, held)
    if not tree or tree == base_tree or (rows and rows[-1][3] == tree):
        return None
    rc, sha, _ = repo.git("commit-tree", tree, "-p", head.strip(), "-m", f"Autosave {stamp()}", env=author("ws autosave"))
    if rc:
        return None
    repo.git("update-ref", f"{REF}{time.time_ns()}", sha.strip())   # the name orders them, whatever the clock resolution
    prune(repo, snapshots(repo, head=head), c["autosave_keep"], base_tree)
    return len(files) - len(held)


def commit_all(repo, msg, who="ws"):
    """A real commit of everything uncommitted except files that look like secrets or conflicts."""
    paths = changed(repo)
    if not paths:
        return False
    from . import secrets
    for p in paths:
        secrets.scrub_file(repo, p)
    held = scan(repo, paths)
    repo.git("add", "-A")
    if held:
        repo.git("reset", "-q", "--", *held)
    if repo.git("diff", "--cached", "--quiet")[0] != 1:
        return False
    return repo.git("commit", "-q", "-m", msg, env=author(who))[0] == 0


def cmd_restore(repo, a):
    """The autosave snapshots of uncommitted work, newest first; give a path to bring its snapshot version back."""
    if not repo.is_git():
        raise WsError("not a git repository", 3)
    rows = list(reversed(snapshots(repo)))
    if not rows:
        print("no autosaves (a commit clears them; they are taken while you have uncommitted work)")
        return 0
    n = max(1, int(a.src or 1))
    if not a.path:
        for i, (ref, sha, ts, tree) in enumerate(rows, 1):
            files = repo.git("diff", "--name-only", "HEAD", tree)[1].split()
            print(f"{i}  {int((time.time() - ts) // 60)} min ago  {len(files)} file(s): " + ", ".join(files[:4]) + (" ..." if len(files) > 4 else ""))
        print("ws restore <path> [--from N] [--apply] brings that file back from snapshot N (1 = newest)")
        return 0
    if n > len(rows):
        raise WsError(f"only {len(rows)} autosave(s)", 2)
    sha = rows[n - 1][1]
    rc, text, _ = repo.git("show", f"{sha}:{a.path}")
    if rc:
        raise WsError(f"{a.path} is not in autosave {n}", 2)
    cur = repo.abs(a.path).read_text(encoding="utf-8") if repo.abs(a.path).exists() else ""
    if text == cur:
        print("identical to the working file")
        return 0
    if not a.apply:
        import difflib
        d = list(difflib.unified_diff(cur.splitlines(), text.splitlines(), "now", f"autosave {n}", lineterm="", n=1))
        print("\n".join(d[:60]) + f"\n(add --apply to bring autosave {n} back)")
        return 0
    atomic_write(repo.abs(a.path), text)
    print(f"restored {a.path} from autosave {n}")
    return 0


def run(repo, cmd, user=None, is_git=None):
    """The automatic steps that follow git, in order. Returns notes already printed."""
    if not flag("YASK_LIFECYCLE") or cmd == "help":
        return
    git_ok = is_git if is_git is not None else repo.is_git()
    if not git_ok:
        return
    c = settings(repo)
    gpaths = git_paths(repo, "MERGE_HEAD", "rebase-merge", "rebase-apply") if c["heal"] or c["autosave"] else {}
    if c["heal"]:
        for n in heal(repo, user, gpaths):     # heal resolves the user only when there is a merge to log
            warn(f"note: healed a merge: {n}")
    if cmd in OWN_COMMITS:
        return
    if c["sweep"]:
        st = load_state(repo)
        if time.time() - float(st.get("swept", 0)) >= c["sweep_hours"] * 3600:
            st["swept"] = time.time()
            save_state(repo, st)
            from . import secrets
            secrets.purge_temp(repo)
            done = sweep(repo, user or repo.user(None))
            if done:
                warn(f"note: closed or parked {len(done)} leftover task(s) ({', '.join(i for _, i in done[:4])}); details: ws sweep")
    autosave(repo, gpaths=gpaths, is_git=git_ok)


# ---- ws sync ------------------------------------------------------------------------------------------
def cmd_sync(repo, a):
    """Exchange with the shared remote: commit what is uncommitted, merge the remote, resolve by our rules, push."""
    if not repo.is_git():
        raise WsError("not a git repository", 3)
    if not repo.git("remote")[1].strip():
        raise WsError("no remote: git remote add origin <url> (local work never needs one)", 2)
    branch = repo.git("rev-parse", "--abbrev-ref", "HEAD")[1].strip()
    if branch == "HEAD":
        raise WsError("detached HEAD: switch to a branch first", 2)
    user = repo.user(a.you)
    log = [f"healed: {n}" for n in heal(repo, user)]
    commit_all(repo, "Sync", "ws")   # files held back for a secret or a conflict marker simply stay out of what is pushed
    for attempt in range(3):
        rc, _, err = repo.git("fetch", "-q", "origin")
        if rc:
            raise WsError(f"fetch failed: {err.strip()[:160]}", 3)
        up = f"origin/{branch}"
        if repo.git("rev-parse", "--verify", "-q", up)[0] == 0 and repo.git("merge-base", "--is-ancestor", up, "HEAD")[0] != 0:
            rc, _, err = repo.git("merge", "--no-edit", "-q", up, env=author("ws"))
            if rc:
                notes = heal(repo, user)
                if merging(repo) or repo.git("diff", "--name-only", "--diff-filter=U")[1].strip():
                    raise WsError("the merge stopped on conflicts ws could not settle; finish it with git, then ws sync", 2)
                log += [f"healed: {n}" for n in notes]
            else:
                log.append(f"merged {up}")
                done = sweep(repo, user)
                if done:
                    log.append(f"closed {len(done)} leftover task(s) the merge brought back")
        from . import gen
        gen.apply(repo, write=True)
        if repo.git("status", "--porcelain", "--", "AGENTS.md")[1].strip():
            repo.git("add", "--", "AGENTS.md")
            repo.git("commit", "-q", "-m", "Refreshed generated blocks", env=author("ws"))
        rc, _, err = repo.git("push", "-q", "-u", "origin", branch)
        if rc == 0:
            log.append(f"pushed {branch}")
            break
        log.append("the remote moved; trying again")
    else:
        raise WsError("push kept being rejected; try again", 3)
    print("\n".join(log) if log else "already in sync")
    return 0
