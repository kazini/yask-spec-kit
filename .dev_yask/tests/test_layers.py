"""Steering layers (_steering/ over _steering/.yask/), override, the generated .ws, ws update and the automatic check."""
import json
import os
import re
import shutil
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_ws import TEMPLATE, WsCase, needs_git
from wslib import update, yamlsub

PLAYBOOK = '---\nkind: steering\nmodule: core\nuse_when: "Handle the zorbulax situation whenever a zorbulax turns up in the project"\ndescription: "Zorbulax."\n---\n# Zorbulax\n1. Do it.\n'


def set_repo(path, repo):
    """Replace the quoted repo value without assuming what the template shipped."""
    text = path.read_text(encoding="utf-8")
    text, n = re.subn(r'(?m)^(\s*repo:\s*)"[^"]*"', lambda m: m.group(1) + json.dumps(repo), text)
    if not n:
        raise AssertionError(f"no quoted repo line in {path}")
    path.write_text(text, encoding="utf-8")


class TestLayers(WsCase):
    def seen(self, rel):
        from wslib.repo import Repo
        return Repo(str(self.root)).read(rel)     # what the tool reads: _steering/ first, then _steering/.yask/

    def test_project_file_supersedes_the_shipped_one_by_path(self):
        shipped = self.read("_steering/.yask/playbooks/record-decision.md")
        self.assertEqual(self.seen("_steering/playbooks/record-decision.md"), shipped)   # a missing path is read from .yask
        self.assertIn("_steering/.yask/playbooks/record-decision.md", self.read("AGENTS.md"))
        self.write("_steering/playbooks/record-decision.md", shipped.replace("# ", "# Our ", 1))
        self.assertIn("# Our ", self.seen("_steering/playbooks/record-decision.md"))
        self.ws("check", "--fix-generated")
        agents = self.read("AGENTS.md")
        self.assertIn("`_steering/playbooks/record-decision.md`", agents)
        self.assertNotIn("_steering/.yask/playbooks/record-decision.md", agents)
        self.assertIn("record-decision.md: _steering/playbooks/record-decision.md (project, supersedes the shipped file)", self.ws("steering", "show", "playbooks/record-decision.md")[1].replace("\n", ""))

    def test_a_project_playbook_is_routed_without_a_module(self):
        self.write("_steering/playbooks/handle-zorbulax.md", PLAYBOOK.replace("module: core\n", ""))
        self.ws("check", "--fix-generated")
        self.assertIn("handle-zorbulax.md", self.ws("route", "a zorbulax turned up")[1])
        self.assertIn("handle-zorbulax.md", self.read("AGENTS.md"))

    def test_override_on_top_of_a_document_switches_off_shipped_files_under_other_names(self):
        self.ws("scaffold", "lessons", "--apply")
        self.assertIn("record-lesson.md", self.read("AGENTS.md"))
        self.write("_steering/playbooks/our-lessons.md", PLAYBOOK.replace("module: core", "module: lessons").replace("---\n# Zorbulax", "override: [playbooks/record-lesson.md]\n---\n# Zorbulax", 1))
        self.ws("check", "--fix-generated")
        agents = self.read("AGENTS.md")
        self.assertNotIn("record-lesson.md", agents)
        self.assertIn("our-lessons.md", agents)
        self.assertFalse(self.ws("steering", "show", "playbooks/record-lesson.md")[0] == 0)
        self.assertIn("switched off by _steering/playbooks/our-lessons.md", self.ws("steering", "show", "playbooks/record-lesson.md")[1])

    def test_override_takes_folders_and_globs_and_warns_when_it_matches_nothing(self):
        self.write("_steering/overrides.md", '---\nkind: steering\ndescription: "off"\noverride: ["modules/software/", "playbooks/document-*.md", "playbooks/not-there.md"]\n---\n# Off\n')
        out = self.ws("check")[1]
        self.assertIn("override 'playbooks/not-there.md' matches no shipped steering file", out)
        self.assertNotIn("modules/software", out)
        self.assertNotIn("software", self.ws("modules")[1])
        self.assertNotIn("playbooks/document-handling.md", self.ws("map", "_steering/")[1] + self.ws("map", "_steering/.yask/playbooks/")[1])
        self.assertNotIn("playbooks/document-handling.md", self.ws("find", "--steering", "document handling")[1])

    def test_switching_off_an_enabled_module_is_an_error(self):
        self.write("_steering/overrides.md", '---\nkind: steering\ndescription: "off"\noverride: [modules/meetings/]\n---\n# Off\n')
        code, out, _ = self.ws("check")
        self.assertEqual(code, 2)
        self.assertIn("module meetings is enabled but has no manifest", out)

    def test_override_and_restore_through_the_tool(self):
        self.assertEqual(self.ws("steering", "override", "playbooks/nope.md")[0], 2)
        self.assertEqual(self.ws("steering", "override", "playbooks/record-lesson.md", "templates/lesson.md", "--why", "we track lessons elsewhere")[0], 0)
        doc = self.read("_steering/overrides.md")
        self.assertIn('override: ["playbooks/record-lesson.md", "templates/lesson.md"]', doc)
        self.assertIn("`playbooks/record-lesson.md`: we track lessons elsewhere", doc)
        self.assertEqual(yamlsub.loads(doc.split("---")[1])["override"], ["playbooks/record-lesson.md", "templates/lesson.md"])
        self.assertIn("2 switched off", self.ws("steering")[1])
        self.assertEqual(self.ws("steering", "restore", "templates/lesson.md")[0], 0)
        self.assertIn('override: ["playbooks/record-lesson.md"]', self.read("_steering/overrides.md"))
        self.assertEqual(self.ws("check")[0], 0)

    def test_copy_makes_an_editable_project_file_that_supersedes(self):
        self.assertEqual(self.ws("steering", "copy", "playbooks/session-state.md")[0], 0)
        self.assertTrue((self.root / "_steering/playbooks/session-state.md").exists())
        self.assertEqual(self.ws("steering", "copy", "playbooks/session-state.md")[0], 2)
        self.assertIn("supersedes", self.ws("steering")[1])
        self.assertEqual(self.ws("steering", "copy", ".yask/README.md")[0], 2)

    def test_project_module_supersedes_and_scaffolds_from_the_project_layer(self):
        self.write("_steering/modules/risks/module.yaml", 'name: risks\ndescription: "Risk files."\ndefault: false\nrequires: [core]\nwhere:\n  - { holds: "A project risk", path: "docs/risks/", kind: canon }\n')
        self.write("_steering/modules/risks/scaffold/docs/risks/README.md", '---\nkind: canon\ndescription: "Risks."\n---\n# Risks\n')
        self.assertIn("risks", self.ws("modules")[1])
        self.assertEqual(self.ws("scaffold", "risks", "--apply")[0], 0)
        self.assertEqual(self.ws("scaffold", "docs/risks", "--apply")[0], 0)
        self.assertTrue((self.root / "docs/risks/README.md").exists())
        self.assertIn("docs/risks/", self.read("AGENTS.md"))

    def test_steering_is_not_searched_by_default_but_the_merged_map_shows_both_layers(self):
        self.write("_steering/playbooks/handle-zorbulax.md", PLAYBOOK)
        listing = self.ws("map", "_steering/")[1]
        self.assertRegex(listing, r"_steering/playbooks/\n\s+handle-zorbulax\.md")
        self.assertRegex(listing, r"_steering/\.yask/templates/\n(\s+\S+.*\n)*")
        self.assertIn("playbooks/", self.ws("map", "_steering/.yask/")[1])
        self.assertNotIn("zorbulax", self.ws("find", "zorbulax")[1].lower())
        self.assertIn("zorbulax", self.ws("find", "--steering", "zorbulax")[1].lower())


