"""Build the files a release carries. Development only: .dev_yask/ is never released.

  python3 .dev_yask/build_release.py [--out dist]

Writes, from _steering/.yask/VERSION:
  yask-<version>.zip         the workspace template: root files except LICENSE, NOTICE and README.md, _workboard/, and _steering/.yask/ (LICENSE and README ship in .yask/LICENSE and .yask/YASK.md; NOTICE ships in .yask/NOTICE from the layer; no .dev_yask or .github, no generated .ws). This is what `ws update` downloads; it applies only the .yask payload.
  yask-<version>.zip.sha256  its checksum, which `ws update` verifies when the release publishes it.
Before packing, root LICENSE and README.md are copied into .yask/LICENSE and .yask/YASK.md when missing or different.
Modes are decided here, not taken from the machine that builds: the root launcher `ws` and every file that starts with a #! line (the sh shims and
ws.py) are stored 0755, everything else 0644, so unzip gives the right bits on Linux and macOS no matter which OS built the zip (a Windows checkout has none).
The zip is checked after it is written, and the build fails rather than publish one whose modes or line endings are wrong.
Attach both files to a GitHub release tagged v<version>. The updater picks the asset whose name starts with "yask".
"""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"__pycache__", ".git", ".dev_yask", ".github", "cache", "snapshots", "reports", "backups"}
TOP_SKIP = {"dist", ".ws", "LICENSE", "NOTICE", "README.md"}  # these stay out of the starter zip root: LICENSE and README ship inside .yask, NOTICE travels with the layer
ROOT_DOCS = (("LICENSE", "LICENSE"), ("README.md", "YASK.md"))


def members(base, rel_to, prefix=""):
    for f in sorted(base.rglob("*")):
        rel = f.relative_to(rel_to)
        if f.is_file() and not (set(rel.parts) & SKIP) and f.suffix != ".pyc":
            yield f, (Path(prefix) / rel).as_posix()


ROOT_LAUNCHER = "ws"   # polyglot (sh and cmd): its first line is not a #! line, so it is named
RUNNABLE = ("_toolstore/_shims/ws", "_toolstore/_shims/yask", "_toolstore/ws/ws", "_toolstore/ws/yask", "_toolstore/ws/ws.py")   # what a package must carry


def is_executable(f, name):
    """Stored 0755: the root launcher, and any file whose first line is a #! line. Decided by content, so a new script cannot be forgotten."""
    if name == ROOT_LAUNCHER:
        return True
    with open(f, "rb") as h:
        return h.read(2) == b"#!"


def mode_problems(zpath):
    """What is wrong with the stored modes of a built zip (empty when fine): an executable that is not 0755, a plain file that is
    executable, or a #! line ending in CR (sh would look for an interpreter called python3\\r)."""
    out = []
    with zipfile.ZipFile(zpath) as z:
        for i in z.infolist():
            mode, data = (i.external_attr >> 16) & 0o777, z.read(i)
            shebang = data[:2] == b"#!"
            want = 0o755 if shebang or i.filename == ROOT_LAUNCHER else 0o644
            if i.create_system != 3 or mode != want:
                out.append(f"{i.filename}: stored {mode:04o} (system {i.create_system}), expected {want:04o}")
            if shebang and b"\r" in data.split(b"\n", 1)[0]:
                out.append(f"{i.filename}: the #! line ends in CR")
    return out


def sync_root_docs(yask):
    """Copy root release docs into .yask under their shipped names when missing or stale."""
    for source_name, target_name in ROOT_DOCS:
        source = ROOT / source_name
        if not source.is_file():
            raise FileNotFoundError(f"root {source_name} not found at {source}")
        target = yask / target_name
        data = source.read_bytes()
        if target.is_file() and target.read_bytes() == data:
            continue
        target.write_bytes(data)
        print(f"synced {source_name} -> _steering/.yask/{target_name}")


def write_zip(path, items):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for f, name in items:
            info = zipfile.ZipInfo.from_file(f, name)
            info.create_system = 3              # Unix: the high bits of external_attr are a mode, not DOS attributes
            info.external_attr = ((0o100755 if is_executable(f, name) else 0o100644) << 16) | (info.external_attr & 0xFFFF)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="dist")
    a = ap.parse_args(argv)
    yask = ROOT / "_steering" / ".yask"
    sync_root_docs(yask)
    version = (yask / "VERSION").read_text(encoding="utf-8").strip()
    out = (ROOT / a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    pkg = out / f"yask-{version}.zip"
    sha = out / (pkg.name + ".sha256")
    top = [p for p in ROOT.iterdir() if p.name not in SKIP and p.name not in TOP_SKIP]
    items = []
    for p in sorted(top):
        items += list(members(p, ROOT)) if p.is_dir() else [(p, p.name)]
    write_zip(pkg, [(f, n) for f, n in items if not n.startswith("_steering/.ws/")])
    sha.write_text(f"{hashlib.sha256(pkg.read_bytes()).hexdigest()}  {pkg.name}\n", encoding="utf-8")
    bad = [f"{pkg.name}: {x}" for x in mode_problems(pkg)]
    if bad:
        print("\n".join(["refusing to release: a package has wrong file modes", *bad]), file=sys.stderr)
        return 1
    for p in (pkg, sha):
        print(f"{p.name}  {p.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
