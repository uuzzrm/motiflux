# Motiflux motion theme atlas

Use this file as a routing table. It is an algorithm catalog, not a list of brand copies.

## Contents

- System-spatial
- Premium-quiet
- Developer-open
- AI-field
- Fintech-trust
- Security-shield
- Commerce-energy
- Automotive-precision
- Sports-impact
- Cinematic-title
- Nature-flow
- Gaming-world
- Accessibility-first
- Theme composition
- Public reference index

## Theme record

For the selected theme, write:

    primary:
    matched_tags: []
    modifiers: []
    public_analogue:
    design_intent:
    algorithm_stack: []
    trajectory_id:
    trajectory_summary:
    implementation:
    controls:
    foreground:
      source_actors: []
      stage_order: []
      path_strategy:
      speed_profile:
      fallback:
      proof: []
    exclusions: []
    qa_focus: []

Use one primary theme and no more than two modifiers. Public analogues describe published design-system principles; they do not prove that a named company uses the exact recipe.

## Foreground construction contract

The foreground is the supplied mark's identity-bearing geometry: paths, strokes,
monogram, wordmark or glyphs, accents, and topology-bearing occluders. Backgrounds,
particles, glow, camera movement, palette, and global opacity are secondary.
They may support a theme, but they cannot be the theme's only difference.

Every theme MUST declare and execute a distinct `(stage_order, path_strategy,
speed_profile)` tuple. `runtime.tempo` is only a baseline; the speed profile MUST
also describe per-stage duration, easing, overlap, or settle behavior. A generic
circle/rectangle crop, full-mark fade, global transform, or decorative particle
field is not a foreground construction unless it exposes measured source actors
in the declared order.

Use these stage roles and map them to real source actors:

- `seed`: one or more source-derived anchors or a minimal identity fragment;
- `trace`: a measured contour, arc, stroke, or component interval;
- `assemble`: identity components join in the theme-specific order;
- `lockup`: monogram, wordmark, glyph order, spacing, and occlusion settle;
- `canonical`: the exact accepted source scene, held long enough to read.

For a source with a symbol and wordmark, a concrete plan may be
`seed -> arc -> bar -> monogram -> wordmark -> canonical`. If a component is not
present or cannot be measured, map the stage to the available source actor and
record the omission; never invent a replacement shape.

The selected record MUST be serialized in `motion-plan.yaml` as `foreground` or
`foreground_plan`, including source actor IDs, stage order, path strategy, speed
profile, fallback, and proof points. Motion evidence MUST show stage-boundary and
mid-stage foreground snapshots with actor IDs, bounds or alpha mass, progress, and
speed. Compare same-source themes on foreground vectors or alpha, not backgrounds.

If decomposition or traversal is unreliable, use measured source intervals as the
fallback. If that is also unavailable, use `static-canonical` (or `opacity-only`
for reduced motion), mark the result `candidate`, and record the missing
`foreground-decomposition` or `trajectory-execution` evidence.

## Theme foreground matrix

Use the row as the minimum executable distinction for the selected theme. The
existing algorithm stack and implementation notes refine the row; they do not
replace it.

