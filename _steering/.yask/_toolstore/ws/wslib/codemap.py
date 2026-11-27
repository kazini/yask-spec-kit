"""Code map and graph: code map, code purposes, graph."""
import ast
import re
from collections import defaultdict, deque
from pathlib import Path

from .index import Index, norm
from .repo import WsError
from .util import atomic_write, emit, stamp


def purpose(text, ext):
    """First sentence of the module docstring or leading comment, or ''."""
    if ext == ".py":
        try:
            d = ast.get_docstring(ast.parse(text))
            if d:
                return d.strip().split("\n")[0][:140]
        except SyntaxError:
            pass
    lines = text.split("\n")[:15]
    buf = []
    for l in lines:
        s = l.strip()
        if not s or s.startswith(("#!", "'use strict'", '"use strict"', "package ", "<?php")) and not buf:
            continue
        m = re.match(r"^(?://!|///|//|#|--|\*|/\*\*?|\"\"\")\s?(.*?)(?:\*/)?$", s)
        if m:
            t = m.group(1).strip(" */\"")
            if t:
                buf.append(t)
            if s.endswith("*/") and buf:
                break
        elif buf:
            break
        else:
            break
    return (buf[0][:140]) if buf else ""


def programs(repo, ix):
    root = repo.code_root().rstrip("/")
    files = repo.code_files()
    prog = defaultdict(list)
    for f in files:
        parts = f[len(root) + 1:].split("/")
        prog[parts[0] if len(parts) > 1 else "(root)"].append(f)
    return root, prog


def cmd_code(repo, a):
    ix = Index(repo).ensure()
    root, prog = programs(repo, ix)
    if not prog:
        print(f"no code under {root}/ (or no adapter for its file types)")
        return 1
    missing = []
    out, edges = [f"{root}/ — {len(prog)} program(s)"], defaultdict(int)
    ext_imports = defaultdict(int)
    owner = {f: p for p, fs in prog.items() for f in fs}
    for e in ix.db.execute("select src, dst, type from edges where type in ('imports','calls')"):
        s, d = norm(e["src"]).split(":")[0], e["dst"].split(":")[0]
        if d.startswith("ext:"):
            ext_imports[d[4:]] += 1
        elif s in owner and d in owner and owner[s] != owner[d]:
            edges[(owner[s], owner[d])] += 1
    for p, fs in sorted(prog.items()):
        nsym = sum(ix.db.execute("select count(*) from symbols where path=?", (f,)).fetchone()[0] for f in fs)
        out.append(f"\n{root}/{p}/  ({len(fs)} files, {nsym} symbols)")
        for f in fs:
            txt = repo.read(f)
            pu = purpose(txt, Path(f).suffix)
            if not pu:
                missing.append(f)
            syms = [r["name"] for r in ix.db.execute("select name from symbols where path=? order by l1", (f,))]
            out.append(f"  {f[len(root) + len(p) + 2:]:<28} {pu or '[no purpose line]'}" + (f"\n      symbols: {', '.join(syms[:8])}{' +%d' % (len(syms) - 8) if len(syms) > 8 else ''}" if syms else ""))
    if edges:
        out.append("\nbetween programs: " + "; ".join(f"{s} -> {d} ({n})" for (s, d), n in sorted(edges.items())))
    if ext_imports:
        out.append("external: " + ", ".join(f"{k} ({v})" for k, v in sorted(ext_imports.items(), key=lambda x: -x[1])[:10]))
    if missing:
        out.append(f"\n{len(missing)} file(s) without a purpose line (module docstring or leading comment)")
    text = "\n".join(out)
    if a.ccmd == "purposes":
        emit(a, missing, "\n".join(missing) or "every code file has a purpose line")
        return 1 if missing else 0
    if a.write:
        atomic_write(repo.ws / "reports" / "code-map.md", f'---\nkind: generated\ndescription: "Code map {stamp()}: programs, files, purposes, symbols and cross-program imports."\n---\n```\n{text}\n```\n')
    emit(a, {"programs": {p: fs for p, fs in prog.items()}, "missing_purpose": missing, "between_programs": [{"from": s, "to": d, "edges": n} for (s, d), n in edges.items()]}, text)
    return 1 if missing else 0


def cmd_graph(repo, a):
    ix = Index(repo).ensure()
    start = a.ref
    seen, edges, dq = {start}, [], deque([(start, 0)])
    while dq:
        cur, d = dq.popleft()
        if d >= a.depth:
            continue
        outs, ins = ix.edges_of(cur)
        for e in outs:
            n = e["dst"] if (":" in e["dst"] and not e["dst"].startswith("ext:")) or "#" in start else norm(e["dst"])
            edges.append((cur, n, e["type"]))
            if n not in seen and len(seen) < a.max:
                seen.add(n)
                dq.append((n, d + 1))
        for e in ins:
            n = e["src"] if (":" in e["src"]) or "#" in start else norm(e["src"])
            edges.append((n, cur, e["type"]))
            if n not in seen and len(seen) < a.max:
                seen.add(n)
                dq.append((n, d + 1))
    edges = sorted(set(edges))
    if a.json:
        return emit(a, [{"from": s, "to": d, "type": t} for s, d, t in edges], "")
    if a.mermaid:
        ids = {n: f"n{i}" for i, n in enumerate(sorted({x for e in edges for x in e[:2]} | {start}))}
        lab = lambda n: n.replace('"', "'")
        print("graph LR")
        for n, i in ids.items():
            print(f'  {i}["{lab(n)}"]')
        for s, d, t in edges:
            print(f"  {ids[s]} -->|{t}| {ids[d]}")
    else:
        print("\n".join(f"{s}  --{t}-->  {d}" for s, d, t in edges) or "no edges")
    return 0
