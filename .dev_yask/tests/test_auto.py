"""The automatic lifecycle: git created when missing, autosave, auto-sweep, healing a stopped merge, ws sync, approval from history, the yask launcher."""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from test_ws import TEMPLATE, WSDIR, WsCase, needs_git

sys.path.insert(0, str(TEMPLATE / ".dev_yask"))
import build_release  # noqa: E402

DOC = '---\nkind: canon\ndescription: "A doc."\n---\n# Doc\nline one\nline two\nline three\n'


def sh(root, user, *argv, git=False):
    env = dict(os.environ, WS_ROOT=str(root), WS_USER=user, YASK_AUTOUPDATE="0", WS_NOW="20261115T0900Z")
    env["YASK_LIFECYCLE"] = "1"
    cmd = ["git", *argv] if git else [sys.executable, str(WSDIR / "ws.py"), *argv]
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True, env=env)


class AutoCase(WsCase):
    def auto_on(self):
        os.environ["YASK_LIFECYCLE"] = "1"

    def config(self, **kv):
        self.ws("modules")
        p = self.root / "_steering/.ws/config.yaml"
        t = p.read_text()
        for k, v in kv.items():
            t = re.sub(rf"(?m)^(\s+){k}:.*$", rf"\g<1>{k}: {v}", t, 1)
        p.write_text(t)


@needs_git
class TestGitCreated(AutoCase):
    def test_git_is_created_with_a_baseline_commit_when_missing(self):
        self.auto_on()
        self.assertFalse((self.root / ".git").exists())
        code, out, err = self.ws("modules")
        self.assertEqual(code, 0)
        self.assertIn("created the git repository", err)
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "HEAD").strip(), "main")
        self.assertEqual(self.git("log", "--format=%s").strip(), "Initialized YASK workspace history")
        self.assertEqual(self.git("status", "--porcelain").strip(), "")
        self.assertTrue(self.git("config", "user.name").strip())                 # commits never fail for lack of an identity
        self.assertEqual(self.ws("modules")[2], "")                              # and it says nothing the second time

    def test_a_secret_is_held_back_but_everything_else_still_gets_its_history(self):
        self.auto_on()
        self.write("_workboard/leak.md", "---\nkind: working\ndescription: x\n---\npassword = hunter2hunter2\n")
        code, out, err = self.ws("modules")
        self.assertIn("held back 1 file(s)", err)
        tracked = self.git("ls-files").split()
        self.assertIn("AGENTS.md", tracked)
        self.assertNotIn("_workboard/leak.md", tracked)                          # the flagged file stays out of history


