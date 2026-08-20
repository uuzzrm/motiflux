---
name: motiflux
description: "Motiflux V1 is an AI-first skill for source-aware logo animation, prompt routing, bounded raster observation, deterministic theme trajectories, tuning, and export guidance. Preserve editable SVG actors; for PNG, JPG, and WebP, keep source pixels authoritative, expose reviewable candidates, and never imply automatic raster-to-equivalent-SVG reconstruction."
---

# Motiflux V1

## Shortest prompt formula

Use this shortest prompt formula, in this order:

```text
source + identity invariant -> surface -> one theme keyword -> observed foreground sequence -> duration/speed/direction -> background/particles -> reduced motion -> output format -> evidence required
```

Interpret each slot literally. `source + identity invariant` names the supplied
file and what must remain unchanged; `surface` names the delivery context;
`one theme keyword` selects one catalog route; `observed foreground sequence`
names only measured or explicitly accepted source actors; `duration/speed/direction`
sets timing and entry intent; `background/particles` sets secondary presentation;
`reduced motion` sets the accessible fallback; `output format` names requested
media; and `evidence required` names the checks that must actually run. A solid
background must include a color. If its color is omitted, resolve
`#0B0D12` and record `runtime.background.source: default`; do not present that
default as user-supplied intent. Direction is currently a preview entry cue
unless a source-specific adapter proves a full actor path. Pre-rendered GIF and
PDF cannot respond to the system reduced-motion setting, so request/provide the
canonical poster or another static output as the fallback.

## Mission and evidence rules

Act as a design-and-verification system. Convert a supplied mark and brand
context into the narrowest honest artifact set: source observations, a motion
plan, a responsive package when allowed, and an evidence ledger. Preserve SVG
structure/topology. For raster input, keep source pixels authoritative and
expose geometric actor candidates without claiming semantic recognition, OCR,
or equivalent editable vector reconstruction.

Use `MUST` for completion requirements, `SHOULD` for defaults, and `MAY` for
optional behavior. Keep these status layers separate:

- `candidate`: overall evidence is useful but open;
- `complete`: overall required evidence is closed;
- `needs-review`: a source role or actor binding is still a hypothesis;
- `preview`, `baked`, `verified`: output lifecycle states;
- `not_run`, `unresolved`: missing proof or unsupported execution.

One status never implies another. An unverified MUST keeps the result
`candidate` and the relevant item in `not_run` or `unresolved`.

Treat role review and artifact delivery as independent state machines. For a
component, `observed` means that pixels or source geometry were measured;
`candidate` means that a geometric role was proposed; `needs-review` means
that the proposal or actor binding is still unconfirmed; and `accepted` means
that the source or a human reviewer explicitly confirmed it. A top-level
`candidate` means that required evidence is still open. Never promote a role,
file, or route merely because a prompt named it.

## AI-readable truth model

Keep these record classes separate: `source-fact` (file and supplied pixels),
`geometric-observation` (masks, bounds, components, groups), `role-hypothesis`
(proposal plus confidence/evidence), `accepted-binding` (source or human
confirmation), and `render-evidence` (files and checks actually produced).
Never infer a later class from an earlier one. The raster handoff is:

```text
decode -> measure -> group -> propose -> review/accept -> bind or fallback
```

The minimum component record is `geometry_strategy: pixel-observation-only`
plus `role_review.proposed_role`, `accepted_role`, `confidence`,
`review_status`, and `evidence`. Keep `accepted_role: null` for
`observed`/`candidate`/`needs-review`; a prompt cannot confirm a role. This is
bounded geometric observation, never OCR, semantic recognition, or equivalent
editable-SVG reconstruction. Unsafe decomposition uses measured source pixels
and `static-canonical`.

## Canonical execution order

Treat the request as seven ordered handoffs. A later handoff cannot promote an
earlier hypothesis, replace a user decision, or supply evidence for a step that
did not run:

```text
source observation -> role review -> theme route -> animation plan
  -> user confirmation/tuning -> export delivery -> evidence
```

