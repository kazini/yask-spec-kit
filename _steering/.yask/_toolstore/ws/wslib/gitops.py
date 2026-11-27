"""save, archive, purge, git health, maintain, offload."""
import hashlib
import json
import os
import posixpath
import re
import shlex
import shutil
import subprocess
import time
from collections import defaultdict
from pathlib import Path

from .checks import redaction_patterns, secret_hits
from .index import Index, norm
from .repo import WsError
from .sessions import scaffold_folder
from .util import atomic_write, emit, file_stamp, now, stamp, table


def need_git(repo):
    if not repo.is_git():
        raise WsError("not a git repository", 3)


def porcelain(repo):
    rc, out, _ = repo.git("status", "--porcelain", "-z", "--untracked-files=all")
    items, parts = [], out.split("\0")
    i = 0
    while i < len(parts):
        p = parts[i]
        if len(p) > 3:
            st, path = p[:2], p[3:]
            if st[0] in "RC":
                i += 1
            items.append((st, path))
        i += 1
    return items


def branch(repo):
    return repo.git("rev-parse", "--abbrev-ref", "HEAD")[1].strip()


# ---- save -----------------------------------------------------------------------
def cmd_save(repo, a):
    need_git(repo)
    cfg = repo.config.get("git") or {}
    paths = [p for _, p in porcelain(repo)]
    if a.paths:
        wanted = [x.rstrip("/") for x in a.paths]
        paths = [p for p in paths if any(p == w or p.startswith(w + "/") for w in wanted)]
    if not paths:
        print("nothing to save")
        return 0
    cur = branch(repo)
    user = repo.user(a.you)
    problems = []
    from . import secrets
    for p in paths:
        secrets.scrub_file(repo, p)           # certain secrets become placeholders in the file, values go to .secrets
    for p in paths:
        f = repo.abs(p)
        if f.is_file() and f.stat().st_size < 2_000_000 and not p.startswith(("_steering/.yask/", ".dev_yask/")):
            try:
                txt = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for n_, name, fp in secret_hits(repo, txt):
                problems.append(f"{p}:{n_}: may be a secret ({name}): ws secret move {p}:{n_} if it is one, ws secret allow {p}:{n_} if not")
    plan = {"branch": cur, "paths": paths, "problems": problems}
    problems = list(dict.fromkeys(problems))   # one line per place
    if problems:
        emit(a, plan, "refusing:\n" + "\n".join("  " + x for x in problems))
        return 2
    msg = a.message
    if not msg:
        raise WsError("--message is required", 2)
    trailers = [f"Ws-Task: {t}" for t in (a.task or [])]
    ai = cfg.get("ai_attribution", "none")
    if a.agent and ai == "trailer":
        trailers.append("AI-Assisted: yes")
    elif a.agent and ai == "co-author":
        trailers.append("Co-authored-by: Claude <noreply@anthropic.com>")
    full = msg + ("\n\n" + "\n".join(trailers) if trailers else "")
    if not a.apply:
        emit(a, plan, f"would commit {len(paths)} path(s) on {cur}:\n" + "\n".join(f"  {p}" for p in paths) + f"\nmessage: {msg}" + ("\n" + "\n".join(trailers) if trailers else "") + "\n(add --apply)")
        return 0
    repo.git("add", "--", *paths, check=True)
    from .collab import agent_env
    repo.git("commit", "-q", "-m", full, "--", *paths, check=True, env=agent_env(repo, user) if a.agent else None)
    out = f"committed {len(paths)} path(s) on {cur}"
    if a.push:
        rc, o, e = repo.git("push", "-u", "origin", "HEAD")
        out += "; pushed" if rc == 0 else f"; push failed: {e.strip()[:200]}"
    emit(a, plan, out)
    return 0


# ---- history rewrite engine ------------------------------------------------------
def have_filter_repo(repo):
    return repo.git("filter-repo", "--version")[0] == 0


def history_commits(repo, paths):
    rc, out, _ = repo.git("log", "--all", "--oneline", "--", *paths)
    return len(out.strip().splitlines()) if rc == 0 else 0


