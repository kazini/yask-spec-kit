# .dev_yask

Development of YASK itself. Nothing here ships to projects.

- `run_tests.py`: `python3 .dev_yask/run_tests.py` runs all categories; `<category>` runs one, `-k <name>` filters. Categories: `core`, `checks`, `steering`, `lifecycle`, `secrets`, `release`.
- `tests/`: grouped by those categories. `evals/`: model cases against steering. `_archive/`: retired snapshots; retired project material goes to root `.archive/`.
- `build_release.py`: builds `yask-<version>.zip`, the workspace template, and its `.sha256`. Syncs root `LICENSE`/`README.md` into `.yask/LICENSE`/`.yask/YASK.md`; `NOTICE` ships from the layer. `ws update` applies only the `.yask` payload; root `LICENSE`/`README.md`/`NOTICE` stay out of the zip root.
- `cleanup.py`: dry run; `--apply` clears `_steering/.ws/`, `_steering/.yask_cache/`, `dist/`, `__pycache__/` and stray `.pyc`.

## Release

Bump `_steering/.yask/VERSION`, run the tests, `python3 .dev_yask/build_release.py`, attach the two `dist/` files to a `v<version>` release. Keep `update.repo` in `_steering/.yask/yask.yaml` as `kazini/yask-spec-kit`. `.github/workflows/release.yaml` builds and publishes on a VERSION push or dispatch. Track the launchers as 100755; run `python3 .dev_yask/cleanup.py --apply` before pushing.

## Constraints

- Python 3.13 for CI: `tests.yaml` and the release build use the same current Python; older versions are not release-gated.
- Git optional: history tests are `@needs_git`. Tests use an empty git config and drop inherited git env vars, so the developer's setup cannot change a result.
- Launchers are 0755 in release zips; `ws update` restores or grants the bit. The git index must track them as 100755; `test_in_a_git_checkout_the_launchers_are_tracked_executable` names them and `git update-index --chmod=+x` fixes them.
