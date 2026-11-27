---
kind: steering
module: evals
use_when: "Test how well agents use this workspace, or re-test after changing rules or playbooks: eval cases, benchmark, regression, score"
description: "Run the workspace's test cases in fresh sessions, record results, and fix causes instead of editing cases."
---
# Run evals

Cases live in `docs/evals/` (scaffold it first, see `scaffold.md`); each follows `_steering/.yask/templates/eval-case.md`.
1. For each case, start a fresh session with the model and tool under test. Try at least one strong and one weak model: weaker models skip gates and overclaim first.
2. Give the case's prompt only. Do not hint at the expected answer.
3. Record, per case: pass or fail for each criterion, the sources the agent cited, whether it read anything it should not have (for example a whole transcript), and token use if measurable.
4. Write the results to `_steering/.ws/reports/evals-<UTC stamp>.md` (generated, ignored by git).
5. On a failure, find the cause: unclear rule in `AGENTS.md` or a playbook, the model, the tool, or missing tooling. Fix the cause. Never edit a case to make it pass; a changed case is a new version and a human decision.
6. Re-run after any change to `AGENTS.md`, a playbook or a module. Keep the set small and sharp (start with 5 to 10 cases).
