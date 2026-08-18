# ADR-005: Make the structured theme catalog the routing authority

## Status

Accepted

## Date

2026-08-18

## Context

Motiflux supports 13 design themes with aliases, public principle analogues,
algorithm families, runtime parameters, controls, exclusions, and QA focus. If
the router, planner, and showcase each keep their own copy, they can disagree
about what a request means or show an algorithm that the runtime does not use.

## Decision

Store the canonical profiles in `skills/motiflux/catalog/themes.json` and
validate them with `themes.schema.json`. The router selects stable IDs; the
planner and runtime compiler consume the selected profile; the showcase creates
a derived display snapshot from the same catalog. Markdown guides explain
rationale but do not act as runtime routing data.

## Alternatives considered

### Parse the Markdown guide at runtime

Rejected because prose headings are a weak machine contract and make display
edits capable of changing routing behavior accidentally.

### Keep separate catalog files for the showcase and skill

Rejected because duplicated aliases and parameters would drift and weaken the
source-preserving comparison.

## Consequences

- Theme IDs and cross-artifact references are testable and stable.
- Adding a theme requires one catalog record plus its runtime effect and tests.
- The showcase reflects routing reality while remaining a display adapter.
- Public design systems remain principle analogues; the catalog does not claim
  access to private vendor recipes.
