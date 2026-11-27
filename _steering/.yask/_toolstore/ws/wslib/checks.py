"""check, review, dupes, insight."""
import hashlib
import json
import re
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from . import gen, yamlsub
from .index import Index, norm, fold, ID_REF
from .orient import check_playbooks, decisions
from .repo import match, read_fm, slug
from .util import atomic_write, emit, now, parse_item, parse_stamp, stamp, table, ATTR

TASK_ST = {"OPEN", "STARTED", "BLOCKED", "INCOMPLETE"}
KINDS = {"raw", "working", "canon", "personal", "generated", "steering"}
ITEM_TYPES = {"question", "decision", "risk", "assumption", "waiting"}
DEC_ST = {"proposed", "accepted", "deferred", "rejected", "withdrawn", "replaced"}
DEC_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}-[0-9a-f]{4}-[a-z0-9-]+$")
LOGLINE = re.compile(r"^- (\d{8}T\d{4}Z) @([\w-]+)(\+agent)? \((\w+)\): (.*?)(?: \{([0-9a-f]{4})\})?$")
ROOTS = ("docs/", "_workboard/", "_steering/", "code/", "_tools/", ".archive/")
NEVER_IGNORED = {"secret-pattern", "secret-tracked"}   # a secret is exempted one match at a time (ws secret allow), never by path


def finding(sev, code, path, msg, line=None):
    return {"severity": sev, "code": code, "path": path, "line": line, "message": msg}


def log_files(repo):
    return sorted(repo.walk((".md",), under="_workboard/people")) if repo.exists("_workboard/people") else []


def last_log_mentions(repo):
    """id -> datetime of the newest log line that mentions it."""
    out = {}
    for f in log_files(repo):
        if "/log/" not in f:
            continue
        for ln in repo.read(f).splitlines():
            m = LOGLINE.match(ln)
            if m:
                for i in ID_REF.findall(m.group(5)):
                    t = parse_stamp(m.group(1))
                    if i not in out or t > out[i]:
                        out[i] = t
    return out


def task_lines(repo, rel):
    out = []
    if repo.exists(rel):
        for n, ln in enumerate(repo.read(rel).split("\n"), 1):
            if ln.startswith("- ") and "{#" in ln:
                out.append((n, ln))
    return out


def resolves(repo, ref, wherepaths):
    ref = re.split(r"[#:]", ref)[0].rstrip("/.,)")
    if not ref or repo.exists(ref):
        return True
    if ref.startswith("_steering/.ws/"):  # optional or generated: cache, reports, backups, update notes
        return True
    return any(ref == w or ref.startswith(w + "/") or w.startswith(ref + "/") for w in wherepaths if w)


def check_ignores(repo):
    """{finding code: [path patterns]} from `.ws/check.yaml`. The code `*` stands for every code; a pattern is a file,
    a folder or a glob (the same forms `override:` takes). Anything that is not a map of codes to paths is left out."""
    try:
        cfg = yamlsub.loads((repo.ws / "check.yaml").read_text(encoding="utf-8"))
    except Exception:
        cfg = {}                           # a broken exceptions file ignores nothing; it never crashes the check
    ign = cfg.get("ignore") if isinstance(cfg, dict) else None
    out = {}
    for code, pats in (ign.items() if isinstance(ign, dict) else []):
        out[str(code)] = [str(x) for x in ([pats] if isinstance(pats, str) else pats if isinstance(pats, list) else [])]
    return out


def split_ignored(repo, F):
    """(kept, ignored): a finding is set aside when its code, or `*`, lists a pattern matching its path. Secret findings never are."""
    rules = check_ignores(repo)
    if not rules:
        return F, []
    kept, ignored = [], []
    for x in F:
        pats = rules.get(x["code"], []) + rules.get("*", [])
        (ignored if x["code"] not in NEVER_IGNORED and any(match(x["path"], p) for p in pats) else kept).append(x)
    return kept, ignored


def run_checks(repo, ix=None):
    """Every finding that counts: all of them, minus the exceptions the project keeps in check.yaml."""
    return split_ignored(repo, all_findings(repo, ix))[0]


