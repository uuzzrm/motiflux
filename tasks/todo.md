# Motiflux V1 Project Kernel Checklist

## Already shipped

- [x] Contract guides and schemas
- [x] ADRs for seams, offline adapters, and evidence semantics
- [x] Initial tools, examples, tests, showcase, CI, and private remote push

## Kernel foundation

- [x] `skills/motiflux/catalog/themes.json` is the authoritative theme source
- [x] `tools/engine/domain.py` defines typed stage records and references
- [x] `tools/engine/artifacts.py` owns deterministic artifact writes
- [x] `tools/engine/planner.py` rejects dangling plan references
- [x] `tools/engine/project_pipeline.py` owns the stage graph

## Executable pipeline

- [x] `motiflux.py project <source> <request> <output>` runs the full pipeline
- [x] The planner creates a valid plan from route + source analysis
- [x] The runtime compiler consumes theme profile data
- [x] `project.json` records stage status and artifact paths
- [x] Evidence aggregation preserves missing browser/raster proof

## Verification and product quality

- [x] Cross-reference and pipeline tests
- [x] Browser smoke test against a generated generic package (showcase browser smoke is complete)
- [x] Showcase consumes catalog data
- [x] README documents the new one-command workflow
- [x] Project validator and plugin validator
- [x] Skill validator
- [x] GitHub Actions
- [x] Private remote SHA verification
