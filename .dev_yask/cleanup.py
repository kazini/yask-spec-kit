"""Clear generated local state before pushing this template to a remote.

  python3 .dev_yask/cleanup.py           dry run: list what would be removed
  python3 .dev_yask/cleanup.py --apply   remove it

Removes only generated state: _steering/.ws/, _steering/.yask_cache/, dist/, __pycache__/ and stray .pyc files.
Never touches .git/, _steering/.yask/, .github/, .dev_yask/ or source documents.
Superseded or sensitive files are reported, not deleted: they need a decision.
Run this last: the next `ws` run regenerates _steering/.ws/.
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ("OLD_README.md", ".secrets", ".apikeys")


def generated():
    """Generated state that is safe to remove from a template checkout."""
    out = [ROOT / rel for rel in ("_steering/.ws", "_steering/.yask_cache", "dist") if (ROOT / rel).exists()]
    for p in ROOT.rglob("__pycache__"):
        if p.is_dir() and ".git" not in p.parts:
            out.append(p)
    for p in ROOT.rglob("*.pyc"):
        if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts:
            out.append(p)
    return sorted(set(out), key=lambda p: p.as_posix())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="remove the listed paths; without this, only list them")
    a = ap.parse_args(argv)
    found = generated()
    if not found:
        print("nothing to clean")
    for p in found:
        rel = p.relative_to(ROOT).as_posix()
        if a.apply:
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()
            print(f"removed {rel}")
        else:
            print(f"would remove {rel}")
    for rel in DECISIONS:
        if (ROOT / rel).exists():
            print(f"left for a decision: {rel}")
    for p in sorted(ROOT.glob(".env*")):
        print(f"left for a decision: {p.name}")
    if found and not a.apply:
        print("dry run; re-run with --apply to remove")
    return 0


if __name__ == "__main__":
    sys.exit(main())
