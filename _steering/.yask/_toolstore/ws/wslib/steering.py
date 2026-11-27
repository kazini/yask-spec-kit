"""ws steering: the two steering layers read as one. The project's `_steering/` is read first, then the shipped
`_steering/.yask/`. A project file supersedes the shipped file at the same path; `override:` on top of any project
steering document (or yaml file) switches off other shipped files or folders it replaces, whatever they are called."""
import re

from .checks import finding
from .repo import FM, WsError, match
from .util import atomic_write, emit, locked, table

DEFAULT_FILE = "_steering/overrides.md"
STARTER = '''---
kind: steering
description: "Shipped steering this project switches off, and why."
---
# Overrides

Shipped steering files and folders this project does not use. `override:` on top of this file (or of any steering
document) names them; they stay in `_steering/.yask/` and are updated with it, but are not read, routed or checked.

'''


def shipped(repo):
    """Relative names (to the steering root) of every shipped file except the tool's own code and the .ws template
    (the project's .ws is generated from that template and is meant to replace it)."""
    return sorted(f.relative_to(repo.base).as_posix() for f in repo.base.rglob("*")
                  if f.is_file() and "__pycache__" not in f.parts and not f.relative_to(repo.base).as_posix().startswith(("_toolstore/", ".ws/")))


def project(repo):
    """Relative names of the project's own steering files (not the shipped layer, not the generated .ws)."""
    out = []
    for f in repo.steer.rglob("*"):
        r = f.relative_to(repo.steer).as_posix()
        if f.is_file() and not r.startswith((".yask/", ".ws/")) and "__pycache__" not in f.parts:
            out.append(r)
    return sorted(out)


def view(repo):
    base, mine = set(shipped(repo)), set(project(repo))
    return {"superseded": sorted(base & mine), "added": sorted(mine - base),
            "switched_off": [(r, repo.overridden_by(r)) for r in sorted(base - mine) if repo.overridden_by(r)],
            "in_force": len([r for r in base if repo.base_active(r)]), "shipped": len(base)}


def stamp_hash(path):
    import hashlib
    return hashlib.sha1(path.read_bytes()).hexdigest()[:12]


def behind(repo):
    """Project files that supersede a shipped one and were copied from an older version of it."""
    from .repo import read_fm
    out = []
    for r in project(repo):
        b = repo.base / r
        if r.endswith(".md") and b.is_file():
            based = read_fm((repo.steer / r).read_text(encoding="utf-8"))[0].get("based_on")
            if based and str(based) != stamp_hash(b):
                out.append(r)
    return out


def set_based_on(path, h):
    t = path.read_text(encoding="utf-8")
    m = FM.match(t)
    if not m:
        return
    head = re.sub(r"(?m)^based_on:.*\n?", "", m.group(1)).rstrip("\n")
    path.write_text("---\n" + head + f"\nbased_on: {h}\n---\n" + t[m.end():], encoding="utf-8", newline="\n")


def norm(t):
    t = str(t).strip().replace("\\", "/")
    t = t[len("_steering/"):] if t.startswith("_steering/") else t
    if t.startswith((".yask", ".ws")) or t.startswith("../") or not t:
        raise WsError("name a steering path relative to _steering/, for example playbooks/record-lesson.md", 2)
    return t


def read_list(text, md):
    from . import yamlsub
    head = FM.match(text).group(1) if md and FM.match(text) else text
    v = yamlsub.loads(head).get("override")
    return [str(x) for x in ([v] if isinstance(v, str) else v or [])]


def write_list(text, items, md):
    line = "override: [" + ", ".join('"%s"' % i for i in items) + "]" if items else ""
    m = FM.match(text) if md else None
    head, rest = (m.group(1), text[m.end():]) if m else (text, "")
    head = re.sub(r"(?m)^override:.*(?:\n[ \t]+-.*)*\n?", "", head).rstrip("\n")
    head = head + ("\n" + line if line else "")
    return ("---\n" + head + "\n---\n" + rest) if m else head.rstrip("\n") + "\n"


def edit(repo, file_rel, add=(), remove=(), why=""):
    p = repo.abs(file_rel)
    if not file_rel.startswith("_steering/") or file_rel.startswith(("_steering/.yask/", "_steering/.ws/")) or not file_rel.endswith((".md", ".yaml")):
        raise WsError("an override lives in a project steering .md or .yaml file under _steering/ (not .yask/ or .ws/)", 2)
    md = file_rel.endswith(".md")
    with locked(repo):
        text = p.read_text(encoding="utf-8") if p.exists() else STARTER
        cur = read_list(text, md)
        new = [x for x in cur if x not in remove] + [a for a in add if a not in cur]
        text = write_list(text, new, md)
        for r in remove:   # the explanatory bullet goes with the entry
            text = re.sub(r"(?m)^- `%s`.*\n" % re.escape(r), "", text)
        if md and add:
            text = text.rstrip("\n") + "\n" + "".join(f"- `{a}`{': ' + why if why else ''}\n" for a in add if a not in cur)
        p.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(p, text)
    return new


