"""Run the tests by category: one line each, and details only for a category that fails.

  python3 .dev_yask/run_tests.py                     every category
  python3 .dev_yask/run_tests.py lifecycle           one category
  python3 .dev_yask/run_tests.py lifecycle -k sync   only the tests whose name has "sync", to find which part failed
"""
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATEGORIES = {                                   # a category is the part of the kit it protects
    "core": ["test_ws"],                         # the ws tool: parsing, state, capture, git
    "checks": ["test_hygiene"],                  # ws check, folders, naming, log editing, report fixes, squash, hooks
    "steering": ["test_layers"],                 # two layers, override, update and auto-update
    "lifecycle": ["test_auto"],                  # git created, snapshots, sweep, sync, approve, launchers
    "secrets": ["test_secrets"],
    "release": ["test_release", "test_evals"],   # the release builder, and the eval cases themselves
}


def run(cat, pattern=None):
    t0, total, bad = time.time(), 0, []
    for mod in CATEGORIES[cat]:
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(HERE / "tests"), "-p", f"{mod}.py"] + (["-k", pattern] if pattern else [])
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE.parent)
        out = r.stdout + r.stderr
        m = re.search(r"Ran (\d+) tests?", out)
        total += int(m.group(1)) if m else 0
        bad += re.findall(r"^(?:FAIL|ERROR): (\S+) \((\S+)\)", out, re.M)
        if r.returncode and not bad and not m:
            bad.append(("(did not run)", out.strip().splitlines()[-1] if out.strip() else ""))
    return total, bad, time.time() - t0


def main(argv):
    pattern = argv[argv.index("-k") + 1] if "-k" in argv else None
    cats = [a for a in argv if a in CATEGORIES] or list(CATEGORIES)
    failed = 0
    for c in cats:
        n, bad, secs = run(c, pattern)
        print(f"{'ok  ' if not bad else 'FAIL'} {c:10} {n:3} tests  {secs:4.1f}s")
        for name, where in bad:
            print(f"       {name}  ({where})")
        if bad:
            print(f"       drill down: python3 .dev_yask/run_tests.py {c} -k <name>")
        failed += bool(bad)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