class TestAutosave(AutoCase):
    def setUp(self):
        super().setUp()
        self.config(autosave_minutes="0")
        self.init_git()
        self.auto_on()

    def snaps(self):
        return [x for x in self.git("for-each-ref", "--format=%(refname)", "refs/yask/autosave/").split() if x]

    def test_uncommitted_work_is_snapshotted_outside_the_branch_silently(self):
        head = self.git("rev-parse", "HEAD").strip()
        self.write("docs/context/new.md", DOC)
        code, out, err = self.ws("status")
        self.assertEqual(err, "")                                                   # nothing to say about a routine snapshot
        self.assertEqual(len(self.snaps()), 1)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), head)               # history is untouched
        self.assertEqual(self.git("log", "--format=%s", "--branches").strip().count("Autosave"), 0)
        self.assertIn("docs/context/new.md", self.git("status", "--porcelain", "-uall"))   # the working tree is untouched too

    def test_staged_work_is_left_alone_and_a_commit_clears_the_snapshots(self):
        self.write("docs/context/a.md", DOC)
        self.git("add", "docs/context/a.md")
        self.ws("status")
        self.assertEqual(len(self.snaps()), 1)                                      # staged work no longer blocks it
        self.assertIn("A  docs/context/a.md", self.git("status", "--porcelain"))    # and it is still staged
        self.git("commit", "-qm", "docs: a")                                         # a manual commit made by plain git
        self.ws("status")
        self.assertEqual(self.snaps(), [])

    def test_only_the_last_few_are_kept_and_the_ones_that_differ_most_survive(self):
        self.config(autosave_keep="3")
        for i, body in enumerate(["a\n", "a\nb\n", "a\nb\nc\n", "totally\ndifferent\ntext\nnow\nhere\n", "totally\ndifferent\ntext\nnow\nhere\nand more\n"]):
            self.write("docs/context/n.md", DOC + body)
            self.ws("status")
        self.assertEqual(len(self.snaps()), 3)
        texts = [self.git("show", f"{r}:docs/context/n.md") for r in self.snaps()]
        self.assertTrue(any("and more" in t for t in texts))                         # the newest is always kept
        self.assertTrue(any("totally" in t for t in texts))                          # the big jump survives
        self.assertTrue(any("totally" not in t for t in texts))                      # and so does an earlier, different state: they are not all copies of each other
        self.assertFalse(any(t.endswith("DOC") for t in texts))
        self.assertEqual(len(set(texts)), 3)                                         # three distinct snapshots, not three near-duplicates

    @needs_git
    def test_secrets_stay_out_of_snapshots_and_say_so_once(self):
        self.write("docs/context/ok.md", DOC)
        self.write("docs/context/s.md", DOC + "password = hunter2hunter2\n")
        err = self.ws("status")[2]
        self.assertIn("autosave leaves out 1 file(s)", err)
        snap = self.snaps()[0]
        self.assertIn("docs/context/ok.md", self.git("ls-tree", "-r", "--name-only", snap))
        self.assertNotIn("docs/context/s.md", self.git("ls-tree", "-r", "--name-only", snap))
        self.assertEqual(self.ws("status")[2], "")

    def test_recent_snapshot_postpones_and_autosave_can_be_off(self):
        self.config(autosave_minutes="30")
        self.write("docs/context/a.md", DOC)
        self.ws("status")
        self.write("docs/context/b.md", DOC)
        self.ws("status")
        self.assertEqual(len(self.snaps()), 1)
        self.config(autosave_minutes="0", autosave="false")
        self.write("docs/context/c.md", DOC)
        self.ws("status")
        self.assertEqual(len(self.snaps()), 1)

    @needs_git
    def test_restore_lists_and_brings_a_file_back(self):
        self.write("docs/context/a.md", DOC)
        self.ws("status")
        os.remove(self.root / "docs/context/a.md")                                   # the work is lost...
        out = self.ws("restore")[1]
        self.assertIn("1  ", out)
        self.assertIn("docs/context/a.md", out)
        self.assertIn("add --apply", self.ws("restore", "docs/context/a.md")[1])
        self.assertFalse((self.root / "docs/context/a.md").exists())                 # a dry run changes nothing
        self.assertIn("restored", self.ws("restore", "docs/context/a.md", "--apply")[1])
        self.assertIn("line one", self.read("docs/context/a.md"))                    # ...and comes back
        self.assertEqual(self.ws("restore", "docs/context/zzz.md")[0], 2)


class TestAutoSweep(AutoCase):
    @needs_git
    def test_finished_tasks_that_were_left_behind_close_themselves(self):
        t = self.ws("task", "add", "wire it")[1].split("{#")[1][:6]
        self.ws("log", "add", f"done {t}", "--type", "FINISHED", "--task", t)
        self.assertIn(t, self.read("tasks.md"))
        self.auto_on()
        code, out, err = self.ws("status")
        self.assertNotIn(t, self.read("tasks.md"))
        self.assertIn("closed or parked 1 leftover", err)


