# Implementation Plan: Motiflux V1 Architecture Upgrade

## Overview

Turn Motiflux from a descriptive skill bundle into a self-validating AI design
system. Keep the original identity, topology, theme-routing, accessibility, and
canonical-end-state requirements while adding stable artifact contracts,
deterministic local tools, a dependency-free web runtime template, and an
end-to-end test seam.

## Architecture decisions

- Keep `skills/motiflux/SKILL.md` as the orchestration module. It defines intent,
  ordering, and completion gates; it does not contain implementation details that
  belong in tools or references.
- Use JSON Schema as the machine-readable contract for the artifacts. YAML plans
  remain supported because JSON is a valid YAML subset and optional YAML input can
  be normalized by the tool adapter.
- Expose four narrow CLI seams: measure, compare, audit, and build. Keep format
  parsing, fingerprinting, and common error semantics inside one internal core
  module.
- Make every validator evidence-preserving. Missing browser, raster, or
  accessibility proof produces `not_run` or `candidate`, never a fabricated pass.
- Generate a dependency-free browser package with explicit runtime controls. The
  package is a delivery adapter, not a replacement for brand-specific motion
  design.

## Task list

### Phase 1: Contracts and architecture

- [ ] Task 1: Add architecture, output-contract, and runtime-contract guides.
- [ ] Task 2: Add schemas for source analysis, motion plans, telemetry, and evidence.
- [ ] Task 3: Record the module/seam decisions in ADRs.

### Phase 2: Executable vertical slices

- [ ] Task 4: Implement SVG/raster source measurement.
- [ ] Task 5: Implement semantic SVG comparison and evidence output.
- [ ] Task 6: Implement telemetry, bounds, progress, and accessibility auditing.
- [ ] Task 7: Implement the dependency-free web package builder and runtime hooks.

### Checkpoint: Toolchain

- [ ] All four tools run through the unified CLI.
- [ ] Tools return structured JSON and distinguish complete from candidate.
- [ ] A minimal SVG can pass measure → compare → build → audit fixtures.

### Phase 3: AI navigation and project quality

- [ ] Task 8: Refactor the main skill to route to the new contracts and tools.
- [ ] Task 9: Add examples and end-to-end tests.
- [ ] Task 10: Update repository validation, README, and CI commands.

### Checkpoint: Release candidate

- [ ] Core skill and plugin validators pass.
- [ ] Project tests pass without network access.
- [ ] No historical identifiers or unverified completion claims remain.
- [ ] Remote private repository matches the local commit.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Raster decoding differs by image format | Medium | Prefer optional Pillow when present; preserve header-only evidence and mark missing pixel analysis as candidate. |
| A semantic SVG match can still render differently | High | Keep browser pixel comparison explicitly separate and report it as `not_run` until exercised. |
| More references make the skill harder to navigate | Medium | Keep the main skill under 500 lines and route each artifact to one direct reference. |
| Generic runtime is mistaken for brand-specific choreography | High | Label the builder as a delivery adapter and require a motion plan plus evidence audit for completion. |

## Definition of done

The upgrade is complete only when the project contains executable tools,
machine-readable contracts, examples, tests, and an updated orchestrator; all
available checks pass; and the project still preserves the original functional
invariants.

