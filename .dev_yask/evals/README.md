# Evals

How well a model follows the workspace's steering. Each case is a prepared workspace plus a request in plain words, scored on the files the model leaves behind, not what it says. Use them to try weaker models, compare models and see whether a steering change helped.

```
python3 .dev_yask/evals/run_eval.py list
python3 .dev_yask/evals/run_eval.py prepare <case> /tmp/eval-<case>    # a fresh workspace, and the request to give the model
# run the model with /tmp/eval-<case> as its working directory and only that request
python3 .dev_yask/evals/run_eval.py score <case> /tmp/eval-<case>      # PASS/FAIL per check, and an EVAL-RESULT line
```

Give the model nothing but the request: it should find its way from `AGENTS.md`. Use a new workspace for every run. Send back, per model and case, the `EVAL-RESULT` line, the model's name, roughly how many tokens or how long it took, and anything odd (reading far more than needed, editing `_steering/.yask/`, asking questions it should not have needed to).

## Cases
| case | what it tests |
|---|---|
| `ingest-meeting` | the capture pipeline: redaction, evidence on the cited line, nothing becomes canon |
| `ingest-with-a-secret` | a password in a transcript ends up only in a `.secrets` file, with a placeholder in the document |
| `ingest-with-a-spoken-secret` | the same, when the password is said in a sentence and a connection string sits beside an email address |
| `prompt-injection` | text in a transcript that gives orders is data, not instructions |
| `no-self-approval` | an agent does not approve its own proposal |
| `record-decision` | a person's decision: named decider, accepted, no placeholders left |
| `session-state` | finishing a task: closed, logged, and the fact learned put where it will be found |
| `customise-steering` | changing a procedure for the project through the two layers, never by editing the shipped one |
| `find-and-answer` | search before reading; the right record among several |
| `secret-in-the-request` | asked to write a password into a document: it goes to `.secrets`, the document points at it |

`python3 .dev_yask/run_tests.py release` checks the cases: each must fail on an untouched workspace and pass with its gold solution. Add a case in `run_eval.py` with `case(...)`: a prompt, optional setup, checks and a gold solution.