class TestGeneratedWs(WsCase):
    def test_ws_is_generated_on_first_run_from_the_shipped_copy_and_never_overwritten(self):
        ws = self.root / "_steering/.ws"
        self.assertFalse(ws.exists())
        self.ws("modules")
        for n in ("config.yaml", "folders.yaml", "redaction.yaml", "retention.yaml", "README.md"):
            self.assertEqual((ws / n).read_text(), (self.root / "_steering/.yask/.ws" / n).read_text())
        cfg = ws / "config.yaml"
        cfg.write_text(cfg.read_text().replace("log_fold_lines: 3", "log_fold_lines: 9"))
        (ws / "folders.yaml").unlink()
        self.ws("modules")
        self.assertIn("log_fold_lines: 9", cfg.read_text())                    # your values stay
        self.assertTrue((ws / "folders.yaml").exists())                        # a missing file is regenerated

    def test_enabling_a_module_edits_the_projects_config_not_the_shipped_one(self):
        shipped = self.read("_steering/.yask/.ws/config.yaml")
        self.ws("scaffold", "software", "--apply")
        self.assertEqual(self.read("_steering/.yask/.ws/config.yaml"), shipped)
        self.assertIn("software", self.read("_steering/.ws/config.yaml"))


def package(tmp, version="9.0.0", nested="owner-repo-abc123/_steering/.yask", with_old=True):
    """A release package built from this template's shipped layer, changed in the ways an update has to cope with."""
    src = Path(tmp) / "src"
    shutil.rmtree(src, ignore_errors=True)          # a second package must not leave an older .yask for find_payload
    dst = src / nested
    if with_old:
        (Path(tmp) / "ws/_steering/.yask/old-notes.md").write_text('---\nkind: steering\ndescription: "A file the next release drops."\n---\n# Old notes\n')
    shutil.copytree(Path(tmp) / "ws/_steering/.yask", dst, ignore=shutil.ignore_patterns("__pycache__"))
    (dst / "VERSION").write_text(version + "\n")
    (dst / "playbooks/new-thing.md").write_text(PLAYBOOK.replace("zorbulax", "gizmo").replace("module: core", "module: core"))
    with open(dst / "playbooks/session-state.md", "a") as f:
        f.write("\nAdded line from the new release.\n")
    (dst / "old-notes.md").unlink(missing_ok=True)
    cfg = dst / ".ws/config.yaml"
    t = cfg.read_text().replace("  log_fold_lines: 3 ", "  brand_new_threshold: 4      # arrives with the release\n  log_fold_lines: 3 ", 1)
    t += "newsection:\n  flag: true\n"
    cfg.write_text(t)
    ck = dst / ".ws/check.yaml"
    ck.write_text(ck.read_text().replace("ignore:\n", "ignore:\n  broken-link: [docs/archived/*.md]\n", 1))
    fy = dst / ".ws/folders.yaml"
    fy.write_text(fy.read_text().replace("folders:\n", "folders:\n  - { path: docs/brand-new, listed: false }\n", 1))
    return src, dst


