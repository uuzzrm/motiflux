---
name: motiflux
description: "Motiflux V1 reconstructs raster brand marks as editable SVG scene graphs and designs responsive, brand-derived motion systems for web delivery. Use for logo reconstruction, logo reveals, splash sequences, brand intros, loading states, idle motion, and hover interactions. Route requests through theme tags such as premium, product-system, developer, AI-generative, fintech, security, luxury, automotive, sports, commerce, cinematic, nature, gaming, and accessibility. Build from a visual constraint graph, choose geometry by explainability, author choreography as a dependency graph, handle crossings with topology-aware occlusion, and validate with landmark error, contour distance, temporal telemetry, accessibility checks, and semantic end-state fingerprints."
---

# Motiflux V1

## AI execution contract

Act as a design-and-verification system. Convert a supplied mark and brand
context into an editable vector scene, a motion plan, a responsive web package,
and an evidence ledger. Optimize in this order: identity landmarks; contour and
negative-space fidelity; editable scene structure and topology; motion
legibility; responsive and accessible behavior; compact implementation.

Use `MUST` for completion requirements, `SHOULD` for defaults, and `MAY` for
optional behavior. If a MUST is not verified, return `candidate` and preserve
the missing item in `not_run` or `unresolved`. Never turn missing evidence into
a pass. Do not infer provenance or licensing from this file.

## Architecture map

The skill is the orchestration module. Keep implementation complexity behind
these narrow seams:

| Phase need | Stable seam | Output |
| --- | --- | --- |
| source observations | `tools/motiflux.py measure` | `source-analysis.json` |
| theme selection | `tools/motiflux.py route` | `theme_selection` |
| artifact contract | `tools/motiflux.py validate` | structured validity report |
| semantic geometry | `tools/motiflux.py compare` | geometry evidence |
| runtime telemetry | `tools/motiflux.py audit` | motion evidence |
| web delivery | `tools/motiflux.py build` | dependency-free package |
| complete source/request job | `tools/motiflux.py project` | `project.json` manifest |
| offline runtime contract | `tools/motiflux.py probe` | runtime-probe evidence |

Read the direct resource for the active phase: `catalog/themes.json` for
canonical profiles; `guides/motion-themes.md` for rationale and aliases;
`guides/algorithm-catalog.md` for algorithm proof gates;
`guides/project-kernel.md` for stage interfaces and execution semantics;
`guides/output-contract.md` and `guides/runtime-contract.md` for delivery;
`schemas/*.schema.json` for contracts; and `tools/*.py` for adapters.

`catalog/themes.json` is the single routing source consumed by the router,
planner, runtime compiler, tests, and showcase. Markdown is explanatory only.

Run tools from the skill directory. Treat their JSON output as evidence, not as
a replacement for design judgment. If an optional capability is unavailable,
record the substitution or missing check; do not invent a result.

Represent every task with four linked models: `constraint_graph` for landmarks,
contours, gaps, symmetry, and color; `scene_graph` for actors, parents, layers,
anchors, and occlusion; `motion_graph` for beats, dependencies, overlaps, and
interaction states; and `evidence_ledger` for geometry, motion, accessibility,
substitutions, `not_run`, and `unresolved`. Every design decision MUST trace to
one model and remain inspectable in an artifact.

## Project pipeline

For a complete source/request job, use the project pipeline in this order:

```text
    analyze -> route -> plan -> reconstruct -> verify-geometry
      -> compile -> verify-package -> verify-motion
```

Run it through the stable command seam:

```text
tools/motiflux.py project <source> <request> <output>
```

The command writes a `project manifest` at `<output>/project.json`, an
`artifact-index.json` with SHA-256, size, and producer records, and one artifact
per stage. `PipelineRunner` executes the registry and `stages.py` supplies the
default handlers. Each stage declares `requires` and `provides`; a missing
prerequisite blocks that stage and every dependent stage rather than running a
partial implementation. The manifest also records capability reports and execution
order. It preserves `complete`, `candidate`, or `blocked`, plus `not_run` and
`unresolved`. It does not replace artifact contracts. Raster input without a
real raster-to-vector adapter remains a candidate; never label a placeholder
vector complete.

