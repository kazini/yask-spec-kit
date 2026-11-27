"""Secrets: moved to .secrets with placeholders, used without being in context, created by agents."""
import os
import re
import subprocess
import sys
from pathlib import Path

from test_ws import WsCase, needs_git

TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
DOC = '---\nkind: canon\ndescription: "api"\n---\n# API\n{}\n'


class SecretsCase(WsCase):
    def setUp(self):
        super().setUp()
        self.init_git()

    def doc(self, rel, line):
        self.write(rel, DOC.format(line))

    def secrets_file(self, folder):
        return (self.root / folder / ".secrets").read_text() if (self.root / folder / ".secrets").exists() else ""


class TestMovingSecrets(SecretsCase):
    @needs_git
    def test_a_certain_secret_moves_on_save_and_never_reaches_git(self):
        self.doc("docs/context/api.md", f"token = {TOKEN}")
        self.assertEqual(self.ws("save", "docs", "-m", "docs: api", "--apply")[0], 0)
        text = self.read("docs/context/api.md")
        self.assertNotIn(TOKEN, text)
        key = re.search(r"\{\{secret:(GITHUB_TOKEN_[0-9A-F]{4})\}\}", text).group(1)
        self.assertIn(f"{key}={TOKEN}", self.secrets_file("docs/context"))
        self.assertEqual(self.git("grep", "-c", TOKEN, "HEAD").strip(), "")              # not in the committed tree
        self.assertNotIn(".secrets", self.git("ls-files"))
        self.assertEqual(subprocess.run(["git", "check-ignore", "-q", "docs/context/.secrets"], cwd=self.root).returncode, 0)
        self.assertEqual(self.ws("check")[0], 0)                                        # a placeholder is not a secret

    @needs_git
    def test_an_unsure_one_is_left_for_the_agent_to_decide(self):
        self.doc("docs/context/p.md", "password = hunter2hunter2")
        code, out, err = self.ws("save", "docs", "-m", "docs: p", "--apply")
        self.assertEqual(code, 2)
        self.assertIn("ws secret move docs/context/p.md:6", out + err)
        self.assertIn("hunter2hunter2", self.read("docs/context/p.md"))                 # nothing was rewritten behind its back
        self.assertEqual(self.ws("secret", "move", "docs/context/p.md:6")[0], 0)
        self.assertNotIn("hunter2hunter2", self.read("docs/context/p.md"))
        self.assertIn("hunter2hunter2", self.secrets_file("docs/context"))
        self.assertEqual(self.ws("save", "docs", "-m", "docs: p", "--apply")[0], 0)

    def test_or_it_is_not_a_secret_and_is_allowed_without_touching_the_file(self):
        self.doc("docs/context/s.md", "password = example-sample-value")
        before = self.read("docs/context/s.md")
        self.assertEqual(self.ws("check")[0], 2)
        self.assertEqual(self.ws("secret", "allow", "docs/context/s.md:6")[0], 0)
        self.assertEqual(self.read("docs/context/s.md"), before)
        self.assertEqual(self.ws("check")[0], 0)
        self.assertEqual(self.ws("secret", "move", "docs/context/s.md:1")[0], 2)         # a line with nothing to move says so

    def test_autosave_moves_certain_secrets_before_it_snapshots(self):
        os.environ["YASK_LIFECYCLE"] = "1"
        self.doc("docs/context/a.md", f"key = {TOKEN}")
        self.ws("status")
        snap = self.git("for-each-ref", "--format=%(refname)", "refs/yask/autosave/").split()[0]
        self.assertNotIn(TOKEN, self.git("show", f"{snap}:docs/context/a.md"))
        self.assertIn(TOKEN, self.secrets_file("docs/context"))

    def test_ingest_moves_secrets_instead_of_refusing(self):
        src = Path(self.tmp) / "call.vtt"
        src.write_text(f"WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nTom: the staging password = Zq81xkLmn92Yt and the token {TOKEN}\n")
        code, out, err = self.ws("ingest", str(src), "--title", "Call", "--apply")
        self.assertEqual(code, 0, out + err)
        meet = next(p for p in (self.root / "_workboard/meetings").iterdir() if p.is_dir())
        t = (meet / "transcript.md").read_text()
        self.assertNotIn("Zq81xkLmn92Yt", t)
        self.assertNotIn(TOKEN, t)
        self.assertEqual(t.count("{{secret:"), 2)
        self.assertIn("Zq81xkLmn92Yt", (meet / ".secrets").read_text())
        self.assertIn("Zq81xkLmn92Yt", src.read_text())                                  # the source is never rewritten
        self.assertEqual(self.ws("check")[0], 0)


