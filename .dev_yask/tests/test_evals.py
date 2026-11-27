"""The eval cases are themselves checked: each fails untouched and passes with its gold solution."""
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "evals"))
import run_eval  # noqa: E402


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class TestEvalCases(unittest.TestCase):
    def test_every_case_fails_untouched_and_passes_with_its_gold_solution(self):
        for cid in run_eval.CASES:
            with self.subTest(case=cid):
                import tempfile
                with tempfile.TemporaryDirectory() as tmp:
                    d = Path(tmp) / "w"
                    run_eval.prepare(cid, d)
                    self.assertFalse(run_eval.score(cid, d)["all"], "an untouched workspace must not pass")
                    run_eval.CASES[cid]["gold"](d)
                    res = run_eval.score(cid, d)
                    self.assertTrue(res["all"], [r for r in res["checks"] if not r["pass"]])


if __name__ == "__main__":
    unittest.main()