def all_findings(repo, ix=None):
    """One read cache per scan; nothing is cached across writes."""
    repo._read_cache = {}
    try:
        return _findings(repo, ix or Index(repo).ensure())
    finally:
        repo._read_cache = None


def _findings(repo, ix):
    F = []
    md = repo.md_files()
    cfg = repo.config
    budget = (cfg.get("budgets") or {})
    hint = "ignore.front-matter in check.yaml"
    # front matter
    for f in md:
        text = repo.read(f)
        fm, body, off = read_fm(text)
        if not text.startswith("---\n"):
            F.append(finding("error", "front-matter", f, f"no front matter (add it, or list the file under {hint})"))
            continue
        if fm.get("_error"):
            F.append(finding("error", "front-matter", f, "front matter does not parse (quote values containing ': ')"))
            continue
        for k in ("kind", "description"):
            if not fm.get(k):
                F.append(finding("error", "front-matter", f, f"missing {k}"))
        if fm.get("kind") and fm["kind"] not in KINDS:
            F.append(finding("error", "front-matter", f, f"unknown kind {fm['kind']!r}: use one of {', '.join(sorted(KINDS))}"))
        for k in ("owner", "author"):
            if k in fm:
                F.append(finding("warn", "front-matter", f, f"{k} field: authorship comes from git and the folder"))
        if f.startswith("_steering/") and "/scaffold/" not in f and "/templates/" not in f and fm.get("kind") != "steering":
            F.append(finding("warn", "front-matter", f, "steering file should be kind: steering"))
    n = len(repo.read("AGENTS.md").splitlines())
    if n > int(budget.get("agents_md_lines", 150)):
        F.append(finding("warn", "size", "AGENTS.md", f"{n} lines over the {budget.get('agents_md_lines', 150)} line budget"))
    if gen.apply(repo)[0]:
        F.append(finding("error", "generated-block", "AGENTS.md", "router or where block is stale: run ws check --fix-generated"))
    # links, anchors
    heads = defaultdict(set)
    for r in ix.db.execute("select path, heading from sections"):
        heads[r["path"]].add(slug(r["heading"]))
    for e in ix.db.execute("select src, dst from edges where type='link'"):
        p, _, anc = e["dst"].partition("#")
        if p and not repo.exists(p):
            F.append(finding("error", "broken-link", norm(e["src"]), f"link target not found: {e['dst']}"))
        elif anc and p in heads and slug(anc) not in heads[p]:
            F.append(finding("error", "broken-anchor", norm(e["src"]), f"no heading for anchor: {e['dst']}"))
    wherepaths = [w["path"].split("<")[0].rstrip("/") for w in repo.where_entries(all_modules=True)]
    code = repo.code_files()
    for f in md:
        if f.startswith("_steering/"):
            continue
        text = repo.read(f)
        fm = repo.fm(f)
        for m in re.finditer(r"(?:src=|derived_from:\s*)([\w./-]+?)(?:#L(\d+))?(?=[\s}\]]|$)", text):
            p, ln = m.group(1), m.group(2)
            if not repo.exists(p):
                F.append(finding("error", "citation", f, f"cited file not found: {p}"))
            elif ln and p.endswith(".md") and int(ln) > len(repo.read(p).splitlines()):
                F.append(finding("error", "citation", f, f"cited line beyond end of file: {p}#L{ln}"))
        cov = fm.get("covers")
        for g in ([cov] if isinstance(cov, str) else cov or []):
            if not repo.globs([g], code):
                F.append(finding("error", "covers", f, f"covers matches no file: {g}"))
        for tok in re.findall(r"`([^`\n]+)`", text):
            if tok.startswith(ROOTS) and not re.search(r"[\s<>*|={}$()\[\]]", tok) and not resolves(repo, tok, wherepaths):
                F.append(finding("warn", "unresolved-path", f, f"path does not resolve: {tok}"))
        if f.startswith("docs/") and len(text.encode()) > int(budget.get("whole_read_kb", 25)) * 1024:
            F.append(finding("info", "size", f, f"{len(text.encode()) // 1024} KB: read by section; split if it mixes topics"))
    # decisions
    ds = decisions(repo)
    names = {d["id"] for d in ds}
    for d in ds:
        if not DEC_NAME.match(d["id"]):
            F.append(finding("warn", "decision", d["path"], "file name should be <YYYY-MM-DD-HHMM>-<4 hex>-<slug>"))
        if d["status"] not in DEC_ST:
            F.append(finding("error", "decision", d["path"], f"status must be one of {sorted(DEC_ST)}"))
        if d["status"] == "accepted" and not d["decider"]:
            F.append(finding("error", "decision", d["path"], "accepted decision needs a decider"))
        ppl = {slug(str(x)) for x in cfg.get("people") or []}
        if d["status"] == "accepted" and d["decider"] and ppl and slug(str(d["decider"]).lstrip("@")) not in ppl:
            F.append(finding("warn", "decision", d["path"], f"decider {d['decider']} is not in `people:` in config.yaml"))
        if d["supersedes"] and str(d["supersedes"]) not in names:
            F.append(finding("error", "decision", d["path"], f"supersedes unknown decision: {d['supersedes']}"))
        if d["governing"] and d["status"] != "accepted":
            F.append(finding("warn", "decision", d["path"], "governing decision is not accepted"))
    # ids and labels
    defs = defaultdict(list)
    for f in repo.md_files(include_archive=False):
        if f.startswith("_steering/"):
            continue
        for n_, ln in enumerate(repo.read(f).split("\n"), 1):
            if "{#" not in ln:
                continue
            m = re.search(r"\{#([tolrm]-[0-9a-f]{4})\b", ln)
            if m and not ln.startswith("    "):
                defs[m.group(1)].append((f, n_))
            if ln.startswith("- ") and "{#" in ln and not ATTR.search(ln):
                F.append(finding("warn", "label-syntax", f, "attribute block is malformed (trailing {#id key=value}, no spaces in values)", n_))
    for i, where in defs.items():
        if len(where) > 1 and not (i.endswith("-0000")):
            F.append(finding("error", "duplicate-id", where[0][0], f"id {i} defined {len(where)} times"))
    lids = defaultdict(list)
    for f in log_files(repo):
        if "/log/" in f:
            for n_, ln in enumerate(repo.read(f).split("\n"), 1):
                m = LOGLINE.match(ln)
                if m and m.group(6):
                    lids[m.group(6)].append((f, n_))
    for i, w in lids.items():
        if len(w) > 1:
            F.append(finding("warn", "duplicate-log-id", w[0][0], f"log id {i} appears {len(w)} times (one line edited on two sides of a merge): keep the one you want, delete the other", w[0][1]))
    stale_h = float((cfg.get("tasks") or {}).get("stale_started_hours", 24))
    mentions = last_log_mentions(repo)
    for n_, ln in task_lines(repo, "tasks.md"):
        it = parse_item(ln)
        if not it:
            continue
        text, iid, at = it
        if not iid.startswith("t-"):
            continue
        st = at.get("st", "OPEN")
        if st not in TASK_ST:
            F.append(finding("error", "task", "tasks.md", f"{iid}: st must be one of {sorted(TASK_ST)}", n_))
        if st == "BLOCKED" and not at.get("reason"):
            F.append(finding("error", "task", "tasks.md", f"{iid}: BLOCKED needs reason=", n_))
        r = at.get("reason", "")
        if r.startswith("o-") and r not in defs:
            F.append(finding("warn", "task", "tasks.md", f"{iid}: reason {r} is not an open item", n_))
        if st == "STARTED" and iid != "t-0000":
            t = mentions.get(iid)
            if t is None or now() - t > timedelta(hours=stale_h):
                F.append(finding("warn", "stale-started", "tasks.md", f"{iid} is STARTED with no log line for {int(stale_h)}h: continue it or mark it INCOMPLETE", n_))
    for n_, ln in task_lines(repo, "_workboard/open-items.md"):
        it = parse_item(ln)
        if it and it[1].startswith("o-") and it[2].get("type") not in ITEM_TYPES:
            F.append(finding("error", "open-item", "_workboard/open-items.md", f"{it[1]}: type must be one of {sorted(ITEM_TYPES)}", n_))
    # logs
    for f in log_files(repo):
        if "/log/" in f:
            if not re.search(r"/log/\d{4}-\d{2}-\d{2}\.md$", f) and not f.endswith("YYYY-MM-DD.md"):
                F.append(finding("warn", "log", f, "log files are named YYYY-MM-DD.md"))
            for n_, ln in enumerate(repo.read(f).split("\n"), 1):
                if ln.startswith("- ") and not LOGLINE.match(ln):
                    F.append(finding("warn", "log", f, "line does not match the log format", n_))
    # playbooks
    for p, s, m in check_playbooks(repo)[1]:
        F.append(finding(s, "playbook", p, m))
    F += module_checks(repo)
    from . import folders, hygiene, secrets, steering
    F += hygiene.findings(repo, md) + folders.folder_findings(repo) + steering.steering_findings(repo) + secrets.tracked_findings(repo)
    # secrets
    F += scan_secrets(repo, [f for f in md if not f.startswith("_steering/")])
    return F


