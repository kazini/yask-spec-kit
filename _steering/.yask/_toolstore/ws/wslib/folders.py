"""ws folders: what the tools do with each folder (see _steering/folders.yaml), and renaming folders a project created."""
import os
import posixpath
import re
from pathlib import Path

from .checks import finding
from .repo import WsError
from .util import atomic_write, emit, locked, table

FLAGS = ("listed", "searched", "checked")
KEYS = FLAGS + ("generated", "purpose")
TEXT_EXT = {".md", ".yaml", ".yml", ".json", ".txt"}


def norm(p):
    p = posixpath.normpath(str(p).replace("\\", "/").strip().strip("/"))
    if p in ("", ".") or p.startswith(".."):
        raise WsError("give a folder path relative to the repository root", 2)
    return p


def project_file(repo):
    return repo.ws / "folders.yaml"


def read_project(repo):
    from . import yamlsub
    f = project_file(repo)
    rows = (yamlsub.loads(f.read_text(encoding="utf-8")).get("folders") or []) if f.exists() else []
    return [e for e in rows if isinstance(e, dict) and e.get("path")]


HEAD = """# What the tools do with each folder. One file, yours: edit it with `ws folders add|set|remove` or by hand.
# listed: ws map shows it. searched: ws find and brief return it. checked: ws check validates it.
# generated: tools write it and never read it. A folder with no entry is content (all true) unless a name
# in its path starts with a dot: then it is out of the way (all false). Asking for a folder by path always works.
"""


def write_project(repo, rows):
    def val(v):
        return "true" if v is True else "false" if v is False else str(v)
    head = HEAD
    body = "folders: []\n" if not rows else "folders:\n" + "".join(
        "  - { " + ", ".join(f"{k}: {val(e[k])}" for k in ("path",) + KEYS if k in e) + " }\n" for e in sorted(rows, key=lambda e: e["path"]))
    atomic_write(project_file(repo), head + body)


def parse_kv(items):
    out = {}
    for kv in items or []:
        k, _, v = kv.partition("=")
        if k not in KEYS:
            raise WsError(f"unknown key {k!r}; use {', '.join(KEYS)}", 2)
        if k == "purpose":
            if not re.fullmatch(r"[a-z][a-z-]*", v):
                raise WsError("purpose is a lowercase word, hyphens allowed", 2)
            out[k] = v
        else:
            if v not in ("true", "false"):
                raise WsError(f"{k} is true or false", 2)
            out[k] = v == "true"
    return out


def protected(repo):
    """Folders the shipped modules and steering rely on by name. Their behaviour can be set; their names stay."""
    keep = {"_steering"}
    for m in repo.manifests:
        if repo.steer_layer(f"modules/{m}/module.yaml") == "base":
            for w in repo.manifests[m].get("where") or []:
                p = str(w.get("path", "")).strip("/")
                if p and "<" not in p:
                    keep.add(p)
    return keep


def cmd_folders(repo, a):
    c = a.fcmd or "list"
    if c == "list":
        rows = []
        for p, e in sorted(repo.folders.items()):
            rows.append((p, *("yes" if e.get(k, not any(x.startswith(".") for x in p.split("/"))) else "no" for k in FLAGS), e.get("purpose", ""),
                         "" if e.get("generated") or (repo.root / p).exists() else "(none yet)"))
        dots = sorted({d.name for d in repo.root.iterdir() if d.is_dir() and d.name.startswith(".") and d.name not in repo.folders and d.name not in (".git",)})
        emit(a, {"folders": repo.folders, "unregistered_dot_folders": dots},
             table(rows, ["path", "listed", "searched", "checked", "purpose", ""])
             + (f"\nout of the way by default (no entry): {', '.join(dots)}" if dots else ""))
        return 0
    with locked(repo):
        rows = read_project(repo)
        if c in ("add", "set", "remove"):
            p = norm(a.path)
            mine = next((e for e in rows if str(e["path"]).strip("/") == p), None)
            if c == "remove":
                if not mine:
                    raise WsError(f"{p} has no entry", 2)
                rows.remove(mine)
                write_project(repo, rows)
                print(f"removed the entry for {p}; it now follows the default (content, or out of the way if a name in its path starts with a dot)")
                return 0
            kv = parse_kv(a.kv)
            if c == "add":
                if mine:
                    raise WsError(f"{p} already has an entry; use `ws folders set {p} ...`", 2)
                if not kv.get("generated") and not (repo.root / p).exists():
                    print(f"note: {p} does not exist yet", file=__import__("sys").stderr)
                rows.append({"path": p, **kv})
            else:
                if not kv:
                    raise WsError("nothing to set: key=value, for example searched=false", 2)
                if not mine:
                    raise WsError(f"no entry for {p}; ws folders add {p}", 2)
                mine.update(kv)
            write_project(repo, rows)
            print(f"{p}: " + ", ".join(f"{k}={'true' if v is True else 'false' if v is False else v}" for k, v in kv.items()))
            return 0
        return rename(repo, a, rows)


# ---- rename ------------------------------------------------------------------------------
def mapped(path, old, new):
    return new + path[len(old):] if path == old or path.startswith(old + "/") else path