| Theme | Foreground order | Path strategy | Speed profile | Minimum proof |
| --- | --- | --- | --- | --- |
| `system-spatial` | `seed -> nodes -> relations -> monogram -> wordmark -> canonical` | `knowledge-graph-lock`: anchor-to-anchor placement and connector order | hierarchy-weighted stagger; monotonic; slower at lock | nodes and relations precede the lockup |
| `premium-quiet` | `seed -> outer contour -> monogram -> wordmark -> canonical` | `contour-etch`: measured perimeter traversal, then solid fill | slow etch, long stillness, low-amplitude settle | source contour leads; no generic crop |
| `developer-open` | `seed -> tokens -> stems/paths -> glyphs -> wordmark -> canonical` | `token-commit`: deterministic actor or glyph commits | even token cadence with declared pauses; no opaque spring | replay preserves commit order |
| `ai-field` | `signals -> points -> arcs -> monogram -> wordmark -> canonical` | `signal-convergence`: deterministic signals land in measured pixels | accelerate toward geometry, decelerate at lockup | signals land in source actors and clear before final |
| `fintech-trust` | `origin -> progress ring -> monogram -> wordmark -> confirm -> canonical` | `progress-confirm`: guarded center/outward progress | steady processing; short bounded confirmation; calm settle | confirmation never precedes canonical geometry |
| `security-shield` | `boundary -> aperture -> interior -> monogram -> wordmark -> canonical` | `boundary-unlock`: perimeter-first occlusion and aperture | guarded perimeter, quick verify, deliberate unlock | boundary precedes interior and remains interruptible |
| `commerce-energy` | `seed -> burst components -> monogram -> wordmark -> action accent -> canonical` | `burst-assembly`: bounded release from a shared origin | anticipation, fast burst, rapid stable settle | action accent follows identity assembly |
| `automotive-precision` | `track -> large forms -> monogram -> wordmark -> scan -> canonical` | `kinematic-lock`: one-axis path with velocity continuity | heavy actors slow; accents fast; jerk-limited handoffs | no teleportation or uncontrolled overshoot |
| `sports-impact` | `compressed silhouette -> axis release -> monogram -> wordmark -> recovery -> canonical` | `impact-release`: bounded compression, directional release, recovery | sharp burst, controlled overshoot, short recovery | peak silhouette remains recognizable |
| `cinematic-title` | `aperture -> contour -> monogram -> wordmark -> reading pause -> canonical` | `aperture-title`: staged aperture and depth reveal | slow exposure, deliberate silence, long reading pause | atmosphere never hides the identity moment |
| `nature-flow` | `root -> curve flow -> monogram -> wordmark -> settle -> canonical` | `organic-current`: curvature-following low-frequency flow | variable drift with damped settle; no jitter | flow follows measured curves and stops at canonical |
| `gaming-world` | `orbit tokens -> emblem -> monogram -> wordmark -> reward clear -> canonical` | `orbit-quest`: seeded orbits and deterministic reward assembly | spawn/accumulate, reward snap, then clear the field | hero actors remain readable and replay is deterministic |
| `accessibility-first` | `semantic seed -> ordered components -> monogram -> wordmark -> static canonical` | `semantic-fade`: order-preserving opacity and minimal translation | opacity-first; short necessary movement; no overshoot | reduced motion preserves order, focus, and static equality |

When the source lacks a listed component, substitute a measured source actor and
record the mapping in `foreground.source_actors`. A theme is not complete when
only its background, color, particles, camera, or labels differ from another
variant.

## 1. System-spatial

Tags: system, product, SaaS, dashboard, enterprise, interface, structured, clear.

Public analogues: Material Design motion, Fluent motion, Atlassian motion, and Carbon-style system thinking.

Design intent: communicate state change, hierarchy, and spatial continuity.

Foreground trajectory: `knowledge-graph-lock` - place semantic nodes, connect
their relationships, and lock the supplied mark component by component. This
also covers education, learning, teaching, course, and knowledge requests.

Algorithm stack:

- scene-graph dependency ordering;
- shared spatial-anchor resolution;
- monotonic cubic interpolation;
- container-aware bounds;
- reduced-motion substitution.

Implementation:

- move actors from their semantic source location;
- preserve parent-child spatial relationships;
- use short interaction transitions and longer contextual reveals;
- derive timing from distance and hierarchy;
- keep the canonical mark visible during uncertainty.

Controls: hierarchy weight, spatial distance, stagger window, reduced-motion mode.

Exclude: decorative particles, unexplained overshoot, random offsets, simultaneous global motion.

QA focus: spatial continuity, no layout shift, focus order, and bounds.

## 2. Premium-quiet

