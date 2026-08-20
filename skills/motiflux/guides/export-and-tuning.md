# Motiflux export and tuning contract

Use this guide after routing and planning. Tune one dimension at a time, keep
the source geometry immutable, and validate the artifact after every material
change. A request preference is not proof that the current renderer executed
it.

## Shortest prompt formula

Use this order when handing a request to the exporter or to another agent:

```text
source + identity invariant -> surface -> one theme keyword -> observed foreground sequence -> duration/speed/direction -> background/particles -> reduced motion -> output format -> evidence required
```

For `solid`/pure-color backgrounds, provide a hex color. If the user did not
provide one, resolve `#0B0D12` and record `background.source: default`; a
user-provided color is `source: prompt`. The current `direction` control is a
preview entry cue, not proof of a full actor path. The web runtime can respond to
`prefers-reduced-motion`; pre-rendered GIF/PDF cannot, so pair either format with
the canonical poster or another static output.

## Contents

- [Parameter mapping](#parameter-mapping)
- [Tuning dimensions](#tuning-dimensions)
- [Safe tuning loop](#safe-tuning-loop)
- [Export workflow](#export-workflow)
- [Single-route manifest](#single-route-manifest)
- [Failure and unverified handoff](#failure-and-unverified-handoff)
- [Format outputs](#format-outputs)
- [Evidence boundary](#evidence-boundary)

## Parameter mapping

### Shortest safe tuning loop

1. Keep the source actors, stage order, and canonical pixels unchanged.
2. Change one measurable dimension, such as `solid #F4F1E8 background`, `2200ms`, `speed 0.75x`, or `no particles`.
3. Use the browser controls only to preview the wording and local shell.
4. Run the named exporter to create media, then inspect the artifact and report `preview`, `baked`, or `verified` separately from `candidate`/`needs-review` evidence.

Selecting an output format in Prompt Lab does not run an exporter. A color
picker value is used only when the background mode is `solid`.

Use the stable plan fields first. Store preferences that the generic runtime
does not consume in `constraints` and report them as unresolved until a
renderer/adapter proves them.

| Request | Plan expression | Current baseline |
| --- | --- | --- |
| Duration | `runtime.duration_ms` as a positive integer | The total authored growth window. The web runtime uses it directly; the showcase derives a theme base duration and its page slider scales preview time only. |
| Speed / tempo | `runtime.tempo` as a positive number; interactive `setTempo` is clamped to `0.25-4` | Playback rate in the web runtime. It is not the same as a stage's `speed_profile` or the route's actor-to-actor pacing. |
| Direction | `runtime.direction` and `runtime.direction_vector` | The generic web runtime consumes it as a bounded entry offset; the selected trajectory still determines the foreground construction. The showcase selector is preview-only. |
| Solid background | `runtime.background: {mode: solid, color: "#...", source: prompt|default}` | Always include a color; if omitted, use `#0B0D12` with `source: default`. The generic web runtime uses it for the stage surface. |
| Particles | `runtime.particles: true/false` plus a deterministic `runtime.seed`; keep particles secondary | Theme-dependent. Particles cannot be the only foreground distinction or replace source actors. |
| No particles | `runtime.particles: false` and `runtime.secondary_effect: plain` | Safe default for identity-first and accessibility-first output. |
| Reduced motion | `runtime.reduced_motion: static-canonical` or `opacity-only` | The web runtime honors `prefers-reduced-motion`; pre-rendered GIF/PDF files cannot react to that system setting, so provide a static poster or a separate reduced-motion export. |
| Output | `runtime.requested_formats: [html, svg, gif, pdf]` | Record each requested surface and map only formats produced by a real generator or capture adapter. |

Interpret the controls in two layers. `runtime.duration_ms` is the authored
growth window; `runtime.tempo` is playback/time scaling; `direction` is a
bounded entry preference unless a source-specific adapter proves a full path;
`background` changes the surface; `particles` controls secondary effects; and
`reduced_motion` declares the fallback policy. A theme's `speed_profile` and
`path_strategy` remain separate from those runtime controls. If a requested
property is not consumed by the selected renderer, retain it as a constraint
with `recorded-unresolved` rather than claiming it was baked.

For small refinements, normalize the request as one change at a time. These
forms are intentionally explicit:

```text
Keep source actors, stage order, and canonical pixels unchanged.
Change only the presentation: solid #F4F1E8 background, no particles,
low-amplitude/no-overshoot motion, speed 0.75x, and left-to-right entry.
Report which controls were baked and keep direction or low-motion unresolved
if the selected adapter only previews them.
```

The phrase `pure color` means one solid background color, not a palette change
to the source mark. `no particles` removes secondary decoration only. `speed`
changes playback or authored timing according to the selected adapter;
`direction` may change only the entry offset. `low-amplitude`, `no overshoot`,
and `opacity-first` are renderer constraints unless the adapter explicitly
implements them. `static-canonical reduced motion` is the accessibility
fallback and is not interchangeable with a low-motion animation.

Example tuning fragment:

```yaml
runtime:
  duration_ms: 1600
  tempo: 0.92
  seed: 7
  direction: left-to-right
  direction_vector: [1, 0]
  background:
    mode: solid
    color: "#0B0D12"
    source: prompt
  particles: false
  secondary_effect: field
  reduced_motion: static-canonical
  requested_formats: [html, svg, gif, pdf]
```

`duration_ms`, `tempo`, `seed`, `direction`, `background`, `particles`, and
`reduced_motion` are stable runtime parameters. A theme's `speed_profile`
describes the relative pacing of its foreground actors; it does not override
the total duration or playback multiplier. Browser pixels, raster contour
quality, accessibility-tree behavior, and export capture still require their
respective adapters and evidence. Keep the output candidate when those checks
are absent.

## Tuning dimensions

Change one dimension per iteration and state what must remain invariant. The
theme route controls foreground choreography; runtime controls tune how that
choreography is presented. A theme change is therefore different from a
background, speed, direction, or particle change.

| Dimension | Safe request form | Preserve | Check |
| --- | --- | --- | --- |
| Theme | `route to ai-field with quiet modifier` | source actors, canonical scene, identity constraints | the selected route has an executable trajectory and the plan records rejected conflicts |
| Foreground variant | `use the route's declared source-pixel variant` | theme identity, stage order, canonical source | same-source midframes or trajectory evidence show the variant; do not report a label-only change |
| Background | `solid #0B0D12 background` | source pixels/vectors, foreground order, topology | the stage surface changed, while the source-derived foreground and canonical ending did not |
| Speed | `1600ms, speed 1.25x` or `2400ms, speed 0.75x` | actor order, route, canonical ending | telemetry and encoded duration reflect the change; distinguish authored duration from playback tempo |
| Direction | `left to right entry` or `center outward` | measured actor geometry and stage order | `center outward` normalizes to executable `radial`; report whether the adapter bakes it or only previews an entry offset |
| Particles | `no particles` or `sparse secondary particles, seed 7` | identity-bearing foreground, contrast, reduced-motion fallback | the planner records density/seed; the generic runtime guarantees the on/off switch, so density remains adapter-dependent |
| Low motion | `low-amplitude, no overshoot, opacity-first, speed 0.75x` | source scene, semantic order, readable canonical stage | speed is executable; low-amplitude/no-overshoot/opacity-first remain renderer constraints unless implemented by the adapter |
| System reduced motion | `static-canonical reduced motion` | exact final source scene and accessibility semantics | the web runtime responds to the system preference; pre-rendered media receives a separate static fallback |

Do not use “more futuristic,” “smoother,” or “more energetic” as a complete
control. Pair the adjective with a canonical theme or measurable parameter.
If the current adapter cannot execute the requested change, keep it in
`constraints`, mark it unresolved, and say whether the visible result is only a
preview.

For the checked-in showcase, `duration_ms` is the nominal theme growth window
and `playback_duration_ms` is the GIF's frame-quantized encoded time. The local
duration control scales the player clock, while the speed control multiplies
that clock; neither changes GIF pixels. Direction is an entry-side preference
in that preview, whereas `path_strategy` and `speed_profile` describe the
theme's actual foreground construction.

For a pure-color request, write the color and the surface together, for example
`solid #0B0D12 background`. This changes the stage background while preserving
the supplied Logo pixels. In the local showcase, the background selector and
color input update the preview shell and copyable request only; they do not
rewrite the checked-in GIF or PDF. To bake the change into either media file,
update the request or theme input, rerun the real generator, and inspect the
new files.

Use a complete tuning sentence when handing the request to another agent:

```text
Keep the observed foreground growth unchanged. Use a solid #F4F1E8 background,
2400ms, speed 0.75x, no particles, reduced motion as static-canonical, and
export GIF plus PDF. Return the generated paths and the validation status.
```

This separates identity, motion, atmosphere, accessibility, and delivery. A
phrase such as `make it more futuristic` is only a modifier; pair it with a
canonical route such as `ai-field` and an executable control such as
`signal convergence`, `no particles`, or `solid #0B0D12 background`.

For a direction request, distinguish entry direction from path direction. The
generic runtime can consume a bounded `direction_vector` as an entry offset, but
the theme's `path_strategy` still determines how observed actors travel. Do not
claim a measured left-to-right draw path when only the initial offset changed.
For a speed request, distinguish `runtime.tempo` from each stage's relative
`speed_profile`; report both when they differ.

## Common refinements

Phrase refinements as an explicit constraint plus the output you want:

| User wants | Use this wording | Verify |
| --- | --- | --- |
| Pure color | `solid #F4F1E8 background` | The rendered stage has one background color and the source-derived foreground is unchanged. |
| No decoration | `no particles, no glow, identity-first foreground` | The logo still has a distinct construction path; removing effects must not remove the trajectory. |
| Slower reading | `2400ms, speed 0.75x, keep the canonical stage readable` | The final frame remains readable and the telemetry duration changes. |
| Directional entry | `left to right` or `right to left` | Treat this as an entry-side preference unless the selected trajectory has a measured directional path. |
| Low-motion design | `low-amplitude, no overshoot, speed 0.75x` | Motion is restrained while the authored foreground remains available. |
| System reduced motion | `static-canonical reduced motion` | The reduced state removes large movement and lands on the unchanged canonical mark. |

Change one row at a time. If a control is only available in the local showcase,
describe it as a preview change until the generator has been rerun and the
output file has been inspected.

For low-motion requests, distinguish `low-amplitude`, `no overshoot`, and
`opacity-first` as motion constraints from `static-canonical reduced motion` as
the system/accessibility fallback. Do not silently substitute one for the
other. For `no particles`, remove only secondary decoration; retain the
identity-bearing foreground trajectory and canonical landing.

## Safe tuning loop

1. Route the request and retain the returned `primary_id`, `matched_tags`, and
   `trajectory_id`.
2. Measure the source before assigning `source_actors`. For SVG, use vector
   observations. For raster, the Pillow adapter may provide foreground mask,
   connected components, bounds, and role candidates; keep `candidate` and
   `needs-review` until those roles are checked.
3. Tune one of duration, tempo, direction, background, secondary effect, or
   reduced motion. Keep `foreground_plan.stage_order` and canonical source
   paint unchanged.
4. Validate the plan and package:

   ```powershell
   python skills/motiflux/tools/motiflux.py validate motion-plan motion-plan.yaml
   python skills/motiflux/tools/motiflux.py build mark.svg motion-plan.yaml work/motiflux-package
   python skills/motiflux/tools/motiflux.py probe work/motiflux-package
   ```

5. Inspect stage snapshots and telemetry. Confirm that the requested change
   affects the intended stage, that source actors remain visible in order, and
   that no background-only change is being presented as a new theme.
6. Keep `status: candidate` when browser, pixel, raster, or accessibility
   evidence is missing. Never remove `not_run` or `unresolved` entries to make
   the report look complete.

At the end of the loop, report three separate layers:

```text
output lifecycle: preview -> baked -> verified
evidence status: candidate|complete
review/gaps: needs-review|not_run|unresolved
```

`preview` means a local control or composition changed; no requested media is
proved. `baked` means a named generator or capture adapter wrote the requested
artifact. `verified` additionally means the artifact opened and the applicable
source, stage, runtime, or export checks passed. `candidate` remains correct
when useful output exists but required evidence is open. `not_run` names a
requested adapter or proof that did not execute; `unresolved` names a known gap
that still requires a decision or check. These labels are reported together,
not collapsed into one status.

Useful tuning heuristics are starting points, not theme rules: around 900 ms
feels fast, 1400–1600 ms is a general reveal range, and 2200 ms or more suits a
quiet reading pause. Recheck legibility and stage boundaries after changing
duration or tempo.

## Export workflow

### Choose the exporter by source

Choose by both the source format and the requested delivery surface. The source
format determines what can be preserved; the requested format determines which
adapter must run.

| Source | Requested format | Select | Boundary / failure rule |
| --- | --- | --- | --- |
| accepted SVG | HTML or SVG | `motiflux.py build` | build the source-specific web package; validate and probe it |
| accepted SVG | GIF or PDF | an approved capture/export adapter | `build` alone is not media evidence; keep the format `not_run` if capture is absent |
| PNG/JPG/WebP | GIF or PDF in this repository | `showcase/generate_showcase.py` | preserves supplied pixels at canonical landing; role review remains `candidate`/`needs-review` |
| PNG/JPG/WebP | HTML or editable SVG | accepted raster reconstruction adapter | without that adapter, do not claim semantic recognition or equivalent SVG; use `not_run` |
| any source | MP4/WebM or another unlisted format | a named approved adapter | no adapter means no invented path and `not_run: [format-export]` |

JPG/PNG observation is a bounded pixel measurement. It is not semantic
recognition, and the showcase GIF/PDF is not an editable-vector reconstruction.
Keep those statements true even when the generated media looks visually
plausible.

For the current supplied JPG/PNG showcase, regenerate the checked-in GIF grid
and PDF with the showcase adapter:

```powershell
python showcase/generate_showcase.py
```

This consumes the bounded raster observation, preserves the source pixels as
the canonical landing, and keeps the result `candidate` until role review and
browser evidence exist. It is the correct path for `export GIF` or `export
PDF` in this repository. It is not an editable-vector exporter.

For the checked-in raster showcase, the supported baked controls are explicit:

```powershell
python showcase/generate_showcase.py --background '#F4F1E8' --duration-ms 2200 --speed 0.75 --no-particles
```

`--background` accepts a hex color, `--duration-ms` must be long enough for the
encoded frame cadence, `--speed` is bounded from `0.25` to `4.0`, and
`--no-particles` removes secondary effects. The generator has no independent
`--direction` flag: a page direction selector is a preview entry cue unless a
source-specific adapter bakes actor direction. The command rewrites the
showcase GIFs, posters, HTML, evidence, and PDF; use `--skip-pdf` when the PDF
should remain unchanged.

To bake only the selected route, pass `--theme <theme-id>`:

```powershell
python showcase/generate_showcase.py --theme ai-field --background '#0B0D12' --duration-ms 1600 --speed 1.25 --no-particles
```

This writes `showcase/output/exports/ai-field/` with `prysai-ai-field.gif`,
`prysai-ai-field-poster.png`, seven named checkpoint PNGs, and
`export-manifest.json`. The manifest is the machine-readable handoff for the
source hash, resolved options, route variant, encoded timing, canonical frame
hash, and `not_run`/`unresolved` gaps. It reports `status: baked`; inspect the
files and run the applicable checks before calling the output `verified`.

The Prompt Lab displays this command for copying only. Its checkpoint slider
changes the visible baked PNG checkpoint and pauses the local review state; it
does not seek or rewrite the native GIF. Reduced motion uses the static
canonical poster, while the GIF download remains the full encoded trajectory.

Build the canonical web package from an accepted SVG scene:

```powershell
python skills/motiflux/tools/motiflux.py measure path/to/source.svg --output work/source-analysis.json
python skills/motiflux/tools/motiflux.py route "AI logo animation"
python skills/motiflux/tools/motiflux.py validate motion-plan motion-plan.yaml
python skills/motiflux/tools/motiflux.py build mark.svg motion-plan.yaml work/motiflux-package
python skills/motiflux/tools/motiflux.py probe work/motiflux-package
```

Use `evidence.json` and the files under `evidence/` as the delivery record.
The package builder is dependency-free and does not itself create a GIF or a
PDF. Do not rename `motion.html` to a media format.

The browser controls have the same boundary: `play`, `pause`, `replay`, and
preview timing demonstrate the validated web runtime; the native GIF preview is
not seekable and the page controls are not a media encoder. Use the
showcase generator for the checked-in 13-theme GIF/PDF atlas, or record a
separate approved capture adapter for another project.

## Single-route manifest

There are two showcase export scopes:

| Scope | Intended command | Output root | Current checked-in state |
| --- | --- | --- | --- |
| Full atlas | `python showcase/generate_showcase.py [options]` | `showcase/assets/animations/`, `showcase/output/` | exposed and used for the 13-theme bake |
| One route | `python showcase/generate_showcase.py --theme <theme-id> [options]` | `showcase/output/exports/<theme-id>/` | `--theme` is exposed; the directory is created on invocation |

The single-route contract is designed for focused iteration. A successful
invocation writes:

```text
showcase/output/exports/<theme-id>/
  prysai-<theme-id>.gif
  prysai-<theme-id>-poster.png
  prysai-<theme-id>-blank.png
  prysai-<theme-id>-spark.png
  prysai-<theme-id>-arc.png
  prysai-<theme-id>-bar.png
  prysai-<theme-id>-monogram.png
  prysai-<theme-id>-wordmark.png
  prysai-<theme-id>-canonical.png
  export-manifest.json
```

The stage checkpoint names are showcase presentation labels. They do not
override the generic runtime's five-stage plan and do not turn a raster role
hypothesis into a confirmed semantic role.

`export-manifest.json` records the route-level handoff:

```yaml
schema_version: "1.0"
status: baked
evidence_status: candidate
source: showcase/assets/prysai-mark-crop.jpg
source_sha256: <hash>
theme: ai-field
trajectory_id: signal-convergence
foreground_variant: polar-counter
export_options: {background: "#0B0D12", duration_ms: 1600, speed: 1.25, particles: false, guides: true}
outputs:
  gif: showcase/output/exports/ai-field/prysai-ai-field.gif
  poster: showcase/output/exports/ai-field/prysai-ai-field-poster.png
  stage_checkpoints: {blank: <path>, canonical: <path>}
encoded_frame_count: <integer>
encoded_duration_ms: <integer>
canonical_frame_sha256: <hash>
not_run: [browser-pixel-review, human-raster-role-review, raster-to-vector-reconstruction]
unresolved: [raster-role-semantics]
```

The manifest proves that the named exporter wrote a route package and records
its inputs/options. It does not prove browser playback, accessibility, human
role acceptance, semantic recognition, or editable-vector equivalence. Keep
`status: baked` and `evidence_status: candidate` until the applicable frames
and checks are inspected. If the CLI flag is not available, report
`not_run: [single-route-cli]` and do not claim that `export-manifest.json`
exists. The manifest is complementary to, not a replacement for,
`showcase/output/growth-evidence.json`, `<output>/project.json`, or
`artifact-index.json`.

### Current single-route CLI boundary

The full-atlas command is the repository-wide showcase bake:

```powershell
python showcase/generate_showcase.py --background '#0B0D12' --duration-ms 1600 --speed 1.25 --no-particles --no-guides
```

The focused command is executable in the current generator:

```powershell
python showcase/generate_showcase.py --theme ai-field --background '#0B0D12' --duration-ms 1600 --speed 1.25 --no-particles
```

Do not silently substitute the full atlas when a user asks for one route. The
single-route command creates its export directory and manifest only when it
runs; before that, do not return a made-up artifact path. If execution is
skipped, leave the requested output in `not_run`.

### Export state handoff

Use this sequence for every requested format:

```text
requested -> adapter selected -> artifact written (baked)
  -> artifact opened/inspected -> applicable proof recorded (verified or candidate)
```

If no adapter exists, keep the format in `not_run` and return no invented path.
If the adapter wrote a file but source-role review, browser pixels, accessibility,
or another required check is missing, report the file as `baked` and the result
as `candidate`. A package build can be baked while its browser behavior remains
unverified; a showcase GIF can be baked while raster roles remain
`needs-review`.

### Failure and unverified handoff

Report the first failed or skipped boundary, the reason, and its consequence.
Use `not_run` for work that did not execute; use `unresolved` for a known gap
that still needs review or an adapter decision. Do not replace either with
`verified: false` alone, and do not return a path for an artifact that was not
written.

| Situation | Report | Do not claim |
| --- | --- | --- |
| source cannot be read or observed | `candidate`, `not_run: [source-observation]`, reason | observed actors or a valid foreground decomposition |
| raster observer ran but roles are unreviewed | output may be `baked`, evidence `candidate`, `unresolved: [raster-role-review]` | semantic identification of JPG/PNG components |
| requested adapter is unavailable | `path: null`, lifecycle `preview`, `not_run: [format-export]` | that a preview or package file is the requested media |
| artifact was written but not opened/checked | lifecycle `baked`, evidence `candidate`, `unresolved: [artifact-inspection]` | `verified` |
| validation or probe fails | retain the error and failed check; do not upgrade lifecycle | a passing export or runtime contract |

Example: a raster request can produce a useful GIF while HTML remains
unavailable and the result is still unverified:

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
evidence_status: candidate
not_run: [html-export, browser-pixels]
unresolved: [raster-role-review, artifact-inspection]
```

If the GIF was never generated, set its `path: null` and `lifecycle: preview`
instead. If it was generated but the final frame was not inspected, keep
`lifecycle: baked`; the missing inspection prevents `verified` but does not
erase the useful artifact.

## Format outputs

| Format | Produced by | Expected path / meaning |
| --- | --- | --- |
| SVG | `motiflux.py build` | `<package>/mark.svg`: canonical editable vector scene used by the package. |
| HTML | `motiflux.py build` | `<package>/motion.html`, with `motion.css` and `motion.js`; exposes the Motiflux runtime controls. |
| GIF | `showcase/generate_showcase.py` for the 13-theme showcase | `showcase/assets/animations/*.gif`; a portable image-to-animation presentation, not generic CLI output. |
| Poster | `showcase/generate_showcase.py` for the 13-theme showcase | `showcase/assets/animations/*-poster.png`; a static canonical final-frame fallback, not a reduced-motion-capable GIF. |
| PDF | `showcase/generate_showcase.py` for the atlas | `showcase/output/pdf/motiflux-theme-atlas.pdf`; a storyboard/overview, not a replacement for runtime evidence. |
| Stage evidence | `showcase/generate_showcase.py` for the atlas | `showcase/output/growth-evidence.json`; progress-point frame indices, foreground mask hashes, alpha mass/bounds/centroids, trajectory fingerprints, cross-theme uniqueness, and unresolved review status. |

The showcase growth evidence is a generator-specific JSON record rather than
one of the generic `validate_artifact.py` kinds. Check it with the project
validator and the showcase tests:

```powershell
python scripts/validate_project.py
python -m unittest discover -s tests -p "test_*.py"
```

For a quick read-only inspection of its cross-theme comparison:

```powershell
python -c "import json; p=json.load(open('showcase/output/growth-evidence.json', encoding='utf-8')); print(p['status'], p['review_status']); print(p['trajectory_comparison'])"
```

### Two delivery contracts

Keep these surfaces separate when explaining an output:

1. **Raster showcase contract.** `showcase/index.html` is a 13-card
   comparison built from the supplied JPG/PNG observation. Each card uses the
   same source derivative and a checked-in theme GIF; the PDF is a static atlas
   of those rendered frames. Its role labels remain `candidate`/
   `needs-review`, and its browser controls do not turn the raster into an
   editable vector scene.
2. **SVG runtime contract.** `motion.html` with `motion.css`, `motion.js`, and
   `mark.svg` is the source-specific web package produced from an accepted SVG
   plan. It exposes `__motifluxReady` and `__motifluxControl`, supports runtime
   controls and reduced motion, and is not itself a GIF/PDF encoder.

The two contracts may share the same theme vocabulary, but their files,
evidence, and claims are different. Use the exporter that matches the source
format and requested surface.

For the raster showcase, report the media evidence precisely: the GIF is the
complete encoded growth trajectory; the poster is the canonical final-frame
fallback for static presentation; and the PDF is a seven-checkpoint static
storyboard. A GIF hash, poster hash, or PDF readability check proves file
integrity/readability only. It does not prove semantic role acceptance, browser
playback, `prefers-reduced-motion` response, or uniqueness of foreground paths
without the corresponding frame and runtime checks.

To regenerate the repository showcase and its GIF/PDF outputs:

```powershell
python showcase/generate_showcase.py
```

Use `--skip-pdf` when only the HTML and GIF showcase assets are needed:

```powershell
python showcase/generate_showcase.py --skip-pdf
```

The showcase generator is scoped to the checked-in 13-theme comparison. For a
different project, use an approved browser/raster capture adapter to make a
GIF from the validated HTML runtime and record that adapter in evidence. The
generic `build` command alone is not GIF evidence.

The local showcase has two distinct actions:

1. **Preview and compose.** Use the route selector and tuning controls to see
   the requested direction/background wording and copy a prompt. These controls
   do not regenerate media in the browser.
2. **Bake and verify.** Run `python showcase/generate_showcase.py` after changing
   a theme/source setting, then inspect the generated GIF/PDF paths and rerun
   the validation commands. Only the second action is evidence that media was
    exported with the new setting.

## Verify an export

After a material change, use this short handoff loop:

```powershell
python showcase/generate_showcase.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/validate_project.py
```

Then inspect one early frame, one active draw-on frame, and the final frame of
at least the selected route. For the 13-theme showcase, confirm that every
`showcase/assets/animations/*.gif` opens, the PDF exists, and the final frame
is the supplied source mark on its selected stage background. The raster role
map remains `candidate`/`needs-review`; a successful file check does not turn
that observation into semantic recognition. GIF and PDF are pre-rendered
media: they cannot respond to `prefers-reduced-motion`; verify the static
poster separately and describe any reduced-motion export as a separate file.

For a complete trajectory check, use `showcase/output/growth-evidence.json` to
locate the selected GIF's stage frame indices and inspect at least one early,
active, and canonical frame. Treat `trajectory_fingerprint` and cross-theme
comparison as supporting metadata when they include route information; they
are not, alone, visual proof that foreground trajectories differ. Record
missing frame inspection, browser checks, or accessibility checks in
`not_run`/`unresolved`.

Use this status vocabulary in the result:

```text
preview: browser controls changed the local demonstration
baked: named generator wrote the requested GIF/PDF/HTML artifact
verified: artifact opens and the source/stage contract was checked
candidate: raster roles, browser pixels, or accessibility evidence still need review
not_run: requested format or proof has no approved adapter
```

These labels are not one enum. Use `preview -> baked -> verified` for the
output lifecycle, `candidate`/`complete` for overall evidence, and
`needs-review`, `not_run`, and `unresolved` for review and evidence gaps. For
example, a GIF can be `baked` yet remain `candidate` because raster role review
or browser evidence is open; a preview can show `needs-review` without
producing any media file. Report all three layers when they differ.

For a multi-format request, report lifecycle per format rather than one global
word:

```yaml
outputs:
  - format: html
    path: work/motiflux-package/motion.html
    lifecycle: baked
  - format: gif
    path: null
    lifecycle: preview
evidence_status: candidate
not_run: [gif-export, browser-pixels]
unresolved: [raster-role-review]
```

If only the background, speed, or direction changed in the browser, report
`preview` only. Re-run the exporter and repeat the frame checks before calling
the setting baked or verified.

For a source-specific handoff, report the boundary explicitly. When the
showcase exporter runs, use `growth-evidence.json` to identify the exact GIF
frame used for `blank`, `spark`, `arc`, `bar`, `monogram`, `wordmark`, and
`canonical`; do not infer a stage from a label or from a player clock alone.

Report the boundary as:

```text
preview: route and controls updated in the local HTML
baked: GIF/PDF regenerated by the named exporter
verified: file exists, opens, and matches the requested source/stage contract
not_run: browser pixels, accessibility tree, or unsupported media formats
```

Never call a preview-only background, speed, or direction change an exported
media result. If the request asks for MP4/WebM or an editable SVG from a raster
source and no approved adapter ran, keep that output in `not_run`.

## Evidence boundary

An SVG source can provide measured elements and semantic geometry evidence when
the corresponding adapters run. It still needs runtime/browser checks for
actual playback, reduced motion, focus, contrast, and browser pixels.

A raster source can provide bounded pixel observations when Pillow is available:
foreground mask, connected components, bounds, centroids, layout groups, and
geometric role candidates. This is a bounded geometric observation, not semantic
recognition or unrestricted shape reconstruction. The plan remains `candidate`
with `needs-review`; the observations do not create an equivalent editable SVG.
The showcase generator can consume these candidate boxes to make
image-to-animation GIFs from the supplied pixels. Do not export a raster-derived
`mark.svg` as if it were source-equivalent without a dedicated reconstruction
adapter.

The canonical stage is the unchanged source scene at the end of the fixed
`seed -> trace -> assemble -> lockup -> canonical` order. A readable ending is
expressed through the authored duration, tempo, and stage timing intent; the
current runtime has no independent canonical reading-hold field and does not
support arbitrary foreground order.

Before handoff, check:

- `mark.svg` is the accepted canonical scene and is unchanged by animation.
- `foreground_plan` contains source actors, stable stage order, distinct
  trajectory strategy, speed profile, fallback, and proof points.
- `motion.html` exposes `__motifluxReady`, `seek`, and `finish`, and the final
  frame is canonical.
- `prefers-reduced-motion` resolves to the declared fallback.
- GIF/PDF paths exist only when their generator or capture adapter actually ran.
- `not_run` and `unresolved` accurately describe missing evidence.

Before calling a result verified, report each requested format separately:

```yaml
outputs:
  - format: gif
    path: actual-path-or-null
    lifecycle: preview|baked|verified
    evidence: complete|candidate
  - format: poster
    path: actual-path-or-null
    lifecycle: preview|baked|verified
    evidence: complete|candidate
  - format: pdf
    path: actual-path-or-null
    lifecycle: preview|baked|verified
    evidence: complete|candidate
not_run: []
unresolved: []
```

`verified` requires the named exporter to have run and the applicable artifact,
source identity, stage, and evidence checks to have been inspected. Keep a
useful file `baked`/`candidate` when role review, browser pixels, or another
required proof remains open.
