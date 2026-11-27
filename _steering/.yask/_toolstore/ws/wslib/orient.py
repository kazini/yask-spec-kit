"""Orient commands: map, where, playbooks, route, modules, tools, outline, section, brief, index, find, related, impact, callers, path, decisions, show."""
import re
import sqlite3
from pathlib import Path

from . import gen
from .index import Index, fold, STOP
from .repo import WsError, read_fm
from .util import emit, table

ROUTE_STOP = STOP | set("without should would could into".split())   # filler a request carries that matches unrelated use_when lines


def _ix(repo):
    return Index(repo).ensure()


def tokens_k(nbytes):
    return max(1, nbytes // 4)


def cmd_map(repo, a):
    base = (a.path or "").strip("/")
    sub = base if base and (repo.root / base).is_dir() else ""
    files = repo.md_files(under=sub, scope="listed")
    hidden = len(repo.md_files(under=sub)) - len(files)   # in checked folders the registry leaves unlisted
    rows, missing = [], 0
    for f in files:
        d = repo.fm(f).get("description")
        if not d:
            missing += 1
        rows.append({"path": f, "kind": repo.fm(f).get("kind", ""), "description": str(d or repo.description(f)), "missing": not d})
    if a.json:
        return emit(a, rows, "")
    cap = int((repo.config.get("budgets") or {}).get("map_files", 120))
    if len(rows) > cap and not a.depth and not getattr(a, "all", False):   # too many to list: a folder summary and where to look next
        groups = {}
        for r in rows:
            rest = r["path"][len(sub):].lstrip("/") if sub else r["path"]
            top = rest.split("/")[0] + "/" if "/" in rest else "./"
            groups.setdefault(top, []).append(r)
        for top, rs in sorted(groups.items()):
            readme = next((x["description"] for x in rs if x["path"].endswith("README.md")), "")
            print(f"{top:<28} {len(rs):>5} files  {readme[:80]}")
        print(f"\n{len(rows)} files: ws map <folder> lists one, --all lists everything ({len(rows) * 30 // 4} tokens or more)")
        return 1 if missing else 0
    out, last = [], None
    for r in rows:
        parts = r["path"].split("/")
        if a.depth and len(parts) > a.depth + 1:
            continue
        d = "/".join(parts[:-1])
        if d != last:
            out.append(f"{d}/" if d else "./")
            last = d
        out.append(f"  {parts[-1]:<32} {r['description'][:110]}" + ("   [no description]" if r["missing"] else ""))
    print("\n".join(out))
    if hidden:
        print(f"\n({hidden} file(s) in set-apart or out-of-the-way folders not listed: ask by path, or see ws folders)")
    if missing:
        print(f"\n{missing} file(s) have no description in front matter")
    return 1 if missing else 0


def cmd_where(repo, a):
    rows = [(w["module"], w["path"], w["kind"], w["holds"]) for w in repo.where_entries(all_modules=a.all)]
    emit(a, [dict(zip(("module", "path", "kind", "holds"), r)) for r in rows], table([(r[1], r[2], r[3]) for r in rows], ["path", "kind", "holds"]))
    return 0


def cmd_modules(repo, a):
    """ws modules                       list them, on or off
    ws modules enable|disable NAME   preview; add --apply to change `modules.enabled` and refresh the generated blocks of AGENTS.md"""
    from . import gen, sessions
    act = getattr(a, "action", None) or "list"
    if act != "list":
        if not a.name:
            raise WsError(f"ws modules {act} <module>", 2)
        plan = sessions.enable_plan(repo, a.name) if act == "enable" else sessions.disable_plan(repo, a.name)
        if not plan:
            emit(a, {"changed": []}, f"{a.name} is already on")
            return 0
        if not a.apply:
            emit(a, {"would": act, "modules": plan}, f"would {act} {', '.join(plan)}; add --apply (enabling or disabling changes which playbooks and checks apply: ask a person first)")
            return 0
        done = sessions.enable_module(repo, a.name) if act == "enable" else sessions.disable_module(repo, a.name)
        gen.apply(repo, write=True)
        note = "" if act == "enable" else "; its files stay where they are, only its playbooks, checks and routing stop applying"
        emit(a, {"changed": done, "state": act + "d"}, f"{act}d: {', '.join(done)}; generated blocks refreshed{note}")
        return 0
    rows = []
    for n, m in repo.manifests.items():
        rows.append({"name": n, "enabled": n in repo.enabled, "default": bool(m.get("default")), "requires": m.get("requires") or [], "description": m.get("description", "")})
    emit(a, rows, table([(r["name"], "on" if r["enabled"] else "off", ",".join(r["requires"]), r["description"][:90]) for r in rows], ["module", "state", "requires", "description"]))
    return 0


def check_playbooks(repo):
    pbs = gen.routed_playbooks(repo)
    problems = []
    toks = {}
    for p in pbs:
        uw = p["use_when"]
        t = {x for x in re.findall(r"\w+", fold(uw)) if x not in STOP and len(x) > 2}
        toks[p["path"]] = t
        if not re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", p["path"].rsplit("/", 1)[-1][:-3]):
            problems.append((p["path"], "warn", "playbook file names are lowercase words joined by hyphens, verb first for what the agent does (record-decision)"))
        if not uw:
            problems.append((p["path"], "error", "no use_when"))
        elif len(uw.split()) < 5:
            problems.append((p["path"], "warn", f"use_when is vague ({len(uw.split())} words): say what it does and when it applies"))
        text = repo.read(p["path"])
        body = read_fm(text)[1]
        if re.search(r"(?im)^#+\s*(when to use|use this when|use when)\b", body):
            problems.append((p["path"], "warn", "when-to-use text in the body belongs in use_when"))
    keys = list(toks)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a_, b_ = toks[keys[i]], toks[keys[j]]
            if a_ and b_:
                sim = len(a_ & b_) / len(a_ | b_)
                if sim >= 0.5:
                    problems.append((keys[i], "warn", f"use_when overlaps {keys[j]} ({sim:.2f})"))
    return pbs, problems


def cmd_playbooks(repo, a):
    pbs, problems = check_playbooks(repo)
    if a.check:
        emit(a, [dict(path=p, severity=s, message=m) for p, s, m in problems],
             "\n".join(f"{s:5} {p}: {m}" for p, s, m in problems) or f"{len(pbs)} playbooks: use_when lines are present, specific and distinct")
        return 2 if any(s == "error" for _, s, _ in problems) else (1 if problems else 0)
    emit(a, pbs, table([(p["path"].split("/")[-1], p["use_when"][:100]) for p in pbs], ["playbook", "use when"]))
    return 0


def stem(t):
    """Crude: drop a common ending so 'editing', 'edited' and 'edits' reach 'edit' (and 'agreed' reaches 'agree...')."""
    for s in ("ing", "ed", "es", "s"):
        if t.endswith(s) and len(t) - len(s) >= 4:
            return t[:-len(s)]
    return t


def cmd_route(repo, a):
    pbs = gen.routed_playbooks(repo)
    toks = [t for t in re.findall(r"\w+", fold(a.query)) if t not in ROUTE_STOP]
    if not toks:
        raise WsError("empty query", 2)
    db = sqlite3.connect(":memory:")
    try:
        db.execute("create virtual table r using fts5(use_when, description, tokenize='unicode61 remove_diacritics 2')")
        for i, p in enumerate(pbs):
            db.execute("insert into r(rowid,use_when,description) values (?,?,?)", (i, p["use_when"], p["description"]))
        q = " OR ".join(f'"{stem(t)}"*' if len(stem(t)) >= 4 and (stem(t) != t or len(t) >= 5) else f'"{t}"' for t in toks)   # a short word stays exact: "long" must not reach "longer"
        rows = db.execute("select rowid, bm25(r, 5.0, 1.0) from r where r match ? order by 2 limit 5", (q,)).fetchall()
        hits = [(pbs[i], round(-s, 2)) for i, s in rows]
    except sqlite3.OperationalError:
        hits = sorted(((p, sum(fold(p["use_when"] + p["description"]).count(stem(t)) for t in toks)) for p in pbs), key=lambda x: -x[1])[:5]
        hits = [(p, s) for p, s in hits if s]
    near = len(hits) > 1 and hits[1][1] >= 0.85 * hits[0][1]
    emit(a, {"query": a.query, "hits": [{"path": p["path"], "score": s, "use_when": p["use_when"]} for p, s in hits], "near_tie": near},
         "\n".join(f"{s:6.2f}  {p['path']}  {p['use_when'][:70]}" for p, s in hits) + ("\n(top two are close: sharpen their use_when lines)" if near else "") if hits else "no playbook matches these words. Routing matches words, not meaning, so this does not mean none applies: try other words for the same thing, or read the router in AGENTS.md")
    return 1 if near or not hits else 0


def cmd_tools(repo, a):
    rows = []
    for n in repo.steer_names("_toolstore"):
        r = repo.steer_path(f"_toolstore/{n}/README.md")
        if r is not None and not n.startswith("_"):
            rows.append({"tool": f"_steering/_toolstore/{n}", "description": str(read_fm(r.read_text(encoding='utf-8'))[0].get("description", ""))})
    d = repo.root / "_tools"
    if d.is_dir():
        for t in sorted(d.iterdir()):
            r = t / "README.md"
            if t.is_dir() and r.exists() and not t.name.startswith("_"):
                rows.append({"tool": f"_tools/{t.name}", "description": str(read_fm(r.read_text(encoding='utf-8'))[0].get("description", ""))})
    emit(a, rows, table([(r["tool"], r["description"][:100]) for r in rows], ["tool", "description"]))
    return 0


def cmd_index(repo, a):
    ix = Index(repo).open()
    if a.force:
        stats = ix.rebuild()
    else:
        stale = ix.stale()
        stats = ix.rebuild() if stale else None
    if stats is None:
        n = ix.db.execute("select count(*) from sections").fetchone()[0]
        emit(a, {"fresh": True, "sections": n}, f"index is fresh ({n} sections)")
    else:
        emit(a, stats, f"indexed {stats['files']} files: {stats['sections']} sections, {stats['edges']} edges, {stats['symbols']} symbols (fts5={stats['fts5']})")
    return 0


def cmd_find(repo, a):
    ix = _ix(repo)
    hits = ix.find(" ".join(a.terms), a.k * 4)
    hits = [h for h in hits if repo.searchable(h["path"], a.steering, a.hidden)]   # the folder registry decides (ws folders)
    hits = hits[:a.k]
    if a.json:
        return emit(a, hits, "")
    if not hits:
        print("no match; try synonyms or the glossary terms in docs/context/")
        return 1
    for h in hits:
        loc = f"{h['path']}:{h['lines'][0]}-{h['lines'][1]}" if h["via"] != "symbol" else f"{h['path']}:{h['lines'][0]}"
        print(f"{h['id'][:90]}\n    {loc}  {h['size']} B  [{h['via']}]  {h['first'][:100]}")
    return 0


def _section_row(ix, path, heading):
    rows = ix.db.execute("select * from sections where path=?", (path,)).fetchall()
    exact = [r for r in rows if r["heading"].lower() == heading.lower()]
    if exact:
        return exact[0], None
    part = [r for r in rows if heading.lower() in r["heading"].lower()]
    if len(part) == 1:
        return part[0], None
    return None, [r["heading"] for r in (part or rows)]


def cmd_outline(repo, a):
    rel = repo.rel(Path(a.file).resolve()) if Path(a.file).is_absolute() else a.file
    if not repo.exists(rel):
        raise WsError(f"no such file: {a.file}", 2)
    ix = _ix(repo)
    if rel.endswith(".md"):
        rows = ix.db.execute("select heading, level, l1, l2, size from sections where path=? order by l1", (rel,)).fetchall()
        data = [dict(r) for r in rows]
        emit(a, data, "\n".join(f"{'  ' * max(0, r['level'] - 1)}{r['heading']}  [{r['l1']}-{r['l2']}, {r['size']} B]" for r in data) or "(no headings)")
    else:
        rows = ix.db.execute("select name, kind, l1, l2 from symbols where path=? order by l1", (rel,)).fetchall()
        data = [dict(r) for r in rows]
        emit(a, data, "\n".join(f"{r['kind']:9} {r['name']}  [{r['l1']}-{r['l2']}]" for r in data) or "(no symbols found; no adapter for this file type)")
    return 0


def cmd_section(repo, a):
    ix = _ix(repo)
    row, cands = _section_row(ix, a.file, a.heading)
    if row is None:
        raise WsError("no unique match; headings: " + "; ".join(cands[:12]), 2)
    lines = repo.read(a.file).split("\n")[row["l1"] - 1:row["l2"]]
    print("\n".join(lines))
    return 0


def cmd_brief(repo, a):
    ix = _ix(repo)
    hits = [h for h in ix.find(" ".join(a.topic), a.k * 4) if h["via"] != "symbol" and repo.searchable(h["path"])][:a.k]
    by = {}
    for h in hits:
        by.setdefault(h["path"], []).append(h)
    total = sum(h["size"] for h in hits)
    rel = []
    for p in list(by)[:3]:
        outs, ins = ix.edges_of(p)
        rel += [e["dst"] for e in outs if e["type"] in ("link", "mentions", "supersedes", "derived", "covers")][:3]
    rel = [r for r in dict.fromkeys(rel) if r not in by][:5]
    data = {"read": [{"path": p, "description": str(repo.fm(p).get("description", "")), "sections": [{"heading": h["heading"], "lines": h["lines"], "size": h["size"]} for h in hs]} for p, hs in by.items()],
            "also_related": rel, "approx_tokens": tokens_k(total)}
    if a.json:
        return emit(a, data, "")
    for p, hs in by.items():
        print(f"{p}  — {repo.fm(p).get('description', '')}")
        for h in hs:
            print(f"    {h['heading']}  [{h['lines'][0]}-{h['lines'][1]}, {h['size']} B]")
    if rel:
        print("also related: " + ", ".join(rel))
    print(f"approx {tokens_k(total)} tokens for the listed sections")
    return 0 if hits else 1


def _node(repo, ref):
    return ref.replace("\\", "/")


def cmd_related(repo, a):
    ix = _ix(repo)
    outs, ins = ix.edges_of(_node(repo, a.ref))
    data = {"out": [{"to": e["dst"], "type": e["type"], "confidence": e["conf"]} for e in outs], "in": [{"from": e["src"], "type": e["type"], "confidence": e["conf"]} for e in ins]}
    if a.json:
        return emit(a, data, "")
    print("points to:")
    print("\n".join(f"  {e['type']:10} {e['dst']}" for e in outs) or "  (none)")
    print("pointed to by:")
    print("\n".join(f"  {e['type']:10} {e['src']}" for e in ins) or "  (none)")
    return 0


def cmd_impact(repo, a):
    ix = _ix(repo)
    res = ix.impact(_node(repo, a.ref))
    emit(a, res, "\n".join(f"{'  ' * (r['depth'] - 1)}{r['node']}  ({r['via']} {r['from']})" for r in res) or "nothing depends on it")
    return 0


def cmd_callers(repo, a):
    ix = _ix(repo)
    syms = ix.symbols_named(a.symbol)
    if not syms:
        raise WsError(f"no symbol named {a.symbol}; run ws find {a.symbol}", 2)
    rows = []
    for s in syms:
        for e in ix.edges_of(f"{s['path']}:{s['name']}")[1]:
            if e["type"] == "calls":
                rows.append({"caller": e["src"], "callee": e["dst"], "confidence": e["conf"]})
    emit(a, rows, table([(r["caller"], r["callee"], r["confidence"]) for r in rows], ["caller", "callee", "confidence"]))
    return 0


def cmd_path(repo, a):
    ix = _ix(repo)

    def ends(x):
        s = ix.symbols_named(x)
        return [f"{r['path']}:{r['name']}" for r in s] or [x]
    for s in ends(a.a):
        for t in ends(a.b):
            p = ix.path_between(s, t)
            if p:
                emit(a, p, " -> ".join(p))
                return 0
    print("no path over calls or imports")
    return 1


def decisions(repo):
    out = []
    for f in sorted(repo.walk((".md",), under="docs/decisions")) if repo.exists("docs/decisions") else []:
        name = Path(f).name
        if name in ("README.md", "rejected.md"):
            continue
        fm = repo.fm(f)
        out.append({"path": f, "id": Path(f).stem, "status": fm.get("status", ""), "decider": fm.get("decider", ""), "supersedes": fm.get("supersedes", ""), "governing": bool(fm.get("governing")), "description": str(fm.get("description", ""))})
    return out


def cmd_decisions(repo, a):
    ds = decisions(repo)
    if a.governing:
        ds = [d for d in ds if d["governing"]]
    emit(a, ds, table([(d["id"], d["status"], d["decider"], d["supersedes"], "yes" if d["governing"] else "") for d in ds], ["decision", "status", "decider", "supersedes", "governing"]))
    return 0


def cmd_show(repo, a):
    rc, out, err = repo.git("log", f"--before={a.as_of}", "-1", "--format=%H", "--", a.doc)
    h = out.strip()
    if rc or not h:
        raise WsError(f"no version of {a.doc} on or before {a.as_of}", 2)
    rc, out, err = repo.git("show", f"{h}:{a.doc}")
    if rc:
        raise WsError(err.strip(), 2)
    print(out)
    return 0
