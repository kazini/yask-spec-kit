---
kind: steering
module: knowledge
use_when: "Find or look up anything in the workspace or code: what was decided, which decisions were made, where it was recorded, who owns it, where it is, or answer a question about the project; search, locate, what do we know about"
description: "Find the right document, section or symbol with the least reading: descriptions, search, outline, links, then the source section."
---
# Find information

Tools: `ws map`, `ws brief`, `ws find`, `ws outline`, `ws section`, `ws related`, `ws impact`. Each step has a manual fallback.
1. Start from descriptions, not files. `ws map <path>`, or `grep -rH -m1 '^description:' <path>`. Look in `docs/` first, then `_workboard/` if `docs/` lacks the answer; `.archive/` only when asked.
2. Get a read-set. `ws brief <topic>` returns the sections to read with their sizes. Without it, use the next two steps.
3. Search by content. `ws find <terms>` ranks sections and symbols; accents do not matter. Manually: `rg -n -i '<term>' <paths>` (or `grep -rn -i`). Try synonyms and the glossary terms in `docs/context/` before concluding something is absent.
4. Read the right amount. A short document the task mostly needs: read it whole. Otherwise `ws outline <file>` (or `grep -n '^#' <file>`), then `ws section <file> <heading>` or that section's line range. Read the whole section, not a few lines of it: definitions and exceptions sit beside the fact.
5. Follow the links. `ws related <path#Heading>` lists links, `supersedes`, `derived_from`, `covers` and cited ids in both directions; `ws impact` lists what depends on it. Manually: `rg -n '<file name, heading or id>' docs`. Read the superseding document, not the superseded one.
6. Code: `ws outline <file>` lists symbols; `ws find <symbol>`, `ws callers <symbol>`, `ws path <a> <b>`; manually `rg -n '<symbol>' code`. The component document named by `covers` says what the code is meant to do.
7. Raw material (`_workboard/meetings/`, `_workboard/reports/`) is searched, never read whole. For a large read, delegate (`delegate-to-subagent.md`).
8. Cite as `path#Heading`, after reading the section. If nothing turns up after synonyms, say what you searched and add an open item. One query that finds nothing does not show absence.
9. Index results are pointers. A snippet or description is never the source; the section is. If `ws check` reports a stale index, search directly.