class TestUpdate(WsCase):
    def setUp(self):
        super().setUp()
        self.ws("modules")                       # generate .ws
        self.src, self.dst = package(self.tmp)

    def touched(self):
        """Everything an update can change, including new or removed files, as content and mode."""
        out = {}
        for rel in ("_steering/.yask", "_steering/.ws", "AGENTS.md"):
            p = self.root / rel
            if p.is_file():
                out[rel] = ("f", p.stat().st_mode, p.read_bytes())
            elif p.is_dir():
                for f in p.rglob("*"):
                    key = rel + "/" + f.relative_to(p).as_posix()
                    out[key] = ("d",) if f.is_dir() else ("f", f.stat().st_mode, f.read_bytes())
        return out

    def test_failed_update_restores_every_touched_path(self):
        before = self.touched()
        with mock.patch("wslib.gen.apply", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.ws("update", "--from", str(self.src), "--apply")
        self.assertEqual(self.touched(), before)
        self.assertFalse((self.root / "_steering/.yask_cache").exists())

    def test_plan_changes_nothing_and_apply_mirrors_yask_but_never_steering(self):
        mine = self.root / "_steering/playbooks/our.md"
        mine.parent.mkdir(parents=True, exist_ok=True)
        mine.write_text(PLAYBOOK)
        before_yask = self.read("_steering/.yask/VERSION")
        code, out, _ = self.ws("update", "--from", str(self.src))
        self.assertEqual(code, 0)
        self.assertIn("1 new", out)
        self.assertIn("removed", out)
        self.assertEqual(self.read("_steering/.yask/VERSION"), before_yask)
        code, out, _ = self.ws("update", "--from", str(self.src), "--apply")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read("_steering/.yask/VERSION").strip(), "9.0.0")
        self.assertTrue((self.root / "_steering/.yask/playbooks/new-thing.md").exists())
        self.assertFalse((self.root / "_steering/.yask/old-notes.md").exists())    # removed in the release
        self.assertIn("Added line from the new release", self.read("_steering/.yask/playbooks/session-state.md"))
        self.assertEqual(mine.read_text(), PLAYBOOK)                                           # the project layer is untouched
        self.assertFalse((self.root / "_steering/.yask_cache").exists())         # a successful update leaves no cache behind
        self.assertIn("new-thing.md", self.read("AGENTS.md"))                                  # generated router refreshed

    def test_reconcile_adds_new_options_and_keeps_the_projects_values(self):
        cfg = self.root / "_steering/.ws/config.yaml"
        cfg.write_text(cfg.read_text().replace("log_fold_lines: 3", "log_fold_lines: 9"))
        chk = self.root / "_steering/.ws/check.yaml"
        chk.write_text(chk.read_text().replace("front-matter: [README.md, _steering/.yask/YASK.md]", "front-matter: [README.md, _steering/.yask/YASK.md, docs/mine.md]"))
        self.ws("update", "--from", str(self.src), "--apply")
        c = yamlsub.loads(cfg.read_text())
        self.assertEqual(c["thresholds"]["log_fold_lines"], 9)                                 # a value the project chose is kept
        self.assertEqual(c["thresholds"]["brand_new_threshold"], 4)                            # a new option arrives inside its section
        self.assertEqual(c["newsection"], {"flag": True})                                      # and a whole new section
        self.assertIn("# arrives with the release", cfg.read_text())
        rules = yamlsub.loads(chk.read_text())["ignore"]
        self.assertEqual(rules["front-matter"], ["README.md", "_steering/.yask/YASK.md", "docs/mine.md"])
        self.assertEqual(rules["broken-link"], ["docs/archived/*.md"])                         # a new finding code arrives inside its section
        self.assertIn("docs/brand-new", self.read("_steering/.ws/folders.yaml"))
        notes = self.read("_steering/.ws/update-notes.md")
        self.assertIn(".ws/config.yaml: added newsection, thresholds.brand_new_threshold", notes)
        self.assertIn(".ws/check.yaml: added ignore.broken-link", notes)
        self.assertIn("update notes", self.ws("start")[1])
        self.assertEqual(self.ws("check")[0], 0, self.ws("check")[1])
        self.assertIn("docs/brand-new", self.ws("update", "--notes")[1] + notes)

    def test_a_project_without_the_check_file_receives_it_and_keeps_its_own_rules(self):
        chk = self.root / "_steering/.ws/check.yaml"
        chk.unlink()
        (self.root / "_steering/.yask/.ws/check.yaml").unlink()   # this release never shipped the file
        self.assertEqual(self.ws("check")[0], 2)                  # YASK.md and README.md are flagged again
        self.ws("update", "--from", str(self.src), "--apply")
        c = yamlsub.loads(chk.read_text())
        self.assertEqual(c["ignore"]["front-matter"], ["README.md", "_steering/.yask/YASK.md"])
        self.assertEqual(self.ws("check")[0], 0, self.ws("check")[1])
        mine = chk.read_text().replace("front-matter: [README.md, _steering/.yask/YASK.md]", "front-matter: [README.md, _steering/.yask/YASK.md, docs/mine.md]")
        chk.write_text(mine)
        merged, added = update.merge_keys(mine, self.read("_steering/.yask/.ws/check.yaml"))
        self.assertEqual((merged, added), (mine, []))             # the project's own exceptions are never rewritten

    @unittest.skipIf(os.name == "nt", "no executable bit on Windows")
    def test_executable_bits_survive_unpack_and_are_granted_never_stripped(self):
        z = Path(self.tmp) / "p.zip"
        with zipfile.ZipFile(z, "w") as f:
            for name, mode in (("a/run", 0o755), ("a/data.txt", 0o644)):
                i = zipfile.ZipInfo(name); i.create_system = 3; i.external_attr = (0o100000 | mode) << 16
                f.writestr(i, "x")
        out = Path(self.tmp) / "out"
        update.unpack(z, out)
        self.assertTrue(os.access(out / "a/run", os.X_OK))
        self.assertFalse(os.access(out / "a/data.txt", os.X_OK))
        shim = "_toolstore/_shims/ws"
        os.chmod(self.dst / shim, 0o755)
        os.chmod(self.root / "_steering/.yask" / shim, 0o644)
        self.assertIn("_toolstore/_shims/ws", self.ws("update", "--from", str(self.src), "--json")[1])   # a mode-only change is a change
        self.ws("update", "--from", str(self.src), "--apply")
        self.assertTrue(os.access(self.root / "_steering/.yask" / shim, os.X_OK))
        os.chmod(self.root / "_steering/.yask" / shim, 0o755)
        os.chmod(self.dst / shim, 0o644)
        pl = update.plan(__import__("wslib.repo", fromlist=["Repo"]).Repo(str(self.root)), self.dst)
        self.assertNotIn(shim, pl["change"])                                                         # never stripped

    def test_reconcile_is_idempotent(self):
        self.ws("update", "--from", str(self.src), "--apply")
        before = self.read("_steering/.ws/config.yaml") + self.read("_steering/.ws/folders.yaml")
        self.assertIn("up to date", self.ws("update", "--from", str(self.src), "--apply")[1])
        text, added = update.merge_keys(self.read("_steering/.ws/config.yaml"), self.read("_steering/.yask/.ws/config.yaml"))
        self.assertEqual(added, [])
        self.assertEqual(self.read("_steering/.ws/config.yaml") + self.read("_steering/.ws/folders.yaml"), before)

    def test_a_zip_and_a_plain_payload_folder_work_too(self):
        z = Path(self.tmp) / "release.zip"
        shutil.make_archive(str(z.with_suffix("")), "zip", self.src)
        self.assertIn("1 new", self.ws("update", "--from", str(z))[1])
        flat = Path(self.tmp) / "flat"
        shutil.copytree(self.dst, flat)
        self.assertIn("1 new", self.ws("update", "--from", str(flat))[1])
        self.assertEqual(self.ws("update", "--from", str(Path(self.tmp) / "missing"))[0], 2)

    @needs_git
    def test_no_source_configured_is_explained_and_dirty_yask_is_refused(self):
        set_repo(self.root / "_steering/.yask/yask.yaml", "")
        code, _, err = self.ws("update")
        self.assertEqual(code, 2)
        self.assertIn("update.repo", err)
        self.init_git()
        with open(self.root / "_steering/.yask/conventions.md", "a") as f:
            f.write("\nlocal edit\n")
        code, _, err = self.ws("update", "--from", str(self.src), "--apply")
        self.assertEqual(code, 2)
        self.assertIn("uncommitted changes", err)
        self.assertEqual(self.ws("update", "--from", str(self.src), "--apply", "--force")[0], 0)

    def test_an_unknown_method_in_the_instructions_is_refused(self):
        (self.dst / "yask.yaml").write_text("update:\n  reconcile:\n    - { file: .ws/config.yaml, method: overwrite-everything }\n")
        code, _, err = self.ws("update", "--from", str(self.src), "--apply")
        self.assertEqual(code, 2)
        self.assertIn("unknown method", err)

    def test_notify_messages_show_once_for_versions_crossed(self):
        (self.dst / "yask.yaml").write_text("update:\n  reconcile: []\n  notify:\n    - { since: \"8.0.0\", message: \"Read the new retention defaults.\" }\n    - { since: \"10.0.0\", message: \"Not yet.\" }\n")
        self.ws("update", "--from", str(self.src), "--apply")
        notes = self.read("_steering/.ws/update-notes.md")
        self.assertIn("Read the new retention defaults.", notes)
        self.assertNotIn("Not yet.", notes)


