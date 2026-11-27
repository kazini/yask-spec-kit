"""Collaboration helpers: agent commit identity, squash, hooks. Git only keeps history; the coordination is in auto.py."""
import os
import re
import stat
from pathlib import Path

from . import yamlsub
from .repo import WsError, slug
from .util import emit, stamp

FOLD = re.compile(r"^(wip|fixup!|squash!|tmp|checkpoint|autosave)\b", re.I)
TRAILER = re.compile(r"^(Ws-Task|AI-Assisted|Co-authored-by):", re.I)


# ---- identity ----------------------------------------------------------------------------
def agent_env(repo, user):
    """Author an agent's commit as <you>+agent (or <you>+<WS_AGENT> when several agents work); the committer stays you. Off with git.agent_author: false."""
    if (repo.config.get("git") or {}).get("agent_author", True) is False:
        return None
    lane = slug(os.environ.get("WS_AGENT", "")) or "agent"
    _, mail, _ = repo.git("config", "user.email")
    mail = mail.strip() or "ws@localhost"
    local, _, dom = mail.partition("@")
    return {"GIT_AUTHOR_NAME": f"{user}+{lane}", "GIT_AUTHOR_EMAIL": f"{local}+{lane}@{dom or 'localhost'}"}


# ---- squash ---------------------------------------------------------------------------------
def squash_base(repo, a):
    if a.base:
        return a.base
    rc, up, _ = repo.git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if rc == 0:
        return up.strip()
    main = (repo.config.get("git") or {}).get("main_branch", "main")
    cur = repo.git("rev-parse", "--abbrev-ref", "HEAD")[1].strip()
    if cur != main:
        rc, mb, _ = repo.git("merge-base", "HEAD", main)
        if rc == 0:
            return mb.strip()
    raise WsError("no upstream to tell which commits are unpushed: pass --base <rev>, for example --base HEAD~6", 2)


def read_commits(repo, base):
    rc, out, e = repo.git("log", "--reverse", "--format=%H%x1f%an%x1f%ae%x1f%at%x1f%aI%x1f%s%x1f%b%x1e", f"{base}..HEAD")
    if rc:
        raise WsError(f"cannot read {base}..HEAD: {e.strip()}", 2)
    cs = []
    for rec in out.split("\x1e"):
        if not rec.strip():
            continue
        sha, an, ae, at, aiso, subj, body = rec.strip("\n").split("\x1f", 6)
        files = repo.git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha)[1].split()
        m = re.match(r"^([\w-]+):", subj)
        task = tuple(sorted(re.findall(r"(?mi)^Ws-Task:\s*(\S+)", body)))
        cs.append({"sha": sha, "an": an, "ae": ae, "at": int(at), "aiso": aiso, "subj": subj, "body": body,
                   "area": m.group(1) if m else "", "task": task, "files": files,
                   "keep": any(f.startswith("docs/decisions/") for f in files)})
    return cs


def group(repo, cs):
    gap = int((repo.config.get("git") or {}).get("squash_gap_minutes", 30)) * 60
    gs = []
    for c in cs:
        p = gs[-1] if gs else None
        join = bool(p) and not c["keep"] and not p["keep"] and c["an"] == p["an"] and (
            FOLD.match(c["subj"]) or (c["task"] and c["task"] == p["task"]) or (c["area"] and c["area"] == p["area"] and c["at"] - p["last"] <= gap))
        if join:
            p["c"].append(c)
            p["last"] = c["at"]
        else:
            gs.append({"c": [c], "an": c["an"], "area": c["area"], "task": c["task"], "last": c["at"], "keep": c["keep"]})
    return gs


def message(g):
    cs = g["c"]
    if len(cs) == 1:
        return cs[0]["subj"] + ("\n\n" + cs[0]["body"].strip() if cs[0]["body"].strip() else "")
    lead = next((c for c in cs if not FOLD.match(c["subj"])), cs[0])
    tr = sorted({t for c in cs for x in c["body"].splitlines() if (t := x.strip()) and TRAILER.match(t)})
    return f"{lead['subj']}\n\nSquashed {len(cs)} commits:\n" + "\n".join(f"- {c['subj']}" for c in cs) + ("\n\n" + "\n".join(tr) if tr else "")