1. **Source observation.** Record the input path/format, identity invariant,
   dimensions, pixels or SVG actors, and observation limitations in
   `source-analysis.json`. Raster output is `observed` only for measured
   geometry.
2. **Role review.** For each candidate component, write `role_review` with
   `proposed_role`, `accepted_role`, `confidence`, `review_status`, and
   measured `evidence`. Keep `accepted_role: null` for `observed`, `candidate`,
   and `needs-review`; only source annotation or explicit human review can
   produce `accepted`.
3. **Theme route.** Match the user's industry, product, audience, style, and
   motion language to one catalog profile. Record the exact `primary_id`,
   `trajectory_id`, `matched_tags`, modifiers, and rejected candidates. Do not
   route from raster appearance as if it were semantic recognition.
4. **Animation plan.** Write `foreground_plan` with confirmed/measured
   `source_actors`, stable `stage_order`, `path_strategy`, `speed_profile`,
   visible proof, the theme's executable variant, runtime controls, and
   `fallback: static-canonical`. Do not invent a missing dot, arc, bar, letter,
   or wordmark.
5. **User confirmation/tuning.** Present the observation boundary, selected
   route, actor/stage plan, controls, requested outputs, and open gaps in a
   compact confirmation record. Wait for approval or a correction when the
   request is plan-only or an unresolved decision changes identity, route,
   stage order, or proof. Apply one tuning change at a time and preserve the
   source, route, and canonical fingerprint unless the user changes them.
6. **Export delivery.** Select a named adapter for each approved format. A
   browser control is `preview`; a generator-written file is `baked`; an
   unavailable adapter has `path: null` and `not_run`. Never treat a requested
   format as permission to fabricate an adapter or path.
7. **Evidence.** Inspect the written artifact and applicable source, stage,
   canonical, runtime, browser, and accessibility checks. Use `verified` only
   for checks that actually passed; otherwise retain `candidate` and list
   `not_run` or `unresolved`.

The compact handoff SHOULD preserve this nesting:

```yaml
source_observation: {status: observed|not_run, source_facts: [], limitations: []}
role_review: {status: accepted|needs-review, components: []}
theme_selection: {primary_id: canonical-id, trajectory_id: canonical-trajectory, matched_tags: [], rejected_candidates: []}
foreground_plan: {source_actors: [], stage_order: [], fallback: static-canonical}
confirmation: {status: pending|approved|revised|declined, scope: route|plan|tuning|role-review, source: user|explicit-request|default}
runtime: {duration_ms: 2200, tempo: 1.0, background: {}, particles: true, reduced_motion: static-canonical}
export: [{format: gif, path: null, lifecycle: preview|baked|verified}]
evidence: {status: complete|candidate, not_run: [], unresolved: []}
```

The lifecycle field answers “what happened”; evidence answers “what is
proven.” A GIF may be `baked` while the result remains `candidate`. Follow the
guides for request assembly and export/tuning details.

## User confirmation and tuning gate

Before export, show a compact confirmation record containing source identity,
observation boundary, route, foreground plan, runtime controls, outputs, and open
gaps. Ask for `approve plan`, `change route`, `change tuning`, `correct actor
mapping`, `preview only`, or `decline` when the choice is unresolved. Approval
does not turn raster hypotheses into semantic roles; explicit source or human
review is still required. Recompute only affected downstream records and keep
the source, stage order, route, and canonical fingerprint stable for tuning-only
changes. See `guides/prompting.md` for the record shape and copy-ready gate.

## Architecture map

Keep complexity behind stable seams:

| Need | Command or module | Main artifact |
| --- | --- | --- |
| source observation | `tools/motiflux.py measure`, `engine/raster.py` | `source-analysis.json` |
| theme routing | `tools/motiflux.py route` | `theme_selection` |
| artifact validation | `tools/motiflux.py validate` | validity report |
| geometry comparison | `tools/motiflux.py compare` | geometry evidence |
| motion audit | `tools/motiflux.py audit` | motion evidence |
| web delivery | `tools/motiflux.py build` | dependency-free package |
| complete job | `tools/motiflux.py project` | `project.json` |
| runtime contract | `tools/motiflux.py probe` | runtime-probe evidence |