def redaction_patterns(repo):
    p = repo.ws / "redaction.yaml"
    pats = (yamlsub.loads(p.read_text(encoding="utf-8")).get("patterns") or []) if p.exists() else []
    out = []
    for x in pats:
        try:
            out.append((x["name"], re.compile(x["regex"]), x.get("action", "flag")))
        except re.error:
            pass
    return out


def secret_allow(repo):
    from . import secrets
    return secrets.allow_set(repo)


def secret_hits(repo, text):
    """(line, pattern, fingerprint) for every secret still in the text. Placeholders are not secrets; a match is exempt only by
    `ws:allow` on its line or its fingerprint under `allow:` in redaction.yaml (ws secret allow). The same routine moves them."""
    from . import secrets
    return [(f["line"], f["name"], secrets.fingerprint(f["value"])) for f in secrets.find(repo, text, include_unsure=True)]


def scan_secrets(repo, files):
    return [finding("error", "secret-pattern", f, f"{name}: is it a secret? ws secret move {f}:{n_} (yes) or ws secret allow {f}:{n_} (no)", n_)
            for f in files for n_, name, fp in secret_hits(repo, repo.read(f))]


def cmd_check(repo, a):
    if a.fix_generated:
        gen.apply(repo, write=True)
    F, ignored = split_ignored(repo, all_findings(repo))
    order = {"error": 0, "warn": 1, "info": 2}
    F.sort(key=lambda x: (order[x["severity"]], x["path"], x["line"] or 0))
    counts = {s: sum(1 for x in F if x["severity"] == s) for s in order}
    if a.json:
        emit(a, {"counts": counts, "findings": F, "ignored": ignored}, "")
    else:
        for x in F:
            if x["severity"] == "info" and not a.all:
                continue
            loc = f"{x['path']}:{x['line']}" if x["line"] else x["path"]
            print(f"{x['severity']:5} {x['code']:14} {loc}  {x['message']}")
        print(f"\n{counts['error']} error(s), {counts['warn']} warning(s), {counts['info']} note(s)")
        if ignored and a.all:   # an exception must never hide silently: --all names every finding it set aside
            print(f"\n{len(ignored)} set aside by `ignore:` in check.yaml:")
            for x in sorted(ignored, key=lambda x: (x["path"], x["code"])):
                print(f"  {x['code']:14} {x['path']}:{x['line']}  {x['message']}" if x["line"] else f"  {x['code']:14} {x['path']}  {x['message']}")
    return 2 if counts["error"] else (1 if counts["warn"] else 0)


