# ADR-004: Use one manifest-producing project pipeline

## Status

Accepted

## Date

2026-08-18

## Context

Motiflux had useful command adapters, but an AI agent still had to assemble
intermediate files and infer which stages had actually run. That made a raster
limitation easy to confuse with a completed reconstruction and made it harder
to trace a theme choice into the delivered runtime.

## Decision

Expose `tools/motiflux.py project <source> <request> <output>` as the stable
project interface. The internal `tools/engine/project_pipeline.py` runs:

```text
analyze -> route -> plan -> reconstruct -> compile -> verify -> package
```

It writes `project.json`, stage records, artifact paths, and explicit
`complete`/`candidate`/`blocked`, `not_run`, and `unresolved` values. Existing
lower-level commands remain independently usable compatibility adapters.

## Alternatives considered

### Make agents assemble each adapter manually

Rejected because ordering and evidence aggregation would be repeated in every
task, increasing the risk of skipped or overstated proof.

### Hide all intermediate artifacts behind one opaque result

Rejected because future agents need inspectable artifacts and precise failure
locality when a source format or browser capability is unavailable.

## Consequences

- One source/request pair produces a reproducible, inspectable project trace.
- Raster limitations remain visible as a candidate instead of a fake pass.
- The internal pipeline can evolve without expanding the public command surface.
- Browser verification is still an explicit adapter; the manifest does not claim
  browser proof merely because compilation succeeded.