class TestSync(AutoCase):
    """Two people with their own copies and a common remote."""

    def setUp(self):
        super().setUp()
        (self.root / ".gitattributes").write_text("* text=auto\n")                 # no union driver: let the conflicts happen
        self.write("docs/context/x.md", DOC)
        self.init_git()
        self.remote = Path(self.tmp) / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.remote)], check=True)
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-q", "-u", "origin", "main")
        self.b = Path(self.tmp) / "bob"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.b)], check=True)
        sh(self.b, "bob", "config", "user.name", "bob", git=True)
        sh(self.b, "bob", "config", "user.email", "b@x", git=True)

    @needs_git
    def test_sync_without_a_remote_explains(self):
        self.git("remote", "remove", "origin")
        code, _, err = self.ws("sync")
        self.assertEqual(code, 2)
        self.assertIn("no remote", err)

    @needs_git
    def test_conflicting_changes_are_settled_by_rule_and_pushed(self):
        # ana changes the document and adds a task, pushes
        self.write("docs/context/x.md", DOC.replace("line two", "line two by ana"))
        self.ws("task", "add", "ana's task", "--for", "@ana")
        self.assertEqual(self.ws("sync")[0], 0)
        # bob changes the same line differently and adds a task in the same place
        (self.b / "docs/context/x.md").write_text(DOC.replace("line two", "line two by bob"))
        r = sh(self.b, "bob", "task", "add", "bob's task", "--for", "@bob")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = sh(self.b, "bob", "sync")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = (self.b / "tasks.md").read_text()
        self.assertIn("ana's task", text)
        self.assertIn("bob's task", text)                                          # both tasks survive
        self.assertNotIn("<<<<<<<", text)
        doc = (self.b / "docs/context/x.md").read_text()
        self.assertIn("line two by ana", doc)                                      # the shared version stays
        self.assertNotIn("<<<<<<<", doc)
        kept = list((self.b / "_workboard/conflicts").glob("*.txt"))
        self.assertEqual(len(kept), 1)
        self.assertIn("line two by bob", kept[0].read_text())                      # bob's copy is set aside
        self.assertIn("Conflict in docs/context/x.md", (self.b / "_workboard/open-items.md").read_text())
        self.assertEqual(sh(self.b, "bob", "check").returncode in (0, 1), True)
        # and it was pushed: ana's next sync brings bob's work in without trouble
        self.assertEqual(sh(self.b, "bob", "log", "--oneline", "-3", git=True).returncode, 0)
        self.assertEqual(self.ws("sync")[0], 0)
        self.assertIn("bob's task", self.read("tasks.md"))

    @needs_git
    def test_a_merge_stopped_by_plain_git_is_finished_by_the_next_ws_command(self):
        self.write("docs/context/x.md", DOC.replace("line two", "line two by ana"))
        self.ws("task", "add", "ana's task", "--for", "@ana")
        self.ws("sync")
        (self.b / "docs/context/x.md").write_text(DOC.replace("line two", "line two by bob"))
        sh(self.b, "bob", "task", "add", "bob's task", "--for", "@bob")
        sh(self.b, "bob", "add", "-A", git=True)
        sh(self.b, "bob", "commit", "-qm", "bob work", git=True)
        sh(self.b, "bob", "pull", "--no-rebase", "--no-edit", "-q", git=True)    # plain git stops on the conflicts
        self.assertTrue(sh(self.b, "bob", "diff", "--name-only", "--diff-filter=U", git=True).stdout.strip())
        r = sh(self.b, "bob", "status")                                              # any ws command finishes it
        self.assertIn("healed a merge", r.stderr)
        self.assertEqual(sh(self.b, "bob", "diff", "--name-only", "--diff-filter=U", git=True).stdout.strip(), "")
        self.assertIn("ana's task", (self.b / "tasks.md").read_text())
        self.assertIn("bob's task", (self.b / "tasks.md").read_text())


class TestApprove(AutoCase):
    def setUp(self):
        super().setUp()
        self.init_git()

    def agent_writes(self, text=DOC):
        self.write("docs/context/x.md", text)
        self.assertEqual(self.ws("save", "docs", "-m", "docs: x", "--agent", "--apply")[0], 0)

    @needs_git
    def test_an_agents_change_waits_and_a_persons_own_commit_clears_it(self):
        self.agent_writes()
        self.assertIn("docs/context/x.md", self.ws("approve")[1])
        self.assertIn("1 change(s)", self.ws("start")[1])
        self.write("docs/context/x.md", DOC.replace("line two", "line two, edited by ana"))
        self.ws("save", "docs", "-m", "docs: x edited", "--apply")                 # no flag, no label: committing it is reading it
        self.assertIn("nothing waits", self.ws("approve")[1])

    @needs_git
    def test_approve_records_a_review_in_your_log_and_only_for_that_content(self):
        self.agent_writes()
        self.assertEqual(self.ws("approve", "--agent", "--all")[0], 2)             # a person approves
        self.assertIn("recorded your review of 1", self.ws("approve", "docs/context/x.md")[1])
        self.assertIn("REVIEWED", "".join(p.read_text() for p in (self.root / "_workboard/people/ana/log").glob("*.md")))
        self.assertIn("nothing waits", self.ws("approve")[1])
        self.agent_writes(DOC + "more\n")                                          # new content: waits again
        self.assertIn("docs/context/x.md", self.ws("approve")[1])

    @needs_git
    def test_review_mode_off_and_all(self):
        self.agent_writes()
        self.config(review="off")
        self.assertIn("nothing waits", self.ws("approve")[1])
        self.config(review="all")
        self.write("docs/context/y.md", DOC)
        self.ws("save", "docs", "-m", "docs: y", "--apply")                        # a person's own change, but nobody else read it
        self.assertIn("docs/context/y.md", self.ws("approve")[1])
        self.ws("approve", "docs/context/y.md")                                    # approving your own change does not count in mode all
        self.assertIn("docs/context/y.md", self.ws("approve")[1])


