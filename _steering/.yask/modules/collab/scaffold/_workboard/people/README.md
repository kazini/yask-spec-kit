---
kind: canon
description: "Personal space per person: an append-only log per day, and drafts. Each file has exactly one writer."
---
# People

Each person has `_workboard/people/<name>/` with `log/YYYY-MM-DD.md` (one file per UTC day, append-only) and drafts. Only that person and their agents write there, so files do not conflict in git; others read them. Create from the starter files in `scaffold.md`.