def cmd_squash(repo, a):
    if not repo.is_git():
        raise WsError("not a git repository", 3)
    cur = repo.git("rev-parse", "--abbrev-ref", "HEAD")[1].strip()
    if a.undo:
        rc, refs, _ = repo.git("for-each-ref", "--sort=-refname", "--format=%(refname) %(objectname)", "refs/ws/backup/")
        if not refs.strip():
            raise WsError("no squash backup to restore", 2)
        ref, sha = refs.splitlines()[0].split()
        if repo.git("rev-parse", "HEAD^{tree}")[1] != repo.git("rev-parse", f"{sha}^{{tree}}")[1]:
            raise WsError("the files changed since that squash: undo would lose work, restore by hand from " + ref, 2)
        repo.git("update-ref", "-m", "ws squash --undo", f"refs/heads/{cur}", sha, check=True)
        print(f"restored {cur} to {sha[:8]}")
        return 0
    if repo.git("status", "--porcelain", "--untracked-files=no")[1].strip():
        raise WsError("uncommitted changes: ws save them first", 2)
    base = squash_base(repo, a)
    if repo.git("rev-list", "--merges", f"{base}..HEAD")[1].strip():
        raise WsError("merge commits in the range: pass a later --base", 2)
    cs = read_commits(repo, base)
    if len(cs) < 2:
        print("nothing to squash")
        return 0
    if repo.git("branch", "-r", "--contains", cs[0]["sha"])[1].strip():
        raise WsError("the first of these commits is already on a remote branch: pushed history is not squashed", 2)
    gs = group(repo, cs)
    plan = [{"commits": [c["sha"][:8] for c in g["c"]], "subject": message(g).split("\n", 1)[0]} for g in gs]
    merged = sum(len(g["c"]) - 1 for g in gs)
    if not merged:
        print(f"{len(cs)} commits, nothing groups safely (same author, same task or area within the gap, or wip/fixup)")
        return 0
    text = "\n".join(f"{len(g['c'])} -> 1  {g['c'][0]['sha'][:8]}..{g['c'][-1]['sha'][:8]}  {message(g).splitlines()[0][:70]}" if len(g["c"]) > 1
                     else f"1       {g['c'][0]['sha'][:8]}  {g['c'][0]['subj'][:70]}" for g in gs)
    if not a.apply:
        emit(a, plan, f"{len(cs)} unpushed commits become {len(gs)} (history is not rewritten until --apply; a backup ref is kept)\n{text}\n(add --apply)")
        return 0
    old, old_tree = repo.git("rev-parse", "HEAD")[1].strip(), repo.git("rev-parse", "HEAD^{tree}")[1].strip()
    parent = repo.git("rev-parse", base)[1].strip()
    for g in gs:
        last = g["c"][-1]["sha"]
        first = g["c"][0]
        env = {"GIT_AUTHOR_NAME": first["an"], "GIT_AUTHOR_EMAIL": first["ae"], "GIT_AUTHOR_DATE": first["aiso"]}
        tree = repo.git("rev-parse", f"{last}^{{tree}}")[1].strip()
        rc, new, e = repo.git("commit-tree", tree, "-p", parent, "-m", message(g), env=env)
        if rc:
            raise WsError(f"commit-tree failed, nothing changed: {e.strip()[:160]}", 3)
        parent = new.strip()
    if repo.git("rev-parse", f"{parent}^{{tree}}")[1].strip() != old_tree:
        raise WsError("internal check failed (final tree differs); nothing changed", 3)
    repo.git("update-ref", f"refs/ws/backup/{stamp()}", old, check=True)
    repo.git("update-ref", "-m", "ws squash", f"refs/heads/{cur}", parent, old, check=True)
    print(f"{len(cs)} commits -> {len(gs)} on {cur}; files unchanged; undo with: ws squash --undo")
    return 0


# ---- hooks ----------------------------------------------------------------------------------
MARK = "# ws-managed"
HOOKS = ("pre-commit", "post-merge")


def hooks_dir(repo):
    rc, p, _ = repo.git("rev-parse", "--git-path", "hooks")
    d = Path(p.strip())
    return d if d.is_absolute() else repo.root / d


def cmd_hooks(repo, a):
    if not repo.is_git():
        raise WsError("not a git repository", 3)
    d = hooks_dir(repo)
    if a.hcmd == "run":
        return run_hook(repo, a.name)
    for h in HOOKS:
        f = d / h
        mine = f.exists() and MARK in f.read_text(errors="replace")
        if a.hcmd == "status":
            print(f"{h:11} {'ws hook installed' if mine else ('another hook (not ours)' if f.exists() else 'not installed')}")
        elif a.hcmd == "install":
            if f.exists() and not mine:
                print(f"{h:11} a hook already exists; not touched. Add this line to it: ws hooks run {h}")
                continue
            d.mkdir(parents=True, exist_ok=True)
            f.write_text(f'#!/bin/sh\n{MARK}: remove with `ws hooks remove`. Skip once: git commit --no-verify, or WS_HOOKS=off\n[ "$WS_HOOKS" = off ] && exit 0\n'
                         f'exec sh "$(git rev-parse --show-toplevel)/_steering/.yask/_toolstore/_shims/ws" hooks run {h}\n', encoding="utf-8", newline="\n")
            f.chmod(f.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            print(f"{h:11} installed")
        elif a.hcmd == "remove" and mine:
            f.unlink()
            print(f"{h:11} removed")
    return 0


def run_hook(repo, name):
    """pre-commit: refuse staged secrets and conflict markers (fast; nothing else). post-merge: report only."""
    from . import hygiene
    from .checks import secret_hits
    if name == "post-merge":
        left = hygiene.state(repo, hygiene.history_snapshot(repo))
        if left:
            print(f"ws: {len(left)} leftover/stale item(s) after the merge: ws sweep")
        return 0
    bad = []
    _, names, _ = repo.git("diff", "--cached", "--name-only", "--diff-filter=ACM", "-z")
    for f in [x for x in names.split("\0") if x and not x.startswith(("_steering/", ".archive/"))]:
        rc, txt, _ = repo.git("show", f":{f}")
        if rc or len(txt) > 2_000_000:
            continue
        bad += [f"{f}:{n} {nm} ({fp})" for n, nm, fp in secret_hits(repo, txt)]
        if f.endswith(".md") and re.search(r"(?m)^<<<<<<< ", txt) and re.search(r"(?m)^>>>>>>> ", txt):
            bad.append(f"{f}: unresolved merge conflict markers")
    if bad:
        print("ws: commit refused:\n  " + "\n  ".join(bad) + "\nfix it, put ws:allow on a harmless sample's line, or skip once with --no-verify", file=__import__("sys").stderr)
        return 2
    return 0
