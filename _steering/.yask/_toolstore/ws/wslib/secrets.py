"""Secrets stay out of the workspace's files and out of the model's context, and agents can still work with them.

A secret the tool is sure about (a provider key, a token, a private key) is replaced in the file by `{{secret:KEY}}` and its value is
stored in a `.secrets` file in the same folder (git-ignored, never snapshotted or pushed). One the tool is unsure about (`password = ...`)
is left for the agent to decide: `ws secret move` (it is one) or `ws secret allow` (it is not). To use a value, `ws secret run -- <command>`
puts the secrets in the command's environment and hides them from its output; `ws secret get KEY` prints one (a person only, by default:
`secrets.agent_read`). An agent can make its own:
`--generate` (random, never shown) for a permanent one, `--temp` for one it supplies, which expires."""
import json
import os
import re
import secrets as rnd
import subprocess
import sys
import hashlib
from datetime import timedelta
from pathlib import Path

from . import yamlsub
from .repo import WsError
from .util import atomic_write, emit, now, parse_stamp, stamp

PLACEHOLDER = re.compile(r"\{\{secret:([A-Z][A-Z0-9_]*)\}\}")
ASSIGN = re.compile(r"(?i)^(?P<label>[A-Za-z][\w-]*)\s*[:=]\s*(?P<val>\S+)$")
FILE = ".secrets"
HEAD = "# Secrets for the files in this folder. Git ignores this file; do not copy values out of it.\n# Use one with: ws secret run -- <command>   (or ws secret get KEY)\n"


_PATTERN_CACHE, _ALLOW_CACHE = {}, {}


def _config_sig(p):
    st = p.stat() if p.exists() else None
    return (str(p), st.st_mtime_ns, st.st_size) if st else (str(p), None, None)


def redaction(repo):
    p = repo.ws / "redaction.yaml"
    sig = _config_sig(p)
    if sig not in _PATTERN_CACHE:
        try:
            cfg = yamlsub.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        except Exception:
            cfg = {}
        out = []
        for x in cfg.get("patterns") or []:
            if x.get("action", "flag") != "flag":
                continue
            try:
                out.append((x["name"], re.compile(x["regex"]), x.get("sure", x["name"] != "assigned-secret") is not False, x.get("shape_only") is True))
            except (re.error, TypeError, AttributeError):
                pass
        _PATTERN_CACHE[sig] = out
        _ALLOW_CACHE[sig] = {str(x) for x in cfg.get("allow") or []}
    return _PATTERN_CACHE[sig], _ALLOW_CACHE[sig]


def patterns(repo):
    """(name, regex, sure, shape_only): the flag patterns of redaction.yaml, compiled once per file version."""
    return redaction(repo)[0]


def allow_set(repo):
    return redaction(repo)[1]


def fingerprint(s):
    return hashlib.sha1(s.encode()).hexdigest()[:6]


def find(repo, text, include_unsure=False, only_line=None):
    """Secrets in text: [{line, start, end, name, key, value, sure, auto}], non-overlapping, certain ones first.
    `auto` is whether ingest may move it: every sure one, and an unsure one the text itself calls a secret ("password is ...");
    never one matched by its shape alone (a card or IBAN number: shape_only in redaction.yaml)."""
    allow = allow_set(repo)
    out = []
    for n, ln in enumerate(text.split("\n"), 1):
        if "ws:allow" in ln or (only_line and n != only_line):
            continue
        cand = []
        holes = [(h.start(), h.end()) for h in PLACEHOLDER.finditer(ln)]
        for name, rx, sure, shape in patterns(repo):
            for m in rx.finditer(ln):
                if any(m.start() < he and m.end() > hs for hs, he in holes):
                    continue
                s, e, label = m.start(), m.end(), name
                groups = rx.groupindex
                a = ASSIGN.match(m.group(0)) if name == "assigned-secret" and "val" not in groups else None
                if "val" in groups and m.group("val") is not None:      # the pattern names the value (and the label) itself
                    s, e = m.span("val")
                    label = m.group("label") if "label" in groups and m.group("label") else name
                elif a:
                    s, e, label = m.start() + a.start("val"), m.start() + a.end("val"), a.group("label")
                if "val" in groups or a:
                    while e > s and ln[e - 1] in "\",;:.?)'`":           # a quote or the punctuation that ends the sentence is not the value
                        e -= 1
                    s += 1 if ln[s:s + 1] in "\"'`" else 0
                if e > s and "{{secret:" not in ln[s:e] and fingerprint(ln[s:e]) not in allow:
                    cand.append((not sure, s, e, label, not shape))
        taken = []
        for unsure, s, e, label, auto in sorted(cand):
            if any(s < te and e > ts for ts, te in taken):
                continue
            taken.append((s, e))
            v = ln[s:e]
            out.append({"line": n, "start": s, "end": e, "name": label, "value": v, "sure": not unsure, "auto": auto, "key": key_for(label, v)})
    return out


