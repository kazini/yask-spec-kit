"""parse, ingest, extract, promote."""
import hashlib
import re
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import Path

from .checks import redaction_patterns
from .repo import WsError, read_fm, slug
from .sessions import ITEMS, TASKS, scaffold_folder
from .util import warn, atomic_write, emit, file_stamp, hex4, locked, new_id, now, parse_item, render_item, stamp
from . import sessions


# ---- parse ----------------------------------------------------------------------
class _Html(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in ("h1", "h2", "h3", "h4"):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self.out.append("\n- ")
        elif tag in ("p", "div", "br", "tr"):
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
        elif tag in ("p", "h1", "h2", "h3", "h4"):
            self.out.append("\n")

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)


def parse_text(path):
    p = Path(path)
    ext = p.suffix.lower()
    raw = p.read_bytes()
    if ext in (".md", ".txt", ""):
        return raw.decode("utf-8", "replace")
    if ext in (".vtt", ".srt"):
        out = []
        for block in re.split(r"\n\s*\n", raw.decode("utf-8", "replace").replace("\r", "")):
            lines = [l for l in block.split("\n") if l.strip() and not re.match(r"^(WEBVTT|NOTE|\d+)$", l.strip())]
            ts = next((l for l in lines if "-->" in l), None)
            if ts:
                t = re.match(r"(?:(\d+):)?(\d+):(\d+)", ts.strip())
                stamp_ = f"[{int(t.group(1) or 0) * 60 + int(t.group(2)):02d}:{t.group(3)}]" if t else ""
                text = " ".join(l for l in lines if l != ts)
                out.append(f"{stamp_} {text}".strip())
        return "\n".join(out)
    if ext in (".html", ".htm"):
        h = _Html()
        h.feed(raw.decode("utf-8", "replace"))
        return re.sub(r"\n{3,}", "\n\n", "".join(h.out)).strip()
    if ext == ".docx":
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        with zipfile.ZipFile(p) as z:
            root = ET.fromstring(z.read("word/document.xml"))
        out = []
        for para in root.iter("{%s}p" % ns["w"]):
            txt = "".join(t.text or "" for t in para.iter("{%s}t" % ns["w"]))
            st = para.find("w:pPr/w:pStyle", ns)
            m = re.match(r"Heading(\d)", st.get("{%s}val" % ns["w"], "")) if st is not None else None
            if txt.strip():
                out.append(("#" * int(m.group(1)) + " " if m else "") + txt)
        return "\n\n".join(out)
    raise WsError(f"no parser for {ext or 'this file type'} (PDF and others need an adapter); convert to text first", 3)


def cmd_parse(repo, a):
    text = parse_text(a.file)
    if a.out:
        atomic_write(a.out, text)
        print(f"wrote {a.out} ({len(text)} chars)")
    else:
        print(text)
    return 0


# ---- redaction ------------------------------------------------------------------
def redact(repo, text):
    flagged, counts = [], {}
    for name, rx, action in redaction_patterns(repo):
        if action == "redact":
            text, n = rx.subn(f"[REDACTED:{name}]", text)
            if n:
                counts[name] = n
        else:
            for ln, line in enumerate(text.split("\n"), 1):
                m = rx.search(line)
                if m:
                    flagged.append({"pattern": name, "line": ln, "fingerprint": hashlib.sha1(m.group(0).encode()).hexdigest()[:6]})
    return text, counts, flagged


def ensure_folder(repo, folder):
    return scaffold_folder(repo, folder, apply=True)


