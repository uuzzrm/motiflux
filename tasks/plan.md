# Implementation Plan: Motiflux V1 Project Kernel Upgrade

## Overview

Turn Motiflux from a collection of useful adapters and a showcase into a
complete, source-aware project kernel. Preserve the original identity,
topology, theme-routing, accessibility, and canonical-end-state requirements
while giving the AI skill one executable pipeline:

```text
analyze -> route -> plan -> reconstruct -> compile -> verify -> package
```

Each stage owns one artifact and reports explicit status. Public commands stay
small; the domain model, catalog, plan compiler, runtime compiler, and evidence
aggregator live behind internal seams.

## Architecture decisions

- Keep `skills/motiflux/SKILL.md` as the orchestration module. It defines intent,
  ordering, and completion gates; it does not contain implementation details that
  belong in tools or references.
- Make `skills/motiflux/catalog/themes.json` the single machine-readable theme
  source. Markdown explains the design rationale; the router, planner, and
  showcase consume the catalog rather than independently parsing prose.
- Introduce one internal deep module, `tools/engine/project_pipeline.py`, whose
  small interface runs the stage graph and writes a project manifest. Existing
  command files remain compatibility adapters over this interface.
- Represent stage outputs with typed domain records and an artifact store. A
  stage may return `complete`, `candidate`, or `blocked`, but it must preserve
  `not_run` and `unresolved` evidence.
- Keep reconstruction and browser rendering behind real adapters. A missing
  adapter creates an honest candidate; it never silently becomes a pass.
- Compile theme profiles into runtime tokens and deterministic CSS/JS so theme
  selection changes executable behavior, not only explanatory text.
- Validate cross-artifact references (theme IDs, actor IDs, beat IDs,
  dependencies, and canonical fingerprints) in code in addition to shape-level
  JSON Schema checks.

## Task list

### Phase 1: Contracts and architecture

- [x] Task 1: Add architecture, output-contract, and runtime-contract guides.
- [x] Task 2: Add schemas for source analysis, motion plans, telemetry, and evidence.
- [x] Task 3: Record the module/seam decisions in ADRs.
- [x] Task 4: Add the canonical structured theme catalog and catalog contract.
- [x] Task 5: Add typed domain records and cross-artifact reference validation.

### Phase 2: Executable vertical slices

- [x] Task 6: Implement the initial SVG/raster source measurement adapter.
- [x] Task 7: Implement the initial semantic SVG comparison and evidence output.
- [x] Task 8: Implement the initial telemetry, bounds, progress, and accessibility auditing.
- [x] Task 9: Implement the initial dependency-free web package builder and runtime hooks.
- [x] Task 10: Implement theme routing through the structured catalog.
- [x] Task 11: Implement plan compilation from source analysis and theme selection.
- [x] Task 12: Implement the end-to-end project pipeline and manifest.
- [x] Task 13: Implement theme-aware runtime compilation and package verification.

### Checkpoint: Toolchain

- [x] All initial tools run through the unified CLI.
- [x] Tools return structured JSON and distinguish complete from candidate.
- [x] A minimal SVG can pass measure → compare → build → audit fixtures.
- [x] One project command runs analyze → route → plan → compile → verify.

### Phase 3: AI navigation and project quality

- [x] Task 14: Refactor the main skill to route to the initial contracts and tools.
- [x] Task 15: Add initial examples and end-to-end tests.
- [x] Task 16: Update initial repository validation, README, and CI commands.
- [x] Task 17: Add an end-to-end fixture with a generated plan, themed runtime,
  project manifest, and evidence aggregation.
- [ ] Task 18: Add browser/runtime verification as an optional adapter with a
  deterministic local fallback.
- [x] Task 19: Make the showcase consume the same catalog and pipeline artifacts.

### Checkpoint: Release candidate

- [x] Core skill and plugin validators pass.
- [x] Project tests pass without network access.
- [x] No historical identifiers or unverified completion claims remain.
- [x] Remote private repository matches the local commit.
- [x] The project pipeline can be rerun from one source/request pair without
  manually assembling intermediate artifacts.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Raster decoding differs by image format | Medium | Prefer optional Pillow when present; preserve header-only evidence and mark missing pixel analysis as candidate. |
| A semantic SVG match can still render differently | High | Keep browser pixel comparison explicitly separate and report it as `not_run` until exercised. |
| More references make the skill harder to navigate | Medium | Keep the main skill under 500 lines and route each artifact to one direct reference. |
| Generic runtime is mistaken for brand-specific choreography | High | Label the builder as a delivery adapter and require a motion plan plus evidence audit for completion. |

## Definition of done

The kernel upgrade is complete only when the project contains executable tools,
machine-readable contracts, examples, tests, and an updated orchestrator; one
source/request pair can produce a traceable project manifest and package; all
available checks pass; and the project still preserves the original functional
invariants.
