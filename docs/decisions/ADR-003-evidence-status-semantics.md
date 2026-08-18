# ADR-003: Treat evidence status as a first-class output

## Status

Accepted

## Date

2026-08-18

## Context

An AI can produce a visually plausible animation without proving identity,
topology, timing, accessibility, or canonical final-state equivalence. Static
validation is useful but cannot stand in for checks that were never run.

## Decision

Every producer returns `complete` or `candidate`, plus explicit `not_run` and
`unresolved` arrays. `complete` is reserved for an artifact whose required
checks ran and passed. `candidate` is the normal result when the design is useful
but evidence is incomplete. The delivery builder therefore emits a candidate
evidence file until runtime and browser checks are actually performed.

## Alternatives considered

### Return a boolean pass/fail

Rejected because it hides whether a check failed or simply never ran.

### Treat missing evidence as success

Rejected because it would turn an absence of observation into a quality claim.

## Consequences

- Downstream agents can decide whether to continue, ask for a tool, or deliver a
  candidate without rereading prose.
- Evidence files are slightly more verbose but remain auditable.
- Release automation can gate on `status`, `not_run`, and `unresolved` separately.