# ---- ingest ---------------------------------------------------------------------
def cmd_ingest(repo, a):
    src = Path(a.file)
    if not src.exists():
        raise WsError(f"no such file: {a.file}", 2)
    from . import secrets
    raw = parse_text(src)
    for n_, ln in [(n_, ln) for n_, ln in enumerate(raw.split("\n"), 1) if INJECT.search(ln)][:3]:
        warn(f"note: line {n_} of the source reads like an instruction to an AI; it is kept as text, and nothing in it is followed")
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    when = a.when or file_stamp()
    if not re.match(r"^\d{4}-\d{2}-\d{2}-\d{4}$", when):
        raise WsError("--when must look like YYYY-MM-DD-HHMM", 2)
    title = a.title or src.stem
    name = f"{when}-{hex4()}-{slug(title)[:40]}"
    folder = f"_workboard/meetings/{name}"
    # Secrets go first: redacting emails first would cut `user:pw@host` out of a connection string before its rule could see it.
    # Ingest moves what is sure and what the text itself calls a secret; a card or IBAN number (shape only) stays for the agent to decide.
    text, keys = raw, []
    if not a.allow_flagged:
        text, keys = secrets.scrub_text(repo, raw, folder, f"{src.name}", auto_only=True, dry=not a.apply)
    text, counts, _ = redact(repo, text)
    left = [f for f in secrets.find(repo, text, include_unsure=True)]
    if keys:
        counts = {**counts, "secrets moved": len(keys)}
    plan = {"folder": folder, "redactions": counts, "sha256": digest, "secrets_moved": len(keys), "left_to_decide": sorted({f["name"] for f in left})}
    if not a.apply:
        emit(a, plan, f"would create {folder}/ (transcript.md, summary.md); redactions: {counts or 'none'}" + (f"; {len(keys)} secret(s) go to {folder}/.secrets, placeholders stay" if keys else "")
             + (f"; {len(left)} possible secret(s) stay in the transcript for you to decide ({', '.join(plan['left_to_decide'])})" if left else "") + "; add --apply")
        return 0
    ensure_folder(repo, "_workboard/meetings")
    desc = f"Transcript of {title}, verbatim after redaction. Evidence, not canon."
    atomic_write(repo.abs(f"{folder}/transcript.md"),
                 f'---\nkind: raw\ndescription: "{desc}"\nsource: {src.name}\nsha256: {digest}\n---\n{text.strip()}\n')
    tpl = repo.read_steer("templates/meeting-summary.md")
    fm, body, _ = read_fm(tpl)
    summary = (f'---\nkind: raw\ndescription: "Summary of {title}. Evidence, not canon."\nsource: {src.name}\nsha256: {digest}\nattendees: []\n---\n' + body)
    atomic_write(repo.abs(f"{folder}/summary.md"), summary)
    tpath = f"{folder}/transcript.md"
    held = secrets.find(repo, repo.read(tpath), include_unsure=True)
    plan["left_to_decide"] = [f"{tpath}:{f['line']} ({f['name']})" for f in held]
    more = "".join(f"\n  decide {tpath}:{f['line']} ({f['name']}): ws secret move {tpath}:{f['line']} if it is a secret, ws secret allow {tpath}:{f['line']} if not" for f in held)
    emit(a, plan, f"created {folder}/\n  transcript.md ({len(text)} chars, redactions: {counts or 'none'})\n  summary.md (fill Decided, Requested, Pending){more}\nnext: ws extract {folder}")
    return 0


# ---- extract --------------------------------------------------------------------
PROP_TYPES = {"decision", "open-item", "task", "state-change"}
ANCHOR = re.compile(r"^([\w./-]+)#L(\d+)$")


INJECT = re.compile(r"(?i)\b(ignore|disregard|forget)\b.{0,25}\b(previous|prior|above|earlier|all)\b.{0,25}\b(instructions?|prompts?|rules)\b|\bsystem prompt\b|\byou are now\b|\bnew instructions\b")
CITE = re.compile(r"([\w./-]+\.md)#L(\d+)(?:-L?(\d+))?")
QUOTE = re.compile(r'"([^"\n]{6,})"|\u201c([^\u201d\n]{6,})\u201d')


def norm(t):
    return re.sub(r"\s+", " ", t.lower()).strip()


