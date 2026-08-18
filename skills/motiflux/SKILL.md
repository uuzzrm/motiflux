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

Read only the direct resource needed for the current phase:

- `guides/motion-themes.md` — theme and algorithm routing;
- `guides/algorithm-catalog.md` — reusable algorithm families and proof gates;
- `guides/output-contract.md` — artifact names and status semantics;
- `guides/runtime-contract.md` — browser hooks and safety behavior;
- `schemas/*.schema.json` — machine-readable artifact contracts;
- `tools/*.py` — executable adapters behind the seams.

Run tools from the skill directory. Treat their JSON output as evidence, not as
a replacement for design judgment. If an optional capability is unavailable,
record the substitution or missing check; do not invent a result.

Represent every task with four linked models: `constraint_graph` for landmarks,
contours, gaps, symmetry, and color; `scene_graph` for actors, parents, layers,
anchors, and occlusion; `motion_graph` for beats, dependencies, overlaps, and
interaction states; and `evidence_ledger` for geometry, motion, accessibility,
substitutions, `not_run`, and `unresolved`. Every design decision MUST trace to
one model and remain inspectable in an artifact.

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

Use `measure` before modeling, `compare` before motion, `build` only after a
contract-valid plan exists, and `audit` before claiming motion completion.

## OBSERVE

Measure and record:

- source dimensions, color mode, alpha, and background;
- foreground color clusters;
- antialiasing, compression, thresholding, and blur artifacts;
- identity-bearing corners, extrema, junctions, terminals, and centers;
- enclosed and open negative spaces;
- likely symmetry, repetition, and alignment relations;
- mark, wordmark, letters, accents, and containers.

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

Assign each visual constraint:

    id:
    kind: landmark | contour | gap | symmetry | color
    importance: identity | structural | cosmetic
    target:
    tolerance:
    dependencies: []

Identity constraints dominate cosmetic pixel agreement.

### Build scene graph

Create one actor for each independently transformable or occluding part. Store
the full actor record in `motion-plan.yaml`:

    id:
    role:
    geometry_strategy:
    parent:
    anchor:
    layer:
    occludes: []
    occluded_by: []

Use stable semantic ids. Avoid child-index selectors.

### Define motion language

Derive three motion traits from the mark and brand context. Map each trait to:

- tempo range;
- acceleration character;
- overlap amount;
- deformation limit;
- preferred spatial direction;
- stillness requirement.

Record the mapping in motion-plan.yaml. Do not choose interpolation or effects without a traceable trait.

## RECONSTRUCT

### Choose geometry by explainability

For each actor, choose the smallest model that explains its constraints:

1. primitive;
2. transformed primitive family;
3. centerline plus width profile;
4. sparse Bezier contour;
5. simplified measured outline.

Escalate only when identity or structural constraints fail.

Prefer editable text when an available font matches sufficiently. Convert to paths only when exact glyph identity or per-glyph deformation requires it.

### Preserve topology

Preserve contour winding, hole count, component count, crossing order, open versus closed state, joins, and terminals.

Do not encode a crossing only as a convenient compound path when later occlusion requires independent control.

### Define draw traversal

For a drawn reveal, store explicit traversal metadata:

    actor:
    start_landmark:
    end_landmark:
    direction:
    measured_length:
    visible_intervals: []

Use browser measurement or geometry tooling to derive real lengths at build time.

### Geometry acceptance

Compute:

- weighted landmark error;
- symmetric contour or Chamfer distance;
- negative-space area and centroid error;
- topology match;
- actor, segment, and control-point counts.

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

Describe motion as named beats:

    beats:
      - id: orient
        intent: establish direction and focus
      - id: form
        intent: reveal identity-bearing structure
      - id: bind
        intent: connect secondary actors
      - id: resolve
        intent: settle into canonical mark

Assign duration weights from visual distance, actor area, curvature, reading order, and interaction context. Normalize weights to target duration. Do not impose a fixed global phase ratio.

### Build dependency graph