class TestUpdateCommit(WsCase):
    def setUp(self):
        super().setUp()
        self.ws("modules")
        self.src, self.dst = package(self.tmp)
        self.init_git()                                   # commits the shipped layer, the generated .ws and the fixture

    def last(self, fmt):
        return self.git("log", "-1", f"--format={fmt}").strip()

    def update(self, src=None, *extra):
        return self.ws("update", "--from", str(src or self.src), "--apply", *extra)

    def test_commits_what_changed_onto_main_as_updated_yask_and_nothing_else(self):
        self.write("docs/context/mine.md", '---\nkind: canon\ndescription: "mine"\n---\nmy own unfinished work\n')
        before = self.last("%H")
        code, out, _ = self.update()
        self.assertEqual(code, 0, out)
        self.assertIn("committed onto main", out)
        self.assertNotEqual(self.last("%H"), before)
        self.assertEqual(self.last("%s"), "Updated YASK")
        self.assertIn(f"Ws-Update: {(TEMPLATE / '_steering/.yask/VERSION').read_text().strip()} -> 9.0.0", self.last("%B"))
        self.assertEqual(self.last("%an|%cn"), "ws update|ana")                     # the tool authored it, you committed it
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "HEAD").strip(), "main")
        files = self.git("show", "--name-only", "--format=", "HEAD").split()
        for f in ("_steering/.yask/VERSION", "_steering/.yask/playbooks/new-thing.md", "_steering/.yask/old-notes.md", "AGENTS.md",
                  "_steering/.ws/config.yaml", "_steering/.ws/update-notes.md"):
            self.assertIn(f, files)
        self.assertNotIn("docs/context/mine.md", files)                              # your own work is never swept in
        self.assertEqual(self.git("status", "--porcelain", "-uall").split(), ["??", "docs/context/mine.md"])

    def test_it_only_commits_onto_main(self):
        self.git("switch", "-q", "-c", "feature")
        before = self.last("%H")
        code, out, _ = self.update()
        self.assertEqual(code, 0)
        self.assertIn("NOT committed: you are on feature", out)
        self.assertEqual(self.last("%H"), before)
        self.assertEqual(self.read("_steering/.yask/VERSION").strip(), "9.0.0")      # the files are replaced, just left for you

    def test_your_uncommitted_work_in_the_touched_paths_stops_the_commit(self):
        with open(self.root / "AGENTS.md", "a") as f:
            f.write("\nA rule I was in the middle of adding.\n")
        before = self.last("%H")
        code, out, _ = self.update()
        self.assertIn("NOT committed: you had uncommitted changes in AGENTS.md", out)
        self.assertEqual(self.last("%H"), before)
        self.assertIn("A rule I was in the middle of adding.", self.read("AGENTS.md"))

    def test_commit_can_be_turned_off_and_does_not_stall_the_next_update(self):
        cfg = self.root / "_steering/.yask/yask.yaml"
        cfg.write_text(cfg.read_text().replace("commit: true", "commit: false"))
        self.git("add", "-A")
        self.git("commit", "-qm", "config")
        before = self.last("%H")
        self.assertIn("not committed", self.update()[1])
        self.assertEqual(self.last("%H"), before)
        self.assertIn("uncommitted changes", self.ws("update", "--from", str(self.src), "--apply")[2] or "uncommitted changes")
        self.git("add", "-A")
        self.git("commit", "-qm", "by hand")
        src2, _ = package(self.tmp, version="10.0.0", nested="o-r-def456/_steering/.yask", with_old=False)
        code, out, err = self.update(src2)
        self.assertEqual(code, 0, out + err)                                        # a committed update leaves the way clear
        self.assertEqual(self.read("_steering/.yask/VERSION").strip(), "10.0.0")

    def test_two_updates_in_a_row_each_get_their_commit(self):
        code, out, err = self.update()
        self.assertEqual(code, 0, out + err)
        src2, _ = package(self.tmp, version="10.0.0", nested="o-r-def456/_steering/.yask", with_old=False)
        code, out, err = self.update(src2)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.git("log", "--format=%s", "-2").split("\n")[:2], ["Updated YASK", "Updated YASK"])
        self.assertEqual(self.git("status", "--porcelain").strip(), "")

    def test_auto_update_commits_too_and_says_so_in_one_line(self):
        cfg = self.root / "_steering/.yask/yask.yaml"
        set_repo(cfg, "acme/yask")
        self.git("add", "-A")
        self.git("commit", "-qm", "repo")
        shutil.make_archive(str(Path(self.tmp) / "release"), "zip", self.src)
        blob = (Path(self.tmp) / "release.zip").read_bytes()
        os.environ["YASK_AUTOUPDATE"] = "1"
        rel = {"version": "9.0.0", "url": "https://example.invalid/y.zip", "sha_url": None}
        with mock.patch.object(update, "latest", return_value=rel), mock.patch.object(update, "http", return_value=blob):
            code, out, err = self.ws("modules")
        self.assertEqual(code, 0)
        self.assertIn("committed onto main (Updated YASK)", err)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertEqual(self.last("%s"), "Updated YASK")