def rewrite_remove(repo, paths):
    paths = [p.rstrip("/") for p in paths]
    if have_filter_repo(repo):
        args = ["filter-repo", "--force", "--invert-paths"]
        for p in paths:
            args += ["--path", p]
        repo.git(*args, check=True)
        method = "git filter-repo"
    else:
        flt = "git rm -r -q --cached --ignore-unmatch -- " + " ".join(shlex.quote(p) for p in paths)
        env = dict(os.environ, FILTER_BRANCH_SQUELCH_WARNING="1")
        r = subprocess.run(["git", "filter-branch", "-f", "--prune-empty", "--index-filter", flt, "--tag-name-filter", "cat", "--", "--all"],
                           cwd=repo.root, capture_output=True, text=True, env=env)
        if r.returncode:
            raise WsError("git filter-branch failed: " + (r.stderr.strip()[-300:] or r.stdout.strip()[-300:]), 3)
        rc, refs, _ = repo.git("for-each-ref", "--format=%(refname)", "refs/original/")
        for ref in refs.split():
            repo.git("update-ref", "-d", ref)
        method = "git filter-branch"
    repo.git("reflog", "expire", "--expire=now", "--all")
    repo.git("gc", "--prune=now", "--quiet")
    return method


def preconditions(repo, paths):
    probs = []
    if porcelain(repo):
        probs.append("working tree is not clean: commit or stash first")
    for p in paths:
        if not repo.git("ls-files", "--", p)[1].strip():
            probs.append(f"{p} is not tracked by git")
        if p.startswith(".archive/"):
            probs.append(f"{p} is already archived")
        if not repo.exists(p):
            probs.append(f"{p} does not exist")
    return probs


def rewrite_plan(repo, paths, verb):
    ix = Index(repo).ensure()
    inbound = []
    for p in paths:
        for e in ix.db.execute("select src, dst, type from edges where dst=? or dst like ?", (p, p + "/%")):
            if not e["src"].startswith("_steering/"):
                inbound.append({"to": e["dst"], "from": norm(e["src"]), "type": e["type"]})
    rc, remotes, _ = repo.git("remote", "-v")
    return {"paths": paths, "commits_touching": history_commits(repo, paths), "inbound_links": inbound,
            "remotes": sorted(set(l.split()[0] for l in remotes.splitlines())), "method": "git filter-repo" if have_filter_repo(repo) else "git filter-branch",
            "backup": f"_steering/.ws/backups/{stamp()}-{verb}.bundle", "after": "force-push all branches and tags yourself, have everyone re-clone, ask the host to garbage-collect"}


LINKRX = re.compile(r"\]\(([^)\s#]+)(#[^)\s]*)?\)")


def rewrite_citations(repo, paths):
    """Point citations and links at the archived copy. Returns the files changed."""
    changed = []
    for f in repo.md_files(include_archive=True):
        if f.startswith(("_steering/", ".archive/")):
            continue
        text = repo.read(f)
        new = text
        for p in paths:
            rx = re.compile(r"((?:src=|derived_from:\s*|source:\s*))" + re.escape(p) + r"(?=[#/)\s}\]]|$)", re.M)
            new = rx.sub(lambda m: m.group(1) + ".archive/" + p, new)
        base = posixpath.dirname(f)

        def link(m):
            tgt = m.group(1)
            if re.match(r"^(https?:|mailto:)", tgt):
                return m.group(0)
            res = posixpath.normpath(posixpath.join(base, tgt))
            if any(res == p or res.startswith(p + "/") for p in paths):
                return "](" + posixpath.relpath(".archive/" + res, base or ".") + (m.group(2) or "") + ")"
            return m.group(0)
        new = LINKRX.sub(link, new)
        if new != text:
            atomic_write(repo.abs(f), new)
            changed.append(f)
    return changed


