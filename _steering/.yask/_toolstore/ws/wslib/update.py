"""ws update: keep `_steering/.yask/` in step with a release package on GitHub.

The shipped layer is mirrored from the release (files added, changed, removed). The project's `_steering/` is never
replaced. Everything about updating is the `update` section of `_steering/.yask/yask.yaml`, which is part of the shipped
layer rather than the project's config: the settings (`auto`, `repo`, `interval_hours`, `commit`) and, from the NEW release's
copy, `reconcile` and `notify`, which say how new options reach the project's own files (`.ws/config.yaml` and the like):
additive merges only, never overwriting a value the project chose. Without that file the automatic check does not run, and
it does nothing until `update.repo` is set in it."""
import hashlib
import io
import json
import os
import re
import shutil
import tarfile
import tempfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

from . import yamlsub
from .repo import WsError
from .util import atomic_write, emit, flag, locked, now, stamp, warn

API = "https://api.github.com/repos/{repo}/releases/latest"
SETTINGS = "yask.yaml"   # in the shipped layer: settings about YASK itself, not about the project; its `update` section holds the update options and instructions
NOTES = "update-notes.md"


def settings(repo):
    """The `update` section of _steering/.yask/yask.yaml. Without the file there is no automatic update."""
    f = repo.base / SETTINGS
    c = (yamlsub.loads(f.read_text(encoding="utf-8")).get("update") or {}) if f.exists() else {}
    return {"auto": f.exists() and c.get("auto", True) is not False, "repo": str(c.get("repo") or "").strip(),
            "interval_hours": float(c.get("interval_hours", 24)), "commit": c.get("commit", True) is not False}


def vkey(v):
    p = tuple(int(x) for x in re.findall(r"\d+", str(v))[:4]) or (0,)
    return p + (0,) * (4 - len(p))


def local_version(repo):
    f = repo.base / "VERSION"
    return f.read_text(encoding="utf-8").strip() if f.exists() else "0"


