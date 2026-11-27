---
kind: steering
module: core
use_when: "A password, token, key or credential is needed, found in a file, email, chat message or request, or must be created: use it without its value ever being in context or in a file; API key, .env, private key, login, connection string, leaked secret"
description: "Use, find and create secrets safely. They live in .secrets files; documents hold placeholders."
---
# Handle secrets

You may use secrets. The value never goes in a file, a log, a commit message or your context: it stays in a `.secrets` file (git ignores it) and the document holds `{{secret:KEY}}`.

1. **Use one.** `ws secret run [--from <folder>] -- sh -c 'curl -H "Authorization: Bearer $KEY" <url>'`. The secrets from that folder up to the root are in the command's environment, and are hidden from its output. `ws secret list` shows the keys and where each came from. `ws secret get KEY` prints one and `ws secret expand <file>` prints a file with the values filled in; both are for a person, and an agent is refused unless `secrets.agent_read` is `true`.
2. **A secret `ws` found.** It was moved already: the file has a placeholder, the value is in the `.secrets` beside it. Nothing to do.
3. **A secret `ws` is not sure about** (`ws check` or `ws save` says "may be a secret"): decide. It is one: `ws secret move <path>:<line>`. It is not (a sample, an id, a test value): `ws secret allow <path>:<line>`.
4. **A new secret you need** (a password for a service you set up, an API key you create): `ws secret set NAME --generate`. It is random, written to `.secrets`, and never shown. Use it with step 1.
5. **A secret someone gives you in a request** and you need only now: `printf %s "$VALUE" | ws secret set NAME --temp` (expires after `secrets.temp_hours`). Do not write it anywhere else.
6. **Never** copy a value out of `.secrets`, commit `.secrets` (`ws check` errors if it is tracked), or put a value in a prompt. Secrets leave the machine only if a person arranges it.

`secrets.agent_read` sets what an agent may do: `run` (the default) allows step 1's `run` and refuses `get` and `expand`; `false` refuses all of `ws secret` with `--agent`; `true` allows everything. When `ws` refuses, ask the person. `run` hides the literal value from the output but cannot stop a command from re-encoding it, so for anything sensitive keep the command simple and set `false`.
