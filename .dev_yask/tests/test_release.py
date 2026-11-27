"""The release builder and the updater agree on what a release is."""
import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from test_ws import TEMPLATE
from wslib import update

sys.path.insert(0, str(TEMPLATE / ".dev_yask"))
import build_release  # noqa: E402
import cleanup  # noqa: E402


class TestBuild(unittest.TestCase):
    def test_shipped_config_points_at_the_release_repository(self):
        text = (TEMPLATE / "_steering/.yask/yask.yaml").read_text(encoding="utf-8")
        self.assertIn('repo: "kazini/yask-spec-kit"', text)
        self.assertNotIn("check:", (TEMPLATE / "_steering/.yask/.ws/config.yaml").read_text(encoding="utf-8"))
        chk = (TEMPLATE / "_steering/.yask/.ws/check.yaml").read_text(encoding="utf-8")
        self.assertIn("ignore:", chk)
        self.assertIn("front-matter: [README.md, _steering/.yask/YASK.md]", chk)

    def test_builds_what_the_updater_expects_and_leaves_development_files_out(self):
        version = (TEMPLATE / "_steering/.yask/VERSION").read_text().strip()
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(build_release.main(["--out", tmp]), 0)
            out = Path(tmp)
            pkg, sha = out / f"yask-{version}.zip", out / f"yask-{version}.zip.sha256"
            for f in (pkg, sha):
                self.assertTrue(f.exists(), f)
            self.assertFalse((out / f"workspace-{version}.zip").exists())
            self.assertEqual(build_release.mode_problems(pkg), [])
            with zipfile.ZipFile(pkg) as z:
                names = z.namelist()
                i = z.getinfo("ws")
                self.assertEqual(i.create_system, 3)
                self.assertEqual((i.external_attr >> 16) & 0o777, 0o755)
                launcher = z.read("ws")
                self.assertIn(b'rm -f "$d/ws-windows-setup.cmd"', launcher)
                self.assertIn(b"2>/dev/null || :", launcher)
                for r in build_release.RUNNABLE:   # the shims and ws.py: what a git hook and the launchers run
                    self.assertEqual((z.getinfo("_steering/.yask/" + r).external_attr >> 16) & 0o777, 0o755, r)
                for n in ("AGENTS.md", "ws", "_workboard/open-items.md", "_steering/.yask/VERSION",
                          "_steering/.yask/LICENSE", "_steering/.yask/YASK.md", "_steering/.yask/README.md",
                          "_steering/.yask/yask.yaml", "_steering/.yask/.ws/config.yaml",
                          "_steering/.yask/.ws/check.yaml", "_steering/.yask/.gitignore",
                          "_steering/.yask/.gitattributes"):
                    self.assertIn(n, names)
                self.assertNotIn("_steering/.gitattributes", names)   # shared rules are in the root file
                for n in ("LICENSE", "NOTICE", "README.md"):
                    self.assertNotIn(n, names)
                self.assertFalse([n for n in names if n.startswith((".dev_yask", ".github", "_steering/.ws/")) or "__pycache__" in n or "tests/" in n])
                self.assertFalse([n for n in names if n.endswith(("update.yaml", "update_instruct.yaml"))])
            self.assertEqual(sha.read_text().split()[0], hashlib.sha256(pkg.read_bytes()).hexdigest())
            self.assertEqual(sha.read_text().split()[1], pkg.name)
            self.assertTrue(pkg.name.startswith("yask-"))   # the updater picks the asset named yask*
            # and the updater can read what was built
            unpacked = out / "unpacked"
            update.unpack(pkg, unpacked)
            self.assertEqual((update.find_payload(unpacked) / "VERSION").read_text().strip(), version)

    def test_syncs_root_docs_into_yask_before_packing(self):
        original_root = build_release.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            yask = root / "_steering" / ".yask"
            yask.mkdir(parents=True)
            (yask / "VERSION").write_text("9.9\n", encoding="utf-8")
            (root / "LICENSE").write_bytes(b"root license\n")
            (root / "README.md").write_bytes(b"root readme\n")
            (yask / "LICENSE").write_bytes(b"stale license\n")
            (yask / "YASK.md").write_bytes(b"stale readme\n")
            build_release.ROOT = root
            try:
                self.assertEqual(build_release.main(["--out", str(root / "dist")]), 0)
            finally:
                build_release.ROOT = original_root
            self.assertEqual((yask / "LICENSE").read_bytes(), b"root license\n")
            self.assertEqual((yask / "YASK.md").read_bytes(), b"root readme\n")
            with zipfile.ZipFile(root / "dist/yask-9.9.zip") as z:
                self.assertEqual(z.read("_steering/.yask/LICENSE"), b"root license\n")
                self.assertEqual(z.read("_steering/.yask/YASK.md"), b"root readme\n")

            for name in ("LICENSE", "YASK.md"):
                (yask / name).unlink()
            build_release.ROOT = root
            try:
                self.assertEqual(build_release.main(["--out", str(root / "dist2")]), 0)
            finally:
                build_release.ROOT = original_root
            self.assertEqual((yask / "LICENSE").read_bytes(), b"root license\n")
            self.assertEqual((yask / "YASK.md").read_bytes(), b"root readme\n")

            (root / "LICENSE").unlink()
            build_release.ROOT = root
            try:
                with self.assertRaises(FileNotFoundError):
                    build_release.main(["--out", str(root / "dist3")])
            finally:
                build_release.ROOT = original_root
            (root / "LICENSE").write_bytes(b"root license\n")
            (root / "README.md").unlink()
            build_release.ROOT = root
            try:
                with self.assertRaises(FileNotFoundError):
                    build_release.main(["--out", str(root / "dist4")])
            finally:
                build_release.ROOT = original_root

    def test_cleanup_removes_generated_state_only_with_apply(self):
        original_root = cleanup.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "_steering/.ws/cache").mkdir(parents=True)
            (root / "_steering/.ws/config.yaml").write_text("generated", encoding="utf-8")
            (root / "_steering/.yask_cache").mkdir(parents=True)
            (root / "_steering/.yask_cache/update-cache.tar").write_bytes(b"x")
            (root / "dist").mkdir()
            (root / "dist/yask-3.1.zip").write_bytes(b"x")
            (root / "__pycache__").mkdir()
            (root / "__pycache__/x.pyc").write_bytes(b"x")
            (root / "nested/__pycache__").mkdir(parents=True)
            (root / "nested/__pycache__/y.pyc").write_bytes(b"x")
            (root / "stray.pyc").write_bytes(b"x")
            (root / "OLD_README.md").write_text("keep", encoding="utf-8")
            (root / ".secrets").write_text("keep out of git", encoding="utf-8")
            cleanup.ROOT = root
            try:
                self.assertEqual(cleanup.main([]), 0)
                self.assertTrue((root / "_steering/.ws/config.yaml").exists())
                self.assertTrue((root / "_steering/.yask_cache").exists())
                self.assertEqual(cleanup.main(["--apply"]), 0)
            finally:
                cleanup.ROOT = original_root
            self.assertFalse((root / "_steering/.ws").exists())
            self.assertFalse((root / "_steering/.yask_cache").exists())
            self.assertFalse((root / "dist").exists())
            self.assertFalse((root / "__pycache__").exists())
            self.assertFalse((root / "nested/__pycache__").exists())
            self.assertFalse((root / "stray.pyc").exists())
            self.assertTrue((root / "OLD_README.md").exists())
            self.assertTrue((root / ".secrets").exists())


if __name__ == "__main__":
    unittest.main()