def cmd_steering(repo, a):
    c = a.scmd or "list"
    base = shipped(repo)
    if c == "list":
        v = view(repo)
        old = set(behind(repo))
        rows = [("supersedes shipped" + (", BEHIND: ws steering diff" if r in old else ""), r, "") for r in v["superseded"]] + [("project only", r, "") for r in v["added"]] + [("switched off", r, f) for r, f in v["switched_off"]]
        head = f"{v['in_force']} of {v['shipped']} shipped steering files in force; {len(v['superseded'])} superseded, {len(v['added'])} added by the project, {len(v['switched_off'])} switched off"
        full = ""
        if getattr(a, "all", False):
            full = "\n\n" + table([(("project" if (repo.steer / r).exists() else "shipped"), r) for r in sorted(set(base) | set(project(repo))) if repo.steer_path(r)], ["layer", "path (relative to _steering/)"])
        emit(a, v, head + ("\n" + table(rows, ["what", "path", "by"]) if rows else "") + full)
        return 0
    if c == "show":
        sub = norm(a.path)
        p = repo.steer_path(sub)
        off = repo.overridden_by(sub)
        if p is None:
            print(f"{sub}: not in force" + (f" (switched off by {off})" if off else " (no such steering file)"))
            return 2
        sup = (repo.base / sub).exists() and p != repo.base / sub
        print(f"{sub}: {p.relative_to(repo.root).as_posix()} ({repo.steer_layer(sub)}{', supersedes the shipped file' if sup else ''})")
        return 0
    if c == "diff":
        import difflib
        sub = norm(a.path)
        src, dst = repo.base / sub, repo.steer / sub
        if not src.is_file() or not dst.is_file():
            raise WsError(f"{sub} needs a shipped file and a project copy", 2)
        if a.done:
            set_based_on(dst, stamp_hash(src))
            print(f"{sub}: marked as compared with the current shipped version")
            return 0
        d = list(difflib.unified_diff(src.read_text(encoding="utf-8").splitlines(), dst.read_text(encoding="utf-8").splitlines(), "shipped", "yours", lineterm="", n=1))
        print("\n".join(d[:80]) + (f"\n... {len(d) - 80} more lines" if len(d) > 80 else "") if d else "identical")
        return 0
    if c == "copy":
        sub = norm(a.path)
        src, dst = repo.base / sub, repo.steer / sub
        if not src.is_file() or not repo.base_active(sub) and not dst.exists():
            raise WsError(f"no shipped file {sub} in force to copy", 2)
        if dst.exists():
            raise WsError(f"_steering/{sub} already exists: edit it", 2)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        if sub.endswith(".md"):
            set_based_on(dst, stamp_hash(src))   # so a later update can say when the shipped file has moved on
        print(f"created _steering/{sub}: edit it; it supersedes the shipped file at the same path")
        return 0
    targets = [norm(t) for t in a.targets]
    file_rel = getattr(a, "into", None) or DEFAULT_FILE
    if c == "override":
        for t in targets:
            if not any(match(b, t) for b in base):
                raise WsError(f"{t} matches no shipped steering file", 2)
        new = edit(repo, file_rel, add=targets, why=a.why or "")
        emit(a, {"file": file_rel, "override": new}, f"{file_rel}: override: {', '.join(new)}")
        return 0
    # restore: drop the targets from every file that carries them (or just --in)
    files = [file_rel] if a.into else sorted({f for p_, f in repo.overrides() if any(p_ == t for t in targets)})
    if not files:
        raise WsError("no override names that", 2)
    for f in files:
        edit(repo, f, remove=targets)
    print(f"restored {', '.join(targets)} (removed from {', '.join(files)})")
    return 0


def steering_findings(repo):
    F = []
    base = shipped(repo)
    for pat, f in repo.overrides():
        if not any(match(b, pat) for b in base):
            F.append(finding("warn", "override", f, f"override {pat!r} matches no shipped steering file"))
    for r in behind(repo):
        F.append(finding("info", "override", f"_steering/{r}", "the shipped file changed since this copy was made: ws steering diff " + r))
    for m in repo.enabled:
        if m not in repo.manifests:
            F.append(finding("error", "override", "_steering/.ws/config.yaml", f"module {m} is enabled but has no manifest (switched off by an override, or removed)"))
    return F
