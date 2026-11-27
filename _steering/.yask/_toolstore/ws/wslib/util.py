"""Clock, ids, atomic writes, attribute blocks and output helpers."""
import json
import os
import random
import re
import secrets
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .repo import WsError

STAMP_FMT = "%Y%m%dT%H%MZ"


def flag(name, default=True):
    """A kit-wide switch from the environment: 0, false, no or off turns it off; 1, true, yes or on turns it on."""
    v = os.environ.get(name, "").strip().lower()
    return default if not v else v not in ("0", "false", "no", "off")


def now():
    """UTC now, to the minute. WS_NOW (YYYYMMDDTHHMMZ) pins the clock."""
    pin = os.environ.get("WS_NOW")
    if pin:
        return datetime.strptime(pin, STAMP_FMT).replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc).replace(second=0, microsecond=0)


def stamp(dt=None):
    return (dt or now()).strftime(STAMP_FMT)


def file_stamp(dt=None):
    return (dt or now()).strftime("%Y-%m-%d-%H%M")


def day(dt=None):
    return (dt or now()).strftime("%Y-%m-%d")


def parse_stamp(s):
    return datetime.strptime(s, STAMP_FMT).replace(tzinfo=timezone.utc)


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".ws-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


_LOCAL = threading.local()


@contextmanager
def locked(repo, wait=10.0):
    """Short write lock held by the tool for milliseconds, so nobody has to remember it. Waits for other ws writers,
    breaks a lock left by a crashed one, and tells the caller (and stderr) how long it waited."""
    if getattr(_LOCAL, "held", False):  # nested call inside the same command
        yield 0.0
        return
    p = repo.ws / "cache" / "write.lock"
    p.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    while True:
        try:
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - p.stat().st_mtime > 15:
                    os.replace(p, p.with_name(f"write.lock.stale{os.getpid()}"))
                    os.unlink(p.with_name(f"write.lock.stale{os.getpid()}"))
                    continue
            except OSError:
                continue
            if time.monotonic() - t0 > wait:
                raise WsError(f"another ws command kept the write lock for {int(wait)}s; try again", 2)
            time.sleep(0.01 + random.random() * 0.03)
    waited = time.monotonic() - t0
    if waited > 0.1:
        warn(f"note: waited {waited:.1f}s for another ws write; yours was applied on top of theirs")
    _LOCAL.held = True
    try:
        yield waited
    finally:
        _LOCAL.held = False
        try:
            os.unlink(p)
        except OSError:
            pass


def append_text(path, header, line):
    """Append one line. Creates the file with `header` if new. Never rewrites existing content."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as f:
            f.write(header)
    except FileExistsError:
        pass
    with open(path, "rb+") as f:
        f.seek(0, 2)
        if f.tell():
            f.seek(-1, 2)
            lead = b"" if f.read(1) == b"\n" else b"\n"
        else:
            lead = b""
    with open(path, "ab") as f:
        f.write(lead + line.encode("utf-8") + b"\n")


def new_id(repo, prefix, extra=()):
    used = set(extra)
    rx = re.compile(rf"\b{prefix}-([0-9a-f]{{4}})\b")
    for f in repo.md_files(include_archive=True):
        used.update(rx.findall(repo.read(f)))
    for _ in range(200):
        h = secrets.token_hex(2)
        if h not in used:
            return f"{prefix}-{h}"
    raise WsError("could not find an unused id")


def hex4(used=()):
    for _ in range(200):
        h = secrets.token_hex(2)
        if h not in used:
            return h
    raise WsError("could not find an unused id")


# -- attribute blocks: `text {#t-ab12 key=value key=value}` -----------------------
ATTR = re.compile(r"\{#([a-z]-[0-9a-f]{4})((?:\s+[\w-]+=[^\s}]+)*)\}\s*$")


def parse_item(line):
    """(text, id, attrs) for an item line with a trailing attribute block, else None."""
    m = ATTR.search(line)
    if not m:
        return None
    text = line[:m.start()].rstrip()
    attrs = dict(a.split("=", 1) for a in m.group(2).split())
    return text, m.group(1), attrs


def render_item(text, iid, attrs):
    block = " ".join(f"{k}={v}" for k, v in attrs.items() if v not in (None, ""))
    return f"{text} {{#{iid}{' ' + block if block else ''}}}"


def words(s):
    return re.sub(r"\s+", "-", s.strip())


# -- output ----------------------------------------------------------------------
def emit(args, obj, text):
    if getattr(args, "json", False):
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    else:
        print(text)


def table(rows, headers):
    if not rows:
        return "(none)"
    cols = list(zip(*([headers] + [[str(c) for c in r] for r in rows])))
    w = [max(len(c) for c in col) for col in cols]
    fmt = "  ".join(f"{{:<{x}}}" for x in w)
    return "\n".join([fmt.format(*headers), fmt.format(*["-" * x for x in w])] + [fmt.format(*[str(c) for c in r]) for r in rows])


def warn(msg):
    print(f"ws: {msg}", file=sys.stderr)