def backup_bundle(repo, rel):
    p = repo.abs(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    repo.git("bundle", "create", str(p), "--all", check=True)
    if repo.git("bundle", "verify", str(p))[0]:
        raise WsError("backup bundle did not verify; nothing was changed", 3)


def cmd_archive(repo, a, purge=False):
    need_git(repo)
    verb = "purge" if purge else "archive"
    paths = [p.rstrip("/") for p in a.paths]
    plan = rewrite_plan(repo, paths, verb)
    probs = preconditions(repo, paths)
    plan["problems"] = probs
    if not a.apply:
        txt = (f"{verb} plan: {', '.join(paths)}\n  history: {plan['commits_touching']} commit(s) touch it; they are rewritten (all branches and tags)\n"
               f"  method: {plan['method']}\n  backup: {plan['backup']} (verified bundle; delete it afterwards, it still holds the old history)\n"
               f"  inbound links that will break: {len(plan['inbound_links'])}" + "".join(f"\n    {l['from']} ({l['type']})" for l in plan['inbound_links'][:10])
               + (f"\n  remotes: {', '.join(plan['remotes'])}" if plan["remotes"] else "\n  remotes: none")
               + ("\nPROBLEMS:\n" + "\n".join("  " + x for x in probs) if probs else "") + f"\nthen: {plan['after']}\nrun: ws {'git purge' if purge else 'archive'} {' '.join(paths)} --apply --yes-rewrite-history")
        emit(a, plan, txt)
        return 2 if probs else 0
    if not a.yes_rewrite_history:
        raise WsError("this rewrites history for every clone: pass --yes-rewrite-history after a person has agreed", 2)
    if probs:
        raise WsError("preconditions failed: " + "; ".join(probs), 2)
    backup_bundle(repo, plan["backup"])
    copied = []
    try:
        if not purge:
            for p in paths:
                dst = repo.abs(f".archive/{p}")
                dst.parent.mkdir(parents=True, exist_ok=True)
                if repo.abs(p).is_dir():
                    shutil.copytree(repo.abs(p), dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(repo.abs(p), dst)
                copied.append(dst)
            scaffold_folder(repo, ".archive", apply=True)
        method = rewrite_remove(repo, paths)  # needs a clean tree: untracked copies are fine, citation edits come after
    except BaseException:
        for d in copied:
            shutil.rmtree(d, ignore_errors=True) if d.is_dir() else d.unlink(missing_ok=True)
        raise
    cited = [] if (purge or getattr(a, "keep_citations", False)) else rewrite_citations(repo, paths)
    msg = f"archive: {', '.join(paths)}" if not purge else f"purge: {', '.join(paths)}"
    if not purge:
        repo.git("add", "--", ".archive", *cited, check=True)
        repo.git("commit", "-q", "-m", msg + "\n\nHistory of the archived path was deleted.", check=True)
    left = history_commits(repo, paths)
    out = f"{verb}d with {method}; commits still touching the old path: {left}\ncitations rewritten to .archive/ in: {', '.join(cited) or 'none'}\nbackup: {plan['backup']} (delete after verifying)\nnext: {plan['after']}"
    emit(a, {**plan, "method": method, "remaining": left}, out)
    return 0 if left == 0 else 2


# ---- health ---------------------------------------------------------------------
def blobs(repo):
    rc, objs, _ = repo.git("rev-list", "--objects", "--all")
    if rc:
        return []
    names = {}
    for ln in objs.splitlines():
        parts = ln.split(" ", 1)
        if len(parts) == 2:
            names[parts[0]] = parts[1]
    p = subprocess.run(["git", "cat-file", "--batch-check=%(objecttype) %(objectname) %(objectsize)"], input="\n".join(names) + "\n", cwd=repo.root, capture_output=True, text=True)
    out = []
    for ln in p.stdout.splitlines():
        t, h, s = ln.split()
        if t == "blob":
            out.append({"path": names[h], "bytes": int(s), "sha": h})
    return sorted(out, key=lambda x: -x["bytes"])


def cmd_health(repo, a):
    if not repo.is_git():
        emit(a, {"error": "not a git repository"}, "not a git repository")
        return 3
    th = repo.config.get("thresholds") or {}
    warn_b, err_b = float(th.get("blob_warn_mb", 5)) * 1048576, float(th.get("blob_error_mb", 25)) * 1048576
    tracked = set(repo.git("ls-files")[1].split("\n"))
    bl = blobs(repo)
    findings, limits = [], []
    if repo.git("rev-parse", "--is-shallow-repository")[1].strip() == "true":
        limits.append("shallow clone: history before the shallow boundary was not analyzed")
    seen = set()
    for b in bl[:25]:
        if b["path"] in seen or b["bytes"] < warn_b:
            continue
        seen.add(b["path"])
        at_head = b["path"] in tracked
        sev = "action" if b["bytes"] >= err_b else "warn"
        findings.append({"id": "heavy-blob", "severity": sev, "confidence": "high", "evidence": {"path": b["path"], "bytes": b["bytes"], "at_head": at_head},
                         "recommend": [{"tier": "offload" if at_head else "purge", "command": f"ws git offload {b['path']} --to <dir>" if at_head else f"ws git purge {b['path']}", "blast": "tree" if at_head else "history"}]})
    for f in sorted(tracked):
        p = repo.abs(f)
        if f and p.is_file() and p.stat().st_size < 1_000_000 and not f.startswith("_steering/"):
            try:
                txt = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for n_, name, fp in secret_hits(repo, txt):
                findings.append({"id": "secret-pattern", "severity": "action", "confidence": "medium", "evidence": {"path": f, "line": n_, "pattern": name, "fingerprint": fp, "at_head": True},
                                 "recommend": [{"tier": "rotate", "command": "rotate the credential first, then reassess a purge", "blast": "none"}]})
    limits.append("secret scan covers files at HEAD only")
    by = defaultdict(int)
    for b in bl:
        by[b["path"].split("/")[0]] += b["bytes"]
    rc, co, _ = repo.git("count-objects", "-vH")
    size = dict(l.split(": ", 1) for l in co.splitlines() if ": " in l)
    packs = list((repo.root / ".git" / "objects" / "pack").glob("*.pack")) if (repo.root / ".git").is_dir() else []
    last_maint = max((p.stat().st_mtime for p in packs), default=0)
    stale_days = int(th.get("maintenance_stale_days", 60))
    if last_maint and (time.time() - last_maint) / 86400 > stale_days:
        findings.append({"id": "maintenance", "severity": "warn", "confidence": "medium", "evidence": {"days_since_pack": int((time.time() - last_maint) / 86400)}, "recommend": [{"tier": "maintain", "command": "ws git maintain --apply", "blast": "none"}]})
    br_days = int(th.get("stale_branch_days", 30))
    rc, refs, _ = repo.git("for-each-ref", "--format=%(refname:short) %(committerdate:unix)", "refs/heads")
    stale = [r.split()[0] for r in refs.splitlines() if r.split()[0].startswith(repo.config.get("git", {}).get("branch_prefix", "ws/")) and (time.time() - int(r.split()[1])) / 86400 > br_days]
    if stale:
        findings.append({"id": "stale-branches", "severity": "warn", "confidence": "high", "evidence": {"branches": stale}, "recommend": [{"tier": "tidy", "command": "delete merged ws/* branches", "blast": "none"}]})
    data = {"schema_version": 1, "head": repo.head(), "git_dir": size.get("size-pack", "?"), "loose": size.get("size", "?"), "bytes_by_top_folder": dict(sorted(by.items(), key=lambda x: -x[1])[:8]),
            "findings": findings, "limits": limits}
    code = 2 if any(f["severity"] == "action" for f in findings) else (1 if findings else 0)
    if a.json:
        emit(a, data, "")
    else:
        print(f"HEAD {data['head']} | packed {data['git_dir']} | loose {data['loose']}")
        print("bytes by top folder: " + ", ".join(f"{k} {v // 1024} KB" for k, v in data["bytes_by_top_folder"].items()))
        for f in findings:
            print(f"[{f['severity']}] {f['id']}: {json.dumps(f['evidence'])}\n     -> {f['recommend'][0]['command']} (blast: {f['recommend'][0]['blast']})")
        print("limits: " + "; ".join(limits))
        print("clean" if not findings else f"{len(findings)} finding(s)")
    return code


def cmd_maintain(repo, a):
    need_git(repo)
    if not a.apply:
        print("would run: git maintenance run (or git gc); --schedule also runs git maintenance start; add --apply")
        return 0
    rc, o, e = repo.git("maintenance", "run")
    if rc:
        rc, o, e = repo.git("gc", "--quiet")
    if a.schedule:
        repo.git("maintenance", "start")
    print("maintenance done" if rc == 0 else f"failed: {e.strip()}")
    return 0 if rc == 0 else 3


def cmd_offload(repo, a):
    paths = [p.rstrip("/") for p in a.paths]
    dest = Path(a.to).resolve()
    plan = []
    for p in paths:
        src = repo.abs(p)
        if not src.is_file():
            raise WsError(f"{p} is not a file in the workspace", 2)
        plan.append((p, src.stat().st_size, hashlib.sha256(src.read_bytes()).hexdigest()))
    if not a.apply:
        emit(a, [{"path": p, "bytes": s, "sha256": h} for p, s, h in plan], "\n".join(f"would offload {p} ({s} B) to {dest}/{p}, verify sha256, then replace it with a stub" for p, s, h in plan) + "\n(add --apply)")
        return 0
    scaffold_folder(repo, ".archive", apply=True)
    man = repo.abs(".archive/manifest.md")
    for p, size, digest in plan:
        t = dest / p
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo.abs(p), t)
        if hashlib.sha256(t.read_bytes()).hexdigest() != digest:
            raise WsError(f"hash mismatch after copy of {p}; the original was kept", 3)
        repo.abs(p).unlink()
        atomic_write(repo.abs(p + ".offloaded.md"), f'---\nkind: raw\ndescription: "Offloaded: {p} ({size} bytes). Stored at {t}."\nsha256: {digest}\nlocation: {t}\n---\nThe original is in cold storage; verify it by sha256 before use.\n')
        line = f"- {p} | sha256={digest} | size={size} | location={t} | retain_until={a.retain or 'contract-end'}"
        atomic_write(man, man.read_text(encoding="utf-8").rstrip("\n") + "\n" + line + "\n")
    emit(a, [{"path": p, "sha256": h} for p, _, h in plan], f"offloaded {len(plan)} file(s); hashes verified before deleting; manifest updated; history untouched")
    return 0
