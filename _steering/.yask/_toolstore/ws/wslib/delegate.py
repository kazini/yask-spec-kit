"""Sub-agent practices: delegate (worker contract + baseline) and report check (the parent's deterministic monitor)."""
import hashlib
import json
import re
from pathlib import Path

from .repo import WsError, read_fm, slug
from .sessions import porcelain_paths
from .util import atomic_write, emit, file_stamp, hex4

SECTIONS = ("## Findings", "## Not found", "## Limits")
EVID = re.compile(r"`?([\w./-]+\.[A-Za-z0-9]+):(\d+)`?")


def state(repo):
    out = {}
    for p in porcelain_paths(repo):
        f = repo.abs(p)
        out[p] = hashlib.sha1(f.read_bytes()).hexdigest() if f.is_file() else "dir"
    return out


def cmd_delegate(repo, a):
    for p in a.inputs or []:
        if not repo.exists(p.split("#")[0].rstrip("/")):
            raise WsError(f"input not found: {p}", 2)
    name = f"_workboard/reports/{file_stamp()}-{hex4()}-{slug(' '.join(a.task))[:40]}.md"
    base = repo.ws / "cache" / ("delegate-" + hashlib.sha1(name.encode()).hexdigest()[:8] + ".json")
    if repo.is_git():
        atomic_write(base, json.dumps({"report": name, "dirty": state(repo)}))
    print(f"""Worker contract
Task: {' '.join(a.task)}
Inputs: {', '.join(a.inputs) if a.inputs else '(none given: ask the parent)'}
Output: write only {name}, from _steering/.yask/templates/report.md.
Findings: each with evidence as `path:line` and a quote of at most 12 words from that line in double quotes; confidence low, medium or high. Add a Not found section naming what you searched, and a Limits section.
Limits: at most {a.cap} bytes; at most {a.steps} tool calls; read-only everywhere else; never read raw transcripts whole.
Progress: ws log add --agent --task <id> "<what you did>" at milestones, so the parent can read it instead of polling.
Parent check afterwards: ws report check {name} --cap {a.cap}""")
    return 0


def cmd_report(repo, a):
    f = a.file
    if not repo.exists(f):
        raise WsError(f"not found: {f}", 2)
    text = repo.read(f)
    fm, body, _ = read_fm(text)
    problems = []
    for k in ("task", "author"):
        if not fm.get(k):
            problems.append(f"front matter missing {k}")
    for s in SECTIONS:
        if s not in body:
            problems.append(f"missing section {s}")
    if a.cap and len(text.encode()) > a.cap:
        problems.append(f"{len(text.encode())} bytes over the cap of {a.cap}")
    checked = 0
    for ln in body.split("\n"):
        for m in EVID.finditer(ln):
            path, num = m.group(1), int(m.group(2))
            if "/" not in path and not repo.exists(path):
                continue
            if not repo.exists(path):
                problems.append(f"evidence file not found: {path}")
                continue
            lines = repo.read(path).split("\n")
            if num > len(lines):
                problems.append(f"evidence line beyond the end: {path}:{num}")
                continue
            q = re.search(r'"([^"]{6,120})"', ln)
            if q:
                checked += 1
                if re.sub(r"\s+", " ", q.group(1).strip().lower()) not in re.sub(r"\s+", " ", lines[num - 1].lower()):
                    problems.append(f"quote not on the cited line: {path}:{num}")
    if repo.is_git():
        cands = list((repo.ws / "cache").glob("delegate-*.json"))
        for c in cands:
            d = json.loads(c.read_text())
            if d["report"] == f:
                now_ = state(repo)
                changed = [p for p, h in now_.items() if d["dirty"].get(p) != h and p != f]
                for p in changed:
                    problems.append(f"changed outside the report: {p}")
                break
    emit(a, {"file": f, "quotes_checked": checked, "problems": problems}, "\n".join(problems) or f"report ok ({checked} quote(s) verified)")
    return 2 if problems else 0