def rewrite(text, here_old, here_new, old, new):
    """Fix every reference to a moved folder. `here_old`/`here_new` are the file's own folder before and after the move."""
    n = [0]

    def link(m):
        tgt = m.group(2)
        if re.match(r"^[a-z][a-z0-9+.-]*:|^#|^/", tgt):
            return m.group(0)
        path, hash_ = (tgt.split("#", 1) + [""])[:2] if "#" in tgt else (tgt, "")
        res = posixpath.normpath(posixpath.join(here_old, path)) if path else ""
        if not path or not (res == old or res.startswith(old + "/") or here_old != here_new):
            return m.group(0)
        new_res = mapped(res, old, new)
        rel = posixpath.relpath(new_res, here_new or ".")
        if rel == path:
            return m.group(0)
        n[0] += 1
        return f"{m.group(1)}{rel}{'#' + hash_ if hash_ else ''})"

    text = re.sub(r"(\]\()([^)\s]+)\)", link, text)
    text = re.sub(rf"(?<![\w./-]){re.escape(old)}(?=/)", lambda m: (n.__setitem__(0, n[0] + 1) or new), text)
    text = re.sub(rf"(?<=`){re.escape(old)}(?=`)", lambda m: (n.__setitem__(0, n[0] + 1) or new), text)
    text = re.sub(rf"(?m)^(\s*(?:-\s*)?(?:\{{\s*)?path:\s*){re.escape(old)}(?=\s*[,}}]|\s*$)", lambda m: (n.__setitem__(0, n[0] + 1) or m.group(1) + new), text)
    return text, n[0]


def rename(repo, a, rows):
    old, new = norm(a.path), norm(a.new)
    if not (repo.root / old).is_dir():
        raise WsError(f"{old} is not a folder", 2)
    if (repo.root / new).exists():
        raise WsError(f"{new} already exists", 2)
    if new.startswith(old + "/"):
        raise WsError("the new path cannot be inside the old one", 2)
    hit = next((p for p in sorted(protected(repo)) if old == p or p.startswith(old + "/")), None)   # the folder itself, or one that contains it
    if hit:
        raise WsError(f"{old} is or contains {hit}, which the shipped steering refers to by name: its behaviour can be changed (ws folders set), its name cannot. Rename only folders your project created", 2)
    plan, files = [], []
    for d, dirs, fs in os.walk(repo.root):
        rd = Path(d).relative_to(repo.root).as_posix()
        rd = "" if rd == "." else rd
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "__pycache__") and not repo.policy((rd + "/" + x).lstrip("/")).get("generated")]
        for f in fs:
            r = (rd + "/" + f).lstrip("/")
            if Path(f).suffix in TEXT_EXT or f in (".gitignore", ".ignore"):
                files.append(r)
    for r in files:
        if r.startswith("_steering/") and not r.startswith("_steering/.ws/") or r.startswith(".archive/"):
            continue
        p = repo.abs(r)
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        folder_old = posixpath.dirname(r)
        new_text, n = rewrite(text, folder_old, posixpath.dirname(mapped(r, old, new)), old, new)
        if n or new_text != text:
            plan.append((r, new_text, n))
    reg = [e for e in rows if str(e["path"]).strip("/") == old or str(e["path"]).strip("/").startswith(old + "/")]
    emit(a, {"from": old, "to": new, "files": [{"path": r, "changes": n} for r, _, n in plan], "registry_entries": len(reg), "applied": bool(a.apply)},
         f"{old} -> {new}\n" + "\n".join(f"  rewrite {r} ({n})" for r, _, n in plan) + (f"\n  re-path {len(reg)} folder entr{'y' if len(reg) == 1 else 'ies'}" if reg else "")
         + ("\n(add --apply; commit first so the rename is one reviewable change)" if not a.apply else ""))
    if not a.apply:
        return 0
    if repo.is_git() and repo.git("status", "--porcelain", "--untracked-files=no")[1].strip():
        raise WsError("uncommitted changes: ws save them first, so the rename is one reviewable change", 2)
    (repo.root / new).parent.mkdir(parents=True, exist_ok=True)
    rc, _, _ = repo.git("mv", old, new) if repo.is_git() else (1, "", "")
    if rc:
        os.rename(repo.root / old, repo.root / new)
    for r, text, _ in plan:
        atomic_write(repo.abs(mapped(r, old, new)), text)
    for e in reg:
        e["path"] = mapped(str(e["path"]).strip("/"), old, new)
    if reg:
        write_project(repo, rows)
    from . import gen
    gen.apply(repo, write=True)
    print(f"renamed. run: ws check   (links and paths are verified there)")
    return 0


# ---- check -----------------------------------------------------------------------------
def folder_findings(repo):
    F = []
    created_on_demand = {str(w.get("path", "")).strip("/") for m in repo.manifests for w in repo.manifests[m].get("where") or []}
    from . import yamlsub
    sf = repo.base / ".ws" / "folders.yaml"   # entries the release ships may name folders that appear later
    created_on_demand |= {str(e.get("path")).strip("/") for e in (yamlsub.loads(sf.read_text(encoding="utf-8")).get("folders") or []) if isinstance(e, dict)} if sf.exists() else set()
    for e in read_project(repo):
        p = str(e["path"]).strip("/")
        for k in e:
            if k not in KEYS + ("path",):
                F.append(finding("warn", "folders", "_steering/.ws/folders.yaml", f"{p}: unknown key {k!r}"))
        for k in FLAGS + ("generated",):
            if k in e and not isinstance(e[k], bool):
                F.append(finding("warn", "folders", "_steering/.ws/folders.yaml", f"{p}: {k} must be true or false"))
        if not (repo.root / p).exists() and not e.get("generated") and p not in created_on_demand:
            F.append(finding("warn", "folders", "_steering/.ws/folders.yaml", f"entry for {p}, which does not exist (typo, or renamed by hand?)"))
    return F