class TestMerge(unittest.TestCase):
    def test_merge_keys_keeps_comments_values_and_flow_values(self):
        proj = "# mine\nnaming: { ignore: [x], allow: [] }   # keep\nthresholds:\n  a: 1   # one\n"
        tmpl = "naming: { ignore: [], allow: [] }\nthresholds:\n  a: 5\n  b: 2   # new\nextra:\n  k: v\n"
        out, added = update.merge_keys(proj, tmpl)
        self.assertEqual(added, ["extra", "thresholds.b"])
        self.assertIn("naming: { ignore: [x], allow: [] }   # keep", out)
        self.assertIn("  a: 1   # one", out)
        self.assertEqual(yamlsub.loads(out)["thresholds"], {"a": 1, "b": 2})

    def test_merge_entries_appends_only_missing_items(self):
        proj = "folders:\n  - { path: a, listed: false }\n"
        tmpl = "folders:\n  - { path: a, listed: true }\n  - { path: b, listed: false }\n"
        out, added = update.merge_entries(proj, tmpl, "path")
        self.assertEqual(added, ["b"])
        self.assertIn("{ path: a, listed: false }", out)
        self.assertEqual(update.merge_entries(out, tmpl, "path")[1], [])
        self.assertEqual(update.merge_entries("folders: []\n", tmpl, "path")[1], ["a", "b"])

    def test_versions_compare_numerically(self):
        self.assertTrue(update.vkey("0.10.0") > update.vkey("0.9.9"))
        self.assertTrue(update.vkey("v1.0") > update.vkey("0.99.99"))


