# Motiflux architecture

Motiflux is an AI-oriented design system, not a single animation script. Its
architecture separates decisions from implementations so an agent can select a
motion language without having to rediscover file formats, evidence rules, or
runtime controls.

## Module map

```text
                    +--------------------------+
                    |  SKILL.md / orchestrator |
                    |  order + decision gates  |
                    +------------+-------------+
                                 |
          +----------------------+----------------------+
          |                      |                      |
          v                      v                      v
   theme catalog          stage registry           artifact contracts
 catalog/themes.json   PipelineRunner/*.py      schemas/*.schema.json
          |                      |                      |
          +--------------+-------+--------------+-------+
                         v                      v
                adapters / core          validators
          measure + build + probe    compare + audit + index
                         |                      |
                         +--------------+-------+
                                        v
                             evidence-led delivery
```

## External seams

The project exposes narrow command seams. Each returns structured artifacts and
can be used independently or through the standard project pipeline.

| Seam | Purpose | Main output |
| --- | --- | --- |
| `measure` | Normalize SVG or raster source observations | `source-analysis.json` |
| `compare` | Compare candidate and canonical SVG semantics | geometry evidence |
| `audit` | Check telemetry, progress, bounds, fingerprints, and accessibility | motion evidence |
| `build` | Assemble a dependency-free web package with runtime hooks | output package |
| `probe` | Check static runtime contracts and optional local Node execution | runtime-probe evidence |
| `project` | Run analyze -> route -> plan -> reconstruct -> compile -> verify -> package | `project.json` |

`catalog/themes.json` is the routing authority. `tools/engine/project_pipeline.py`
is the compatibility façade behind the small `project` interface;
`tools/engine/pipeline.py` owns the dependency-checked stage registry and
`tools/engine/artifacts.py` owns the content index. The pipeline writes a
manifest even when reconstruction or browser proof is unavailable, preserving
`candidate`, `blocked`, `not_run`, and `unresolved`.

`tools/motiflux_core.py` is an internal seam shared by these adapters. It owns
SVG parsing, semantic fingerprints, structured-document loading, safe writes, and
common status handling. Callers should not depend on its internal functions;
they should use the four CLI seams or the artifact files.

## Data flow

1. `measure` turns an input mark into observations. It does not invent a vector
   reconstruction.
2. The catalog router selects one theme and the planner creates a plan from the
   observations, request, and at most two modifiers.
3. Reconstruction produces `mark.svg` only when a canonical vector is real;
   raster input without that adapter remains a candidate.
4. `build` compiles the selected profile into a dependency-free runtime package.
5. The runtime emits telemetry and `audit` turns it into evidence.
6. `artifact-index.json` hashes every emitted file except the index and
   manifest; `project.json` links stages, capabilities, execution order, and
   named artifacts. Missing proof remains visible as `not_run` or `unresolved`.

The showcase is a separate display adapter: it consumes the same catalog and
the supplied source raster, then renders a playable image-to-animation grid.
Its PDF records four static checkpoints of the HTML sequence; it is not a
substitute for runtime evidence.

## Deep-module rules

- Keep format-specific logic behind adapters. The orchestrator reasons in terms
  of constraints, actors, beats, and evidence rather than PNG chunks or XML
  namespaces.
- Keep identity constraints upstream of motion. A theme can change timing,
  interpolation, and secondary effects, but never the source mark's topology or
  canonical fingerprint.
- Keep validators pure where possible: input files in, report out. This makes
  them easy to rerun after any AI revision.
- Make nondeterminism explicit. Seeds, substitutions, browser versions, and
  unavailable tools belong in evidence.
- Prefer replacement over layering. If a new algorithm is added, give it a
  contract and a test fixture; do not add another undocumented branch to the
  orchestrator.
- Keep the façade thin. Add stage behavior behind `PipelineRunner`, and add
  artifact writes through `ArtifactStore` so provenance and integrity remain
  automatic.

## Extension protocol

To add a new algorithm family:

1. Add a named theme or modifier to `motion-themes.md` only if it changes
   routing decisions.
2. Add its parameters and constraints to `motion-plan.schema.json`.
3. Add an implementation adapter or template behind an existing CLI seam.
4. Add one positive and one failure fixture.
5. Update the relevant guide and ADR if the seam changes.
6. If the change affects stage ordering, artifacts, capabilities, or evidence
   meaning, update `guides/project-kernel.md` and add an ADR.
7. Keep the main skill concise; link to the new reference instead of duplicating
   the algorithm description.