Tags: premium, luxury, fashion, beauty, editorial, quiet, elegant, minimal.

Public analogues: restrained editorial motion patterns and Apple-style emphasis on purpose, hierarchy, and user control.

Design intent: create perceived value through restraint, material presence, and deliberate timing.

Algorithm stack:

- low-amplitude transform field;
- opacity and mask sequencing;
- slow monotonic interpolation;
- optical-alignment correction;
- low-frequency highlight pass.

Implementation:

- reveal the highest-value contour first;
- use small translation and scale ranges;
- reserve contrast changes for the final identity moment;
- maintain generous stillness between beats;
- avoid visible mechanical overshoot.

Controls: amplitude, pause ratio, contrast reveal, optical offset.

Exclude: bounce, noisy particles, fast per-letter cascades, and excessive blur.

QA focus: contour integrity, optical centering, frame-to-frame calm, and typography.

## 3. Developer-open

Tags: developer, open source, API, CLI, code, tooling, technical, precise.

Public analogues: GitHub Primer motion and interface-oriented system motion.

Design intent: make transformation legible to technical users and preserve an inspectable causal chain.

Algorithm stack:

- deterministic state machine;
- tokenized property channels;
- typed event timeline;
- path and actor metadata;
- reproducible seek controls.

Implementation:

- expose named phases and inspectable actor ids;
- show construction or assembly through explicit dependencies;
- prefer exact state transitions over atmospheric effects;
- include keyboard-accessible replay and debug labels when requested.

Controls: phase stepping, event log, seek, and reduced-motion fallback.

Exclude: opaque procedural randomness, hidden external services, and timing that cannot be replayed.

QA focus: determinism, event order, inspectability, and keyboard operation.

## 4. AI-field

Tags: AI, machine learning, neural, data, model, generative, future, intelligent.

Public analogues: public AI product motion patterns using progressive disclosure, signal flow, and responsive feedback. Do not attribute an exact internal recipe.

Design intent: suggest intelligence through organized transformation, not science-fiction decoration.

Foreground trajectory: `signal-convergence` - deterministic external signals
travel into measured Logo pixels, then the supplied wordmark assembles.

Algorithm stack:

- constraint-to-signal mapping;
- particle field only as a secondary layer;
- graph flow or vector-field guidance;
- progressive disclosure;
- confidence-bounded morphing.

Implementation:

- start from a stable semantic mark;
- let abstract signals converge into the mark's real geometry;
- use deterministic seeded particles when particles are necessary;
- give signal density a functional meaning;
- end with a quiet canonical state.

Controls: field density, convergence rate, signal amplitude, seed, and accessibility mode.

Exclude: random neural-network imagery, fake data claims, uncontrolled noise, and particle-first identity.

QA focus: determinism, semantic landing, performance, reduced motion, and no misleading data implication.

## 5. Fintech-trust

Tags: fintech, banking, payments, trust, secure, finance, institutional, reliable.

Public analogues: system design patterns prioritizing predictable feedback, hierarchy, and calm state transitions.

Design intent: communicate reliability, controlled movement, and successful resolution.

Algorithm stack:

- monotonic progress;
- guarded state transitions;
- bounded spring only for confirmation;
- high-contrast completion cue;
- failure-safe cancellation.

Implementation:

- use clear start, processing, success, and idle states;
- never make money or security status ambiguous;
- keep motion reversible or cancellable;
- use a compact completion accent after the mark resolves.

Controls: progress mode, confirmation amplitude, cancellation, and reduced motion.

Exclude: playful bounce during security states, sudden camera motion, and ambiguous looping.

QA focus: state correctness, cancellation, contrast, announcement timing, and no false success.

## 6. Security-shield

Tags: security, privacy, identity, authentication, defense, shield, compliance.

Public analogues: accessible system motion with clear focus, status feedback, and user control.

Design intent: convey boundary, verification, and controlled access.

Algorithm stack:

