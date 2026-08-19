# Motiflux project kernel

This guide is the AI-facing map of the executable architecture. Load it when a
task spans more than one artifact, adds an adapter, changes stage ordering, or
needs to explain why a project is `candidate` or `blocked`.

## Stable interface

Use the unified command seam:

```text
tools/motiflux.py project <source> <request> <output>
```

The internal implementation is replaceable. Callers should consume the files
and statuses, not import stage handlers directly. Lower-level commands remain
useful for isolated inspection and are compatibility adapters.

## Stage graph

```text
source + request
      │
      ├── analyze ── source-analysis.json
      ├── route ──── theme-selection.json
      └── plan ───── motion-plan.yaml
                         │
source ───────── reconstruct ── mark.svg (SVG only)
                         │
                 verify-geometry ── evidence/geometry/semantic.json
                         │
                    compile ── package/
                         │
                 verify-package ── evidence/package-validation.json
                         │
                  verify-motion ── motion audit + runtime probe
```

The graph is implemented by `engine.PipelineRunner`. Each stage has a small
interface:

- `requires`: logical values that must already exist in the context;
- `provides`: logical values the handler promises to publish;
- `handler`: domain work that returns one `StageResult`.

If a required value is absent, the runner emits a `blocked` result with
`missing-prerequisite:<id>` and does not call the handler. If a handler cannot
provide a declared product, it remains inspectable as a `candidate` unless the
handler itself failed. This is the main protection against fake downstream
success.

## Internal modules

| Module | Deep interface | Responsibility |
| --- | --- | --- |
| `pipeline.py` | `PipelineRunner.run(context)` | stage ordering, prerequisites, failure locality |
| `domain.py` | `StageResult`, `ArtifactRef`, `CapabilityReport` | typed kernel vocabulary |
| `artifacts.py` | `ArtifactStore` | safe writes and content-addressed index |
| `catalog.py` | `ThemeCatalog` | canonical theme lookup and routing |
| `planner.py` | `build_plan` | source/request/theme to motion plan |
| `runtime.py` | `compile_runtime` | plan to dependency-free package files |
| `runtime_probe.py` | `probe_runtime` | scoped offline runtime evidence |
| `project_pipeline.py` | `run_project` | compatibility façade and manifest assembly |

The façade is intentionally thin. New functionality belongs behind one of the
internal seams, with a contract and a test at that seam.

## Artifact index

Every file below the project output root is indexed after stage execution in
`artifact-index.json`, except the index itself and `project.json`. Each record
contains:

- normalized relative `path`;
- SHA-256 `sha256`;
- byte count `bytes`;
- producing stage `producer`;
- stable `media_type`.

Validate the index with:

```text
tools/motiflux.py validate artifact-index <output>/artifact-index.json
```

The validator re-reads each file and recomputes its hash. A missing or changed
artifact is an integrity failure, not a documentation issue.

## Capability and evidence semantics

The manifest reports local capabilities such as semantic SVG support, raster
pixel decoding, Node, and browser runtime. Capability availability is not proof
that a stage ran. Stage results and evidence files remain authoritative.

`runtime-probe` has a deliberately narrow scope. A `complete` probe means the
static package contract and, when available, the local Node harness passed. It
does not mean browser pixels, real layout, console cleanliness, or the
accessibility tree passed. Those checks remain `not_run` until a browser adapter
actually runs them.

## Extension protocol

When adding an implementation:

1. Decide whether it is a new stage product or an adapter behind an existing
   stage.
2. Add or update a machine-readable schema before changing orchestration.
3. Give the stage explicit `requires` and `provides` values.
4. Keep the default path offline and deterministic; record optional capabilities.
5. Add one success test and one missing-prerequisite or failure test.
6. Update the relevant ADR and this guide if the seam or evidence meaning
   changes.

Do not add a second hidden pipeline, duplicate catalog, or direct write that
escapes `ArtifactStore`.
