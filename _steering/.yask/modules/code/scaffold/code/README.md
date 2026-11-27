---
kind: canon
description: "The product's code: one subfolder per program or module. Documented in docs/architecture/, not here."
---
# Code

One subfolder per program or module (`code/<program>/`), each with `src/`, tests and build files. Create one when the program exists, not before. Versions are git branches and tags, not folders; `code/<program>-v1/` is only for long-term parallel versions. List separate repositories here (submodule or short manifest) so the workspace knows where the code is.

Purpose and design live in `docs/architecture/`; the component document names its code with `covers: code/<program>/**`. Generated outlines and symbol graphs live in `_steering/.ws/cache/`, never here.
