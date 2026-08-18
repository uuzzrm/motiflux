---
name: motiflux
description: "Motiflux V1 reconstructs raster brand marks as editable SVG scene graphs and designs responsive, brand-derived motion systems for web delivery. Use for logo reconstruction, logo reveals, splash sequences, brand intros, loading states, idle motion, and hover interactions. Route requests through theme tags such as premium, product-system, developer, AI-generative, fintech, security, luxury, automotive, sports, commerce, cinematic, nature, gaming, and accessibility. Build from a visual constraint graph, choose geometry by explainability, author choreography as a dependency graph, handle crossings with topology-aware occlusion, and validate with landmark error, contour distance, temporal telemetry, accessibility checks, and semantic end-state fingerprints."
---

# Motiflux V1

## Operating contract

Convert a raster mark into an editable vector scene and a responsive motion package.

Optimize in this order:

1. identity-bearing landmarks;
2. contour and negative-space fidelity;
3. editable scene structure;
4. motion legibility and brand character;
5. responsive and accessible behavior;
6. compact implementation.

Use MUST for completion requirements, SHOULD for defaults, and MAY for optional behavior. If a MUST cannot be verified, return candidate, not_run, or blocked; do not claim completion.

Do not infer provenance from this file. Preserve truthful attribution and licensing separately when the project incorporates prior work.

## Motiflux model

Represent the job with four linked models:

    constraint_graph:
      landmarks: []
      contours: []
      negative_spaces: []
      symmetry_axes: []
      color_regions: []

    scene_graph:
      actors: []
      parent_links: []
      occlusion_links: []
      transform_anchors: []

    motion_graph:
      beats: []
      dependencies: []
      overlaps: []
      interaction_states: []

    evidence_ledger:
      geometry_metrics: {}
      motion_metrics: {}
      accessibility: {}
      unresolved: []

Every design decision MUST trace to one of these models.

## Preflight

Resolve files relative to this SKILL.md. Inspect available tools/, guides/, templates/, and agents/openai.yaml.

Use optional resources only when present:

- guides/form-reconstruction.md for difficult geometry;
- guides/motion-language.md for personality-to-motion mapping;
- guides/crossing-topology.md for self-crossing marks;
- guides/web-runtime.md for package hooks and responsive behavior;
- guides/motion-themes.md for theme routing and algorithm recipes;
- tools/measure_mark.py for source analysis;
- tools/compare_shape.py for geometry metrics;
- tools/audit_motion.py for temporal telemetry;
- tools/build_web_package.py for delivery assembly.

If a resource is absent, use an equivalent local capability and record the substitution. Do not invent a missing file or report its checks as run.

If agents/openai.yaml exists, ensure its name, summary, and default prompt match Motiflux V1.

## Theme router

When the request includes a style, industry, reference system, audience, or motion adjective, read guides/motion-themes.md before composing.

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

Require one PNG, JPG, WebP, or screenshot source. Use supplied brand context. Ask only when ambiguity changes the intended surface or motion behavior.

Default surface: responsive web intro that settles into a static mark.

Required package:

    mark.svg
    motion.html
    motion-plan.yaml
    evidence.json
    evidence/
      source-analysis.json
      geometry/
      motion/
      accessibility/

Optional:

    motion.css
    motion.js
    preview.webp

Do not require a particular internal script or filename beyond this package contract.

## Workflow

    OBSERVE
      -> MODEL
      -> RECONSTRUCT
      -> COMPOSE
      -> INSTRUMENT
      -> VALIDATE
      -> DELIVER

Do not compose motion before the reconstructed scene reaches geometry acceptance.

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

Create one actor for each independently transformable or occluding part:

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

The delivery MUST:

- be dependency-free unless dependencies are approved;
- expose window.__motifluxReady;
- expose window.__motifluxControl.seek(ms);
- expose window.__motifluxControl.finish();
- render the canonical mark after finish;
- support replay and current-playback tempo changes;
- pause when the document is hidden;
- show the canonical mark under reduced motion;
- provide keyboard-accessible semantic controls;
- avoid motion-triggered layout shift.

Interactive studies are optional unless requested.

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

Verify reduced motion, keyboard controls, visible focus, no console errors, no unapproved external requests, no layout shift, and correct replay and tempo behavior.

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