class TestSpokenSecrets(SecretsCase):
    """A secret written as a sentence, not as `key = value`."""
    CONN = "postgres://app:s3cr3tpw@db.internal:5432/prod"

    def ingest(self, text):
        src = Path(self.tmp) / "call.txt"
        src.write_text(text)
        code, out, err = self.ws("ingest", str(src), "--title", "Call", "--apply")
        self.assertEqual(code, 0, out + err)
        meet = next(p for p in (self.root / "_workboard/meetings").iterdir() if p.is_dir())
        return meet, (meet / "transcript.md").read_text(), out

    def test_a_password_in_a_sentence_is_found_and_the_full_stop_is_not_part_of_it(self):
        self.doc("docs/context/s.md", "The staging DB password is Hunter2Hunter2. Keep it safe.")
        code, out, _ = self.ws("check")
        self.assertEqual(code, 2)
        self.assertIn("docs/context/s.md:6", out)
        self.assertEqual(self.ws("secret", "move", "docs/context/s.md:6")[0], 0)
        self.assertNotIn("Hunter2Hunter2", self.read("docs/context/s.md"))
        self.assertIn("{{secret:PASSWORD_", self.read("docs/context/s.md") )
        self.assertIn(". Keep it safe.", self.read("docs/context/s.md"))                 # the sentence is intact
        vals = self.secrets_file("docs/context")
        self.assertIn("=Hunter2Hunter2\n", vals)                                         # no stray period in the stored value

    def test_other_ways_to_say_it(self):
        for n, line in enumerate(('password for the vpn is "Zq81xkLmn92Yt"', "my passphrase: correct-Horse-9", "the api key is hunterTwoThree"), 1):
            self.doc(f"docs/context/w{n}.md", line)
            self.assertEqual(self.ws("check")[0], 2, line)
            self.assertEqual(self.ws("secret", "move", f"docs/context/w{n}.md:6")[0], 0, line)

    def test_sentences_that_only_mention_the_word_are_not_flagged(self):
        self.doc("docs/context/ok.md", "The token is expired. The password is required for login. The secret is in the vault.\nThe pin is set and the api key is rotated.")
        self.assertEqual(self.ws("check")[0], 0)

    def test_ingest_moves_a_spoken_password_and_keeps_the_sentence(self):
        meet, t, _ = self.ingest("Tom: the staging DB password is Hunter2Hunter2. Please keep it safe.\n")
        self.assertNotIn("Hunter2Hunter2", t)
        self.assertRegex(t, r"password is \{\{secret:PASSWORD_[0-9A-F]{4}\}\}\. Please")
        self.assertIn("=Hunter2Hunter2\n", (meet / ".secrets").read_text())
        self.assertEqual(self.ws("check")[0], 0)

    def test_ingest_keeps_a_connection_string_whole_instead_of_redacting_it_as_an_email(self):
        meet, t, _ = self.ingest(f"Tom: connect with {self.CONN} and mail tom@clientco.com\n")
        self.assertNotIn("s3cr3tpw", t)
        self.assertNotIn("REDACTED:email]:5432", t)                                      # the rule for emails did not eat the URL
        self.assertRegex(t, r"\{\{secret:CONNECTION_STRING_[0-9A-F]{4}\}\}")
        self.assertIn(self.CONN, (meet / ".secrets").read_text())                        # the whole value is kept, not lost
        self.assertIn("[REDACTED:email]", t)                                             # a real address still is redacted

    def test_ingest_does_not_move_a_card_number_and_says_what_is_left_to_decide(self):
        meet, t, out = self.ingest("Tom: the test card is 4111 1111 1111 1111 for now.\n")
        self.assertIn("4111 1111 1111 1111", t)
        self.assertFalse((meet / ".secrets").exists())
        self.assertIn("payment-card", out)
        self.assertIn("ws secret move", out)
        self.assertEqual(self.ws("check")[0], 2)                                         # ws check reports it until someone decides

    def test_a_dry_run_of_ingest_stores_nothing(self):
        src = Path(self.tmp) / "call.txt"
        src.write_text("Tom: the staging DB password is Hunter2Hunter2.\n")
        code, out, _ = self.ws("ingest", str(src), "--title", "Call")
        self.assertEqual(code, 0)
        self.assertIn("1 secret(s)", out)
        self.assertNotIn("Hunter2Hunter2", out)
        self.assertFalse((self.root / "_workboard/meetings").exists() and any((self.root / "_workboard/meetings").rglob(".secrets")))


