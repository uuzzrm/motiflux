# Motiflux prompting contract

Use this guide to turn a natural-language logo-animation request into a
deterministic Motiflux plan. The prompt describes intent; `motion-plan.yaml`
records the selected theme, source actors, foreground stages, runtime, and
proof. Do not treat a visual adjective as evidence of an executed trajectory.

## Shortest prompt formula

Start every request with this exact order:

```text
source + identity invariant -> surface -> one theme keyword -> observed foreground sequence -> duration/speed/direction -> background/particles -> reduced motion -> output format -> evidence required
```

This is the shortest usable formula, not a completion claim. `source + identity
invariant` says which supplied asset is authoritative and what must not change;
`surface` selects the delivery context; `one theme keyword` selects one primary
catalog route; `observed foreground sequence` permits only measured or explicitly
accepted actors; `duration/speed/direction` expresses timing and entry intent;
`background/particles` controls secondary presentation; `reduced motion` declares
the accessible fallback; `output format` names the requested media; and `evidence
required` names the checks that must run. Direction is currently a preview entry
cue unless a source-specific adapter proves a full actor path.

For a solid or pure-color background, include a hex color. When the user asks for
`solid background` without one, normalize it to `#0B0D12` and record
`background.source: default`; never imply that the user supplied that color. The
web runtime can honor `prefers-reduced-motion`, but pre-rendered GIF and PDF
cannot react to the system setting, so request/provide the canonical poster or
another static output as the reduced-motion fallback.

## Contents

