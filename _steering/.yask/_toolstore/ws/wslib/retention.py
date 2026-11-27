"""retention: which raw items are past the policy in _steering/.ws/retention.yaml (plan only; archiving rewrites history).

`then:` is review (default: a person decides, nothing is planned), offload (cold storage, history untouched) or archive (rewrites
history). An unknown value is read as review, so a typo never plans a history rewrite."""
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from . import yamlsub
from .util import emit, now, table


def age_days(repo, rel):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})-(\d{4})", Path(rel).name)
    if m:
        t = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)[:2]), int(m.group(4)[2:]), tzinfo=timezone.utc)
    else:
        rc, out, _ = repo.git("log", "--format=%cI", "--reverse", "--", rel)
        first = out.strip().splitlines()[0] if rc == 0 and out.strip() else ""
        t = datetime.fromisoformat(first) if first else datetime.fromtimestamp(repo.abs(rel).stat().st_mtime, timezone.utc)
    return (now() - t).days


def cmd_retention(repo, a):
    p = repo.ws / "retention.yaml"
    pol = yamlsub.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    rows = []
    for e in repo.where_entries(all_modules=True):
        key = (repo.manifests.get(e["module"]) or {}).get("retention")
        rule = pol.get(key) if key else None
        if e["kind"] != "raw" or not rule or not e["path"].endswith("/") or not repo.exists(e["path"].rstrip("/")):
            continue
        base = repo.abs(e["path"].rstrip("/"))
        for child in sorted(base.iterdir()):
            rel = child.relative_to(repo.root).as_posix()
            if child.name == "README.md" or child.name.startswith(".") or child.name.endswith(".offloaded.md"):
                continue
            d = age_days(repo, rel)
            act = ""
            if rule.get("cold_after_days") and d > int(rule["cold_after_days"]):
                act = "cold"
            elif rule.get("in_tree_days") and d > int(rule["in_tree_days"]):
                act = rule.get("then", "review")
                act = act if act in ("archive", "offload") else "review"
            if act:
                offload = f"ws git offload <files in {rel}> --to <dir>"
                cmd = {"archive": f"ws archive {rel}   (rewrites history: needs a person's go-ahead, see archive-and-retention.md)",
                       "review": f"a person decides: keep, {offload}, or ws archive {rel} (rewrites history)"}.get(act, offload)
                rows.append({"path": rel, "age_days": d, "due": act, "rule": key, "command": cmd})
    emit(a, rows, table([(r["path"], r["age_days"], r["due"], r["command"]) for r in rows], ["path", "days", "due", "command"]) if rows else "nothing is past its retention period")
    return 1 if rows else 0