For each action, record:

    actor:
    beat:
    starts_after: []
    may_overlap: []
    must_finish_before: []
    anchor:
    property_channels: []

Prevent lockstep through dependencies, not arbitrary delays.

### Derive interpolation

Choose interpolation per property and beat:

- monotonic cubic for directed reveals;
- critically damped spring for controlled settling;
- linear for physically uniform channels;
- stepped for intentional discrete states.

Store Motiflux variables:

    :root {
      --motiflux-tempo: 1;
      --motiflux-settle-damping: 0.82;
      --motiflux-stage-inline: clamp(1rem, 6vw, 6rem);
    }

Do not assume one curve fits every property.

### Responsive stage

Derive scale:

    available_width = container_width - 2 * inline_safe_area
    available_height = container_height - 2 * block_safe_area
    scale = min(available_width / mark_width, available_height / mark_height)

Set safe areas from maximum transformed actor bounds. Do not use a fixed presentation multiplier.

### Crossing topology

For self-crossing or braided marks:

1. identify crossing nodes;
2. record over/under order per traversal;
3. split the visibility graph as needed;
4. reveal segments with clip regions or ordered occluders;
5. preserve one global progress variable;
6. derive local progress from measured arc intervals;
7. verify no nonlocal branch appears early.

Use a moving cursor accent only when it belongs to the brand language. It MUST NOT hide a topology or timing defect.

### Web runtime

Follow `guides/runtime-contract.md`. The delivery MUST be dependency-free unless
dependencies are approved, expose the required readiness and control globals,
render the canonical mark after finish, pause when hidden, respect reduced
motion, provide keyboard-accessible controls, and avoid layout shift.

## INSTRUMENT

At each beat boundary and risk interval, collect:

    time_ms:
    active_beat:
    actor_states:
    visible_bounds:
    progress_values:
    changed_pixels_or_alpha_mass:
    runtime_errors:

Risk intervals include crossings, occluder changes, actor handoffs, spring extrema, viewport approaches, and loop seams.

Build a dependency-free delivery adapter only after the motion plan validates:

```text
tools/motiflux.py validate motion-plan motion-plan.yaml
tools/motiflux.py build mark.svg motion-plan.yaml <output-dir>
```

## VALIDATE

### Geometry

Verify declared constraint tolerances, topology, enlarged edge quality, and scene complexity.

### Temporal behavior

Check:

- intended progress is monotonic;
- velocity and acceleration have no unexplained discontinuities;
- no required handoff stalls;
- no branch appears before its visibility interval;
- transformed bounds remain inside safe areas;
- loop state and first derivative are seam-compatible.

Use telemetry plus targeted frames. Do not rely on evenly spaced screenshots alone.

### Canonical end state

Define a semantic fingerprint:

    viewBox:
    actor_ids:
    path_data_hashes:
    paint_attributes:
    transform_matrices:
    layer_order:

At runtime finish:

1. serialize the final scene;
2. compare its fingerprint with the canonical mark;
3. require exact geometry, paint, transform, and layer equality;
4. render both states through the same browser;
5. compare with declared antialiasing tolerance, default 0.25% differing pixels and maximum channel delta 8;
6. fail semantic inequality even when pixels look close.

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

Return complete only when:

- required package files exist;
- identity and topology constraints pass;
- scene graph matches vector structure;
- motion graph traces to motion language;
- telemetry has no unexplained discontinuity;
- canonical semantic fingerprint matches;
- rendered end state is within declared tolerance;
- accessibility and runtime checks pass;
- not_run and unresolved are empty.

Otherwise return candidate and preserve unresolved evidence.

## Invariants

- Identity constraints outrank raster noise.
- Geometry is accepted before choreography.
- Scene actors encode transform and occlusion responsibilities.
- Timing emerges from beat content and dependencies.
- Crossing behavior is solved as visibility topology.
- Runtime telemetry accompanies visual judgment.
- Canonical vector semantics outrank pixel coincidence.
- Missing evidence remains missing.