The canonical catalog is `catalog/themes.json`. It is consumed by routing,
planning, runtime compilation, tests, and the showcase. Every profile MUST
have a unique `trajectory_id` and `trajectory_summary`; metadata without an
executable foreground effect is incomplete. Represent decisions with linked
`constraint_graph`, `scene_graph`, `motion_graph`, and `evidence_ledger` models.

## Canonical project pipeline

For a new source/request job, run the stable seam:

```text
tools/motiflux.py project <source> <request> <output>
```

The phase graph is `analyze -> route -> plan -> reconstruct -> verify-geometry -> compile -> verify-package -> verify-motion -> deliver`.

`PipelineRunner` records stage prerequisites, products, capabilities, order,
status, `not_run`, and `unresolved`. It also writes an artifact index with
SHA-256, size, and producer records. Theme IDs, actor IDs, beat IDs, parent,
occlusion, and dependency references MUST resolve. Raster input without a real
raster-to-vector adapter remains `candidate`; never label a placeholder vector
complete.

The project manifest is `<output>/project.json`; the companion
`artifact-index.json` is the file-level integrity record. `foreground_plan`,
`foreground_evidence`, `static-canonical`, and `complete evidence` are
contract vocabulary, not claims that a missing adapter ran.

The single-route showcase manifest is documented in
`guides/export-and-tuning.md`; it does not replace `<output>/project.json`,
`artifact-index.json`, or `showcase/output/growth-evidence.json`.

## Foreground construction contract

Identity-bearing source geometry is foreground: paths, monogram, wordmark,
glyphs, accents, and occluders. Backgrounds, particles, glow, camera, color,
and full-mark opacity are secondary and MUST NOT be the only theme difference.

Every selected theme MUST provide a `foreground_plan` containing
`source_actors`, `stage_order`, per-stage `path_strategy`, `speed_profile`,
visible `proof`, an executable `foreground_variant`, and a `static-canonical`
fallback. Use the stable machine
sequence `seed -> trace -> assemble -> lockup -> canonical`; the showcase may
label those stages `blank -> origin dot -> circular arc -> horizontal bar ->
P / monogram -> Prysai wordmark -> complete Logo` when those candidate roles
exist. Do not invent a missing dot, arc, bar, monogram, wordmark, or glyph.

The 13 themes MUST change how measured actors enter, travel, and settle. A
generic crop, global transform, complete-mark fade, or decorative field is not
foreground construction. A `foreground_variant` such as `scan-forward`,
`polar-counter`, `diagonal-reverse`, `wave-phase-a`, or `opacity-stable` is an
executable source-pixel reveal grammar, not a tag: it must be visible in
same-source midframes and must still land on the exact canonical source.
Evidence MUST include stage boundaries and one or more
progress-point snapshots with `stage_id`, source actors, foreground bounds or
alpha mass, path, speed, and a trajectory fingerprint. The canonical stage MUST
match the source exactly. For the checked-in atlas, use
`showcase/output/growth-evidence.json` for progress-point frame indices,
foreground mask hashes, and cross-theme trajectory comparison.

## Theme router

When a request contains industry, style, audience, reference system, or motion
language, read `guides/motion-themes.md`, then run `route`. Use
`guides/algorithm-catalog.md` to justify the stack. Normalize to:

```yaml
theme_selection:
  primary: one canonical theme ID
  primary_id: one canonical theme ID
  trajectory_id: catalog trajectory ID
  modifiers: []
  matched_tags: []
  rejected_candidates: []
  public_reference_basis: []
  algorithm_stack: []
```

Rules:

1. Match explicit industry/style language before inferring from the logo.
2. Choose one primary theme and at most two modifiers.
3. Record rejected conflicts instead of silently blending them.
4. If no route is clear, use `system-spatial` with quiet and accessible modifiers.
5. Set `primary_id` and `trajectory_id` from the same catalog profile; do not
   invent either identifier from prose.
6. Record matched language, algorithm types, controls, and rejected candidates
   in `motion-plan.yaml`. The route and algorithm stack describe a plan, not
   proof that a renderer executed it.