class TestUsingSecrets(SecretsCase):
    def setUp(self):
        super().setUp()
        self.doc("docs/context/api.md", f"token = {TOKEN}")
        self.ws("save", "docs", "-m", "docs: api", "--apply")
        self.key = re.search(r"\{\{secret:([A-Z0-9_]+)\}\}", self.read("docs/context/api.md")).group(1)

    @needs_git
    def test_list_shows_keys_never_values_and_get_prints_one(self):
        out = self.ws("secret", "list", "--from", "docs/context")[1]
        self.assertIn(self.key, out)
        self.assertNotIn(TOKEN, out)
        self.assertEqual(self.ws("secret", "get", self.key, "--from", "docs/context")[1].strip(), TOKEN)
        self.assertEqual(self.ws("secret", "get", "NOPE", "--from", "docs/context")[0], 2)

    @needs_git
    def test_run_gives_a_command_the_secret_and_hides_it_from_the_output(self):
        os.environ["YASK_LIFECYCLE"] = "1"      # as it really runs: the automatic steps must cope with this command too
        code, out, err = self.ws("secret", "run", "--from", "docs/context", "--", sys.executable, "-c", f"import os; print(os.environ['{self.key}']); raise SystemExit(3)")
        self.assertEqual(code, 3)                                                       # the command's own exit code
        self.assertNotIn(TOKEN, out + err)
        self.assertIn("{{secret}}", out)

    @needs_git
    def test_expand_is_the_explicit_way_to_see_a_file_with_its_values(self):
        out = self.ws("secret", "expand", "docs/context/api.md")[1]
        self.assertIn(f"token = {TOKEN}", out)
        self.assertIn("{{secret:", self.read("docs/context/api.md"))                     # the file itself is unchanged

    def set_agent_read(self, value):
        cfg = self.root / "_steering/.ws/config.yaml"
        cfg.write_text(re.sub(r"(?m)^(\s*agent_read:)\s*\S+", rf"\g<1> {value}", cfg.read_text()))

    def agent(self, sub, *rest):
        """The command as an agent runs it (--agent), from the folder the secret lives in."""
        return self.ws("secret", sub, *rest, "--agent") if sub == "expand" else self.ws("secret", sub, *rest, "--agent", "--from", "docs/context")

    @needs_git
    def test_by_default_an_agent_may_run_with_secrets_but_not_print_them(self):
        self.assertRegex(self.read("_steering/.ws/config.yaml"), r"(?m)^\s*agent_read: run\b")
        for sub, arg in (("get", self.key), ("expand", "docs/context/api.md")):
            code, out, err = self.agent(sub, arg)
            self.assertEqual(code, 2)
            self.assertIn("agent_read", err)
            self.assertIn("run", err)                                                   # it says what the agent may do instead
            self.assertNotIn(TOKEN, out + err)
        code, out, err = self.ws("secret", "run", "--agent", "--from", "docs/context", "--", sys.executable, "-c", f"import os; print(os.environ['{self.key}'])")
        self.assertEqual(code, 0, err)
        self.assertNotIn(TOKEN, out + err)
        self.assertIn("{{secret}}", out)

    @needs_git
    def test_a_person_is_never_limited_by_agent_read(self):
        for value in ("run", "false"):
            self.set_agent_read(value)
            self.assertEqual(self.ws("secret", "get", self.key, "--from", "docs/context")[1].strip(), TOKEN)
            self.assertIn(TOKEN, self.ws("secret", "expand", "docs/context/api.md")[1])

    @needs_git
    def test_a_person_can_allow_agents_to_print_secrets(self):
        self.set_agent_read("true")
        self.assertEqual(self.agent("get", self.key)[1].strip(), TOKEN)
        self.assertIn(TOKEN, self.agent("expand", "docs/context/api.md")[1])

    @needs_git
    def test_an_unknown_value_is_read_as_the_safe_default(self):
        self.set_agent_read("ture")                                                     # a typo must not open anything up
        self.assertEqual(self.agent("get", self.key)[0], 2)
        self.assertEqual(self.ws("secret", "run", "--agent", "--from", "docs/context", "--", sys.executable, "-c", "pass")[0], 0)

    @needs_git
    def test_a_person_can_switch_agent_access_off(self):
        self.set_agent_read("false")
        for sub, arg in (("get", self.key), ("expand", "docs/context/api.md")):
            code, _, err = self.agent(sub, arg)
            self.assertEqual(code, 2)
            self.assertIn("agent_read", err)
        code, _, err = self.ws("secret", "run", "--agent", "--from", "docs/context", "--", sys.executable, "-c", "pass")
        self.assertEqual(code, 2)                                                       # false refuses run as well
        self.assertIn("agent_read", err)
        self.assertEqual(self.ws("secret", "get", self.key, "--from", "docs/context")[0], 0)   # a person still can