# ---- getting a release -----------------------------------------------------------------------
def http(url, timeout=6, limit=60_000_000):
    if not url.startswith("https://"):
        raise WsError("updates are fetched over https only", 2)
    req = urllib.request.Request(url, headers={"User-Agent": "yask-ws", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(limit + 1)
    if len(data) > limit:
        raise WsError("release package is larger than the limit", 2)
    return data


def latest(slug):
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", slug):
        raise WsError(f"update.repo must look like owner/name, not {slug!r}", 2)
    d = json.loads(http(API.format(repo=slug)).decode("utf-8"))
    assets = d.get("assets") or []
    zips = [x for x in assets if str(x.get("name", "")).endswith(".zip")]
    pick = next((x for x in zips if str(x["name"]).lower().startswith("yask")), zips[0] if zips else None)
    url = pick["browser_download_url"] if pick else d.get("zipball_url")
    sha = next((x["browser_download_url"] for x in assets if pick and x.get("name") == pick["name"] + ".sha256"), None)
    if not url:
        raise WsError("that release has no package (no .zip asset and no source zip)", 2)
    return {"version": str(d.get("tag_name", "")).lstrip("vV"), "url": url, "sha_url": sha}


def unpack(blob, into):
    with zipfile.ZipFile(io.BytesIO(blob) if isinstance(blob, bytes) else blob) as z:
        for n in z.namelist():
            t = (Path(into) / n).resolve()
            if Path(into).resolve() not in t.parents and t != Path(into).resolve():
                raise WsError("release package has an unsafe path; refusing", 2)
        z.extractall(into)
        for i in z.infolist():   # extractall drops the stored modes, and a launcher that is not executable stops every git hook
            if i.create_system == 3 and (i.external_attr >> 16) & 0o100:
                grant_exec(Path(into) / i.filename)


def grant_exec(p):
    """Give a file the executable bits that match its read bits. Never takes one away, and does nothing where the file system has none."""
    m = p.stat().st_mode
    p.chmod(m | ((m & 0o444) >> 2))


def lacks_exec(new, old):
    """The release's copy is executable and the project's is not: only ever a grant, so a project that chose otherwise keeps its mode."""
    return bool(new.stat().st_mode & 0o100) and not old.stat().st_mode & 0o100


def find_payload(folder):
    """The shipped layer inside an unpacked package: a folder with VERSION and playbooks/, preferring one called .yask."""
    cands = [v.parent for v in Path(folder).rglob("VERSION") if (v.parent / "playbooks").is_dir() and (v.parent / "modules").is_dir()]
    if not cands:
        raise WsError("no steering payload (VERSION with playbooks/ and modules/) in that package", 2)
    return sorted(cands, key=lambda p: (p.name != ".yask", len(p.parts)))[0]


# ---- planning and applying ---------------------------------------------------------------------
def files(root):
    return {f.relative_to(root).as_posix(): f for f in Path(root).rglob("*") if f.is_file() and "__pycache__" not in f.parts}


def plan(repo, pay):
    new, old = files(pay), files(repo.base)
    add = sorted(set(new) - set(old))
    change = sorted(r for r in set(new) & set(old) if new[r].read_bytes() != old[r].read_bytes() or lacks_exec(new[r], old[r]))
    remove = sorted(set(old) - set(new))
    return {"add": add, "change": change, "remove": remove}


def snapshot(repo, cache):
    """Store everything an update touches in the temporary `_steering/.yask_cache/` area."""
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.unlink(missing_ok=True)
    with tarfile.open(cache, "w") as t:
        for rel in TOUCHED:
            p = repo.root / rel
            if p.exists() or p.is_symlink():
                t.add(p, arcname=rel, recursive=True)


def restore(repo, cache):
    """Put the pre-update state back when an update fails part-way through."""
    blob = cache.read_bytes()                 # the cache lives inside .ws, which is about to be replaced
    for rel in TOUCHED:
        p = repo.root / rel
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p)
        elif p.exists() or p.is_symlink():
            p.unlink()
    root = repo.root.resolve()
    with tarfile.open(fileobj=io.BytesIO(blob)) as t:
        for m in t.getmembers():
            target = (root / m.name).resolve()
            if target != root and root not in target.parents:
                raise WsError("update cache holds an unsafe path; refusing to restore", 2)
        try:
            t.extractall(path=repo.root, filter="tar")
        except TypeError:                     # Python before the tarfile filter argument
            t.extractall(path=repo.root)


def dirty_base(repo):
    if not repo.is_git():
        return False
    rc, out, _ = repo.git("status", "--porcelain", "--", "_steering/.yask")
    return rc == 0 and bool(out.strip())


TOUCHED = ("_steering/.yask", "_steering/.ws", "AGENTS.md")   # everything an update can change


def changed_paths(repo):
    rc, out, _ = repo.git("status", "--porcelain", "-uall", "--", *TOUCHED)
    return sorted({ln[3:].split(" -> ")[-1].strip().strip('"') for ln in out.splitlines() if ln.strip()}) if rc == 0 else []


def commit_update(repo, old, new, before):
    """Commit exactly what the update changed, straight onto main. This skips the review route on purpose: the content
    is a release the project chose to follow, not steering someone wrote. It never commits onto another branch and never
    takes in a change you had not committed. Returns None when committed, else why it was left for you."""
    if not repo.is_git():
        return "not a git repository"
    main = (repo.config.get("git") or {}).get("main_branch", "main")
    branch = repo.git("rev-parse", "--abbrev-ref", "HEAD")[1].strip()
    if branch != main:
        return f"you are on {branch or 'a detached HEAD'}, and updates are committed only onto {main}"
    if before:
        return f"you had uncommitted changes in {', '.join(before[:3])}; commit them, then the update"
    paths = changed_paths(repo)
    if not paths:
        return "nothing changed"
    if repo.git("add", "--", *paths)[0]:
        return "git add failed"
    msg = f"Updated YASK\n\n{old} -> {new}\n\nWs-Update: {old} -> {new}"
    rc, _, err = repo.git("commit", "-q", "-m", msg, "--", *paths, env={"GIT_AUTHOR_NAME": "ws update", "GIT_AUTHOR_EMAIL": "ws-update@localhost"})
    return None if rc == 0 else f"git commit refused it ({err.strip()[:100]})"


def mirror(repo, pay, pl):
    for r in pl["add"] + pl["change"]:
        dst = repo.base / r
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pay / r, dst)
        if (pay / r).stat().st_mode & 0o100:
            grant_exec(dst)
    for r in pl["remove"]:
        (repo.base / r).unlink(missing_ok=True)
    for d, dirs, fs in os.walk(repo.base, topdown=False):
        if not dirs and not fs and Path(d) != repo.base:
            Path(d).rmdir()


# ---- reconciling the project's own files -------------------------------------------------------
TOP = re.compile(r"^([A-Za-z_][\w-]*):(.*)$")