def key_for(label, value):
    return re.sub(r"[^A-Z0-9]+", "_", label.upper()).strip("_") + "_" + hashlib.sha1(value.encode()).hexdigest()[:4].upper()


# ---- the .secrets files -----------------------------------------------------------------------------
def parse(path):
    vals, meta = {}, {}
    if Path(path).exists():
        for ln in Path(path).read_text(encoding="utf-8").split("\n"):
            m = re.match(r"^# ([A-Z][A-Z0-9_]*): (.*)$", ln)
            if m:
                meta[m.group(1)] = m.group(2)
            elif "=" in ln and not ln.startswith("#"):
                k, _, v = ln.partition("=")
                vals[k.strip()] = v
    return vals, meta


def registry(repo):
    return repo.ws / "cache" / "secret-files.json"


def store(repo, folder, key, value, note, until=None):
    p = repo.abs(f"{folder}/{FILE}" if folder else FILE)
    vals, meta = parse(p)
    if vals.get(key) == value:
        return p
    lines = p.read_text(encoding="utf-8").split("\n") if p.exists() else HEAD.split("\n")
    lines = [l for l in lines if not (l.startswith(f"{key}=") or l.startswith(f"# {key}: "))]
    while lines and not lines[-1].strip():
        lines.pop()
    lines += [f"# {key}: " + (f"temp until {stamp(until)}" if until else note), f"{key}={value}", ""]
    p.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(p, "\n".join(lines))
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    try:
        known = json.loads(registry(repo).read_text(encoding="utf-8")) if registry(repo).exists() else []
        rel = p.relative_to(repo.root).as_posix()
        if rel not in known:
            registry(repo).parent.mkdir(parents=True, exist_ok=True)
            registry(repo).write_text(json.dumps(known + [rel]), encoding="utf-8")
    except (OSError, ValueError):
        pass
    return p


def chain(repo, start):
    """KEY -> (value, file, note): the .secrets files from a folder up to the workspace root, nearest first."""
    d = repo.abs(start) if start else repo.root
    d = d if d.is_dir() else d.parent
    out, seen = {}, set()
    for cur in [d, *d.parents]:
        if repo.root not in [cur, *cur.parents]:
            break
        f = cur / FILE
        if f.exists():
            vals, meta = parse(f)
            for k, v in vals.items():
                if k not in out:
                    out[k] = (v, f.relative_to(repo.root).as_posix(), meta.get(k, ""))
        if cur == repo.root:
            break
    return out


