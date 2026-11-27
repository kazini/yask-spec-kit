"""Generated blocks in AGENTS.md (router and where-a-new-fact-goes) and routed playbook listing."""
import re

from .repo import read_fm
from .util import atomic_write


def routed_playbooks(repo):
    """Playbooks in force, from both steering layers. A shipped one is routed when its module is on; the project's own
    (_steering/playbooks/) always are. The path given is the file that is in force."""
    en = list(repo.enabled)
    found, mine = [], []
    for name, f in repo.steer_list("playbooks").items():
        if name == "README.md":
            continue
        fm = read_fm(f.read_text(encoding="utf-8"))[0]
        shipped = repo.base / "playbooks" / name
        module = fm.get("module") or (read_fm(shipped.read_text(encoding="utf-8"))[0].get("module") if shipped.exists() else None)
        row = {"module": module or "project", "path": f.relative_to(repo.root).as_posix(), "use_when": str(fm.get("use_when", "")),
               "description": str(fm.get("description", ""))}
        if module in en:
            found.append((en.index(module), row))
        elif module is None and repo.steer / "playbooks" == f.parent:
            mine.append(row)
    return [p for _, p in sorted(found, key=lambda x: x[0])] + mine


def router_block(repo):
    rows = [f"| {p['use_when']} | `{p['path']}` |" for p in routed_playbooks(repo)]
    return "| If the task is | Do this |\n|---|---|\n" + "\n".join(rows)


def where_block(repo):
    rows = [f"| {w['holds']} | `{w['path']}` | {w['kind']} |" for w in repo.where_entries()]
    return "| Holds | Path | Kind |\n|---|---|---|\n" + "\n".join(rows)


def apply(repo, write=False):
    """Return (stale, new_text). Writes AGENTS.md when write is true."""
    p = repo.abs("AGENTS.md")
    old = p.read_text(encoding="utf-8")
    new = old
    for name, block in (("router", router_block(repo)), ("where", where_block(repo))):
        new = re.sub(rf"(<!-- ws:generated:{name} start -->\n).*?(<!-- ws:generated:{name} end -->)",
                     lambda m: m.group(1) + block + "\n" + m.group(2), new, flags=re.S)
    if write and new != old:
        atomic_write(p, new)
    return new != old, new
