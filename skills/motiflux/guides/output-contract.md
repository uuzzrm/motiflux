# Motiflux output contract

The output package is a set of named artifacts. Generate only the artifacts
needed by the requested surface, but never rename a required artifact.

## Required package

```text
mark.svg
motion.html
motion-plan.yaml
evidence.json
evidence/
  source-analysis.json
  geometry/
  motion/
  accessibility/
```

`motion.css`, `motion.js`, and `preview.webp` are optional. The project builder
can generate the first two as a dependency-free baseline; brand-specific motion
may replace their implementation while preserving the runtime interface.

## Artifact ownership

| Artifact | Producer | Authority |
| --- | --- | --- |
| `source-analysis.json` | measure adapter | observations only; never a reconstruction |
| `mark.svg` | reconstruction step | canonical vector scene after acceptance |
| `motion-plan.yaml` | agent + theme router | selected theme, constraints, beats, runtime contract |
| geometry evidence | compare adapter | semantic equality and geometry metrics |
| motion evidence | runtime + audit adapter | progress, bounds, errors, end-state checks |
| accessibility evidence | runtime/browser check | reduced motion, focus, controls, contrast, layout |
| `evidence.json` | delivery step | aggregate status and unresolved proof |

## Status semantics

```yaml
status: complete | candidate
not_run: []
unresolved: []
```

Use `complete` only when required evidence is present and passing. Use
`candidate` when the artifact is useful but any required check is missing or
unresolved. Never delete an unresolved item merely to make a report look clean.

## Plan minimum

Every plan must include:

```yaml
schema_version: "1.0"
project:
  name: "..."
theme_selection:
  primary: "..."
  modifiers: []
  matched_tags: []
  rejected_candidates: []
motion_language:
  traits: []
beats: []
runtime:
  duration_ms: 1200
  reduced_motion: "static-canonical"
```

Add constraints, actors, dependencies, interpolation, safe areas, and controls
when the source task requires them. Keep one primary theme and no more than two
modifiers unless the user explicitly asks for a collision.

