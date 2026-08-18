# ADR-002: Prefer offline deterministic adapters

## Status

Accepted

## Date

2026-08-18

## Context

Logo reconstruction and motion validation often run inside an agent session with
unknown network access, changing browser versions, and different optional image
libraries. Reproducibility and privacy matter more than silently reaching for a
remote service.

## Decision

Ship local Python adapters with standard-library implementations where practical.
Optional capabilities may be detected, but unavailable capabilities must be
recorded in `not_run` or `substituted_tools`. Do not make remote requests, upload
source marks, or claim raster/pixel/browser proof when only semantic analysis ran.

## Alternatives considered

### Always use a hosted vision or rendering service

Rejected because it creates an unapproved data-egress path and makes evidence
non-reproducible.

### Require every optional dependency

Rejected because installing a full imaging or browser stack is disproportionate
for a skill that should remain portable.

## Consequences

- SVG and structured artifact checks are reliable offline.
- Raster analysis can be richer when an image adapter is installed, while the
  header-only fallback remains honest.
- Browser rendering is a separate verification step, not an implied side effect.

