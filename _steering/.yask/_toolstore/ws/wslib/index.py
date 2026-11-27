"""Section and symbol index (SQLite; FTS5 when available) and the edge graph.
Stored in _steering/.ws/cache/index.db; in-place markdown edits refresh markdown rows, other changes rebuild."""
import hashlib
import posixpath
import re
import sqlite3
import unicodedata
from collections import deque
from pathlib import Path

from .repo import read_fm, slug

HEAD = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
TICK = re.compile(r"`([^`\n]+)`")
LABEL_ID = re.compile(r"\{#([tolr]-[0-9a-f]{4})\b")
ID_REF = re.compile(r"\b([tolrm]-[0-9a-f]{4})\b")
REQ_DEF = re.compile(r"^#{2,4}\s+([A-Z][A-Z0-9]{0,5}-\d+(?:\.\d+)*)\b")
REQ_REF = re.compile(r"\b([A-Z][A-Z0-9]{0,5}-\d+(?:\.\d+)*)\b")
STOP = set("the a an of to in on for and or is are be it this that with as by at from how what when where which do does i you we".split())
KEYWORDS = set("if for while switch return catch else elif def class function new print len range str int list dict set map get put and or not in is lambda with try except finally yield await async import from as pass raise assert del global".split())

SYMBOLS = {
    ".py": [(r"^\s*(?:async\s+)?def\s+(\w+)", "function"), (r"^\s*class\s+(\w+)", "class")],
    ".js": [(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(\w+)", "function"), (r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)", "class"),
            (r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>", "function")],
    ".rs": [(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+(\w+)", "function"), (r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+(\w+)", "type")],
    ".go": [(r"^func\s+(?:\([^)]*\)\s*)?(\w+)", "function"), (r"^type\s+(\w+)\s+(?:struct|interface)", "type")],
    ".java": [(r"^\s*(?:public|private|protected|static|final|abstract|\s)*(?:class|interface|enum)\s+(\w+)", "class"),
              (r"^\s*(?:public|private|protected|static|final|abstract|synchronized|\s)+[\w<>\[\],.?\s]+?\s+(\w+)\s*\([^;{]*\)\s*(?:throws [\w, .]+)?\s*\{", "function")],
    ".rb": [(r"^\s*def\s+(?:self\.)?(\w+)", "function"), (r"^\s*(?:class|module)\s+(\w+)", "class")],
    ".php": [(r"^\s*(?:public|private|protected|static|\s)*function\s+(\w+)", "function"), (r"^\s*(?:abstract\s+)?class\s+(\w+)", "class")],
    ".sh": [(r"^\s*(?:function\s+)?(\w+)\s*\(\)\s*\{", "function")],
    ".c": [(r"^[A-Za-z_][\w\s\*]*?\s+\**(\w+)\s*\([^;]*\)\s*\{?\s*$", "function")],
}
for _e in (".mjs", ".ts", ".tsx", ".jsx"):
    SYMBOLS[_e] = SYMBOLS[".js"]
for _e in (".cs",):
    SYMBOLS[_e] = SYMBOLS[".java"]
for _e in (".h", ".cpp"):
    SYMBOLS[_e] = SYMBOLS[".c"]
IMPORTS = {
    ".py": r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))",
    ".js": r"""(?:import\s+[^'"]*?from\s+|import\s+|require\()\s*['"]([^'"]+)['"]""",
    ".rs": r"^\s*(?:pub\s+)?mod\s+(\w+)\s*;",
    ".go": r'^\s*(?:import\s+)?"([\w./-]+)"',
}
for _e in (".mjs", ".ts", ".tsx", ".jsx"):
    IMPORTS[_e] = IMPORTS[".js"]


STRONG = {"ref", "derived", "supersedes", "covers", "calls", "imports"}


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def sha(b):
    return hashlib.sha1(b).hexdigest()