class TestLaunchers(WsCase):
    def test_a_python_older_than_the_minimum_is_told_so_plainly(self):
        code = "import sys; sys.version_info = (3, 7, 9, 'final', 0); sys.argv = ['ws.py', '--version']; exec(open(sys.argv_path).read())"
        r = subprocess.run([sys.executable, "-c", code.replace("sys.argv_path", repr(str(WSDIR / "ws.py")))], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("needs Python 3.8 or newer", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    @needs_git
    def test_in_a_git_checkout_the_launchers_are_tracked_executable(self):
        """A clone on Linux or macOS gets its modes from the index, and a Windows checkout cannot show them, so ask git."""
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=TEMPLATE, capture_output=True, text=True).stdout.strip()
        if not top or Path(top).resolve() != TEMPLATE.resolve():
            self.skipTest("the workspace is not the root of a git checkout")
        want = ["ws"] + ["_steering/.yask/" + r for r in build_release.RUNNABLE]
        out = subprocess.run(["git", "ls-files", "-s", "--", *want], cwd=TEMPLATE, capture_output=True, text=True).stdout
        tracked = {line.split("\t")[1]: line.split()[0] for line in out.splitlines()}
        if not tracked:
            self.skipTest("no launcher is committed yet")
        wrong = sorted(n for n, mode in tracked.items() if mode != "100755")
        self.assertEqual(wrong, [], "tracked without the executable bit; fix with: git update-index --chmod=+x " + " ".join(wrong))

    def test_yask_is_the_same_tool_as_ws_on_linux_and_windows(self):
        if shutil.which("sh") is None:
            self.skipTest("sh is not on the PATH")
        shims = TEMPLATE / "_steering/.yask/_toolstore"
        for d in ("_shims", "ws"):
            for name in ("ws", "yask"):
                sh_ = shims / d / name
                self.assertIn(f"WS_PROG={name}", sh_.read_text())
                self.assertNotIn(b"\r", sh_.read_bytes())                           # LF for sh
                cmd = (shims / d / f"{name}.cmd").read_bytes()
                self.assertIn(b"\r\n", cmd)                                         # CRLF for cmd.exe
                self.assertEqual(cmd.count(b"\n"), cmd.count(b"\r\n"))
                self.assertIn(b"WS_PYTHON", cmd)                                    # explicit override wins
                self.assertIn(b'python "%~dp0', cmd)
                self.assertIn(b'py -3 "%~dp0', cmd)
                self.assertLess(cmd.index(b'python "%~dp0'), cmd.index(b'py -3 "%~dp0'))  # python first; py -3 is a fallback
        env = dict(os.environ, WS_ROOT=str(self.root))
        outs = {n: subprocess.run(["sh", str(shims / "_shims" / n), "--version"], capture_output=True, text=True, env=env).stdout.split() for n in ("ws", "yask")}
        self.assertEqual(outs["ws"][1], outs["yask"][1])
        self.assertEqual((outs["ws"][0], outs["yask"][0]), ("ws", "yask"))
        r = subprocess.run(["sh", str(shims / "_shims" / "yask"), "check"], capture_output=True, text=True, env=dict(env, WS_NO_AUTO="1", YASK_AUTOUPDATE="0"))
        self.assertIn("0 error(s)", r.stdout)


if __name__ == "__main__":
    import unittest
    unittest.main()
