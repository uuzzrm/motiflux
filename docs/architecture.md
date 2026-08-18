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
   theme router            artifact contracts       output contract
 motion-themes.md       schemas/*.schema.json     guides/output-contract.md
          |                      |                      |
          +--------------+-------+--------------+-------+
                         v                      v
                adapters / core          validators
             measure + build          compare + audit
                         |                      |
                         +--------------+-------+
                                        v
                             evidence-led delivery
```

## External seams

The project exposes four narrow command seams. Each accepts a file path and
returns structured JSON; each can be used independently or in the standard
pipeline.

| Seam | Purpose | Main output |
| --- | --- | --- |
| `measure` | Normalize SVG or raster source observations | `source-analysis.json` |
| `compare` | Compare candidate and canonical SVG semantics | geometry evidence |
| `audit` | Check telemetry, progress, bounds, fingerprints, and accessibility | motion evidence |
| `build` | Assemble a dependency-free web package with runtime hooks | output package |

`tools/motiflux_core.py` is an internal seam shared by these adapters. It owns
SVG parsing, semantic fingerprints, structured-document loading, safe writes, and
common status handling. Callers should not depend on its internal functions;
they should use the four CLI seams or the artifact files.

## Data flow

1. `measure` turns an input mark into observations. It does not invent a vector
   reconstruction.
2. The agent creates a `motion-plan.yaml` from those observations, user intent,
   and one primary theme plus at most two modifiers.
3. The agent reconstructs `mark.svg` and uses `compare` against the accepted
   canonical mark.
4. `build` creates a runtime package. Its generic motion is a delivery adapter;
   brand-specific choreography remains encoded by the plan and runtime edits.
5. The runtime emits telemetry. `audit` turns that telemetry into evidence.
6. `evidence.json` is complete only when every required check has evidence. A
   missing check remains visible as `not_run`.

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

## Extension protocol

To add a new algorithm family:

1. Add a named theme or modifier to `motion-themes.md` only if it changes
   routing decisions.
2. Add its parameters and constraints to `motion-plan.schema.json`.
3. Add an implementation adapter or template behind an existing CLI seam.
4. Add one positive and one failure fixture.
5. Update the relevant guide and ADR if the seam changes.
6. Keep the main skill concise; link to the new reference instead of duplicating
   the algorithm description.

