# ADR-007: Separate raster observations from bounded runtime controls

## Status

Accepted

## Context

Motiflux accepts PNG, JPG, and WebP inputs, but a raster image does not expose
semantic actors or editable paths. The skill also needs user-requested controls
such as duration, tempo, direction, background, particle policy, reduced motion,
and requested output formats to remain inspectable and executable.

## Decision

Add a deterministic raster observation adapter behind the `measure` seam. It
derives a foreground mask, connected components, bounds, centroids, and
explainable geometric role candidates. The adapter writes those observations as
`candidate` data with `needs-review` and `vector_reconstruction: not-claimed`;
it never promotes pixel segmentation to a completed editable scene.

Parse bounded runtime controls from the request into `motion-plan.yaml`, then
make the runtime compiler consume the supported controls. Unknown or
renderer-specific wishes remain explicit constraints and do not become proof.

## Alternatives considered

### Header-only raster handling

Rejected because it prevents the skill from recognizing even measurable pixel
structure and makes foreground planning needlessly blind.

### Automatic raster-to-vector completion

Rejected because heuristic segmentation cannot establish identity, topology, or
editable path fidelity without review and a canonical comparison.

### UI-only tuning controls

Rejected because a showcase control that never reaches the plan/runtime creates
an attractive but non-executable contract.

## Consequences

- Raster projects expose useful, deterministic observations while remaining
  honest candidates until reconstruction and review are complete.
- SVG projects keep their existing semantic path and canonical-fingerprint path.
- Prompt-driven runtime controls are testable in generated plans and packages.
- Pillow remains an optional decoder; its absence preserves the header-only
  fallback and candidate status.