- boundary-first reveal;
- occlusion and aperture logic;
- finite-state verification sequence;
- restrained lock/unlock transition;
- interruptible animation.

Implementation:

- reveal perimeter or boundary before interior detail;
- use one explicit verification transition;
- make secure and insecure states visually distinct;
- freeze safely when interrupted or hidden.

Controls: verification state, interrupt, focus target, and reduced motion.

Exclude: glitch as default identity, flickering security warnings, and hidden state changes.

QA focus: semantic state, interruption, focus, contrast, and temporal clarity.

## 7. Commerce-energy

Tags: commerce, retail, shopping, marketplace, consumer, sale, friendly, conversion.

Public analogues: public commerce design systems using quick interaction feedback and clear affordances.

Design intent: create approachability and action without making the brand feel unstable.

Algorithm stack:

- short interaction transitions;
- spring-like confirmation;
- badge or accent choreography;
- responsive hit-area anchoring;
- action-completion state machine.

Implementation:

- make the mark react to action context;
- use a small anticipatory cue before a cart, save, or purchase confirmation;
- reserve larger motion for high-value moments;
- return rapidly to a stable idle state.

Controls: interaction speed, confirmation scale, touch-safe range, and reduced motion.

Exclude: constant motion, bait-like pulses, and delayed affordance feedback.

QA focus: input latency, hit-area stability, repeat action, focus, and touch behavior.

## 8. Automotive-precision

Tags: automotive, mobility, transport, engineering, precision, performance, industrial.

Public analogues: engineering-oriented motion emphasizing physical continuity, hierarchy, and controlled acceleration.

Design intent: express mass, direction, precision, and mechanical confidence.

Algorithm stack:

- kinematic trajectory planning;
- acceleration and jerk limits;
- anchor-based transforms;
- directional light sweep;
- constrained settle.

Implementation:

- define physical source and destination for each actor;
- use velocity continuity at handoffs;
- slow large masses and sharpen small accents;
- keep the camera stable unless explicitly requested.

Controls: mass, acceleration limit, directional vector, and settle damping.

Exclude: weightless teleportation, arbitrary rotation, and uncontrolled elastic overshoot.

QA focus: jerk continuity, clipping, anchor correctness, and responsive bounds.

## 9. Sports-impact

Tags: sports, fitness, competition, speed, impact, bold, dynamic.

Public analogues: broadcast and performance-interface motion grammar; use as a general design analogue.

Design intent: create energy through anticipation, compression, release, and recovery.

Algorithm stack:

- anticipation compression;
- velocity burst;
- directional smear or stretch;
- controlled overshoot;
- recovery-to-idle state.

Implementation:

- build tension with a short counter-motion;
- release along the mark's dominant axis;
- limit deformation so identity survives speed;
- finish with a readable recovery pose.

Controls: impact strength, axis, stretch limit, and recovery time.

Exclude: distortion that changes glyph identity, perpetual shake, and unreadable peak frames.

QA focus: silhouette recognition at peak, motion-blur bounds, reduced motion, and no seizure risk.

## 10. Cinematic-title

Tags: cinematic, film, title, trailer, story, dramatic, suspense.

Public analogues: title-sequence grammar and editorial staging, not a claim about a specific studio pipeline.

Design intent: reveal meaning through attention control, scale, silence, and composition.

Algorithm stack:

- camera-space composition;
- depth-layer parallax;
- masked reveal;
- light-to-dark exposure curve;
- beat-driven soundless timing.

Implementation:

- establish atmosphere only after the mark's composition is known;
- stage the primary identity moment;
- use depth sparingly and protect the final silhouette;
- support a static fallback for reduced motion.

Controls: depth, exposure, camera drift, reveal aperture, and pause.

Exclude: atmosphere that obscures the logo, arbitrary lens effects, and no final reading pause.

QA focus: final readability, crop safety, contrast, reduced motion, and static fallback.

## 11. Nature-flow