7. A public company or system is a principle analogue only; never claim its
   private recipe or endorsement.

Theme keywords are routing signals, not evidence about the supplied mark. Use
the most explicit industry or product context first, then style and motion
modifiers. Return the exact catalog `id`, `trajectory_id`, `matched_tags`, and
`rejected_candidates`; do not create a new theme ID from an adjective. A theme
must change the source-derived foreground route. A palette, particle field,
camera move, or label-only change is a tuning change, not a new trajectory.

The 13 canonical keyword categories are: system/product/education,
premium/luxury, developer/open source, AI/data, fintech/trust, security/privacy,
commerce/retail, automotive/engineering, sports/competition, cinematic/title,
nature/organic, gaming/world-building, and accessibility/reduced motion.
`education` is an alias within `system-spatial`, not a fourteenth route. Choose
one category using this precedence: explicit industry or product context first;
explicit accessibility or motion constraints second; broad style words only as a
tiebreaker. Select one primary canonical ID, add at most two modifiers, and
record rejected candidates. If no category is clear, use `system-spatial` with
quiet and accessible modifiers.

Canonical Chinese aliases include:

```text
教育/学习/课程/教学/知识 -> system-spatial; 科技/产品/SaaS/企业系统 -> system-spatial; 奢侈/时尚/美妆/极简/高级感 -> premium-quiet
开发者/开源/代码/API/工具 -> developer-open; 人工智能/AI/生成式/生成式AI/AI科技/数据/未来感 -> ai-field; 金融/支付/银行/可信/稳健 -> fintech-trust
安全/隐私/认证/防护/盾牌 -> security-shield; 电商/零售/购物/消费/促销 -> commerce-energy; 汽车/交通/工业/工程/性能 -> automotive-precision
体育/健身/竞技/速度/冲击 -> sports-impact; 电影/片头/预告/叙事/戏剧 -> cinematic-title; 自然/有机/健康/环保/成长 -> nature-flow
游戏/电竞/奇幻/科幻/街机 -> gaming-world; 无障碍/低动效/包容/键盘/辅助 -> accessibility-first
```

The router changes foreground choreography, not identity constraints. Public
aliases such as Material, Fluent, Spectrum, Primer, Polaris, HIG, Atlassian,
and Lottie may inform principles, but do not authorize copied artwork or
private implementation claims.

## Reference-brand and source policy

Use the user's supplied logo as the default demonstration source. Do not fetch,
embed, redraw, or animate a third-party company logo merely as an industry
example. If a third-party asset is supplied for a private experiment, retain
its provenance and request permission before publication. Keep unlicensed
third-party reference assets out of the default showcase.

## Inputs, prompts, and output boundaries

Require one PNG, JPG, WebP, or SVG source plus brand context. Keep the field
order from the shortest formula: source, surface, one route, observed
foreground, runtime, accessibility, outputs, and evidence. Read
`guides/prompting.md` for request assembly and `guides/export-and-tuning.md` for
keywords, pure backgrounds, tuning, and lifecycle states.

An omitted value is a recorded default or an open question, never permission to
invent identity. For `solid background`/`纯色背景` without a color, write
`background: {mode: solid, color: "#0B0D12", source: default}`. A user color is
`source: prompt`; transparent/theme modes stay explicit. Use measurable forms
such as `2200ms`, `speed 1.25x`, `no particles`, and `static-canonical reduced
motion`. Change one tuning field at a time and preserve actors, stage order, and
the canonical fingerprint. Browser changes are preview-only until an exporter
writes a file.

Keep `request`, `observation`, `plan`, and `evidence` separate. A prompt, route,
algorithm stack, preview, or hash supports a decision but does not prove
semantic role recognition, browser behavior, or a complete trajectory.

## OBSERVE

Measure dimensions, color/alpha, background, foreground mask, clusters, bounds,
centroids, layout, landmarks, and negative space; write `source-analysis.json`.
For SVG run `tools/motiflux.py measure <source.svg>`. For PNG/JPG/WebP, the
adapter produces bounded geometric candidates only:

