---
kind: steering
module: meetings
use_when: "Ingest a meeting, call, workshop, recording, meeting notes or transcript the client or team sent: file a redacted verbatim record and a one-page summary; do not change canon"
description: "Capture meeting evidence with a summary, redaction and source hash for later extraction. `ws ingest` automates it."
---
# Ingest a meeting

Tool: `ws ingest`. Manual steps:
1. Create `_workboard/meetings/<stamped name>/` (`conventions.md`, Ids). The stamp is the meeting's start (UTC, to the minute) or the clock; the id is random hex, checked unused.
2. Redact before saving anything: remove secrets, credentials and personal data that is not needed. Do not let unredacted text reach an agent or a commit; purging git later cannot unsend it.
3. Save `transcript.md`: verbatim after redaction, with front matter (`kind: raw`, `description`, `source`). Large files stay outside git; record them in `.archive/manifest.md`.
4. Compute `sha256sum` of the original and record it in the summary front matter.
5. Write `summary.md` from `_steering/.yask/templates/meeting-summary.md`: one page. Decided (only what attendees explicitly decided, with who), Requested, Pending. The first line says it is evidence.
6. Do not edit canon and do not close decisions here. The next step is `extract-proposals.md`.
7. Add a `note` line to your log.