# ---- review ---------------------------------------------------------------------
def metrics(repo, ix):
    md = repo.md_files()
    by = defaultdict(int)
    depth = 0
    sizes = []
    for f in md:
        by[f.split("/")[0] if "/" in f else "."] += 1
        depth = max(depth, f.count("/"))
        sizes.append(repo.abs(f).stat().st_size)
    sizes.sort()
    startup = sum(repo.abs(p).stat().st_size for p in ("AGENTS.md", "status_log.md", "tasks.md", "_workboard/open-items.md") if repo.exists(p))
    inbound = defaultdict(int)
    for e in ix.db.execute("select src, dst from edges"):
        if norm(e["src"]) != norm(e["dst"]):
            inbound[norm(e["dst"])] += 1
    docs = [f for f in md if f.startswith("docs/") and not f.endswith("README.md")]
    raw = [f for f in md if f.startswith("_workboard/meetings/") or f.startswith("_workboard/reports/")]
    churn = {}
    if repo.is_git():
        rc, out, _ = repo.git("log", "--since=90 days ago", "--name-only", "--format=")
        cnt = defaultdict(int)
        for ln in out.splitlines():
            if ln.strip():
                cnt[ln.split("/")[0]] += 1
        churn = dict(sorted(cnt.items(), key=lambda x: -x[1])[:5])
    return {"stamp": stamp(), "md_files": len(md), "sections": ix.db.execute("select count(*) from sections").fetchone()[0], "files_by_top_folder": dict(by),
            "max_depth": depth, "median_file_bytes": sizes[len(sizes) // 2] if sizes else 0, "largest_file_bytes": sizes[-1] if sizes else 0,
            "startup_read_bytes": startup, "startup_read_tokens": startup // 4, "orphans": sum(1 for f in docs if not inbound.get(f)),
            "raw_files": len(raw), "docs_files": len(docs), "churn_90d": churn}


def cmd_review(repo, a):
    ix = Index(repo).ensure()
    m = metrics(repo, ix)
    snap = repo.ws / "snapshots" / "review.json"
    old = json.loads(snap.read_text()) if snap.exists() else None
    ratio = float((repo.config.get("thresholds") or {}).get("growth_warn_ratio", 0.25))
    reasons = []
    if old:
        for k in ("md_files", "sections", "startup_read_bytes"):
            if old.get(k) and (m[k] - old[k]) / old[k] > ratio:
                reasons.append(f"{k} grew {(m[k] - old[k]) / old[k]:.0%} since {old['stamp']}")
        if m["orphans"] - old.get("orphans", 0) >= 5:
            reasons.append(f"{m['orphans'] - old['orphans']} more orphan documents")
    if m["largest_file_bytes"] > int((repo.config.get("budgets") or {}).get("whole_read_kb", 25)) * 1024:
        reasons.append("a document passes the whole-read threshold")
    due = bool(reasons)
    if a.apply:
        atomic_write(snap, json.dumps(m, indent=2))
    emit(a, {"metrics": m, "previous": old and old["stamp"], "review_due": due, "reasons": reasons},
         "\n".join(f"{k}: {v}" for k, v in m.items()) + f"\n\nreview due: {'yes' if due else 'no'}" + ("".join(f"\n  - {r}" for r in reasons)) + ("" if old else "\n(no previous snapshot; run with --apply to record one)"))
    return 1 if due else 0


# ---- dupes ----------------------------------------------------------------------
def cmd_dupes(repo, a):
    ix = Index(repo).ensure()
    paras = []
    for r in ix.db.execute("select s.sid, s.path, f.body from sections s join sfts f on f.rowid = s.id"):
        if r["path"].startswith("_steering/") and not a.steering:
            continue
        for p in re.split(r"\n\s*\n", r["body"]):
            w = re.findall(r"\w+", fold(p))
            if len(w) >= 20 and not p.lstrip().startswith(("|", "```")):
                paras.append((r["sid"], r["path"], p.strip()[:80].replace("\n", " "), w))
    inv = defaultdict(set)
    sh = []
    for i, (_, _, _, w) in enumerate(paras):
        s = {" ".join(w[j:j + 5]) for j in range(len(w) - 4)}
        sh.append(s)
        for x in s:
            inv[x].add(i)
    pairs = defaultdict(int)
    for ids in inv.values():
        if 1 < len(ids) < 8:
            l = sorted(ids)
            for x in range(len(l)):
                for y in range(x + 1, len(l)):
                    pairs[(l[x], l[y])] += 1
    out = []
    for (i, j), c in pairs.items():
        if c < 3 or paras[i][0] == paras[j][0]:
            continue
        jac = len(sh[i] & sh[j]) / len(sh[i] | sh[j])
        if jac >= a.threshold:
            out.append({"a": paras[i][0], "b": paras[j][0], "similarity": round(jac, 2), "text": paras[i][2]})
    out.sort(key=lambda x: -x["similarity"])
    heads = defaultdict(set)
    generic = {"open", "rules", "steps", "findings", "limits", "notes", "tasks", "context", "design", "requirements", "setup", "prompt", "ids", "contract"}
    for r in ix.db.execute("select path, heading, level from sections where level >= 2"):
        if fold(r["heading"]) not in generic:
            heads[fold(r["heading"])].add(r["path"])
    rep = [{"heading": h, "files": sorted(p)} for h, p in heads.items() if len(p) >= 3]
    emit(a, {"paragraphs": out[:30], "repeated_headings": rep[:20]},
         "\n".join(f"{x['similarity']:.2f}  {x['a']}\n      ~ {x['b']}" for x in out[:30]) + ("\n\nrepeated headings:\n" + "\n".join(f"  {r['heading']}: {len(r['files'])} files" for r in rep[:20]) if rep else "") or "no near-duplicates")
    return 1 if out else 0


# ---- insight --------------------------------------------------------------------
def cmd_insight(repo, a):
    ix = Index(repo).ensure()
    F = []
    stale_days = int((repo.config.get("thresholds") or {}).get("open_item_stale_days", 30))
    t0 = now()
    for n_, ln in task_lines(repo, "_workboard/open-items.md"):
        it = parse_item(ln)
        if not it or it[1] == "o-0000":
            continue
        rc, out, _ = repo.git("log", "--format=%cI", "--reverse", f"-S{{#{it[1]}", "--", "_workboard/open-items.md")
        first = out.strip().splitlines()[0] if rc == 0 and out.strip() else ""
        if first:
            from datetime import datetime
            age = (t0 - datetime.fromisoformat(first)).days
            if age > stale_days:
                F.append(("stale open item", f"{it[1]} ({it[2].get('type', '?')}, {age} days): {it[0][:80]}"))
    for d in decisions(repo):
        if d["status"] == "accepted":
            ins = [e for e in ix.edges_of(d["path"])[1] if not norm(e["src"]).endswith("README.md")]
            if not ins:
                F.append(("decision with no follow-up", f"{d['id']}: nothing links to it (no task, document or lesson)"))
    for f in repo.md_files():
        rb = repo.fm(f).get("review_by")
        if rb and str(rb)[:10] < t0.strftime("%Y-%m-%d"):
            F.append(("past review_by", f"{f} (review_by {str(rb)[:10]})"))
    for x in run_checks(repo, ix):
        if x["code"] == "stale-started":
            F.append(("stale STARTED task", x["message"]))
    body = "\n".join(f"- **{k}:** {v}" for k, v in F) or "- nothing found"
    report = f"---\nkind: generated\ndescription: \"Insight report {stamp()}: deterministic findings with sources.\"\n---\n# Insight {stamp()}\n\n{body}\n"
    atomic_write(repo.ws / "reports" / f"insight-{stamp()}.md", report)
    emit(a, [{"finding": k, "detail": v} for k, v in F], "\n".join(f"{k}: {v}" for k, v in F) or "nothing found")
    return 1 if F else 0


# ---- module checks --------------------------------------------------------------
REQ_H = re.compile(r"^###\s+([A-Z][A-Z0-9]*)-(\d+)\b")
AXIOM = re.compile(r"^\s*(A\d+)\s+(invariant|principle)\b(.*)$")


def component_docs(repo):
    return [f for f in (repo.walk((".md",), under="docs/architecture") if repo.exists("docs/architecture") else []) if not f.endswith("README.md")]


TERM = re.compile(r"^\s*([a-z_]\w*)(?:\([^)]*\))?\s*:=\s*(.+?)\s*$")
CHECK_REF = re.compile(r"→\s*([A-Za-z_]\w*)")
OBSERVABLE = re.compile(r"[<>=!]=?|\(|\w\.\w|\b(?:and|or|not|for all|exists)\b|\d")


def criteria_blocks(body, off):
    """[(requirement key, criterion number, line, text)] for the numbered criteria under each requirement heading. A criterion runs over
    the indented or bulleted lines that follow it, up to a blank line, the next number or a heading."""
    out, in_req, key, cur = [], False, None, None
    for n, ln in enumerate(body.split("\n"), 1 + off):
        if ln.startswith("## "):
            in_req, key, cur = ln.strip() == "## Requirements", None, None
            continue
        m = REQ_H.match(ln)
        if m:
            key, cur = f"{m.group(1)}-{m.group(2)}", None
            continue
        if ln.startswith("###"):
            key, cur = None, None
            continue
        c = re.match(r"^\s*(\d+)\.\s", ln)
        if c and in_req and key:
            cur = [key, int(c.group(1)), n, ln]
            out.append(cur)
        elif cur and ln.strip() and (ln[:1] in " \t" or ln.lstrip()[:1] in "-*"):
            cur[3] += "\n" + ln
        else:
            cur = None
    return [tuple(x) for x in out]


def term_findings(repo, terms, texts):
    """terms: {name: (file, line, rhs)}; texts: every component document, to see where a term is used."""
    F = []
    for name, (f, n, rhs) in terms.items():
        if not OBSERVABLE.search(rhs) and not all(t in terms for t in re.findall(r"[a-z_]\w*", rhs)):
            F.append(finding("warn", "software", f, f"term {name} := {rhs} is not observable: define it by a field, count or duration a test can check (or by other defined terms), not a judgment", n))
        used = any(re.search(rf"\b{re.escape(name)}\b", ln) for t, tn in texts for k, ln in enumerate(t.split("\n"), 1) if not (TERM.match(ln) and TERM.match(ln).group(1) == name))
        if not used:
            F.append(finding("warn", "software", f, f"term {name} is defined and no requirement, axiom or design uses it", n))
    return F


def software_checks(repo):
    F = []
    ids_all, unapproved, terms, texts, named = {}, {}, {}, [], []
    for f in component_docs(repo):
        text = repo.read(f)
        fm, body, off = read_fm(text)
        texts.append((body, off))
        binding = fm.get("status") == "approved" and bool(fm.get("approved_by"))
        reqs, axioms, criteria, cur = {}, {}, defaultdict(set), None
        in_req = False
        for n, ln in enumerate(body.split("\n"), 1 + off):
            if ln.startswith("## "):
                in_req = ln.strip() == "## Requirements"
            m = REQ_H.match(ln)
            if m:
                key = f"{m.group(1)}-{m.group(2)}"
                if key in reqs:
                    F.append(finding("error", "software", f, f"requirement id {key} appears twice", n))
                reqs[key] = n
                cur = int(m.group(2))
                ids_all[key] = f
                continue
            if ln.startswith("###") or (ln.startswith("## ") and ln.strip() != "## Requirements"):
                cur = None
            c = re.match(r"^\s*(\d+)\.\s", ln)
            if c and cur is not None and in_req:
                criteria[cur].add(int(c.group(1)))
            t = TERM.match(ln) if in_req and not reqs else None
            if t:
                if t.group(1) in terms:
                    F.append(finding("error", "software", f, f"term {t.group(1)} is defined twice (also {terms[t.group(1)][0]}:{terms[t.group(1)][1]}): define it once, in the owning component, and cite it elsewhere", n))
                else:
                    terms[t.group(1)] = (f, n, t.group(2))
            a = AXIOM.match(ln)
            if a:
                if a.group(1) in axioms:
                    F.append(finding("error", "software", f, f"axiom {a.group(1)} appears twice", n))
                axioms[a.group(1)] = n
                if a.group(2) == "invariant" and not re.search(r"→\s*\w+", a.group(3)):
                    F.append(finding("error", "software", f, f"invariant {a.group(1)} names no check (→ name)", n))
                named += [(f, n, x, a.group(1)) for x in CHECK_REF.findall(a.group(3))]
        nums = {int(k.split("-")[1]) for k in reqs}
        for key, num, n, block in criteria_blocks(body, off):
            refs = CHECK_REF.findall(block)
            if not refs:
                F.append(finding("error" if binding else "warn", "software", f, f"criterion {key}.{num} names no check (→ name on its line): say how it is verified", n))
            named += [(f, n, x, f"{key}.{num}") for x in refs]
        design = body.split("## Design", 1)[1].split("\n## ", 1)[0] if "## Design" in body else ""
        for br in re.findall(r"\[([^\]\n]+)\]", design):
            for tok in [x.strip() for x in br.split(",")]:
                if re.fullmatch(r"\d+(\.\d+)?", tok):
                    n_, _, c_ = tok.partition(".")
                    if int(n_) not in nums or (c_ and int(c_) not in criteria.get(int(n_), set())):
                        F.append(finding("error", "software", f, f"trace reference [{tok}] matches no requirement criterion"))
                elif re.fullmatch(r"A\d+", tok) and tok not in axioms:
                    F.append(finding("error", "software", f, f"trace reference [{tok}] matches no axiom"))
        if fm.get("status") != "approved" or not fm.get("approved_by"):
            for k in reqs:
                unapproved[k] = f
    if unapproved and repo.exists("tasks.md"):
        for n, ln in enumerate(repo.read("tasks.md").split("\n"), 1):
            for k, f in unapproved.items():
                if re.search(rf"\b{re.escape(k)}\b", ln):
                    F.append(finding("error", "software", "tasks.md", f"task cites {k} but {f} is not approved (status: approved and approved_by)", n))
    if repo.exists("_workboard/stages"):
        for f in repo.walk((".md",), under="_workboard/stages"):
            for n, ln in enumerate(repo.read(f).split("\n"), 1):
                for m in re.finditer(r"validates\s+([A-Z][A-Z0-9]*-\d+(?:\.\d+)?)", ln):
                    if m.group(1).split(".")[0] not in ids_all:
                        F.append(finding("error", "software", f, f"validates {m.group(1)}, which no component defines", n))
    F += term_findings(repo, terms, texts)
    code = repo.code_files()
    if code and named:     # with no code yet there is nothing to resolve a name against
        corpus = "\n".join(repo.read(c) for c in code if (repo.abs(c).stat().st_size < 1_000_000))
        for f, n, name, owner in dict.fromkeys(named):
            if not re.search(rf"\b{re.escape(name)}\b", corpus):
                F.append(finding("warn", "software", f, f"{owner} names the check {name}, which no file in {repo.code_root()} mentions: write the test or correct the name", n))
    return F


def module_checks(repo):
    F, en = [], set(repo.enabled)
    if "software" in en:
        F += software_checks(repo)
    if "lessons" in en and repo.exists("docs/lessons"):
        for f in repo.walk((".md",), under="docs/lessons"):
            if f.endswith("README.md"):
                continue
            for n, ln in enumerate(repo.read(f).split("\n"), 1):
                if ln.startswith("- ") and "{#" in ln and "trigger=" not in ln:
                    F.append(finding("warn", "lesson", f, "lesson has no trigger=", n))
    if "evals" in en and repo.exists("docs/evals"):
        for f in repo.walk((".md",), under="docs/evals"):
            if not f.endswith("README.md") and not all(h in repo.read(f) for h in ("## Prompt", "## Pass criteria")):
                F.append(finding("warn", "eval", f, "case needs ## Prompt and ## Pass criteria"))
    if "code" in en and repo.code_files():
        from .codemap import purpose
        for f in repo.code_files():
            if not purpose(repo.read(f), Path(f).suffix):
                F.append(finding("info", "code-purpose", f, "no purpose line (module docstring or leading comment)"))
    return F