- [Structured input contract](#structured-input-contract)
- [Prompt fields](#prompt-fields)
- [Theme routing](#theme-routing)
- [Prompt assembly rule](#prompt-assembly-rule)
- [User confirmation gate](#user-confirmation-gate)
- [Tuning vocabulary](#tuning-vocabulary)
- [Foreground growth sequence](#foreground-growth-sequence)
- [Request template](#request-template)
- [Closed-loop handoff](#closed-loop-handoff)
- [Source evidence boundary](#source-evidence-boundary)

## Prompt sizes

Choose the smallest request that still preserves identity and makes the
requested proof observable:

| Size | Include | Use when |
| --- | --- | --- |
| `minimal` | source, identity rule, one theme/context, output | testing routing or asking for a first plan |
| `recommended` | `minimal` plus observed-actor rule, runtime controls, reduced-motion policy, and evidence request | creating a real logo-animation route |
| `precision` | `recommended` plus one changed tuning dimension, adapter boundary, stage checkpoints, and manifest/path reporting | iterating or comparing exports |

Do not add adjectives to compensate for missing fields. If the request is
short, the agent expands it into the normalized record below and marks every
default, hypothesis, and unsupported preference explicitly.

## Five-step fast path

For a first request, give the agent only these five decisions in order:

1. Attach the source and state the identity invariant: what must remain unchanged.
2. Name the surface and one route, or describe the industry/context so the catalog can route it.
3. For raster input, require `observed-actors-only` and a static-canonical fallback.
4. Add measurable tuning words: duration, speed, direction, background color, particles, and reduced motion.
5. Name the output format and required evidence, then ask for file paths and separate lifecycle/evidence status.

This fast path is a request recipe, not proof that an exporter or reviewer has run.

## User confirmation gate

The skill has two different kinds of confirmation. A user can confirm the
desired route, animation plan, or tuning values; only source annotation or
explicit component review can confirm a raster role. Do not merge these into a
single “approved” state.

After source observation, route selection, and the first animation plan, show a
short confirmation card before export when any decision is still open:

```text
SOURCE: <path> / <format> / identity unchanged
OBSERVATION: <measured facts>; role hypotheses remain candidate or needs-review
ROUTE: <theme id> / <trajectory id> / matched context
GROWTH: <stage order> / <actor bindings> / static-canonical fallback
TUNING: <background> / <duration> / <speed> / <direction> / <particles> / <reduced motion>
OUTPUT: <format> / <named adapter> / proof requested
OPEN: <not_run> / <unresolved>

Reply with: approve plan | change route | change tuning | correct actor mapping
| preview only | decline
```

Continue to export only when the user has approved the relevant scope or the
original request explicitly authorized execution with all required choices
resolved. If the user says “change tuning”, change only the named runtime
field; preserve source actors, route, stage order, and canonical pixels. If the
user says “correct actor mapping”, record that as explicit review evidence and
recompute the affected plan. If the user says “preview only” or does not
resolve a material open choice, do not write the requested media.

Approval of the plan does not prove OCR, semantic raster recognition, or an
equivalent editable SVG. A user may say “this is the P” as a review decision,
but the handoff must identify it as explicit human review, not automatic
observation. Keep `accepted_role: null` until that review is actually recorded.

### Confirmation response format

The AI SHOULD return this machine-readable checkpoint before export:

```yaml
confirmation:
  status: pending|approved|revised|declined
  scope: route|plan|tuning|role-review
  source: user|explicit-request|default
source_observation:
  status: observed|not_run
  facts: []
  hypotheses: []
  limitations: []
theme_selection:
  primary_id: canonical-id
  trajectory_id: canonical-trajectory
  matched_tags: []
  rejected_candidates: []
foreground_plan:
  source_actors: []
  stage_order: [seed, trace, assemble, lockup, canonical]
  fallback: static-canonical
runtime: {duration_ms: 2200, tempo: 1.0, direction: entry-only, background: {mode: solid, color: "#0B0D12", source: default}, particles: true, reduced_motion: static-canonical}
outputs: [{format: gif, adapter: named-adapter, requested: true}]
open: {not_run: [], unresolved: []}
```

Choose the smallest prompt that still states the identity constraint. The
agent should normalize every prompt into the same ordered fields; these are
three user-facing ways to provide them:

**Minimal** - use for a quick route test:

> Animate this supplied logo for an AI technology company. Route to
> `ai-field`. Preserve the source and export a GIF.

**Recommended** - use for a real request:

> Use `brand/logo.jpg` unchanged. This is an AI technology product; route to
> `ai-field`. Grow only observed actors from point to arc to bar to monogram to
> wordmark to canonical. Use a solid `#0B0D12` background, `2200ms`, `1.25x`,
> no particles, respect reduced motion, and export GIF. Request HTML/SVG only
> when an accepted SVG source or an approved raster reconstruction adapter is
> available; otherwise record HTML/SVG as `not_run`.

**Precision** - add only when the result needs controlled iteration:

> Keep the selected route and source geometry unchanged. Change one dimension:
> use a left-to-right entry, `2200ms`, a `0.75x` tempo, and make the final
> canonical stage readable within that authored duration. Re-export GIF and
> report the changed control separately from unchanged foreground evidence.

Do not put unrelated visual adjectives into a single route request. Prefer one
primary theme and at most two modifiers, then state measurable controls. A
named vendor or public product may be a design-principle analogue; it is not a
request to copy its artwork or private implementation.

## Structured input contract

Natural language is the user-facing input, but the agent MUST normalize it into
the following fields before routing or generating. A missing field is not an
invitation to invent source structure or an exporter. Record the omission and
ask only when it changes identity, delivery surface, or required proof.

| Field | Type / allowed values | Required rule | If missing or invalid |
| --- | --- | --- | --- |
| `source.path` | readable SVG, PNG, JPG, WebP, or supplied asset reference | always | stop source observation; keep `candidate`, add `not_run: [source-observation]` |
| `source.identity_rule` | explicit preservation rule, normally unchanged geometry/paint or unchanged source pixels | always | do not plan a canonical stage; request clarification |
| `surface` | `web-intro`, `splash`, `loading`, `idle`, or `showcase` | required when output behavior depends on it | record `unresolved: [surface-selection]`; do not select an exporter from a visual adjective |
| `theme` | one catalog ID or routable keywords | required for a themed route | use `system-spatial` only as the documented fallback and record the fallback |
| `foreground` | observed actor IDs/order plus `observed-actors-only` rule | required for source-aware growth | use `static-canonical`; do not invent missing stages |
| `runtime` | duration, tempo, direction, background, particles, reduced-motion policy | required for non-default controls | preserve omitted controls as adapter defaults; a solid background needs a color, otherwise resolve `#0B0D12` with `source: default` |
| `outputs.requested` | one or more of `html`, `svg`, `gif`, `pdf`, or an explicitly unsupported format | required for export work | treat the result as planning only; do not claim an artifact |
| `evidence.require` | named checks such as source observation, stage frames, browser pixels, or reduced motion | required before `verified` | keep evidence `candidate` and list the missing checks |

The normalized record MUST preserve the distinction between omitted, `false`,
`null`, and unsupported values. `particles: false` is an executable request;
`particles: null` is unresolved input. An unsupported control stays in
`constraints` with `status: recorded-unresolved`; it is never silently coerced
to a nearby effect. The request record describes intent, while the plan and
evidence records describe what was actually bound, written, and checked.

Minimal normalized handoff:

```yaml
request:
  source:
    path: brand/logo.jpg
    identity_rule: preserve source pixels and final proportions
  surface: showcase
  theme: ai-field
  foreground:
    rule: observed-actors-only
  runtime:
    background: {mode: solid, color: "#0B0D12", source: prompt}
    particles: false
    tempo: 0.75
  outputs:
    requested: [gif, html]
  evidence:
    require: [source-observation, final-frame, browser-pixels]
```

This record is sufficient to route and plan, not to claim that either output
exists. After execution, add actual paths and the separate lifecycle,
evidence, `not_run`, and `unresolved` fields shown below.

### Normalization order (fixed)

The agent MUST normalize natural language in this order. Later fields may tune
earlier decisions, but they must not silently replace them:

| Order | Field | AI action | Required boundary |
| --- | --- | --- | --- |
| 1 | `source` | identify path/asset, format, and identity invariant | source pixels or accepted SVG geometry remain authoritative |
| 2 | `surface` | select `web-intro`, `splash`, `loading`, `idle`, or `showcase` | surface selects a delivery contract; it does not create an exporter |
| 3 | `theme` | match one canonical ID from context keywords | return `primary_id`, `trajectory_id`, `matched_tags`, and rejected candidates |
| 4 | `foreground` | bind only observed/accepted actors to stable stages | prompt labels remain hypotheses; retain `static-canonical` fallback |
| 5 | `runtime` | resolve duration, tempo, direction, background, particles, and secondary effects | distinguish baked controls from preview-only controls; direction is currently a preview entry cue |
| 6 | `accessibility` | resolve reduced motion, pause/replay, keyboard, and contrast needs | pre-rendered GIF/PDF cannot respond to a system preference; provide a canonical poster/static output |
| 7 | `outputs` | select a named adapter for each requested format | no adapter means `path: null` and `not_run` |
| 8 | `evidence` | list required frame, source, runtime, browser, and accessibility checks | missing proof keeps the result `candidate` |

Preserve omitted, `false`, `null`, and unsupported values as different states.
Never infer a missing source actor from the requested stage name. Never infer
that a file exists because the output field was requested.

## Closed-loop execution

The prompt is an input contract, not a completion claim. Carry it through these
seven handoffs in order. A later handoff cannot promote an earlier hypothesis,
replace a user decision, or supply evidence for a step that did not run:

```text
source observation -> role review -> theme route -> animation plan
  -> user confirmation/tuning -> export delivery -> evidence
```

| Record | Required fields | Decision gate |
| --- | --- | --- |
| `source_observation` | path/format, identity rule, dimensions, pixels or SVG actors, limitations, `source-analysis.json` | Measure only what the adapter can observe; raster geometry is not semantic recognition. |
| `role_review` | per-component `proposed_role`, `accepted_role`, `confidence`, `review_status`, `evidence` | `accepted_role` stays `null` for `observed`, `candidate`, and `needs-review`; acceptance requires source annotation or explicit human review. |
| `theme_selection` | `primary_id`, `trajectory_id`, `matched_tags`, modifiers, rejected candidates | Route from user context and explicit keywords, not from raster appearance as if it were semantic recognition. |
| `animation_plan` | theme, `source_actors`, `stage_order`, `mode`, `variant`, `timing`, `easing`, `path_strategy`, `speed_profile`, `fallback` | Bind only confirmed/measured actors; keep `fallback: static-canonical` and never invent a missing actor. |
| `confirmation` | status, scope, selected route/plan/tuning, requested outputs, open gaps | Before export, wait for approval or a correction when identity, route, actor mapping, stage order, output, or proof is unresolved. |
| `runtime` | `duration_ms`, `tempo`, direction/entry, background, particles, secondary effects, reduced-motion policy | Apply approved tuning separately from the foreground plan; preserve unsupported controls as unresolved constraints. |
| `export` | requested format, named adapter, actual path, `lifecycle` | `preview` is browser state, `baked` is a file written by a named generator, and no adapter means `path: null` plus `not_run`. |
| `evidence` | inspected artifacts, source/stage/canonical/runtime/browser/accessibility checks, `not_run`, `unresolved` | Use `verified` only for checks that actually passed; otherwise keep `candidate`. |

The planner consumes nested `role_review` records when present. A proposed
role is still a hypothesis even when confidence is high or the prompt names
it. A route ID, algorithm list, preview, file hash, or existing file is not
proof of semantic role acceptance, browser behavior, or a complete trajectory.
If a phase cannot run, keep it visible in `not_run` or `unresolved` and do not
return a made-up path.

## Refinement language

Use explicit control phrases so an AI agent can distinguish a foreground change
from a presentation change:

| If the user says... | Normalize to... | Keep unchanged... |
| --- | --- | --- |
| "纯色背景" / "clean background" | `solid #RRGGBB background` | source actors, stage order, canonical pixels |
| "不要粒子" / "less decoration" | `no particles, no glow, identity-first foreground` | selected trajectory and timing unless changed |
| "从左到右" | `left to right entry` | source geometry; report if the adapter only previews it |
| "更慢、更容易看懂" | `2400ms, speed 0.75x, readable canonical stage` | route and actor order |
| "低动效" / "更克制" | `low-amplitude, no overshoot, speed 0.75x` | final source scene and semantic order; low-amplitude/no-overshoot are recorded renderer constraints, while speed is executable |
| "系统减少动效" / "无障碍动效" | `static-canonical reduced motion` | final source scene and semantic order |
| "只改颜色" | `change visual background/color only` | foreground path, timing, and source pixels |

If a phrase cannot be baked by the selected exporter, preserve it in the plan
as an unresolved constraint. Treat `低动效` as a visual motion preference and
`static-canonical reduced motion` as the accessibility/system fallback unless
the user explicitly asks for both. Never describe a browser preview adjustment
as a new GIF or PDF file.

The checked-in raster showcase has a deliberately narrow bake surface:

| Requested control | Browser showcase | `generate_showcase.py` bake | Meaning |
| --- | --- | --- | --- |
| `solid #RRGGBB background` | Changes the local preview shell | `--background '#RRGGBB'` | The next generator run writes the selected color into the GIF/PDF export. |
| `1600ms` or another duration | Changes the local player clock | `--duration-ms 1600` | Re-encodes the checked-in raster showcase at the requested duration. |
| `speed 1.25x` | Changes the local timing preview | `--speed 1.25` | Re-encodes progression; it does not change the theme trajectory. |
| `left to right` / `center outward` | Shows an entry cue in the page shell | no standalone showcase flag | Keep it as a route/adapter constraint unless the selected generator implements actor direction. |
| `no particles` | Hides auxiliary shell effects | `--no-particles` | Removes secondary decoration while preserving source-derived foreground growth. |

The browser column is a preview claim. The bake column is an adapter action,
not automatic proof: after baking, inspect the output and record the applicable
evidence. `low-amplitude`, `no overshoot`, `opacity-first`, and a requested
direction may remain renderer constraints when the selected adapter does not
implement them; keep them in `constraints` with `unresolved` rather than
silently translating them into a different effect.

## Tuning vocabulary

Use one field per refinement pass. The following phrases are intentionally
explicit so a user can ask for a change without accidentally changing the
identity, route, or foreground choreography:

| User intent | Write in the prompt | AI interpretation | Preserve |
| --- | --- | --- | --- |
| Pure color | `solid #0B0D12 background` | one solid stage color | source pixels/vectors, actor order, canonical landing |
| Speed | `speed 1.25x` or `tempo 0.75x` | playback/time multiplier or authored tempo, depending on adapter | route and trajectory; report which timing layer changed |
| Duration | `1600ms` or `2.4 seconds` | total authored growth window | stage order and final reading state |
| Direction | `left to right entry`, `right to left entry`, `center outward` | entry preference unless the selected adapter proves a path direction | source geometry and actor order |
| Particles | `no particles` or `sparse secondary particles, seed 7` | toggle or constrain secondary decoration | identity-bearing foreground route |
| Low motion | `low-amplitude, no overshoot, opacity-first, speed 0.75x` | restrained motion preferences; only executable portions are proof | source scene, route, stage order, canonical ending |
| System reduced motion | `static-canonical reduced motion` | static or declared reduced-motion fallback | exact canonical source and accessibility semantics |

Do not treat `low motion` as the same request as `reduced motion`. The first
can still be an animation; the second is the system/accessibility fallback.
Likewise, `direction` is not automatically a measured actor path, and `speed`
is not automatically a change to a theme's relative `speed_profile`.

### Tuning response contract

When a user asks for a refinement, acknowledge the invariant and the changed
field before applying it:

```text
KEEP: source identity / selected route / source actors / stage order / canonical pixels
CHANGE: <one runtime field and resolved value>
PREVIEW OR BAKE: <what the selected surface can actually execute>
OPEN PROOF: <not_run> / <unresolved>
```

Examples:

```text
Keep the selected ai-field foreground route unchanged. Change only the stage
surface to solid #F4F1E8 and the authored duration to 2200ms. Keep particles
off. Show the revised plan first; export only after approval.
```

```text
Keep the route and source actors unchanged. Use low-amplitude, no overshoot,
speed 0.75x. This is a restrained animation request, not a static reduced-
motion substitution. Report any renderer constraint that remains unresolved.
```

```text
Keep the route and canonical source unchanged. Use static-canonical reduced
motion. For a pre-rendered GIF, provide or reference the static poster because
the GIF itself cannot react to a system motion preference.
```

If the requested control is preview-only, say so and keep the lifecycle
`preview`. If a named exporter writes the artifact, use `baked`; use
`verified` only after the applicable file and behavior checks pass.

### Full atlas versus single-route export

The currently exposed `showcase/generate_showcase.py` command bakes the full
13-theme showcase. Its checked-in options apply to every theme in that run:

```powershell
python showcase/generate_showcase.py --background '#0B0D12' --duration-ms 1600 --speed 1.25 --no-particles --no-guides
```

The generator source also contains a single-route export contract named
`build_single_theme_export(...)`, and the current CLI exposes it through
`--theme`. The command and output shape are:

```powershell
python showcase/generate_showcase.py --theme ai-field --background '#0B0D12' --duration-ms 1600 --speed 1.25 --no-particles
```

```text
showcase/output/exports/ai-field/
  prysai-ai-field.gif
  prysai-ai-field-poster.png
  prysai-ai-field-blank.png
  prysai-ai-field-spark.png
  prysai-ai-field-arc.png
  prysai-ai-field-bar.png
  prysai-ai-field-monogram.png
  prysai-ai-field-wordmark.png
  prysai-ai-field-canonical.png
  export-manifest.json
```

The command is exposed in the checked-in generator, but
`showcase/output/exports/` is created only when the command is actually run.
Treat the command above as executable capability, not evidence that its files
already exist. Before invocation, report the requested route as `preview` or
`not_run: [single-route-export]` according to the requested handoff; after
invocation, return only the manifest and artifact paths that exist. The full
atlas command remains available for a repository-wide bake.

When the single-route contract is active, `export-manifest.json` is a compact
per-route record. It includes the source path and SHA-256, theme and
`trajectory_id`, `foreground_variant`, resolved export options, GIF/poster/
stage-checkpoint paths, encoded frame count and duration, canonical final-frame
hash, plus `not_run` and `unresolved` lists. It is a delivery ledger, not a
semantic role review, browser proof, or replacement for the project
`artifact-index.json` and showcase `growth-evidence.json`.

The manifest's expected initial status is:

```yaml
status: baked
evidence_status: candidate
not_run:
  - browser-pixel-review
  - human-raster-role-review
  - raster-to-vector-reconstruction
unresolved:
  - raster role semantics remain candidate hypotheses
```

Do not upgrade `status` or `evidence_status` from the presence of the
manifest. Open the files, inspect the stage checkpoints and canonical frame,
then add the applicable review evidence separately.

Use the exact bake command for a solid background, including quotes around the
hex value in PowerShell:

```powershell
python showcase/generate_showcase.py --background '#F4F1E8' --duration-ms 2200 --speed 0.75 --no-particles
```

That command regenerates the checked-in GIFs, posters, HTML, evidence, and PDF
unless `--skip-pdf` is supplied. It is a repository showcase command, not a
general-purpose raster-to-vector exporter.

For one route only, add `--theme <theme-id>`. The isolated export is written
under `showcase/output/exports/<theme-id>/` and includes the route GIF, its
canonical poster, seven static checkpoint PNGs, and `export-manifest.json`.
The manifest records the source hash, route/variant, resolved bake options,
encoded frame count/duration, canonical-frame hash, and open review gaps. Its
`status: baked` means the named generator wrote files; it does not mean
`verified` or `complete` evidence.

```powershell
python showcase/generate_showcase.py --theme ai-field --background '#0B0D12' --duration-ms 1600 --speed 1.25 --no-particles
```

In Prompt Lab, the same command is displayed and can be copied; the browser
never executes it. The per-card checkpoint slider is a review aid that swaps
in baked PNG checkpoints. It does not seek the native GIF, which remains a
portable looping file.

## Prompt fields

Provide explicit values for the fields that affect output. Omit a field only
when the default is acceptable.

| Field | Required information | Plan/evidence consequence |
| --- | --- | --- |
| `source` | File path or supplied asset, format, and identity rule | Run `measure`; preserve the accepted source geometry and paint. |
| `surface` | `web-intro`, `splash`, `loading`, `idle`, or `showcase` | Select the delivery contract and required controls. |
| `theme` | One canonical theme ID or its user-language keywords | Run the catalog router; record `primary`, `primary_id`, `matched_tags`, and rejected candidates. |
| `foreground` | Ordered source-derived construction and actor mapping | Write `foreground_plan`, including `stage_order`, `path_strategy`, `speed_profile`, and proof. |
| `timing` | Duration, tempo, pauses, and direction | Write `runtime.duration_ms`, `runtime.tempo`, and per-stage timing intent. |
| `visual` | Background, color, contrast, glow, and particle policy | Keep identity-bearing geometry primary; record renderer-dependent preferences as constraints. |
| `accessibility` | Reduced-motion behavior, pause, replay, keyboard, and contrast needs | Use `runtime.reduced_motion`; verify static-canonical behavior and controls. |
| `outputs` | Requested `gif`, `html`, `svg`, and/or `pdf` | Record requested formats; report only paths produced by a real exporter or capture adapter. |
| `evidence` | Required checks and unresolved limitations | Keep `candidate`, `not_run`, and `unresolved` honest. |

Use one primary theme and no more than two modifiers. If the request contains
conflicting themes, route the strongest intent and record the rejected
candidates instead of silently blending them.

## Agent execution order

Apply this order every time. Do not jump from a style adjective directly to a
visual effect:

1. **Identify the source.** Record the path, format, identity rule, and surface.
2. **Observe structure.** For SVG, use source actors. For PNG/JPG/WebP, run the
   bounded raster adapter and label role hypotheses `candidate`/
   `needs-review`. Record pixels, components, bounds, and layout evidence
   separately from role interpretation.
3. **Review the raster boundary.** For each raster component, preserve the proposed
   role and evidence; set `accepted_role` only from explicit source or reviewer
   confirmation. Keep `accepted_role: null` for `needs-review` and `observed`.
4. **Route the theme.** Select one canonical theme from `catalog/themes.json`
   using the user's industry, product, audience, and motion keywords. Record
   `primary_id`, `trajectory_id`, matched tags, modifiers, and rejected
   candidates; do not infer semantic context from raster appearance.
5. **Plan the foreground animation.** Bind `seed -> trace -> assemble -> lockup ->
   canonical` to observed actors. This machine order is stable; user-visible
   substeps map into it and do not create an arbitrary foreground order. Never
   invent a dot, arc, bar, P, or glyph to satisfy the wording of a prompt.
6. **Present confirmation and apply one tuning change.** Show the selected route,
   actor/stage plan, controls, requested outputs, and open gaps. Apply only the
   user's approved route, actor correction, or one runtime refinement; preserve
   source facts and the canonical final frame unless the user changes them.
7. **Choose approved output adapters.** Use the generic builder for the source-specific
   HTML/SVG package; use the showcase generator or an approved capture adapter
   for GIF/PDF. If an output adapter is missing, keep the request in the plan and
   mark the output `not_run` instead of manufacturing a path.
8. **Validate and report proof.** Return generated paths plus `candidate`, `not_run`, and
   `unresolved` evidence. A copied prompt is not execution evidence.

## Fast path: natural language first

The current planner reads natural-language controls. Use these exact forms when
you want deterministic parsing:

| Intent | Example phrase |
| --- | --- |
| Duration | `1600ms` or `1.6 seconds` |
| Speed | `speed 1.25x`, `tempo 1.25x`, or `速度 1.25x` |
| Direction | `left to right`, `right-to-left`, `从左到右`, or `center outward` |
| Solid color | `solid #0B0D12`, `pure color background`, or `纯色背景 #0B0D12` |
| Particles | `no particles`, `particle-free`, or `不要粒子` |
| Formats | `export GIF HTML SVG PDF` |
| Surface | `web intro`, `splash`, `loading`, `idle`, or `showcase` |

## Prompt assembly rule

Compose requests in this fixed order so the agent can separate identity from
style and delivery:

```text
source + identity invariant -> surface -> one theme keyword
-> observed foreground sequence -> duration/speed/direction
-> background/particles -> reduced motion -> output format -> evidence required
```

For a solid background, write its color. If the user omits it, use
`#0B0D12` and record `source: default`; a user-provided color is
`source: prompt`. In the current showcase, direction remains a preview entry cue
unless an approved source-specific adapter proves actor travel direction. GIF
and PDF are pre-rendered, so reduced motion requires the canonical poster or a
separate static output.

Use the canonical theme ID when precision matters (`ai-field`, not `AI-field`);
use the display name only for prose. Industry keywords select the foreground
trajectory, while modifiers refine it:

- `人工智能`, `AI 科技`, `生成式 AI` -> `ai-field` / signal convergence;
- `教育`, `学习`, `课程` -> `system-spatial` / spatial lock;
- `高级`, `奢侈`, `极简` -> `premium-quiet` / contour etch;
- `代码`, `开发者`, `API` -> `developer-open` / token commit;
- `低动效`, `无障碍`, `键盘` -> `accessibility-first` / opacity-first.

Do not use a keyword to force an unavailable shape. Write `只使用观测到的
source actors` for raster input and let the plan map missing roles to a
candidate or static fallback. Add refinements as executable phrases such as
`纯色背景 #0B0D12`, `不要粒子`, `2400ms`, `speed 0.75x`, `从左到右`, and
`export GIF and PDF`.

Route keywords through the catalog, then keep the selected trajectory tied to
the observed actors. For example, `AI 科技` or `人工智能` routes to `ai-field`
and `signal-convergence`; `教育`, `学习`, or `课程` routes to `system-spatial`
and `knowledge-graph-lock`. The route changes how the supplied actors enter,
connect, or settle; it does not authorize a new emblem or a different
foreground stage order.

Record the route as `primary_id`, `matched_tags`, `rejected_candidates`,
`trajectory_id`, and `algorithm_stack`. A unique `trajectory_id` identifies the
planned motion in the catalog; it is not evidence that every stage or path was
rendered. If a route cannot be resolved, use `system-spatial` and record the
fallback rather than blending several primary themes invisibly.

### Keyword-to-motion interpretation

Treat a keyword as a routing signal, not as a request to copy a vendor style or
invent a new logo shape. Resolve it through this sequence:

```text
user wording -> canonical theme -> foreground trajectory -> measured actors
              -> timing/easing -> secondary atmosphere -> export + proof
```

The selected theme MUST be visible in how source actors enter, travel, reveal,
or settle. For example, `AI technology` selects `ai-field`, whose signal
convergence guides the observed dot, arc, bar, monogram, and glyph actors into
their source positions. It does not authorize a generic neural-network field
or a different emblem. `education` selects `system-spatial`, whose ordered
spatial locks make the same actor relationships easier to read.

When the request needs a visibly different same-logo result, preserve the
three-part route description:

```text
theme mode -> foreground variant -> path strategy
ai-field -> polar-counter -> seeded signals converge into measured actors
sports-impact -> diagonal-reverse -> directional source-pixel release
accessibility-first -> opacity-stable -> ordered opacity with stable geometry
```

The variant is an implementation choice the skill can select from the catalog;
the user normally only needs to name the industry or intent. Do not turn a
variant into a background adjective, and do not claim that a variant exists
unless the chosen exporter implements it.

When the request is underspecified, preserve this default rather than asking
for decorative preferences first:

1. keep the supplied identity and final proportions;
2. map the observed growth into the stable machine sequence
   `blank -> seed -> trace -> assemble -> lockup -> canonical`, using the
   showcase labels `origin dot -> circular arc -> horizontal bar -> P /
   monogram -> Prysai wordmark -> complete Logo` only when those candidate
   roles exist;
3. choose one route and at most two modifiers;
4. use a static-canonical reduced-motion fallback;
5. report actual files and keep unsupported output or proof in `not_run`.

### Agent response checklist

Return the normalized request before claiming completion:

```yaml
route: ai-field
matched_tags: [AI technology]
foreground: [blank, origin-dot, arc, bar, monogram, wordmark, canonical]
controls: [solid-background, 1600ms, speed-1.25x, no-particles]
outputs: [gif]
evidence: [source-observation, stage-snapshots, canonical-fallback]
status: candidate
```

For raster input, add the review boundary before using semantic role wording:

```yaml
observation:
  source_facts: [dimensions, alpha, foreground-mask, components, bounds]
  role_hypotheses: [candidate-role-or-null]
  accepted_roles: []
  review_status: needs-review
foreground:
  rule: observed-actors-only
  fallback: static-canonical
evidence:
  status: candidate
  not_run: [browser-pixels]
  unresolved: [role-confirmation]
```

This is a planning/handoff shape, not proof. Replace placeholders with actual
values and keep `not_run` or `unresolved` when the adapter or review did not
run.

For example, a raster request with a missing vector adapter must say so
explicitly rather than returning a made-up `motion.html` or `mark.svg` path:

```yaml
outputs:
  - format: gif
    path: showcase/assets/animations/ai-field.gif
    lifecycle: baked
    evidence: candidate
  - format: html
    path: null
    lifecycle: preview
    evidence: candidate
observation_status: candidate
review_status: needs-review
not_run: [html-export, browser-pixels]
unresolved: [raster-role-confirmation]
```

Then list the source observation boundary, generated paths, and unresolved
checks. This makes a prompt legible to another agent and prevents a route label,
algorithm list, or preview control from being mistaken for executed output.

The YAML below is an internal planning record for an agent or an artifact. It
is not a second user-facing input format and the CLI does not accept arbitrary
YAML pasted as the request. Translate it into the natural-language form above;
if a desired control is not executed by the selected adapter, keep it in
`constraints` with `status: recorded-unresolved` and report it as unresolved.
The planner recognizes surface words and records the selected surface in
`project.surface`; a surface label does not by itself create a new exporter.

## Theme routing

Treat `catalog/themes.json` as the routing authority. Markdown descriptions are
explanatory only. Route the complete request, not a single isolated adjective:

```powershell
python skills/motiflux/tools/motiflux.py route "AI education logo animation"
```

The 13 canonical routes are:

These are the 13 keyword categories to recognize: system/product/education,
premium/luxury, developer/open source, AI/data, fintech/trust, security/privacy,
commerce/retail, automotive/engineering, sports/competition, cinematic/title,
nature/organic, gaming/world-building, and accessibility/reduced motion.
`education` is an alias of `system-spatial`, not a fourteenth route. Choose one
category by explicit industry or product context first, explicit accessibility or
motion constraints second, and broad style words only as a tiebreaker. Select one
primary canonical ID, add at most two modifiers, and record rejected candidates;
if no category is clear, use `system-spatial` with quiet and accessible modifiers.

| Canonical ID | Typical keywords | Executable foreground trajectory |
| --- | --- | --- |
| `system-spatial` | product, SaaS, dashboard, enterprise, interface, education, learning, 教育, 学习, 课程, 教学, 知识 | `knowledge-graph-lock`: place nodes, connect relations, then lock the mark. |
| `premium-quiet` | premium, luxury, fashion, beauty, editorial, elegant, minimal, 奢侈, 时尚, 美妆, 高级, 极简 | `contour-etch`: trace the measured contour, then resolve the solid mark. |
| `developer-open` | developer, open source, API, CLI, code, tooling, technical, precise, 开发者, 开源, 代码, 工具 | `token-commit`: commit deterministic source tokens in an inspectable order. |
| `ai-field` | AI, artificial intelligence, machine learning, neural, data, model, generative, 人工智能, 生成式, AI科技, 数据, 未来感 | `signal-convergence`: guide deterministic signals into measured logo pixels. |
| `fintech-trust` | fintech, banking, payments, finance, trust, institutional, reliable, 金融, 银行, 支付, 可信, 稳健 | `progress-confirm`: use bounded progress, confirmation, and canonical settle. |
| `security-shield` | security, privacy, identity, authentication, defense, compliance, 安全, 隐私, 认证, 防护, 合规 | `boundary-unlock`: establish boundary, verify interior, unlock the lockup. |
| `commerce-energy` | commerce, retail, shopping, marketplace, sale, conversion, friendly, 电商, 零售, 购物, 消费, 促销 | `burst-assembly`: compress components, release from a shared origin, settle. |
| `automotive-precision` | automotive, mobility, transport, engineering, industrial, mechanical, 汽车, 交通, 工业, 工程, 性能 | `kinematic-lock`: carry actors along a directional, velocity-continuous path. |
| `sports-impact` | sports, fitness, competition, speed, impact, bold, dynamic, 体育, 健身, 竞技, 速度, 冲击 | `impact-release`: compress, release on the dominant axis, and recover. |
| `cinematic-title` | cinematic, film, movie, title, trailer, dramatic, suspense, 电影, 片头, 预告, 叙事, 戏剧 | `aperture-title`: open the title aperture, stage the lockup, hold for reading. |
| `nature-flow` | nature, organic, wellness, sustainable, water, wind, growth, calm, 自然, 有机, 健康, 环保, 成长 | `organic-current`: follow a bounded low-frequency current into the source position. |
| `gaming-world` | gaming, esports, fantasy, sci-fi, quest, arcade, playful, 游戏, 电竞, 奇幻, 科幻, 街机 | `orbit-quest`: use deterministic orbits, assemble the reward, then clear effects. |
| `accessibility-first` | accessible, accessibility, reduced motion, calm, inclusive, keyboard, 无障碍, 低动效, 包容, 键盘, 辅助 | `semantic-fade`: preserve order and geometry with opacity-first motion. |

`education` is an alias of `system-spatial`, not a fourteenth theme. The
router must return the exact catalog ID and trajectory ID in the plan. A
particle field, background, palette, camera move, or label change alone is not
a theme distinction.

Use keyword precedence in this order: explicit industry/product context,
explicit motion or accessibility constraint, then broad style adjective. When
two themes match, choose one primary route, keep at most two modifiers, and
record the rejected route. Do not route from the logo's visual appearance
alone when the user has supplied industry context.

## Foreground growth sequence

When the requested story is “点 → 圆弧 → 横杠 → P/字母 → 完整 logo”, express it
as source-derived stages. Motiflux keeps the machine stage IDs stable:

| User-visible step | Motiflux stage | Required source proof |
| --- | --- | --- |
| 点 / seed | `seed` | One measured source anchor, dot, or minimal identity fragment. |
| 圆弧 / contour | `trace` | A measured arc, curve, or contour interval from a source actor. |
| 横杠 / stroke | `assemble` | A measured bar, stroke, or component joining the existing geometry. |
| P / monogram / letters | `lockup` | The supplied monogram, glyphs, wordmark, and occlusion order. |
| 完整 logo | `canonical` | The exact accepted source scene, held long enough to read. |

The serialized order remains fixed:

```yaml
foreground_plan:
  stage_order: [seed, trace, assemble, lockup, canonical]
```

The runtime does not expose an independent canonical reading-hold field, and it
does not promise arbitrary foreground reordering. Express a slower or more
readable ending through `runtime.duration_ms`, `runtime.tempo`, and the stage
timing intent; keep the canonical stage as the unchanged source scene.

### Stage vocabulary boundary

The generic source-aware runtime uses five semantic stages. The raster
showcase uses seven visible checkpoints so a viewer can read the supplied
Prysai mark growing in more detail. They are related, but they are not the
same output contract:

| Generic runtime stage | Showcase checkpoint | Meaning |
| --- | --- | --- |
| no stage | `blank` | Empty pre-stage; no identity actor is visible. |
| `seed` | `spark` | First observed anchor, shown as the origin dot. |
| `trace` | `arc` | Measured contour or arc interval is drawn on. |
| `assemble` | `bar` | A measured stroke or component joins the construction. |
| `lockup` | `monogram` and `wordmark` | The supplied symbol and wordmark resolve in readable substeps. |
| `canonical` | `canonical` | Exact accepted source scene; keep it readable within the authored runtime. |

`showcase/index.html` and its GIFs use the seven-checkpoint presentation.
The SVG delivery package uses `motion.html`, `motion.css`, and `motion.js`
with the five-stage plan. Do not claim that the showcase labels are a
universal Logo schema or that the raster showcase is an editable SVG package.

Put `arc`, `bar`, `monogram`, and `wordmark` in the stage descriptions and
`source_actors`; do not invent a shape to fill a missing stage. Every stage
must declare `path_strategy`, `speed_profile`, `source_actors`, and
`visible_proof`. The final stage must use `static-canonical` and must not
redraw the identity.

For an uncertain decomposition, ask the user to identify the actors or use
measured source intervals. If neither is reliable, use
`static_canonical_fallback.mode: static-canonical`, mark the result
`candidate`, and name the missing `foreground-decomposition` evidence.

## Copy-ready request

Use natural language when sending a request to an AI agent. This is the form
the current planner parses most reliably:

> Animate the supplied logo for an AI technology company. Route it to
> `ai-field`. Preserve the source geometry and grow the observed foreground in
> this order: point, arc, bar, P/monogram, wordmark, canonical logo. Use a
> solid `#0B0D12` background, 1600 ms, speed `1.25x`, center outward, no
> particles, respect reduced motion, and export GIF and HTML.

Replace the theme, background, timing, and output words as needed. Keep the
identity rule and construction order explicit whenever the source is a raster
image. The agent must report the actual route, generated paths, and any
`candidate`, `not_run`, or `unresolved` evidence instead of treating the
request as proof that a format or trajectory executed.

## Request template

Use this compact structure in a user prompt. The keys are request fields; the
planner maps them to the stable plan contract and records unsupported wishes as
constraints rather than pretending they executed.

```yaml
source:
  path: "path/to/brand-mark.svg"
  identity_rule: "preserve geometry, topology, paint, and final proportions"
surface: web-intro
theme: "AI technology logo animation"
foreground:
  sequence: [seed-dot, arc, bar, monogram-or-P, wordmark, canonical]
  rule: "grow from source actors; do not invent replacement geometry"
runtime:
  duration_ms: 1600
  tempo: 0.92
  direction: radial
  direction_vector: [0, 0]
  background:
    mode: solid
    color: "#0B0D12"
    source: prompt
  particles: false
  reduced_motion: static-canonical
  requested_formats: [html, svg, gif, pdf]
evidence:
  require: [source-actors, stage-snapshots, canonical-end-state, reduced-motion]
```

For raster input, make the review boundary explicit in the request:

```yaml
source:
  path: "path/to/brand-mark.jpg"
  identity_rule: "preserve source pixels; do not claim OCR, semantic recognition, or editable-vector equivalence"
foreground:
  sequence: [observed-actors-only, canonical]
  role_policy: "propose geometric roles; keep unconfirmed roles needs-review"
review:
  require: [component-role-review]
  accepted_roles: []
outputs:
  requested: [gif, html]
  report: [actual-paths, lifecycle-status, evidence-status, not_run, unresolved]
```

The `sequence` is deliberately conservative: it allows the planner to use
observed actors without asserting that a pixel cluster is a dot, arc, letter, or
wordmark. If the user wants a specific role, record it as a requested hypothesis
until the source or reviewer confirms it.

## Closed-loop handoff

Return one compact record after planning, generation, and validation. Fill in
actual values; do not leave a lifecycle word standing in for a path or proof:

```yaml
route: ai-field
foreground: [raster-component-001, raster-component-002]
stage_order: [seed, trace, assemble, lockup, canonical]
controls:
  duration_ms: 1600
  tempo: 1.25
  direction: center-outward
  background: solid #0B0D12
  particles: false
  reduced_motion: static-canonical
outputs:
  - format: gif
    path: null
    lifecycle: preview
    evidence: candidate
review_status: needs-review
not_run: [gif-export]
unresolved: [raster-role-confirmation, browser-pixels]
```

Use three separate status layers exactly as follows:

| Layer | Values | Question answered |
| --- | --- | --- |
| output lifecycle | `preview`, `baked`, `verified` | Did a local control change, did a named generator write a file, and was that file checked? |
| overall evidence | `candidate`, `complete` | Is the required proof set closed? |
| review/gaps | `needs-review`, `not_run`, `unresolved` | Which interpretation, adapter, or proof remains open? |

`baked` does not mean `verified`; `verified` does not mean every requested
format ran; and `complete` is unavailable while required evidence remains open.
For raster input, role review can be accepted while the overall result remains
`candidate` because browser, reconstruction, accessibility, or export proof is
still missing.

For the checked-in showcase, use these evidence meanings when reporting an
output:

- `GIF`: the complete encoded growth trajectory, provided its selected stage
  frames and the corresponding growth evidence were inspected;
- `poster`: the canonical final-frame fallback for static presentation or
  reduced-motion substitution; it is not evidence that the GIF responds to a
  system motion preference;
- `PDF`: a seven-checkpoint static storyboard, not a playable timeline and not
  a replacement for runtime/browser evidence.

GIF and PDF are pre-rendered files: neither responds to the operating system's
`prefers-reduced-motion`. When either is requested, include the canonical poster
or another static output in the requested outputs and report it separately from
the animated file.

Translate ambiguous language into a parameter question only when it changes
identity, surface, or proof. For example, “make it more AI” is insufficient;
“route to `ai-field`, converge seeded secondary signals into the measured arc,
use a solid `#0B0D12` background, 1600 ms, and static-canonical reduced motion”
is executable.

## Source evidence boundary

For SVG input, `measure` can inspect supported vector elements, viewBox,
attributes, and source actors. `compare` can provide semantic vector evidence;
this does not prove browser pixels, raster contours, or accessibility-tree
behavior.

For PNG, JPG, or WebP input, the available Pillow adapter performs a bounded
geometric observation of decoded pixels: foreground mask, connected components,
bounds, centroids, layout groups, and geometric role candidates. This is
candidate observation only: it does not identify the brand, read text, recognize
semantic actors, or reconstruct an equivalent editable SVG. It returns `candidate`
with `needs-review`; high confidence is still not acceptance without source or
reviewer confirmation. The showcase adapter may consume the observed boxes to
stage a GIF from the supplied pixels; the generic vector-dependent builder
still requires a dedicated raster reconstruction adapter.

Use this boundary when reviewing an observation:

| May be recorded as observed | Must remain a hypothesis or unresolved |
| --- | --- |
| decoded dimensions, alpha/background samples, foreground mask, component bounds, centroids, and pixel adjacency | “this component is the P”, OCR text, brand meaning, semantic actor identity, or accepted reading order |
| geometric groups and a proposed `path_strategy` tied to those groups | a missing dot/arc/bar/letter, a reconstructed vector path, or source-equivalent SVG |
| exact supplied pixels at the canonical landing | that JPG/PNG was semantically understood or that its GIF/PDF is equivalent to an editable SVG scene |

If the observer fails, times out, or cannot read the file, record the source
facts that were actually checked and stop there:

```yaml
observation:
  status: not_run
  reason: raster-observer-unavailable
  source_facts: ["format: jpg"]
  role_hypotheses: []
  accepted_roles: []
foreground:
  rule: observed-actors-only
  fallback: static-canonical
evidence_status: candidate
not_run: [component-observation, html-export]
unresolved: [foreground-decomposition]
```

Do not upgrade this record because the prompt supplied labels such as “dot” or
“wordmark”, because a file was generated, or because a preview looks plausible.

The source image remains authoritative at the canonical landing. A prompt that
says “dot”, “arc”, “bar”, “P”, or “wordmark” requests a hypothesis unless the
same structure is observed and accepted; it must not create a missing actor.

If Pillow or another declared raster observer is unavailable, keep only the
source-level facts that can actually be checked (format, dimensions, and any
human-provided annotations). Mark component observation as `not_run`, keep the
project `candidate`, and use the static-canonical fallback. Never promote
fallback boxes or prompt-supplied labels to `observed` or accepted semantic
roles.

## Unsupported preference handoff

Keep the user's intent even when the current renderer cannot execute it. The
planner records renderer-specific requests such as `glow`, high contrast,
keyboard/focus proof, timed pause, or MP4/WebM export as top-level
`constraints` with `status: recorded-unresolved`. This gives the next adapter a
machine-readable handoff and prevents a prompt from being mistaken for proof.

Example:

```json
{
  "id": "glow-policy",
  "kind": "visual",
  "importance": "cosmetic",
  "target": "glow preference requires a renderer adapter",
  "status": "recorded-unresolved",
  "source": "request"
}
```

## Automatic structure handoff

When the source is raster, the plan should make the observation handoff explicit:

1. `measure` records pixels, foreground components, and symbol/wordmark layout
   groups.
2. The planner uses group-local geometry to propose `origin-dot`, `arc`,
   `monogram`, and `wordmark` roles where the evidence supports them.
3. Every proposed role is serialized with `review_status: needs-review` and
   maps to a source actor and stage; it is never treated as a confirmed semantic
   label merely because the request used that word.
4. Raster actors use `geometry_strategy: pixel-observation-only`. The showcase
   may animate those exact source pixels, while the vector package remains
   blocked until a real reconstruction adapter accepts an editable scene.

For SVG, the same plan may use `geometry_strategy: preserve-source-vector` and
the source element IDs are the runtime actor selectors. In both cases, the
canonical stage must use the unchanged supplied identity.

When the decomposition is uncertain, tell the agent what the visible actors are
or request a static-canonical fallback. Never turn `dot`, `arc`, `bar`, `P`, or
`wordmark` labels into facts solely because they appeared in a prompt.

## A good request shape

Write the request in this order: source and identity rule -> industry/theme ->
foreground growth sequence -> visual controls -> accessibility -> output and
proof. For example:

> Use `brand/logo.jpg` as the unchanged source. This is an AI technology logo;
> route it to `ai-field`. Grow the observed foreground from point to arc to bar
> to P/letter to wordmark, use a solid `#0B0D12` background, `1600ms`, `1.25x`,
> no particles, respect reduced motion, and export a GIF. Keep the result
> `candidate` unless source-role review and final-frame evidence are present.

## Copy-ready examples

Use these as natural-language patterns. Keep the source rule and the requested
output explicit so the agent can separate identity, motion, and delivery:

**AI technology**

> Use `brand/logo.jpg` unchanged for an AI technology company. Route to
> `ai-field`. Grow the observed source actors from point to arc to bar to
> P/monogram to wordmark to canonical logo. Guide deterministic secondary
> signals into the measured actors, use a solid `#0B0D12` background, `1600ms`,
> `1.25x`, no particles, respect reduced motion, and export GIF and HTML.

**Education**

> Use `brand/logo.svg` as the canonical source for an education product. Route
> to `system-spatial` with an accessible modifier. Place the observed actors on
> a clear spatial grid, reveal the arc and bar before the monogram, then stage
> the wordmark left to right. Use `2400ms`, `0.75x`, a quiet solid background,
> pause/replay controls, static-canonical reduced motion, and export HTML/SVG.

**Pure background refinement**

> Keep the selected foreground trajectory and source geometry unchanged. Use a
> pure solid `#F4F1E8` background, no particles, no glow, `1800ms`, and export
> GIF plus PDF. If the renderer cannot bake that preference into media, keep it
> in `constraints` and state that the browser preview only was changed.