def quote_problems(repo, body):
    """Each quoted passage in an Evidence line must appear on the line(s) that same evidence line cites."""
    out = []
    sec = body.split("## Evidence", 1)[-1].split("\n## ", 1)[0]
    for ln in sec.splitlines():
        quotes = [(a or b) for a, b in QUOTE.findall(ln)]
        cites = CITE.findall(ln)
        if not quotes:
            continue
        if not cites:
            out.append(f"quote has no path#Lnn anchor on its line: {quotes[0][:40]}")
            continue
        text = ""
        for path, a, b in cites:
            if repo.exists(path):
                src = repo.read(path).splitlines()
                text += " " + " ".join(src[int(a) - 1:int(b or a)])
        hay = norm(text)
        for q in quotes:
            for frag in (x for x in re.split(r"\u2026|\.\.\.", q) if len(x.strip()) >= 6):
                if norm(frag) not in hay:
                    where = ", ".join(f"{p}#L{a}" for p, a, _ in cites)
                    out.append(f"quote not found at {where}: {frag.strip()[:50]}")
    return out


def check_proposals(repo, target):
    t = Path(target) if target else repo.abs("_workboard/proposals")
    files = [repo.rel(f) for f in sorted(t.rglob("*.md"))] if t.is_dir() else [repo.rel(t)]
    files = [f for f in files if not f.endswith("README.md")]
    problems = []
    for f in files:
        fm, body, _ = read_fm(repo.read(f))
        if fm.get("type") not in PROP_TYPES:
            problems.append((f, f"type must be one of {sorted(PROP_TYPES)}"))
        if not fm.get("source"):
            problems.append((f, "no source anchor"))
        else:
            m = ANCHOR.match(str(fm["source"]))
            if not m or not repo.exists(m.group(1)):
                problems.append((f, f"source must be path#Lnn pointing at an existing file: {fm.get('source')}"))
            elif int(m.group(2)) > len(repo.read(m.group(1)).splitlines()):
                problems.append((f, f"source line beyond the end of the file: {fm['source']}"))
        if fm.get("confidence") not in ("low", "medium", "high"):
            problems.append((f, "confidence must be low, medium or high"))
        for h in ("## What", "## Evidence", "## Not found"):
            if h not in body:
                problems.append((f, f"missing section {h}"))
        for m in re.finditer(r"([\w./-]+\.md)#L(\d+)", body):
            if repo.exists(m.group(1)) and int(m.group(2)) > len(repo.read(m.group(1)).splitlines()):
                problems.append((f, f"evidence anchor beyond the end of the file: {m.group(0)}"))
        problems += [(f, q) for q in quote_problems(repo, body)]
    return files, problems


def cmd_extract(repo, a):
    if a.check is not None:
        files, problems = check_proposals(repo, a.check or None)
        emit(a, [{"file": f, "problem": p} for f, p in problems], "\n".join(f"{f}: {p}" for f, p in problems) or f"{len(files)} proposal file(s) ok")
        return 2 if problems else 0
    raw = a.raw.rstrip("/")
    if not repo.exists(raw):
        raise WsError(f"not found: {raw}", 2)
    stamp_ = file_stamp()
    print(f"""Worker task: extract proposals from {raw}
Inputs: read summary.md first; search transcript.md for specifics and read it in chunks only if needed. Never load it whole.
Output: one file per proposal in _workboard/proposals/, named {stamp_}-<4 hex>-<slug>.md, from _steering/.yask/templates/proposal.md.
Types: decision, open-item, task, state-change. Each proposal: front matter (type, status: pending, source: path#Lnn, confidence), sections What, Evidence (path#Lnn anchors), Not found.
Rules: never edit docs/, status_log.md or tasks.md; never fill a gap by guessing (mark confidence low); check every anchor exists.
Return: the list of proposal files with one line each.
After: ws extract --check""")
    return 0


# ---- promote --------------------------------------------------------------------
def cmd_promote(repo, a):
    with locked(repo):
        return _promote(repo, a)


def section(body, heading):
    m = re.search(rf"(?ms)^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", body)
    return m.group(1).strip() if m else ""