def top_blocks(lines):
    idx = [i for i, ln in enumerate(lines) if TOP.match(ln)]
    out = {}
    for n, i in enumerate(idx):
        nxt = idx[n + 1] if n + 1 < len(idx) else len(lines)
        end = nxt
        while end - 1 > i and (not lines[end - 1].strip() or lines[end - 1].startswith("#")):
            end -= 1
        start = i
        while start > 0 and lines[start - 1].startswith("#"):
            start -= 1
        out[TOP.match(lines[i]).group(1)] = {"start": start, "line": i, "end": end}
    return out


def merge_keys(proj, tmpl):
    """Add the template's keys the project file lacks: whole top-level blocks, and missing children of block-style sections."""
    pl, tl = proj.split("\n"), tmpl.split("\n")
    pb, tb = top_blocks(pl), top_blocks(tl)
    added = []
    for key, t in tb.items():
        if key not in pb:
            while pl and not pl[-1].strip():
                pl.pop()
            pl += [""] + tl[t["start"]:t["end"]]
            added.append(key)
    pb = top_blocks(pl)
    for key, t in tb.items():
        if key not in pb or key in added:
            continue
        head = TOP.match(pl[pb[key]["line"]]).group(2).split("#")[0].strip()
        if head:
            continue   # a one-line value (flow style): nothing to add inside it
        have = {m.group(1) for ln in pl[pb[key]["line"] + 1:pb[key]["end"]] if (m := re.match(r"^  ([A-Za-z_][\w-]*):", ln))}
        for ln in tl[t["line"] + 1:t["end"]]:
            m = re.match(r"^  ([A-Za-z_][\w-]*):", ln)
            if m and m.group(1) not in have:
                last = max(i for i in range(pb[key]["line"], pb[key]["end"]) if pl[i].strip())
                pl.insert(last + 1, ln)
                pb = top_blocks(pl)
                added.append(f"{key}.{m.group(1)}")
    return "\n".join(pl), added


def merge_entries(proj, tmpl, key):
    """Append the template's one-line list items whose `key` value the project's list lacks."""
    pl, tl = proj.split("\n"), tmpl.split("\n")
    pb, tb = top_blocks(pl), top_blocks(tl)
    added = []
    rx = re.compile(rf"\b{re.escape(key)}:\s*\"?([^,}}\"\s]+)")
    for name, t in tb.items():
        items = [ln for ln in tl[t["line"] + 1:t["end"]] if re.match(r"^\s*-\s*\{", ln) and rx.search(ln)]
        if not items:
            continue
        if name not in pb:
            while pl and not pl[-1].strip():
                pl.pop()
            pl += [""] + tl[t["start"]:t["end"]]
            added += [rx.search(i).group(1) for i in items]
            pb = top_blocks(pl)
            continue
        if TOP.match(pl[pb[name]["line"]]).group(2).split("#")[0].strip() not in ("", "[]"):
            continue
        have = {rx.search(ln).group(1) for ln in pl[pb[name]["line"] + 1:pb[name]["end"]] if rx.search(ln)}
        for it in items:
            v = rx.search(it).group(1)
            if v not in have:
                if TOP.match(pl[pb[name]["line"]]).group(2).split("#")[0].strip() == "[]":
                    pl[pb[name]["line"]] = f"{name}:"
                last = max(i for i in range(pb[name]["line"], pb[name]["end"]) if pl[i].strip())
                pl.insert(last + 1, it)
                pb = top_blocks(pl)
                have.add(v)
                added.append(v)
    return "\n".join(pl), added


def reconcile(repo, pay, old_version):
    """Apply the `update` instructions (reconcile, notify) in the new release's yask.yaml to the project's own steering files. Returns note lines."""
    f = pay / SETTINGS
    if not f.exists():
        return []
    ins = yamlsub.loads(f.read_text(encoding="utf-8")).get("update") or {}
    notes = []
    for r in ins.get("reconcile") or []:
        rel, method = str(r.get("file", "")), str(r.get("method", ""))
        tpl, mine = pay / rel, repo.steer / rel
        if method == "ignore" or not tpl.exists():
            continue
        if not mine.exists():
            mine.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(tpl, mine)
            notes.append(f"{rel}: created from the shipped copy")
            continue
        text = mine.read_text(encoding="utf-8")
        if method == "add-missing-keys":
            new, added = merge_keys(text, tpl.read_text(encoding="utf-8"))
        elif method == "add-missing-entries":
            new, added = merge_entries(text, tpl.read_text(encoding="utf-8"), str(r.get("key", "")))
        elif method == "notify":
            notes.append(f"{rel}: {r.get('message', 'changed in the release; review it')}")
            continue
        else:
            raise WsError(f"{SETTINGS}: update.reconcile: unknown method {method!r}", 2)
        if added:
            mine.write_text(new, encoding="utf-8", newline="\n")
            notes.append(f"{rel}: added {', '.join(added)}")
    for n in ins.get("notify") or []:
        if vkey(old_version) < vkey(n.get("since", "0")) <= vkey((pay / "VERSION").read_text().strip()):
            notes.append(str(n.get("message", "")))
    return [x for x in notes if x]