def purge_temp(repo):
    """Drop expired temporary secrets. Returns how many."""
    try:
        files = json.loads(registry(repo).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    gone = 0
    for rel in files:
        p = repo.abs(rel)
        vals, meta = parse(p)
        dead = [k for k, m in meta.items() if m.startswith("temp until ") and k in vals and parse_stamp(m[11:].strip()) <= now()]
        if dead:
            lines = [l for l in p.read_text(encoding="utf-8").split("\n") if not any(l.startswith(f"{k}=") or l.startswith(f"# {k}: ") for k in dead)]
            atomic_write(p, "\n".join(lines))
            gone += len(dead)
    return gone


# ---- moving secrets out of files -----------------------------------------------------------------------------
def skip(repo, rel):
    return (rel.endswith(FILE) or rel.startswith(("_steering/.yask/", ".git/", ".dev_yask/")) or not repo.policy(rel)["checked"])


def scrub_text(repo, text, folder, note_path, include_unsure=False, only_line=None, auto_only=False, dry=False):
    """Replace secrets in a text with placeholders and store their values in `folder`/.secrets. Returns (new text, [keys]).
    auto_only (ingest): sure ones, and unsure ones that are not shape_only. dry: change nothing on disk."""
    found = [f for f in find(repo, text, include_unsure or auto_only, only_line) if f["sure"] or (f["auto"] if auto_only else include_unsure)]
    if not found:
        return text, []
    lines = text.split("\n")
    for f in sorted(found, key=lambda f: (f["line"], -f["start"])):
        ln = lines[f["line"] - 1]
        lines[f["line"] - 1] = ln[:f["start"]] + "{{secret:" + f["key"] + "}}" + ln[f["end"]:]
        if not dry:
            store(repo, folder, f["key"], f["value"], f"{f['name'].lower()}, moved from {note_path}:{f['line']}")
    return "\n".join(lines), [f["key"] for f in found]


def scrub_file(repo, rel, include_unsure=False, only_line=None):
    """Move the secrets of one file into the .secrets beside it. Returns the keys moved (the file is rewritten only if there are any)."""
    p = repo.abs(rel)
    if skip(repo, rel) or not p.is_file() or p.stat().st_size > 2_000_000:
        return []
    try:
        text = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    parent = Path(rel).parent.as_posix()
    new, keys = scrub_text(repo, text, "" if parent == "." else parent, rel, include_unsure, only_line)
    if keys:
        atomic_write(p, new)
    return keys


# ---- commands --------------------------------------------------------------------------------------------------
def cwd_rel(repo):
    try:
        r = Path.cwd().resolve().relative_to(repo.root).as_posix()
        return "" if r == "." else r
    except ValueError:
        return ""


def agent_ok(repo, a, sub="run"):
    """secrets.agent_read: `run` (default: an agent may use secrets through `run` but not print them with `get` or `expand`),
    `true` (an agent may do all three) or `false` (an agent may do none). An unknown value is read as `run`."""
    if not getattr(a, "agent", False):
        return
    mode = (repo.config.get("secrets") or {}).get("agent_read", "run")
    if mode is True:
        return
    if mode is False:
        raise WsError("a person has not allowed agents to use secrets (secrets.agent_read in _steering/.ws/config.yaml)", 2)
    if sub != "run":
        raise WsError(f"agents may use secrets with `ws secret run` but not print them with `{sub}` (secrets.agent_read: run in _steering/.ws/config.yaml); ask a person", 2)


def where(a):
    p, _, n = str(a.target).rpartition(":")
    if not n.isdigit() or not p:
        raise WsError("give <path>:<line>, the place ws reported", 2)
    return p, int(n)


def cmd_secret(repo, a):
    c = a.scmd
    purge_temp(repo)
    start = getattr(a, "src", None) or cwd_rel(repo)
    if c == "list":
        rows = chain(repo, start)
        emit(a, {k: {"file": f, "note": n} for k, (v, f, n) in rows.items()},
             "\n".join(f"{k:28} {f}  {n}" for k, (v, f, n) in sorted(rows.items())) or "no secrets here (they are moved to .secrets when ws finds them)")
        return 0
    if c == "get":
        agent_ok(repo, a, "get")
        rows = chain(repo, start)
        if a.key not in rows:
            raise WsError(f"no secret {a.key} here" + (f"; known: {', '.join(sorted(rows))}" if rows else ""), 2)
        print(rows[a.key][0])
        return 0
    if c == "run":
        agent_ok(repo, a)
        cmd = [x for x in a.argv if x != "--"]
        if not cmd:
            raise WsError("ws secret run -- <command ...>", 2)
        rows = chain(repo, start)
        env = dict(os.environ, **{k: v for k, (v, _, _) in rows.items()})
        r = subprocess.run(cmd, env=env, capture_output=True, text=True)
        hide = lambda s: re.sub("|".join(re.escape(v) for v, _, _ in rows.values() if v) or "(?!)", "{{secret}}", s)   # noqa: E731
        sys.stdout.write(hide(r.stdout))
        sys.stderr.write(hide(r.stderr))
        return r.returncode
    if c == "expand":
        agent_ok(repo, a, "expand")
        text = repo.read(a.target)
        rows = chain(repo, a.target)
        print(PLACEHOLDER.sub(lambda m: rows[m.group(1)][0] if m.group(1) in rows else m.group(0), text), end="")
        return 0
    if c in ("move", "allow"):
        path, line = where(a)
        text = repo.read(path)
        found = find(repo, text, include_unsure=True, only_line=line)
        if not found:
            raise WsError(f"nothing on {path}:{line} looks like a secret", 2)
        if c == "move":
            keys = scrub_file(repo, path, include_unsure=True, only_line=line)
            emit(a, {"moved": keys}, f"moved {', '.join(keys)} to the .secrets beside {path}; the file now has the placeholder" if keys else "nothing moved")
            return 0
        rp = repo.ws / "redaction.yaml"
        t = rp.read_text(encoding="utf-8") if rp.exists() else "allow: []\n"
        cur = [str(x) for x in (yamlsub.loads(t).get("allow") or [])]
        fps = [fingerprint(text.split("\n")[line - 1][f["start"]:f["end"]]) for f in found]
        new = sorted(set(cur) | set(fps))
        t = re.sub(r"(?m)^allow:.*$", "allow: [" + ", ".join(new) + "]", t) if re.search(r"(?m)^allow:", t) else t.rstrip("\n") + "\nallow: [" + ", ".join(new) + "]\n"
        atomic_write(rp, t)
        print(f"{path}:{line} is marked as not a secret (fingerprint {', '.join(fps)} in redaction.yaml)")
        return 0
    # set
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", a.key):
        raise WsError("a key is UPPER_SNAKE_CASE, for example STAGING_DB_PASSWORD", 2)
    folder = (a.into or start or "").strip("/")
    if a.generate:
        value = rnd.token_urlsafe(int(a.generate) if str(a.generate).isdigit() else 32)
        until, shown = None, "random, not shown"
    else:
        value = a.value if a.value is not None else (sys.stdin.read().strip() if not sys.stdin.isatty() else "")
        if not value:
            raise WsError("give --generate (a random permanent secret, never shown), or a value with --temp [hours]", 2)
        if a.temp is None:
            if getattr(a, "agent", False):
                raise WsError("an agent supplies a value only with --temp (it expires); for a permanent one use --generate, so the value is never in context", 2)
            until = None
        else:
            hours = float(a.temp) if str(a.temp).replace(".", "").isdigit() else float((repo.config.get("secrets") or {}).get("temp_hours", 24))
            until = now() + timedelta(hours=hours)
        shown = "temporary" if until else "permanent"
    p = store(repo, folder, a.key, value, "created by ws", until)
    print(f"stored {a.key} in {p.relative_to(repo.root).as_posix()} ({shown}); use it with: ws secret run -- <command>")
    return 0


def tracked_findings(repo):
    from .checks import finding
    if not repo.is_git():
        return []
    rc, out, _ = repo.git("ls-files", "--", "*.secrets", ".secrets")
    return [finding("error", "secret-tracked", f, "a .secrets file is in git: git rm --cached it; secrets never leave the machine") for f in out.split("\n") if f.strip()]
