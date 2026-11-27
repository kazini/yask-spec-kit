"""Workspace discovery: root, configuration, module manifests, kinds, file walking."""
import fnmatch
import os
import re
import shutil
import subprocess
from pathlib import Path

from . import yamlsub

FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)
BASE_PREFIX = "_steering/.yask/"
SETTINGS = ("config.yaml", "check.yaml", "redaction.yaml", "retention.yaml", "folders.yaml", "README.md")   # the project .ws is generated from these
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "target", "dist", "build", ".yask_cache"}   # tool and language folders, not workspace choices
CODE_EXT = {".py", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".rs", ".go", ".java", ".cs", ".c", ".h", ".cpp", ".rb", ".php", ".sh"}


class WsError(Exception):
    def __init__(self, msg, code=3):
        super().__init__(msg)
        self.code = code


def find_root(start=None):
    p = Path(start or os.environ.get("WS_ROOT") or os.getcwd()).resolve()
    for d in [p, *p.parents]:
        if (d / "AGENTS.md").exists() and (d / "_steering").is_dir():
            return d
    raise WsError("not inside a workspace (no AGENTS.md next to _steering/)")


def read_fm(text):
    m = FM.match(text)
    if not m:
        return {}, text, 0
    try:
        fm = yamlsub.loads(m.group(1))
    except Exception:
        fm = {"_error": "unparseable front matter"}
    return (fm if isinstance(fm, dict) else {}), text[m.end():], text[:m.end()].count("\n")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def match(sub, pat):
    """Does the steering-relative path `sub` fall under `pat` (a file, a folder, or a glob)?"""
    pat = str(pat).strip().strip("/")
    return bool(pat) and (sub == pat or sub.startswith(pat + "/") or fnmatch.fnmatchcase(sub, pat))