Before delivery, validate cross-artifact references in addition to JSON shape:
theme IDs must exist in `catalog/themes.json`; actor, beat, parent, occlusion,
and dependency references must resolve; and the compiled package must preserve
the selected theme and canonical source mark.
Theme profiles are executable inputs: the planner and runtime compiler turn
their motion parameters into beats, controls, CSS, and JavaScript behavior.
An algorithm list without a corresponding runtime effect is incomplete.

## Theme router

When the request includes a style, industry, reference system, audience, or
motion adjective, read `guides/motion-themes.md` and run the `route` seam before
composing. Use `guides/algorithm-catalog.md` to justify the selected stack.

Normalize the request into:

    theme_selection:
      primary:
      modifiers: []
      matched_tags: []
      rejected_candidates: []
      public_reference_basis: []
      algorithm_stack: []

Routing rules:

1. Match explicit style or industry words before inferring from the logo.
2. Choose one primary theme.
3. Add at most two modifiers such as quiet, bold, technical, organic, playful, cinematic, or accessible.
4. Reject conflicting themes unless the user explicitly requests the collision.
5. If no theme reaches a clear match, use system-spatial with quiet and accessible modifiers.
6. Record matched language, selected algorithm types, implementation controls, and rejected candidates in motion-plan.yaml.
7. Never claim that a public company uses the exact internal algorithm; describe it as a public design-system analogue.

Normalize case, punctuation, spaces, and hyphens before matching. Public-system aliases are routed as follows:

    Material or Google Material -> system-spatial
    Apple HIG -> premium-quiet + accessibility-first
    Microsoft Fluent -> system-spatial + accessibility-first
    Adobe Spectrum -> system-spatial + accessibility-first
    Atlassian -> developer-open + system-spatial
    Shopify Polaris -> commerce-energy + system-spatial
    GitHub Primer -> developer-open + system-spatial
    Airbnb Lottie -> developer-open with vector-animation runtime

Chinese aliases:

    科技、产品、SaaS、企业系统 -> system-spatial
    奢侈、时尚、美妆、极简、高级感 -> premium-quiet
    开发者、开源、代码、API、工具 -> developer-open
    人工智能、AI、生成式、数据、未来感 -> AI-field
    金融、支付、银行、可信、稳健 -> fintech-trust
    安全、隐私、认证、防护、盾牌 -> security-shield
    电商、零售、购物、消费、促销 -> commerce-energy
    汽车、交通、工业、工程、性能 -> automotive-precision
    体育、健身、竞技、速度、冲击 -> sports-impact
    电影、片头、预告、叙事、戏剧 -> cinematic-title
    自然、有机、健康、环保、成长 -> nature-flow
    游戏、电竞、奇幻、科幻、街机 -> gaming-world
    无障碍、低动效、包容、键盘、辅助 -> accessibility-first

The selected theme changes choreography and implementation parameters, not the identity constraints of the source mark.

## Inputs and outputs

Require one PNG, JPG, WebP, or SVG source plus supplied brand context. Ask only
when ambiguity changes the intended surface, identity, or motion behavior.
Default surface: a responsive web intro that settles into a static mark.

Follow `guides/output-contract.md` for the required filenames. Use these machine
contracts when writing artifacts:

- `schemas/source-analysis.schema.json`;
- `schemas/motion-plan.schema.json`;
- `schemas/telemetry.schema.json`;
- `schemas/evidence.schema.json`.

Validate generated artifacts with `tools/motiflux.py validate` before delivery.
The generic builder is a delivery adapter; it does not prove brand-specific
choreography, browser pixels, or accessibility-tree behavior.

## Workflow

    OBSERVE
      -> MODEL
      -> RECONSTRUCT
      -> COMPOSE
      -> INSTRUMENT
      -> VALIDATE
      -> DELIVER

Do not compose motion before the reconstructed scene reaches geometry acceptance.

The executable vertical slice is:

```text
measure -> model -> reconstruct -> compare -> compose -> build -> audit -> deliver
```