def norm(node):
    return node.split("#")[0] if "#" in node else node


class Index:
    def __init__(self, repo):
        self.repo = repo
        self.path = repo.ws / "cache" / "index.db"
        self.db = None
        self.fts = True

    # -- lifecycle ---------------------------------------------------------
    def _files(self):
        return self.repo.md_files(scope="indexed") + self.repo.code_files()

    def open(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            create table if not exists files(path text primary key, hash text, size int, mtime int);
            create table if not exists sections(id integer primary key, sid text, path text, heading text, level int, l1 int, l2 int, size int, first text);
            create table if not exists edges(src text, dst text, type text, conf text);
            create table if not exists code_edges(src text, dst text, type text, conf text);
            create table if not exists symbols(id integer primary key, name text, kind text, path text, l1 int, l2 int);
            create table if not exists meta(k text primary key, v text);
            create index if not exists e_src on edges(src); create index if not exists e_dst on edges(dst);
            create index if not exists s_path on sections(path); create index if not exists y_name on symbols(name);""")
        if not self.db.execute("select 1 from code_edges limit 1").fetchone() and self.db.execute("select 1 from edges limit 1").fetchone():
            self.db.execute("insert into code_edges select src, dst, type, conf from edges where type in ('imports','calls')")
        try:
            self.db.execute("create virtual table if not exists sfts using fts5(heading, body, meta, tokenize='unicode61 remove_diacritics 2')")
        except sqlite3.OperationalError:
            self.fts = False
            self.db.execute("create table if not exists sfts(rowid integer primary key, heading text, body text, meta text)")
        return self

    def stale(self):
        self.changed, self.added, self.removed = [], [], []
        have = {r["path"]: (r["hash"], r["size"], r["mtime"]) for r in self.db.execute("select * from files")}
        files = self._files()
        added, removed = set(files) - set(have), set(have) - set(files)
        if added or removed:
            self.added, self.removed = sorted(added), sorted(removed)
            self.changed = sorted(added | removed)
            return True
        for f in files:
            st = self.repo.abs(f).stat()
            h, size, mt = have[f]
            if size != st.st_size or mt != st.st_mtime_ns:
                if sha(self.repo.abs(f).read_bytes()) != h:
                    self.changed.append(f)
                else:
                    self.db.execute("update files set size=?, mtime=? where path=?", (st.st_size, st.st_mtime_ns, f))
        self.db.commit()
        return bool(self.changed)

    def _incremental_ok(self, changed):
        """Only modified, indexed markdown can be refreshed narrowly; added/removed files or code change global ids/confidence."""
        if not changed or getattr(self, "added", []) or getattr(self, "removed", []):
            return False
        md, code = set(self.repo.md_files(scope="indexed")), set(self.repo.code_files())
        return set(changed) <= md and not (set(changed) & code)

    def ensure(self):
        if self.db is None:
            self.open()
        if self.stale():
            changed = getattr(self, "changed", [])
            self.update(changed) if self._incremental_ok(changed) else self.rebuild()
        return self

    # -- build -------------------------------------------------------------
    def rebuild(self):
        r, db = self.repo, self.db
        for t in ("files", "sections", "edges", "code_edges", "symbols", "sfts"):
            db.execute(f"delete from {t}")
        md, code = r.md_files(scope="indexed"), r.code_files()
        raw = {}
        for f in md + code:
            b = r.abs(f).read_bytes()
            st = r.abs(f).stat()
            db.execute("insert into files values (?,?,?,?)", (f, sha(b), st.st_size, st.st_mtime_ns))
            raw[f] = b.decode("utf-8", "replace")
        sections, defs, fms = self._parse_md(md, raw)
        md_edges = self._md_edges(sections, md, code, fms, defs)
        code_edges = set()
        self._code(code, raw, lambda a, b, t, c="": code_edges.add((a, b, t, c)))
        db.executemany("insert into edges values (?,?,?,?)", sorted(md_edges | code_edges))
        db.executemany("insert into code_edges values (?,?,?,?)", sorted(code_edges))
        db.execute("insert or replace into meta values ('built', datetime('now'))")
        db.commit()
        return {"files": len(md) + len(code), "sections": len(sections), "edges": len(md_edges | code_edges),
                "symbols": db.execute("select count(*) from symbols").fetchone()[0], "fts5": self.fts}

    def update(self, changed):
        """Refresh markdown rows after in-place md edits; code rows stay untouched."""
        r, db = self.repo, self.db
        md, code = r.md_files(scope="indexed"), r.code_files()
        raw = {}
        for f in md:
            b = r.abs(f).read_bytes()
            st = r.abs(f).stat()
            raw[f] = b.decode("utf-8", "replace")
            if f in changed:
                db.execute("update files set hash=?, size=?, mtime=? where path=?", (sha(b), st.st_size, st.st_mtime_ns, f))
        for t in ("sections", "sfts"):
            db.execute(f"delete from {t}")
        sections, defs, fms = self._parse_md(md, raw)
        md_edges = self._md_edges(sections, md, code, fms, defs)
        code_edges = {tuple(x) for x in db.execute("select src, dst, type, conf from code_edges")}
        db.execute("delete from edges")
        db.executemany("insert into edges values (?,?,?,?)", sorted(md_edges | code_edges))
        db.execute("insert or replace into meta values ('built', datetime('now'))")
        db.commit()
        return {"files": len(md) + len(code), "sections": len(sections), "edges": len(md_edges | code_edges),
                "symbols": db.execute("select count(*) from symbols").fetchone()[0], "fts5": self.fts}

    def _parse_md(self, md, raw):
        """Insert sections/FTS, then return their stable ids, label/requirement defs and front matter."""
        db = self.db
        sections, defs, fms = [], {}, {}
        for f in md:
            fm, body, off = read_fm(raw[f])
            fms[f] = fm
            meta = f"{f} {fm.get('description', '')}"
            for s in split_sections(body, off):
                sid = f"{f}#{s['heading']}"
                n = 2
                while sid in defs.get("_sids", set()):
                    sid = f"{f}#{s['heading']} ({n})"
                    n += 1
                defs.setdefault("_sids", set()).add(sid)
                s.update(sid=sid, path=f, fm=fm, meta=meta)
                sections.append(s)
        for s in sections:
            cur = db.execute("insert into sections(sid,path,heading,level,l1,l2,size,first) values (?,?,?,?,?,?,?,?)",
                             (s["sid"], s["path"], s["heading"], s["level"], s["l1"], s["l2"], len(s["text"].encode()), s["first"]))
            db.execute("insert into sfts(rowid,heading,body,meta) values (?,?,?,?)", (cur.lastrowid, s["heading"], s["text"], s["meta"]))
            for m in LABEL_ID.finditer(s["text"]):
                defs[m.group(1)] = s["sid"]
            m = REQ_DEF.match(s["text"].split("\n", 1)[0])
            if m:
                defs[m.group(1)] = s["sid"]
        return sections, defs, fms

    def _md_edges(self, sections, md, code, fms, defs):
        """All edges derivable from markdown; code-derived ones live in code_edges."""
        r, edges = self.repo, set()
        allmd, by_base = set(md), {}
        for f in md:
            by_base.setdefault(Path(f).name, []).append(f)

        def add(a, b, t, c=""):
            if a != b:
                edges.add((a, b, t, c))
        for s in sections:
            f, sid, text = s["path"], s["sid"], s["text"]
            base = posixpath.dirname(f)   # repo paths are POSIX, even on Windows (Path would emit backslashes)
            plain = re.sub(r"`[^`\n]*`", "", re.sub(r"```.*?```", "", text, flags=re.S))
            for tgt in LINK.findall(plain):
                if re.match(r"^(https?:|mailto:|#)", tgt):
                    continue
                p, _, anc = tgt.partition("#")
                resolved = posixpath.normpath(posixpath.join(base, p)) if p else f
                add(sid, resolved + (f"#{anc}" if anc else ""), "link")
            for tok in TICK.findall(text):
                t = re.split(r"[#:]", tok)[0].rstrip("/.,)")
                if " " in tok or not t:
                    continue
                if t in allmd or (r.exists(t) and (r.abs(t).is_file()) and t != f):
                    add(sid, t, "mentions")
                elif t.endswith(".md") and "/" not in t:
                    cand = [x for x in by_base.get(t, []) if x.startswith(("_steering/playbooks/", "_steering/templates/", "_steering/.yask/playbooks/", "_steering/.yask/templates/"))]
                    if len(cand) == 1:
                        add(sid, cand[0], "mentions")
            for m in re.finditer(r"(?:src=|derived_from:\s*)([\w./-]+?)(?:#L\d+)?(?=[\s}\]]|$)", text):
                if m.group(1) in allmd:
                    add(sid, m.group(1), "derived")
            for m in ID_REF.finditer(text):
                d = defs.get(m.group(1))
                if d and d != sid:
                    add(sid, d, "ref")
            for m in REQ_REF.finditer(text):
                d = defs.get(m.group(1))
                if d and d != sid and norm(d) != f:
                    add(sid, d, "ref")
        for f in md:
            fm = fms.get(f, {})
            for key in ("derived_from", "source"):
                v = fm.get(key)
                if isinstance(v, str) and v.split("#")[0] in allmd:
                    add(f, v.split("#")[0], "derived")
            if fm.get("supersedes"):
                stem = str(fm["supersedes"]).replace(".md", "")
                hit = [p for p in md if Path(p).stem == stem]
                if hit:
                    add(f, hit[0], "supersedes")
            for g in ([fm["covers"]] if isinstance(fm.get("covers"), str) else fm.get("covers") or []):
                for c in r.globs([g], code):
                    add(f, c, "covers")
        return edges

    def _code(self, code, raw, add):
        db = self.db
        allsyms = {}
        per_file = {}
        for f in code:
            ext = Path(f).suffix
            pats = [(re.compile(p), k) for p, k in SYMBOLS.get(ext, [])]
            lines = raw[f].split("\n")
            found = []
            for i, l in enumerate(lines, 1):
                for rx, kind in pats:
                    m = rx.match(l)
                    if m and m.group(1) not in KEYWORDS:
                        found.append((m.group(1), kind, i))
                        break
            per_file[f] = (lines, found)
            for idx, (name, kind, l1) in enumerate(found):
                l2 = (found[idx + 1][2] - 1) if idx + 1 < len(found) else len(lines)
                db.execute("insert into symbols(name,kind,path,l1,l2) values (?,?,?,?,?)", (name, kind, f, l1, l2))
                allsyms.setdefault(name, []).append(f)
        names = {n for n in allsyms if len(n) >= 3 and n not in KEYWORDS}
        callrx = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
        for f, (lines, found) in per_file.items():
            ext = Path(f).suffix
            if ext in IMPORTS:
                rx = re.compile(IMPORTS[ext], re.M)
                for m in rx.finditer(raw[f]):
                    mod = next((g for g in m.groups() if g), "")
                    tgt = self._resolve_import(f, mod, ext, set(code))
                    add(f, tgt or f"ext:{mod}", "imports", "syntactic")
            for idx, (name, kind, l1) in enumerate(found):
                l2 = (found[idx + 1][2] - 1) if idx + 1 < len(found) else len(lines)
                seen = set()
                for ln in lines[l1:l2]:
                    for c in callrx.findall(ln):
                        if c in names and c != name and c not in seen:
                            seen.add(c)
                            conf = "syntactic" if len(allsyms[c]) == 1 else "ambiguous"
                            for tf in allsyms[c]:
                                add(f"{f}:{name}", f"{tf}:{c}", "calls", conf)

    def _resolve_import(self, f, mod, ext, files):
        if not mod:
            return None
        here = posixpath.dirname(f)       # keep the candidate paths POSIX-style on every OS
        root = self.repo.code_root().rstrip("/")
        cands = []
        if ext == ".py":
            rel = mod.replace(".", "/")
            for base in (here, root, posixpath.dirname(here)):
                cands += [f"{base}/{rel}.py", f"{base}/{rel}/__init__.py"]
        elif ext == ".rs":
            cands += [f"{here}/{mod}.rs", f"{here}/{mod}/mod.rs"]
        elif mod.startswith("."):
            p = posixpath.normpath(posixpath.join(here, mod))
            p = re.sub(r"(^|/)\./", r"\1", p)
            while re.search(r"[^/.]+/\.\./", p):
                p = re.sub(r"[^/.]+/\.\./", "", p, count=1)
            cands += [p] + [p + e for e in (".js", ".ts", ".tsx", ".jsx", ".mjs")] + [f"{p}/index{e}" for e in (".js", ".ts")]
        for c in cands:
            c = c.lstrip("./") if c.startswith("./") else c
            if c in files:
                return c
        return None

    # -- queries -----------------------------------------------------------
    def aliases(self):
        g = self.repo.abs("docs/context/glossary.md")
        groups = []
        if g.exists():
            for line in g.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*[-*]\s+(.+?):\s+(.+)$", line)
                if m:
                    groups.append({fold(x.strip()) for x in [m.group(1)] + m.group(2).split(",") if x.strip()})
        return groups

    def tokens(self, terms):
        toks = [t for t in re.findall(r"\w+", fold(terms)) if t not in STOP]
        extra = []
        for grp in self.aliases():
            if any(t in grp for t in toks):
                extra += [x for x in grp if x not in toks]
        return toks, extra

    def find(self, terms, k=8):
        toks, extra = self.tokens(terms)
        if not toks:
            return []
        out = []
        if self.fts:
            q = " OR ".join((f'"{t}"*' if len(t) >= 4 else f'"{t}"') for t in toks + extra[:8])
            rows = self.db.execute(
                "select s.sid, s.path, s.heading, s.l1, s.l2, s.size, s.first, bm25(sfts, 6.0, 1.0, 3.0) as sc from sfts join sections s on s.id = sfts.rowid where sfts match ? order by sc limit ?",
                (q, k)).fetchall()
            for x in rows:
                out.append({"id": x["sid"], "path": x["path"], "heading": x["heading"], "lines": [x["l1"], x["l2"]], "size": x["size"],
                            "first": x["first"], "score": round(-x["sc"], 2), "via": "lexical"})
        else:
            scored = []
            for x in self.db.execute("select s.sid, s.path, s.heading, s.l1, s.l2, s.size, s.first, f.heading as h, f.body as b, f.meta as m from sections s join sfts f on f.rowid = s.id"):
                hay = fold(x["h"] + " " + x["b"] + " " + x["m"])
                sc = sum((6 if t in fold(x["h"]) else 0) + hay.count(t) for t in toks + extra)
                if sc:
                    scored.append((sc, x))
            for sc, x in sorted(scored, key=lambda p: -p[0])[:k]:
                out.append({"id": x["sid"], "path": x["path"], "heading": x["heading"], "lines": [x["l1"], x["l2"]], "size": x["size"],
                            "first": x["first"], "score": sc, "via": "text-scan"})
        for t in toks:
            for x in self.db.execute("select name, kind, path, l1, l2 from symbols where lower(name) like ? limit 5", (f"%{t}%",)):
                out.append({"id": f"{x['path']}:{x['name']}", "path": x["path"], "heading": x["name"], "lines": [x["l1"], x["l2"]], "size": 0,
                            "first": x["kind"], "score": 1.0, "via": "symbol"})
        return out[: k + 5]

    def edges_of(self, node):
        """Outgoing and incoming edges for a path (file-level plus its sections), a section, or a symbol."""
        db = self.db
        if "#" in node or ":" in node and not node.startswith("ext:"):
            outs = db.execute("select * from edges where src=?", (node,)).fetchall()
            ins = db.execute("select * from edges where dst=?", (node,)).fetchall()
        else:
            outs = db.execute("select * from edges where src=? or src like ? or src like ?", (node, node + "#%", node + ":%")).fetchall()
            ins = db.execute("select * from edges where dst=? or dst like ? or dst like ?", (node, node + "#%", node + ":%")).fetchall()
        return ([dict(e) for e in outs if norm(e["dst"]) != norm(node) or e["type"] in ("calls",)],
                [dict(e) for e in ins if norm(e["src"]) != norm(node) or e["type"] in ("calls",)])

    def impact(self, node, limit=200):
        """Transitive dependents: who points at it, and who points at them."""
        seen, order, dq = {norm(node) if "#" in node else node}, [], deque([(node, 0)])
        while dq and len(order) < limit:
            cur, d = dq.popleft()
            ins = self.edges_of(cur)[1]
            for e in ins:
                if d >= 1 and e["type"] not in STRONG:
                    continue
                s = norm(e["src"]) if e["type"] != "calls" else e["src"]
                if s not in seen:
                    seen.add(s)
                    order.append({"node": s, "via": e["type"], "from": cur, "depth": d + 1})
                    dq.append((s, d + 1))
        return order

    def path_between(self, a, b):
        db = self.db
        dq, prev = deque([a]), {a: None}
        while dq:
            cur = dq.popleft()
            if cur == b:
                out = []
                while cur is not None:
                    out.append(cur)
                    cur = prev[cur]
                return out[::-1]
            for e in db.execute("select dst, type from edges where src=? and type in ('calls','imports')", (cur,)):
                if e["dst"] not in prev:
                    prev[e["dst"]] = cur
                    dq.append(e["dst"])
                f = e["dst"].split(":")[0]
                if e["type"] == "imports" and f not in prev:
                    prev[f] = cur
                    dq.append(f)
        return None

    def symbols_named(self, name):
        return [dict(x) for x in self.db.execute("select * from symbols where name=?", (name,))]


def clean_md(s):
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    return re.sub(r"[`*_]", "", s).strip()


def first_sentence(lines):
    for l in lines:
        t = l.strip()
        if not t or t.startswith(("|", "-", "*", ">", "`", "<!--", "#", "{")):
            continue
        t = clean_md(t)
        m = re.match(r"^(.{20,200}?[.!?])(\s|$)", t)
        return (m.group(1) if m else t[:160]).strip()
    return ""


def split_sections(body, off):
    lines = body.split("\n")
    marks, fence = [], False
    for i, l in enumerate(lines):
        if l.lstrip().startswith(("```", "~~~")):
            fence = not fence
        m = None if fence else HEAD.match(l)
        if m:
            marks.append((i, len(m.group(1)), clean_md(m.group(2))))
    out = []
    if not marks or marks[0][0] > 0 and any(x.strip() for x in lines[: marks[0][0]]):
        end = marks[0][0] if marks else len(lines)
        out.append({"heading": "(top)", "level": 0, "l1": off + 1, "l2": off + end, "text": "\n".join(lines[:end]), "first": first_sentence(lines[:end])})
    for n, (i, lvl, h) in enumerate(marks):
        j = marks[n + 1][0] if n + 1 < len(marks) else len(lines)
        seg = lines[i:j]
        out.append({"heading": h, "level": lvl, "l1": off + i + 1, "l2": off + j, "text": "\n".join(seg), "first": first_sentence(seg[1:])})
    return out
