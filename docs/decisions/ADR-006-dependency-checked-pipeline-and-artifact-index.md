# ADR-006: Use a dependency-checked pipeline and artifact index

## Status

Accepted

## Date

2026-08-18

## Context

The first project-kernel pass exposed a one-command pipeline, but its stage
logic lived in one large function. It was difficult for an AI agent to tell
which stage had really run, which output a stage promised, or whether an output
had changed after it was written. Downstream work could also be mistaken for a
successful continuation after an unavailable raster or browser capability.

## Decision

Keep `run_project(source, request, output)` as the stable external interface,
but execute its work through a dependency-checked `PipelineRunner`. Each stage
declares logical `requires` and `provides` values and returns a typed
`StageResult`. The runner blocks missing prerequisites and records the reason.

After execution, `ArtifactStore` writes `artifact-index.json` containing a
normalized path, SHA-256 digest, byte count, media type, and producer for every
file in the project root except the index and manifest. A validator recomputes
these values.

Runtime verification is a separate scoped adapter. Static contract checks and a
local Node harness may prove the generated JavaScript seam; browser pixels,
layout, and accessibility-tree evidence remain separate and explicit.

## Alternatives considered

### Keep the monolithic runner

Rejected because stage ordering, failure handling, and artifact ownership stay
implicit and every new adapter expands one high-risk function.

### Treat output filenames as sufficient provenance

Rejected because a filename does not show who produced the file, whether it was
modified, or whether a stale file was reused.

### Mark a local Node probe as full browser validation

Rejected because JavaScript execution cannot establish layout, pixels, browser
accessibility, or real interaction semantics.

## Consequences

- The public command and existing artifact paths remain compatible.
- Future stages and adapters have a narrow, testable internal seam.
- Project manifests become auditable across reruns and environments.
- Raster and browser limitations remain visible instead of being hidden by a
  green static check.
- The project has more explicit metadata and one additional index file to
  maintain, but both are machine-readable and deterministically regenerated.