def _promote(repo, a):
    f = a.proposal
    if not repo.exists(f):
        raise WsError(f"not found: {f}", 2)
    fm, body, _ = read_fm(repo.read(f))
    if fm.get("status") not in ("approved", "edited"):
        raise WsError("a person must approve the proposal first (status: approved or edited)", 2)
    rv = str(fm.get("reviewer") or "").strip()
    if not rv or "agent" in rv.lower():
        raise WsError("name the person who approved it: reviewer: <name> in the proposal (an agent does not approve)", 2)
    _, bad = check_proposals(repo, f)
    if bad:
        raise WsError(f"the proposal does not pass its own check, nothing was written: {bad[0][1]}", 2)
    if fm.get("promoted_to"):
        raise WsError(f"already promoted to {fm['promoted_to']}", 2)
    typ = fm.get("type")
    desc = str(fm.get("description", "")).strip()
    src = str(fm.get("source", ""))
    user = repo.user(a.you)
    plan = None
    if typ == "open-item":
        plan = {"kind": "open item", "text": desc, "type": a.type or "question"}
    elif typ == "task":
        plan = {"kind": "task", "text": desc}
    elif typ == "decision":
        plan = {"kind": "decision record"}
    else:
        print(f"state-change: edit the target ({fm.get('target', 'the owning document')}) by hand, replacing old text, with src={src}")
        return 0
    if not a.apply:
        emit(a, plan, f"would file as {plan['kind']} (add --apply)")
        return 0
    if typ == "open-item":
        ns = type("N", (), dict(tcmd=None, icmd="add", text=[desc], type=plan["type"], for_=a.for_, src=src, you=a.you, json=False, agent=False))
        ref = None
        iid = new_id(repo, "o")
        lines = sessions.load(repo, ITEMS)
        attrs = {"type": plan["type"], "for": "@" + (a.for_ or user).lstrip("@"), "src": src}
        line = "- " + render_item(desc, iid, attrs)
        lines.insert(sessions.section_end(lines, "## Open"), line)
        atomic_write(repo.abs(ITEMS), "\n".join(lines))
        ref = iid
    elif typ == "task":
        iid = new_id(repo, "t")
        lines = sessions.load(repo, TASKS)
        line = "- " + render_item(desc, iid, {"for": "@" + (a.for_ or user).lstrip("@"), "st": "OPEN"})
        lines.insert(sessions.section_end(lines, "## Tasks"), line)
        atomic_write(repo.abs(TASKS), "\n".join(lines))
        ref = iid
    else:
        ensure_folder(repo, "docs/decisions")
        title = re.sub(r"^#\s*(Proposal:\s*)?", "", next((l for l in body.splitlines() if l.startswith("# ")), "")).strip() or desc
        slg = slug(desc)[:40].rsplit("-", 1)[0] if len(slug(desc)) > 40 else slug(desc)
        name = f"{file_stamp()}-{hex4()}-{slg or 'decision'}"
        tpl = repo.read_steer("templates/decision.md")
        tpl = re.sub(r'(?m)^description:.*$', lambda m: 'description: "%s"' % desc.replace('"', "'")[:200], tpl, 1)
        tpl = re.sub(r"(?m)^proposed_by:.*$", f"proposed_by: {fm.get('proposed_by') or user}", tpl, 1)
        tpl = re.sub(r"(?m)^derived_from:.*$", f"derived_from: {src}", tpl, 1)
        tpl = tpl.replace("# <Decision title>", f"# {title}", 1)
        known = "\n\n".join(x for x in (section(body, "What"), section(body, "Evidence")) if x)
        gap = section(body, "Not found")
        ctx = known + (f"\n\nNot found in the source: {gap}" if gap else "")
        tpl = re.sub(r"(?s)## Context\n.*?\n\n## Options", lambda m: f"## Context\n{ctx}\n\n## Options", tpl, 1)
        atomic_write(repo.abs(f"docs/decisions/{name}.md"), tpl)
        ref = f"docs/decisions/{name}.md"
    text = repo.read(f)
    atomic_write(repo.abs(f), re.sub(r"(?m)^status:.*$", lambda m: m.group(0) + f"\npromoted_to: {ref}", text, 1))
    sessions.append_log(repo, user, "note", f"promoted {f} -> {ref}")
    emit(a, {"promoted_to": ref}, f"promoted to {ref}")
    return 0