class Repo:
    """Steering is two layers read as one: the project's own `_steering/` first, then the shipped `_steering/.yask/`.
    A project file supersedes the shipped file at the same relative path; a project file with `override:` on top
    also switches off the shipped files it names, whatever their names."""

    def __init__(self, root=None):
        self.root = find_root(root)
        self.steer = self.root / "_steering"
        self.base = self.steer / ".yask"
        self.ws = self.steer / ".ws"
        self._ov = None
        self.seed_ws()
        cfg = self.ws / "config.yaml"
        self.config = yamlsub.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}
        self.manifests = {}
        for n in self.steer_names("modules"):
            f = self.steer_path(f"modules/{n}/module.yaml")
            if f:
                m = yamlsub.loads(f.read_text(encoding="utf-8"))
                self.manifests[m.get("name", n)] = m
        self.enabled = list((self.config.get("modules") or {}).get("enabled") or [])
        self._fm = {}
        self._read_cache = None       # a check can reuse reads for the length of one scan; never across writes
        self.folders = self.load_folders()

    # -- the two steering layers ---------------------------------------------------------
    def seed_ws(self):
        """The project's .ws is generated here the first time the tool runs: its settings start as copies of the shipped ones."""
        src = self.base / ".ws"
        if not src.is_dir() or not os.access(self.root, os.W_OK):
            return
        self.ws.mkdir(parents=True, exist_ok=True)
        for n in SETTINGS:
            if (src / n).exists() and not (self.ws / n).exists():
                shutil.copyfile(src / n, self.ws / n)

    def overrides(self):
        """(pattern, file that carries it): `override:` on top of a project steering document (front matter) or yaml file."""
        if self._ov is None:
            out = []
            if self.steer.is_dir():
                for d, dirs, files in os.walk(self.steer):
                    dirs[:] = [x for x in dirs if x not in (".yask", ".ws") and x not in SKIP_DIRS]
                    for f in files:
                        if f.endswith((".md", ".yaml")):
                            p = Path(d) / f
                            try:
                                t = p.read_text(encoding="utf-8")
                                v = read_fm(t)[0].get("override") if f.endswith(".md") else yamlsub.loads(t).get("override")
                            except Exception:
                                continue
                            for x in ([v] if isinstance(v, str) else v if isinstance(v, list) else []):
                                out.append((str(x), p.relative_to(self.root).as_posix()))
            self._ov = out
        return self._ov

    def overridden_by(self, sub):
        return next((f for pat, f in self.overrides() if match(sub, pat)), None)

    def base_active(self, sub):
        """A shipped file is in force unless the project has a file at the same path or an override switches it off."""
        return not (self.steer / sub).exists() and self.overridden_by(sub) is None

    def steer_path(self, sub):
        """The file in force for a steering-relative path: the project's, else the shipped one if not switched off."""
        sub = sub.strip("/")
        if sub.startswith(".yask/"):   # the shipped layer is reached through the merge, never by its own name
            return (self.steer / sub) if (self.steer / sub).exists() else None
        p = self.steer / sub
        if p.exists():
            return p
        b = self.base / sub
        return b if b.exists() and self.overridden_by(sub) is None else None

    def steer_layer(self, sub):
        p = self.steer_path(sub)
        return None if p is None else ("base" if self.base in p.parents else "project")

    def steer_rel(self, sub):
        p = self.steer_path(sub)
        return p.relative_to(self.root).as_posix() if p else None

    def read_steer(self, sub):
        p = self.steer_path(sub)
        if p is None:
            raise WsError(f"no steering file {sub} (project _steering/ or the shipped _steering/.yask/)", 2)
        return p.read_text(encoding="utf-8")

    def steer_list(self, sub, pattern="*.md"):
        """name -> Path of the files directly in a steering folder, both layers, project first."""
        sub = sub.strip("/")
        out = {}
        for layer in (self.base, self.steer):
            d = layer / sub
            if d.is_dir():
                for f in sorted(d.glob(pattern)):
                    if f.is_file() and (layer is self.steer or self.base_active(f"{sub}/{f.name}")):
                        out[f.name] = f
        return out

    def steer_rglob(self, sub, pattern="*.md"):
        """relative name -> Path for every file under a steering folder, both layers, project first."""
        sub = sub.strip("/")
        out = {}
        for layer in (self.base, self.steer):
            d = layer / sub
            if d.is_dir():
                for f in sorted(d.rglob(pattern)):
                    r = f.relative_to(d).as_posix()
                    if f.is_file() and "__pycache__" not in f.parts and (layer is self.steer or self.base_active(f"{sub}/{r}")):
                        out[r] = f
        return out

    def steer_names(self, sub):
        """Names of the folders directly in a steering folder, both layers (switched-off ones excluded)."""
        sub = sub.strip("/")
        names = set()
        for layer in (self.base, self.steer):
            d = layer / sub
            if d.is_dir():
                names |= {x.name for x in d.iterdir() if x.is_dir() and not x.name.startswith((".", "__")) and (layer is self.steer or self.overridden_by(f"{sub}/{x.name}") is None)}
        return sorted(names)

    def steer_has_dir(self, sub):
        sub = sub.strip("/")
        return (self.steer / sub).is_dir() or ((self.base / sub).is_dir() and self.overridden_by(sub) is None)

    def load_folders(self):
        """Entries of _steering/.ws/folders.yaml by path."""
        f = self.ws / "folders.yaml"
        rows = yamlsub.loads(f.read_text(encoding="utf-8")).get("folders") if f.exists() else []
        return {str(e["path"]).strip("/"): {**e, "path": str(e["path"]).strip("/")} for e in rows or [] if isinstance(e, dict) and e.get("path")}

    def policy(self, rel, entered=""):
        """Flags for a path: the longest matching folder entry, else the prefix default (dot = out of the way).
        `entered` is a folder the caller asked for by path; entries at or above it do not apply."""
        rel = rel.strip("/")
        best = None
        for p, e in self.folders.items():
            if (rel == p or rel.startswith(p + "/")) and not (entered and (entered == p or entered.startswith(p + "/"))):
                if best is None or len(p) > len(best["path"]):
                    best = e
        ent = entered.strip("/")
        view = re.sub(r"^_steering/\.yask(/|$)", lambda m: "_steering" + m.group(1), rel)   # the shipped layer is part of steering, not a hidden folder
        tail = view[len(ent):].strip("/") if ent and (view == ent or view.startswith(ent + "/")) else view
        tail = tail if not ent.startswith("_steering/.yask") else rel[len(ent):].strip("/")
        hidden = any(x.startswith(".") for x in tail.split("/") if x)
        dflt = not hidden
        e = best or {}
        return {k: bool(e.get(k, dflt)) for k in ("listed", "searched", "checked")} | {"generated": bool(e.get("generated")), "purpose": e.get("purpose", "")}

    def searchable(self, rel, steering=False, hidden=False):
        p = self.policy(rel)
        return hidden or p["searched"] or (steering and p["purpose"].startswith("steering"))

    # -- paths -------------------------------------------------------------
    def rel(self, p):
        return Path(p).resolve().relative_to(self.root).as_posix()

    def abs(self, rel):
        """Where a write goes: always the project's own path."""
        return self.root / rel

    def seen(self, rel):
        """Where a read goes. A path under _steering/ is looked up in _steering/ first, then in the shipped _steering/.yask/."""
        p = self.root / rel
        if not p.exists() and rel.startswith("_steering/") and not rel.startswith(("_steering/.yask", "_steering/.ws")):
            sub = rel[len("_steering/"):]
            if (self.base / sub).exists() and self.overridden_by(sub) is None:
                return self.base / sub
        return p

    def exists(self, rel):
        return self.seen(rel).exists()

    def read(self, rel):
        if self._read_cache is not None and rel in self._read_cache:
            return self._read_cache[rel]
        text = self.seen(rel).read_text(encoding="utf-8", errors="replace")
        if self._read_cache is not None:
            self._read_cache[rel] = text
        return text

    def fm(self, rel):
        if rel not in self._fm:
            self._fm[rel] = read_fm(self.read(rel))[0]
        return self._fm[rel]

    def skip(self, rel, include_archive=False, scope="checked", entered=""):
        parts = rel.split("/")
        if any(x in SKIP_DIRS for x in parts):
            return True
        if rel.startswith(BASE_PREFIX) and not self.base_active(rel[len(BASE_PREFIX):]):   # superseded or switched off
            return True
        p = self.policy(rel, entered)
        if p["generated"]:
            return True
        if include_archive:
            return False
        return not (p["checked"] or p["searched"]) if scope == "indexed" else not p[scope]

    def walk(self, exts=(".md",), include_archive=False, under="", scope="checked"):
        """include_archive=True also returns folders the registry hides (never generated ones)."""
        base = self.root / under if under else self.root
        under = under.strip("/")
        out = []
        for d, dirs, files in os.walk(base):
            rd = Path(d).relative_to(self.root).as_posix()
            rd = "" if rd == "." else rd
            dirs[:] = sorted(x for x in dirs if not self.skip((rd + "/" + x).lstrip("/"), include_archive, scope, under))
            for f in sorted(files):
                r = (rd + "/" + f).lstrip("/")
                if Path(f).suffix in exts and not self.skip(r, include_archive, scope, under):
                    out.append(r)
        return out

    def md_files(self, **kw):
        return self.walk((".md",), **kw)

    def code_files(self):
        root = self.code_root()
        return self.walk(tuple(CODE_EXT), under=root.rstrip("/")) if root and self.exists(root.rstrip("/")) else []

    def code_root(self):
        for e in self.where_entries(all_modules=True):
            if e["module"] == "code" and e["path"].endswith("/"):
                return e["path"]
        return "code/"

    # -- manifests ---------------------------------------------------------
    def where_entries(self, all_modules=False):
        out = []
        names = list(self.manifests) if all_modules else self.enabled
        for n in names:
            for w in (self.manifests.get(n) or {}).get("where") or []:
                out.append({**w, "module": n})
        return out

    def kind_of(self, rel):
        best, bl = None, -1
        for e in self.where_entries(all_modules=True):
            p = e["path"].split("<")[0]
            if (rel == p.rstrip("/") or rel.startswith(p if p.endswith("/") else p + "/") or (not p.endswith("/") and rel == p)) and len(p) > bl:
                best, bl = e["kind"], len(p)
        if best and best != "any":
            return best
        if rel.startswith("_steering/"):
            return "steering"
        if rel.endswith(".md") and self.exists(rel):
            k = self.fm(rel).get("kind")
            if k:
                return k
        return best or "canon"

    def description(self, rel):
        d = self.fm(rel).get("description")
        if d:
            return str(d)
        for line in self.read(rel).splitlines():
            if line.startswith("#"):
                return line.lstrip("# ").strip()
        return ""

    # -- git ---------------------------------------------------------------
    def git(self, *args, check=False, env=None):
        try:
            r = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace",
                               env={**os.environ, **env} if env else None)
        except FileNotFoundError:
            return 127, "", "git not found"
        if check and r.returncode:
            raise WsError(f"git {' '.join(args)}: {r.stderr.strip()}", 3)
        return r.returncode, r.stdout, r.stderr

    def is_git(self):
        return self.git("rev-parse", "--is-inside-work-tree")[0] == 0

    def head(self):
        rc, out, _ = self.git("rev-parse", "--short", "HEAD")
        return out.strip() if rc == 0 else ""

    def user(self, override=None):
        u = override or os.environ.get("WS_USER")
        if not u:
            rc, out, _ = self.git("config", "user.name")
            u = out.strip() if rc == 0 else ""
        u = slug(u)
        if not u:
            raise WsError("who are you? pass --you NAME or set WS_USER", 3)
        return u

    def globs(self, patterns, files):
        out = []
        for g in patterns:
            gg = g.replace("**/", "*").replace("**", "*")
            out += [f for f in files if fnmatch.fnmatch(f, gg)]
        return out