class TestRedactionPatterns(SecretsCase):
    JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    CONN = "postgres://app:s3cr3tpw@db.internal:5432/prod"

    @needs_git
    def test_a_jwt_and_a_connection_string_move_to_secrets_on_save(self):
        self.doc("docs/context/c.md", f"session {self.JWT}\ndatabase {self.CONN}")
        self.assertEqual(self.ws("save", "docs", "-m", "docs: c", "--apply")[0], 0)
        text = self.read("docs/context/c.md")
        for value in (self.JWT, self.CONN, "s3cr3tpw"):
            self.assertNotIn(value, text)
            self.assertNotIn(value, self.git("show", "HEAD:docs/context/c.md"))
        self.assertRegex(text, r"\{\{secret:JWT_[0-9A-F]{4}\}\}")
        self.assertRegex(text, r"\{\{secret:CONNECTION_STRING_[0-9A-F]{4}\}\}")
        self.assertIn(self.CONN, self.secrets_file("docs/context"))
        self.assertEqual(self.ws("check")[0], 0)

    @needs_git
    def test_a_card_or_an_iban_is_left_for_the_agent_to_decide(self):
        for rel, line, name in (("card", "pays with 4111 1111 1111 1111", "payment-card"), ("iban", "account DE89 3704 0044 0532 0130 00", "iban")):
            self.doc(f"docs/context/{rel}.md", line)
            before = self.read(f"docs/context/{rel}.md")
            code, out, err = self.ws("save", "docs", "-m", f"docs: {rel}", "--apply")
            self.assertEqual(code, 2, out + err)
            self.assertIn(name, out + err)
            self.assertIn(f"ws secret move docs/context/{rel}.md:6", out + err)
            self.assertEqual(self.read(f"docs/context/{rel}.md"), before)                # nothing is rewritten behind its back
            self.assertEqual(self.ws("secret", "move", f"docs/context/{rel}.md:6")[0], 0)
            self.assertIn("{{secret:", self.read(f"docs/context/{rel}.md"))
            self.assertEqual(self.ws("save", "docs", "-m", f"docs: {rel}", "--apply")[0], 0)

    def test_ordinary_numbers_ids_and_urls_are_not_flagged(self):
        self.doc("docs/context/ok.md", "build 2026-11-26-143012 grew +5% on v1.2.3, see http://localhost:3000/x and ssh://git@github.com:org/r.git, ticket AB12 is open")
        self.assertEqual(self.ws("check")[0], 0)


class TestMakingSecrets(SecretsCase):
    def test_generate_stores_a_random_permanent_secret_and_never_shows_it(self):
        code, out, err = self.ws("secret", "set", "SVC_DB_PASSWORD", "--generate", "--agent")
        self.assertEqual(code, 0, err)
        stored = re.search(r"(?m)^SVC_DB_PASSWORD=(\S+)$", self.secrets_file(""))
        self.assertGreaterEqual(len(stored.group(1)), 32)
        self.assertNotIn(stored.group(1), out + err)
        self.ws("secret", "set", "SVC_OTHER", "--generate", "--agent")
        self.assertNotEqual(stored.group(1), re.search(r"(?m)^SVC_OTHER=(\S+)$", self.secrets_file("")).group(1))

    def test_an_agent_supplies_a_value_only_if_it_expires(self):
        code, _, err = self.ws("secret", "set", "GIVEN", "--value", "abc12345", "--agent")
        self.assertEqual(code, 2)
        self.assertIn("--temp", err)
        self.assertEqual(self.ws("secret", "set", "GIVEN", "--value", "abc12345", "--temp", "1", "--agent")[0], 0)
        self.assertIn("GIVEN=abc12345", self.secrets_file(""))
        self.ws("secret", "set", "KEPT", "--generate", "--agent")
        os.environ["WS_NOW"] = "20261115T1100Z"                                           # two hours later
        out = self.ws("secret", "list")[1]
        self.assertNotIn("GIVEN", out)                                                    # expired and gone
        self.assertIn("KEPT", out)                                                        # a generated one stays
        self.assertNotIn("abc12345", self.secrets_file(""))

    def test_keys_are_upper_snake_case_and_a_tracked_secrets_file_is_an_error(self):
        self.assertEqual(self.ws("secret", "set", "bad-key", "--generate")[0], 2)
        self.ws("secret", "set", "OK_KEY", "--generate")
        self.git("add", "-f", ".secrets")
        code, out, _ = self.ws("check")
        self.assertEqual(code, 2)
        self.assertIn("a .secrets file is in git", out)


if __name__ == "__main__":
    import unittest
    unittest.main()