```text
decode -> foreground mask -> connected components -> layout groups
  -> role hypotheses -> review/accept or static-canonical fallback
```

Raster observation is not brand recognition, OCR, or equivalent SVG
reconstruction. Keep `proposed_role`, `accepted_role`, `confidence`,
`review_status`, and `evidence` together. Until explicit source/human review,
`role` and `selected_role` remain `unknown`, `accepted_role` remains `null`,
`review_status` remains `needs-review`, and generic runtime uses
`static-canonical`. Showcase candidate growth is a separate reviewable demo.

## MODEL

Build `constraint_graph`, `scene_graph`, `motion_graph`, and `evidence_ledger`.
Store actor IDs, roles, geometry strategy, parent, anchor, layer, occlusion,
topology, timing traits, and tolerances. SVG keeps source IDs/topology; raster
uses `pixel-observation-only` and does not gain semantic roles from prompts,
confidence scores, or layout heuristics.

## RECONSTRUCT

Choose the smallest explainable model: source vectors, measured outlines, or
bounded raster masks. Preserve winding, holes, crossings, component count,
joins, terminals, and negative space. Compare with landmark, Chamfer/contour,
topology, and complexity checks using `tools/motiflux.py compare`; semantic
vector equality does not prove raster or browser-pixel equality. If acceptance
fails, keep `candidate` and list unresolved constraints.

## COMPOSE

Declare beats, actors, `starts_after`, `may_overlap`, `must_finish_before`,
anchors, and property channels. Use monotonic cubic for reveals, damped spring
for settling, linear for uniform channels, and stepped interpolation for
discrete states. For self-crossing marks, model over/under order and split
visibility with clips/occluders under one progress variable. Decorative glints
must not conceal topology or timing defects.

## INSTRUMENT

At beat boundaries record time, active beat, actor states, bounds, progress,
foreground stage/actors, path/speed, alpha mass, and runtime errors. Include
crossings, occluders, handoffs, spring extrema, viewport bounds, and loop seams.
Run `build` then the scoped `probe`; Node proof is not browser-pixel or
accessibility proof. The runtime exposes ready/seek/finish/play/pause/replay,
hidden-page pause, keyboard controls, and a static canonical reduced-motion
fallback.

## VALIDATE

Check geometry, topology, monotonic progress, continuity, handoffs, visibility,
bounds, replay, tempo, reduced motion, focus, keyboard, console, external
requests, and layout shift. Same-source themes must differ in foreground
midframes or trajectories; decoration alone is insufficient. At finish require
an exact semantic fingerprint match. Missing browser/accessibility/canonical
evidence keeps the result `candidate`; complete evidence has no open checks.

## DELIVER

Write `evidence.json` with source, metrics, `foreground_evidence`, canonical
fingerprint, accessibility, substitutions, `not_run`, and `unresolved`. Keep
unsupported formats in `not_run` and validate with `tools/motiflux.py validate`.
Report each output independently:

```yaml
outputs:
  - format: gif
    path: actual-path-or-null
    lifecycle: preview|baked|verified
    evidence: complete|candidate
not_run: []
unresolved: []
```

`preview` is a browser/prompt change; `baked` is a file written by a named
generator; `verified` means that file and applicable checks passed. The showcase
GIF is the encoded trajectory, the poster is the canonical static fallback, and
the PDF is a seven-checkpoint storyboard. None proves raster role acceptance or
browser `prefers-reduced-motion` behavior. The checkpoint slider swaps baked PNGs
and Prompt Lab copy never executes a shell command.

## Runtime and delivery references

Read these only when the active task needs them:

- `guides/output-contract.md` for filenames and artifact shape;
- `guides/runtime-contract.md` for browser controls and static fallback;
- `guides/prompting.md` for AI-readable request assembly and route examples;
- `guides/export-and-tuning.md` for pure backgrounds, keywords, and export state;
- `guides/motion-themes.md` and `guides/algorithm-catalog.md` for the 13 routes;
- `guides/project-kernel.md` for stage graph and artifact index;
- `schemas/*.schema.json` for machine-readable contracts.
