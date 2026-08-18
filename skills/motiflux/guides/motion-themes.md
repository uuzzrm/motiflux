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
    implementation:
    controls:
    exclusions: []
    qa_focus: []

Use one primary theme and no more than two modifiers. Public analogues describe published design-system principles; they do not prove that a named company uses the exact recipe.

## 1. System-spatial

Tags: system, product, SaaS, dashboard, enterprise, interface, structured, clear.

Public analogues: Material Design motion, Fluent motion, Atlassian motion, and Carbon-style system thinking.

Design intent: communicate state change, hierarchy, and spatial continuity.

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