The project pipeline is the preferred one-command path when intermediate
artifacts do not already exist. Use the lower-level seams when an existing
artifact needs isolated inspection or when a missing adapter must remain
explicitly `not_run`.

Use `measure` before modeling, `compare` before motion, `build` only after a
contract-valid plan exists, and `audit` before claiming motion completion.

## OBSERVE

Measure dimensions, color mode, alpha, background, foreground clusters,
antialiasing/compression, identity corners/extrema/junctions/terminals/centers,
negative spaces, symmetry, repetition, alignment, and mark/wordmark/letter/
accent/container roles.

Write evidence/source-analysis.json.

For SVG input, run:

```text
tools/motiflux.py measure <source.svg> --output evidence/source-analysis.json
```

For PNG, JPG, or WebP, a header-only result is a candidate. Pixel decoding,
color clustering, landmark detection, and topology analysis remain `not_run`
unless an approved image adapter is available.

## MODEL

### Build constraint graph

Assign each constraint `id`, `kind` (`landmark`, `contour`, `gap`, `symmetry`,
or `color`), `importance` (`identity`, `structural`, or `cosmetic`), target,
tolerance, and dependencies. Identity constraints outrank raster noise.

Identity constraints dominate cosmetic pixel agreement.

### Build scene graph

Create one actor per independently transformable or occluding part. Store `id`,
`role`, `geometry_strategy`, `parent`, `anchor`, `layer`, `occludes`, and
`occluded_by` in `motion-plan.yaml`.

Use stable semantic ids. Avoid child-index selectors.

### Define motion language

Derive three motion traits from the mark and context. Record tempo,
acceleration, overlap, deformation limit, direction, and stillness for each in
the plan. Every interpolation and effect must trace to a trait.

## RECONSTRUCT

### Choose geometry by explainability

Choose the smallest model that explains constraints: primitive; transformed
primitive family; centerline plus width profile; sparse Bezier contour; or
simplified measured outline.

Escalate only when identity or structural constraints fail.

Prefer editable text when an available font matches sufficiently. Convert to paths only when exact glyph identity or per-glyph deformation requires it.

### Preserve topology

Preserve contour winding, hole count, component count, crossing order, open versus closed state, joins, and terminals.

Do not encode a crossing only as a convenient compound path when later occlusion requires independent control.

### Define draw traversal

For a drawn reveal, store `actor`, `start_landmark`, `end_landmark`, `direction`,
`measured_length`, and `visible_intervals`.

Use browser measurement or geometry tooling to derive real lengths at build time.

### Geometry acceptance

Compute weighted landmark error, symmetric contour/Chamfer distance,
negative-space area/centroid error, topology, and actor/segment/control-point
counts.

Render at source scale and one enlarged inspection scale.

Accept geometry when:

    topology_match: true
    identity_landmarks: within_declared_tolerance
    negative_spaces: within_declared_tolerance
    visible_kinks: 0
    unexplained_complexity: 0

Do not use one universal overlap score. Derive tolerances from source resolution and feature size.

### Refinement stop rule

After each revision, compare weighted constraint error with the previous accepted candidate.

Stop when:

- all acceptance conditions pass;
- two consecutive revisions improve total weighted error by less than 1%;
- remaining error comes from source ambiguity;
- the next revision would add complexity without fixing identity.

If acceptance fails, deliver a candidate with unresolved constraints.

Run semantic comparison before composing motion:

```text
tools/motiflux.py compare mark.svg canonical.svg --output evidence/geometry/semantic.json
```

Semantic vector equality does not imply raster contour or browser-pixel equality.
Keep those proof types separate.

## COMPOSE

### Build named beats

Name beats such as `orient`, `form`, `bind`, and `resolve`. Weight duration from
visual distance, actor area, curvature, reading order, and context; do not use a
fixed global phase ratio.

### Build dependency graph

For each action record actor, beat, `starts_after`, `may_overlap`,
`must_finish_before`, anchor, and property channels.

Prevent lockstep through dependencies, not arbitrary delays.

### Derive interpolation