class TestAutoUpdate(WsCase):
    def setUp(self):
        super().setUp()
        self.ws("modules")
        self.src, self.dst = package(self.tmp)
        z = Path(self.tmp) / "release"
        shutil.make_archive(str(z), "zip", self.src)
        self.blob = (Path(self.tmp) / "release.zip").read_bytes()
        os.environ["YASK_AUTOUPDATE"] = "1"
        os.environ.pop("CI", None)
        os.environ["WS_NOW"] = "20261115T0900Z"
        self.cfg = self.root / "_steering/.yask/yask.yaml"

    def configure(self, repo="acme/yask", auto=True, interval=24):
        set_repo(self.cfg, repo)
        t = self.cfg.read_text().replace("auto: true", f"auto: {str(auto).lower()}").replace("interval_hours: 24", f"interval_hours: {interval}")
        self.cfg.write_text(t)

    def patched(self, version="9.0.0"):
        rel = {"version": version, "url": "https://example.invalid/yask.zip", "sha_url": None}
        return mock.patch.object(update, "latest", return_value=rel), mock.patch.object(update, "http", return_value=self.blob)

    def test_nothing_happens_until_a_repo_is_set(self):
        set_repo(self.cfg, "")
        a, b = self.patched()
        with a as latest, b:
            self.assertEqual(self.ws("modules")[0], 0)
            self.assertEqual(latest.call_count, 0)
        self.assertNotEqual(self.read("_steering/.yask/VERSION").strip(), "9.0.0")

    def test_updates_silently_on_a_normal_command_once_a_repo_is_set(self):
        self.configure()
        a, b = self.patched()
        with a, b:
            code, out, err = self.ws("modules")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("_steering/.yask/VERSION").strip(), "9.0.0")
        self.assertIn("updated _steering/.yask", err)                           # one line, not a flood
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertIn("update notes", self.ws("start")[1])
        self.assertIn("brand_new_threshold", self.read("_steering/.ws/config.yaml"))

    def test_checks_are_throttled_and_failures_are_silent(self):
        self.configure(interval=24)
        a, b = self.patched(version="0.0.1")                                    # nothing newer
        with a as latest, b:
            self.ws("modules")
            self.ws("modules")
            self.assertEqual(latest.call_count, 1)                              # the second command did not ask again
        os.remove(self.root / "_steering/.ws/cache/update-check.json")
        with mock.patch.object(update, "latest", side_effect=OSError("offline")):
            code, out, err = self.ws("modules")
        self.assertEqual((code, err), (0, ""))                                  # a failed check never gets in the way
        self.assertIn("offline", json.loads((self.root / "_steering/.ws/cache/update-check.json").read_text())["error"])

    def test_update_settings_come_from_yask_yaml_and_not_from_config_yaml(self):
        self.assertNotIn("update:", self.read("_steering/.ws/config.yaml"))
        self.assertNotIn("update:", self.read("_steering/.yask/.ws/config.yaml"))
        self.assertEqual(update.settings(self.repo()), {"auto": True, "repo": "kazini/yask-spec-kit", "interval_hours": 24.0, "commit": True})
        self.configure(repo="acme/yask", auto=False, interval=6)
        self.assertEqual(update.settings(self.repo()), {"auto": False, "repo": "acme/yask", "interval_hours": 6.0, "commit": True})

    def test_without_yask_yaml_the_automatic_update_does_not_run(self):
        self.configure()
        self.cfg.unlink()
        self.assertFalse(update.settings(self.repo())["auto"])
        a, b = self.patched()
        with a as latest, b:
            self.assertEqual(self.ws("modules")[0], 0)
            self.assertEqual(latest.call_count, 0)
        self.assertFalse(self.cfg.exists())                                      # and nothing recreates it

    def test_off_switches(self):
        self.configure(auto=False)
        a, b = self.patched()
        with a as latest, b:
            self.ws("modules")
            self.assertEqual(latest.call_count, 0)
        self.cfg.write_text(self.cfg.read_text().replace("auto: false", "auto: true"))
        os.environ["CI"] = "1"
        with a as latest, b:
            self.ws("modules")
            self.assertEqual(latest.call_count, 0)

    def test_a_checksum_mismatch_refuses_the_package(self):
        self.configure()
        rel = {"version": "9.0.0", "url": "https://example.invalid/yask.zip", "sha_url": "https://example.invalid/yask.zip.sha256"}
        with mock.patch.object(update, "latest", return_value=rel), mock.patch.object(update, "http", side_effect=lambda u, *a, **k: b"0" * 64 + b"  yask.zip\n" if u.endswith("sha256") else self.blob):
            self.assertEqual(self.ws("modules")[2], "")
        self.assertNotEqual(self.read("_steering/.yask/VERSION").strip(), "9.0.0")

    def test_tool_code_changes_make_the_command_run_again_on_the_new_code(self):
        self.configure()
        (self.dst / "_toolstore/ws/README.md").write_text(self.read("_steering/.yask/_toolstore/ws/README.md") + "\nchanged\n")
        z = Path(self.tmp) / "release2"
        shutil.make_archive(str(z), "zip", self.src)
        blob = (Path(self.tmp) / "release2.zip").read_bytes()
        rel = {"version": "9.0.0", "url": "https://example.invalid/y.zip", "sha_url": None}
        with mock.patch.object(update, "latest", return_value=rel), mock.patch.object(update, "http", return_value=blob):
            self.assertTrue(update.auto_update(self.repo()))

    def repo(self):
        from wslib.repo import Repo
        return Repo(str(self.root))


if __name__ == "__main__":
    unittest.main()