Tags: nature, organic, wellness, sustainable, water, wind, growth, calm.

Public analogues: organic motion built from continuous curves and variable velocity.

Design intent: imply growth, breath, flow, and connection without losing mark structure.

Algorithm stack:

- curvature-following flow;
- bounded low-frequency noise;
- phase-offset secondary actors;
- damped wave or drift;
- organic settle.

Implementation:

- derive direction from the mark's curves;
- use low-frequency variation rather than random jitter;
- couple secondary actors to the primary contour;
- maintain a stable canonical endpoint.

Controls: flow amplitude, frequency, phase, coupling, and calm mode.

Exclude: unbounded noise, liquid deformation that erases topology, and endless movement in a logo lockup.

QA focus: smoothness, amplitude bounds, topology, loop seam, and reduced motion.

## 12. Gaming-world

Tags: gaming, esports, fantasy, sci-fi, character, quest, arcade, playful.

Public analogues: interactive-entertainment motion grammar; do not copy a named game's assets or signature.

Design intent: create personality, reward, and world-building around a recognizable mark.

Algorithm stack:

- stateful combo or quest beats;
- particle and emblem secondary layers;
- stylized squash and stretch;
- camera emphasis;
- interaction-triggered replay.

Implementation:

- define the hero mark as the stable player-readable object;
- use secondary effects to signal state, not replace identity;
- make replay deterministic with a seed;
- provide a quiet idle state.

Controls: effect density, seed, intensity, camera emphasis, and accessibility mode.

Exclude: copyrighted character imitation, uncontrolled flashing, and effects that block controls.

QA focus: readability, deterministic replay, flashing limits, performance, and reduced motion.

## 13. Accessibility-first

Tags: accessible, reduced motion, calm, inclusive, low motion, keyboard, assistive.

Public analogues: Apple, Fluent, Spectrum, and other public systems' emphasis on purposeful motion and user control.

Design intent: preserve orientation and feedback while minimizing vestibular, cognitive, and visual load.

Algorithm stack:

- opacity and color state changes;
- short translation only when necessary;
- user-controlled pause and tempo;
- focus-preserving transitions;
- static canonical fallback.

Implementation:

- design the static state first;
- replace large movement with opacity, color, or border changes;
- respect prefers-reduced-motion;
- keep keyboard focus and reading order stable;
- expose pause and replay when motion is nonessential.

Controls: pause, reduced motion, tempo, contrast, and focus behavior.

Exclude: parallax, camera shake, forced autoplay, flashing, and motion-only meaning.

QA focus: accessibility tree, focus, contrast, reduced motion, and static equivalence.

## 14. Theme composition

Examples:

    AI security startup -> AI-field + Security-shield + technical
    quiet luxury skincare -> Premium-quiet + Nature-flow + calm
    high-performance sports car -> Automotive-precision + Sports-impact + bold
    developer tool for finance -> Developer-open + Fintech-trust + quiet
    indie game title reveal -> Gaming-world + Cinematic-title + dramatic

Resolve collisions by priority:

1. explicit user requirement;
2. product risk and accessibility;
3. brand personality;
4. industry convention;
5. visual inference from the source.

Write the selected primary, modifiers, rejected alternatives, and rationale to motion-plan.yaml.

## Public reference index

Use these as public principle references, not implementation claims:

- Material Design 3 motion: https://m3.material.io/styles/motion/overview
- Apple Human Interface Guidelines, Motion: https://developer.apple.com/design/human-interface-guidelines/motion
- Microsoft Fluent 2 Motion: https://fluent2.microsoft.design/motion
- Adobe Spectrum Motion: https://spectrum.adobe.com/page/motion/
- Atlassian Motion: https://atlassian.design/foundations/motion/
- Shopify Polaris motion: https://polaris.shopify.com/design/motion
- GitHub Primer: https://primer.style/product/guides/motion
- Airbnb Lottie documentation: https://airbnb.io/lottie/