Choose monotonic cubic for directed reveals, critically damped spring for
controlled settling, linear for uniform channels, and stepped for intentional
discrete states. Store tempo, settle damping, and stage safe-area variables;
never assume one curve fits every property.

### Responsive stage

Derive scale from available width/height minus inline/block safe areas and set
those areas from maximum transformed actor bounds. Do not use a fixed multiplier.

### Crossing topology

For self-crossing or braided marks: identify nodes and over/under order; split
visibility as needed; reveal with clips or ordered occluders; preserve one global
progress variable; derive local progress from measured arcs; and verify no
nonlocal branch appears early.

Use a moving cursor accent only when it belongs to the brand language. It MUST NOT hide a topology or timing defect.

### Web runtime

Follow `guides/runtime-contract.md`. The delivery MUST be dependency-free unless
dependencies are approved, expose the required readiness and control globals,
render the canonical mark after finish, pause when hidden, respect reduced
motion, provide keyboard-accessible controls, and avoid layout shift.

## INSTRUMENT

At beat boundaries and risk intervals collect `time_ms`, `active_beat`,
`actor_states`, `visible_bounds`, `progress_values`,
`changed_pixels_or_alpha_mass`, and `runtime_errors`.

Risk intervals include crossings, occluder changes, actor handoffs, spring extrema, viewport approaches, and loop seams.

Build a dependency-free delivery adapter only after the motion plan validates:

```text
tools/motiflux.py validate motion-plan motion-plan.yaml
tools/motiflux.py build mark.svg motion-plan.yaml <output-dir>
```

After compilation, run the scoped offline runtime probe:

```text
tools/motiflux.py probe <output-dir>
```

This may prove static runtime markers, JavaScript syntax, and the local Node
harness. It does not prove browser layout, pixels, console behavior in a real
browser, or the accessibility tree. Those remain explicit `not_run` items.

## VALIDATE

### Geometry

Verify constraint tolerances, topology, enlarged edges, and scene complexity.

### Temporal behavior

Check monotonic progress, velocity/acceleration continuity, handoffs, visibility
intervals, safe bounds, and loop seam compatibility.

Use telemetry plus targeted frames. Do not rely on evenly spaced screenshots alone.

### Canonical end state

Define a semantic fingerprint with `viewBox`, `actor_ids`, `path_data_hashes`,
`paint_attributes`, `transform_matrices`, and `layer_order`.

At runtime finish, serialize the final scene, compare its fingerprint with the
canonical mark, require exact geometry/paint/transform/layer equality, then
render both states through the same browser. Apply a declared antialiasing
tolerance (default 0.25% differing pixels and maximum channel delta 8); semantic
inequality always fails.

Vector semantics are authoritative; pixel tolerance absorbs renderer noise.

### Accessibility and runtime

Verify reduced motion, keyboard controls, visible focus, no console errors,
unapproved external requests, layout shift, and incorrect replay or tempo
behavior. Apply the browser/runtime contract from `guides/runtime-contract.md`.

Audit structured telemetry with:

```text
tools/motiflux.py audit telemetry.json --duration-ms <duration>
```

An audit with missing canonical, browser, or accessibility evidence remains a
candidate even when available progress samples are monotonic.

## DELIVER

Write evidence.json:

    status: complete | candidate
    source:
    constraint_summary:
    geometry_metrics:
    motion_metrics:
    canonical_fingerprint:
    pixel_tolerance:
    accessibility:
    substituted_tools: []
    not_run: []
    unresolved: []

Return `complete` only when the package exists; identity, topology, scene graph,
motion graph, telemetry, canonical fingerprint, rendered end state,
accessibility, and runtime checks pass; and `not_run` and `unresolved` are empty.
Otherwise return `candidate` and preserve every missing or uncertain item.

## Invariants

- Identity constraints outrank raster noise.
- Geometry is accepted before choreography.
- Scene actors encode transform and occlusion responsibilities.
- Timing emerges from beat content and dependencies.
- Crossing behavior is solved as visibility topology.
- Runtime telemetry accompanies visual judgment.
- Canonical vector semantics outrank pixel coincidence.
- Missing evidence remains missing.