def write_notes(repo, old, new, notes):
    p = repo.ws / NOTES
    head = '---\nkind: steering\ndescription: "What ws update changed in this project\'s own files, and what needs a person. Delete when read."\n---\n# Update notes\n\n'
    text = p.read_text(encoding="utf-8") if p.exists() else head
    text += f"## {old} to {new} ({stamp()})\n" + ("".join(f"- {n}\n" for n in notes) or "- nothing in your files needed changing\n") + "\n"
    p.write_text(text, encoding="utf-8", newline="\n")


def apply_update(repo, pay, commit=False):
    old = local_version(repo)
    new = (pay / "VERSION").read_text(encoding="utf-8").strip()
    pl = plan(repo, pay)
    before = changed_paths(repo) if commit and repo.is_git() else []   # what you had in progress, so it is never swept in
    cache = repo.steer / ".yask_cache" / "update-cache.tar"
    try:
        snapshot(repo, cache)                 # inside the workspace; removed before this command returns
        with locked(repo):
            try:
                mirror(repo, pay, pl)
                notes = reconcile(repo, pay, old)
                from . import steering
                notes += [f"{r}: the shipped file changed since your copy was made (ws steering diff {r})" for r in steering.behind(repo)]
                from . import gen
                gen.apply(repo, write=True)
                write_notes(repo, old, new, notes)
            except Exception:
                restore(repo, cache)          # failed apply: every touched path is exactly as it was
                raise
    finally:
        cache.unlink(missing_ok=True)
        if cache.parent.is_dir() and not any(cache.parent.iterdir()):
            cache.parent.rmdir()
    code = any(r.startswith("_toolstore/") for k in pl.values() for r in k)
    why = commit_update(repo, old, new, before) if commit and repo.is_git() else None
    return {"from": old, "to": new, "plan": pl, "notes": notes, "code_changed": code,
            "committed": commit and repo.is_git() and why is None, "not_committed": why or ""}


# ---- commands -------------------------------------------------------------------------------------
def source(repo, a):
    """An unpacked payload folder, from --from (folder or zip) or the configured GitHub repo. Returns (payload, tempdir)."""
    tmp = tempfile.mkdtemp(prefix="yask-")
    if a.src:
        s = Path(a.src)
        if s.is_dir():
            return find_payload(s), tmp
        if not s.is_file():
            raise WsError(f"{a.src} is not a folder or a zip", 2)
        unpack(s, tmp)
        return find_payload(tmp), tmp
    slug = a.repo or settings(repo)["repo"]
    if not slug:
        raise WsError("no update source: set update.repo (owner/name) in _steering/.yask/yask.yaml, or use --from <folder or zip>", 2)
    rel = latest(slug)
    blob = http(rel["url"])
    if rel["sha_url"]:
        want = http(rel["sha_url"]).decode().split()[0].lower()
        if hashlib.sha256(blob).hexdigest() != want:
            raise WsError("package checksum does not match the published one; refusing", 2)
    unpack(blob, tmp)
    return find_payload(tmp), tmp


