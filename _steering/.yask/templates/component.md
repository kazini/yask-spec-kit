---
kind: canon
description: "<Component>: requirements, then design, then open questions."
label: aspirational
status: draft
approved_by:
covers: []   # code paths it describes, e.g. code/<program>/**
---
# <Component>
Position in the system: <one line>.

## Requirements
Terms (optional)
  <predicate> := <observable condition>
Axioms
  A1 invariant: <statement> → <named check>
  A2 principle: <statement; prefer / consider>

### <PFX>-1 <Title>
Acceptance criteria (the system SHALL)
1. WHEN <trigger>: <response> → <check name>
2. IF <condition>: <recovery> → <check name>

## Design
Boundaries: <what this component owns and does not own>
Contracts: <name(in) → out | errors; pre; post> [<ids>]
Flow: <arrow chain, including neighbouring components>
Decisions: D1: <choice>, over <alternative>; <reason> [<ids>]
Tests: <which test covers which requirement or axiom>

## Open
- <question, listed rather than guessed>