def cmd_update(repo, a):
    if a.notes:
        p = repo.ws / NOTES
        print(p.read_text(encoding="utf-8") if p.exists() else "no update notes")
        return 0
    pay, tmp = source(repo, a)
    try:
        new, old = (pay / "VERSION").read_text(encoding="utf-8").strip(), local_version(repo)
        pl = plan(repo, pay)
        n = sum(len(v) for v in pl.values())
        text = f"_steering/.yask {old} -> {new}: {len(pl['add'])} new, {len(pl['change'])} changed, {len(pl['remove'])} removed\n" \
               + "\n".join(f"  {k:7} {r}" for k in ("add", "change", "remove") for r in pl[k][:30])
        if not a.apply:
            emit(a, {"from": old, "to": new, **pl}, text + "\n(add --apply; your _steering/ is never replaced, and the old .yask is backed up first)")
            return 0
        if dirty_base(repo) and not a.force:
            raise WsError("_steering/.yask has uncommitted changes (edits belong in _steering/, which supersedes it): commit or revert them, or use --force", 2)
        if not n:
            print("already up to date")
            return 0
        r = apply_update(repo, pay, commit=a.commit or settings(repo)["commit"])
        tail = "committed onto main: Updated YASK" if r["committed"] else (f"NOT committed: {r['not_committed']}" if r["not_committed"] else "not committed (update.commit is off or this is not a git repository)")
        emit(a, r, f"updated .yask {r['from']} -> {r['to']}\n" + "\n".join(f"  {x}" for x in r["notes"]) + f"\n{tail}\nnotes: _steering/.ws/update-notes.md. Run: ws check")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_state(repo):
    state = repo.ws / "cache" / "update-check.json"
    try:
        return state, json.loads(state.read_text(encoding="utf-8")) if state.exists() else {}
    except (OSError, ValueError):
        return state, {}


def write_check_state(repo, st):
    try:
        with locked(repo):
            atomic_write(repo.ws / "cache" / "update-check.json", json.dumps(st))
    except (OSError, WsError):
        pass


def check_due(repo, c, st):
    if not c["auto"] or not c["repo"] or not flag("YASK_AUTOUPDATE") or any(os.environ.get(k) for k in ("WS_UPDATED", "CI")):
        return False
    now_t = time.time()
    if now_t - float(st.get("claim", 0)) < 60:      # a check claimed but not finished (process exited) is retried after a minute
        return False
    interval = c["interval_hours"] * 3600
    if st.get("error"):
        interval = min(interval, 900.0)            # back off after a network failure, but do not wait a whole day
    return now_t - float(st.get("checked", 0)) >= interval


def check(repo, c, st):
    """Release metadata only. The worker never downloads or applies anything: that happens at a command boundary."""
    try:
        rel = latest(c["repo"])
        st["release"] = rel
        st["seen"] = rel["version"]
        st["error"] = ""
    except Exception as e:
        st["error"] = str(e)[:200]
    st["checked"] = time.time()
    st["claim"] = 0
    write_check_state(repo, st)


def schedule_check(repo):
    """Claim a check and run it off the command path. `WS_UPDATE_SYNC=1` makes it synchronous."""
    c = settings(repo)
    _, st = check_state(repo)
    if not check_due(repo, c, st):
        return False
    st["claim"] = time.time()
    write_check_state(repo, st)
    if os.environ.get("WS_UPDATE_SYNC"):
        check(repo, c, st)
    else:
        threading.Thread(target=check, args=(repo, c, st), daemon=True, name="yask-update-check").start()
    return True


def auto_update(repo):
    """Apply a release the check already found. Returns True when tool code changed (the caller re-runs on the new code)."""
    c = settings(repo)
    if not c["auto"] or not c["repo"] or not flag("YASK_AUTOUPDATE") or any(os.environ.get(k) for k in ("WS_UPDATED", "CI")):
        return False
    _, st = check_state(repo)
    rel = st.get("release")
    if not rel and os.environ.get("WS_UPDATE_SYNC") and not st.get("checked"):
        check(repo, c, st)                          # direct callers with no prior check
        rel = st.get("release")
    if not rel or not rel.get("version"):
        return False
    if vkey(rel["version"]) <= vkey(local_version(repo)) or dirty_base(repo):
        return False
    tmp = None
    try:
        blob = http(rel["url"])
        if rel["sha_url"] and hashlib.sha256(blob).hexdigest() != http(rel["sha_url"]).decode().split()[0].lower():
            raise WsError("package checksum mismatch", 2)
        tmp = tempfile.mkdtemp(prefix="yask-")
        unpack(blob, tmp)
        r = apply_update(repo, find_payload(tmp), commit=c["commit"])
        repo._update_applied = True
        warn(f"note: updated _steering/.yask {r['from']} -> {r['to']}" + (f"; {len(r['notes'])} change(s) to your files, see _steering/.ws/update-notes.md" if r["notes"] else "")
             + ("; committed onto main (Updated YASK)" if r["committed"] else (f"; not committed: {r['not_committed']}" if r["not_committed"] else "")))
        st["updated"] = r["to"]
        write_check_state(repo, st)
        return r["code_changed"]
    except Exception as e:   # silent by design: a failed check must never get in the way of the command
        st["error"] = str(e)[:200]
        write_check_state(repo, st)
        return False
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
