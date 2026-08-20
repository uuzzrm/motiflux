# Motiflux V1 showcase

Public preview: [open the GitHub Pages showcase](https://uuzzrm.github.io/motiflux/)
or open `index.html` locally. The page is a static, checked-in demonstration;
browser controls never execute the exporter.

This directory is the visual, source-preserving demonstration for Motiflux V1.
It uses the supplied Prysai raster logo as one identity source and presents 13
different image-to-animation routes. The source identity is held constant;
the foreground actors enter, travel, and settle according to the selected
theme's trajectory.

## Start here

Open `index.html` in a local browser. Read each card as:

```text
same supplied image -> theme-specific foreground growth -> exact canonical landing
```

The left comparison cell is the source derivative. The right cell is a
checked-in GIF result. The browser surface provides play, pause, replay,
route filtering, prompt composition, tuning preview, and reduced-motion
fallback behavior for the page. These controls do not encode a new GIF or PDF.

The visible showcase checkpoints are:

```text
blank -> origin dot -> circular arc -> horizontal bar
  -> P / monogram -> Prysai wordmark -> complete Logo
```

These seven labels are presentation checkpoints for this raster showcase. The
generic Motiflux runtime uses the five machine stages
`seed -> trace -> assemble -> lockup -> canonical`; the two vocabularies must
not be treated as interchangeable schemas.

## What changes across the 13 routes

The route difference is the identity-bearing foreground choreography, not just
the background, glow, particles, or camera treatment. The current catalog
routes are:

| Theme ID | Trigger examples | Foreground trajectory |
| --- | --- | --- |
| `system-spatial` | education, learning, product, SaaS, structured | `knowledge-graph-lock` |
| `premium-quiet` | luxury, fashion, editorial, minimal, 高级感 | `contour-etch` |
| `developer-open` | developer, open source, API, code, tooling | `token-commit` |
| `ai-field` | AI, artificial intelligence, generative, data, 未来感 | `signal-convergence` |
| `fintech-trust` | fintech, banking, payments, reliable | `progress-confirm` |
| `security-shield` | security, privacy, authentication, protection | `boundary-unlock` |
| `commerce-energy` | commerce, retail, shopping, conversion | `burst-assembly` |
| `automotive-precision` | automotive, mobility, industrial, engineering | `kinematic-lock` |
| `sports-impact` | sports, fitness, speed, impact, dynamic | `impact-release` |
| `cinematic-title` | cinematic, film, title, trailer, dramatic | `aperture-title` |
| `nature-flow` | nature, organic, wellness, sustainable, growth | `organic-current` |
| `gaming-world` | gaming, esports, fantasy, sci-fi, quest | `orbit-quest` |
| `accessibility-first` | accessible, inclusive, calm, low motion, keyboard | `semantic-fade` |

`education` is a routing alias for `system-spatial`, not a fourteenth theme.
Use the explicit product or industry context before inferring from the image.
Public design systems are principle analogues only; this showcase does not
claim a vendor's private algorithm, endorsement, or copied artwork.

## Source observation boundary

The original supplied asset is `assets/prysai-logo-white.jpg`. The showcase
also keeps display derivatives such as `assets/prysai-mark-crop.jpg` and
`assets/prysai-mark-transparent.png`; they are derived from the supplied
source for layout and rendering, not a new identity design.

The raster observer may measure decoded dimensions, color/background samples,
foreground masks, connected components, bounds, centroids, adjacency, and
layout groups. It may propose geometric role candidates for planning. It does
not perform OCR, semantic recognition, or equivalent editable-SVG
reconstruction. A prompt saying “dot”, “P”, or “wordmark” cannot confirm that
role. The checked-in source analysis remains `candidate` / `needs-review`
until an explicit source annotation or human review accepts the binding.

The canonical ending is the supplied source pixels. A plausible-looking GIF,
poster, hash, or PDF does not by itself prove semantic role acceptance,
browser playback, accessibility behavior, or editable-vector equivalence.

## Prompt Lab: how to ask for a useful result

Use this order when writing a request for the skill:

```text
source and identity rule
-> surface/use case
-> one theme keyword or catalog ID
-> observed foreground sequence and fallback
-> duration, speed, direction, and pause
-> background, color, particles, and secondary effects
-> accessibility behavior
-> output formats and required proof
```

Example:

> Use the supplied logo unchanged for an AI technology product. Route it to
> `ai-field`. Animate only observed source actors and land on the exact
> canonical pixels. Use a solid `#0B0D12` background, `1600ms`, speed `1.25x`,
> center-outward entry, no particles, respect reduced motion, and export GIF.
> Keep unreviewed raster roles as hypotheses and report actual paths,
> lifecycle, evidence, `not_run`, and `unresolved`.

For education, say `education` or `system-spatial`; for a pure color say
`solid #F4F1E8 background`; for restrained motion say `low-amplitude, no
overshoot, speed 0.75x`; for an accessibility fallback say
`static-canonical reduced motion`. These are different controls: low motion
does not automatically mean system reduced motion.

Read [`skills/motiflux/guides/prompting.md`](../skills/motiflux/guides/prompting.md)
for the normalized fields, keyword table, raster review boundary, and
copy-ready prompts.

## Preview, bake, and verify

Keep these states separate:

| State | Meaning in this showcase |
| --- | --- |
| `preview` | A browser route, prompt, background, speed, duration, direction, particle, or motion control changed the local demonstration. No media was re-encoded. |
| `baked` | A named generator wrote a GIF, poster, HTML snapshot, evidence file, or PDF. The artifact still needs applicable inspection. |
| `verified` | The written artifact opened and the relevant source identity, stage, frame, runtime, and accessibility checks passed. |
| `candidate` | Useful output or observation exists, but required proof remains open. |
| `needs-review` | A raster role or actor binding is still a hypothesis. |
| `not_run` | A requested adapter or proof did not execute. |
| `unresolved` | A known limitation still needs review or an adapter decision. |

Changing a control in the browser is `preview`. To bake the current
repository-wide raster showcase, run from the project root:

```powershell
python showcase\generate_showcase.py --background '#F4F1E8' --duration-ms 2200 --speed 0.75 --no-particles
```

The supported bake controls are:

- `--background '#RRGGBB'` for one solid stage color;
- `--duration-ms MS` for the encoded growth window;
- `--speed X`, bounded from `0.25` to `4.0`, for progression shaping;
- `--no-particles` to remove secondary particle/field effects;
- `--no-guides` to remove secondary trajectory guides while retaining
  source-pixel growth;
- `--skip-pdf` to leave the PDF atlas unchanged.

The currently exposed command applies options to all 13 theme outputs. It
rewrites the checked-in GIFs, posters, HTML snapshot, machine-readable
evidence, and, unless skipped, the PDF atlas. Re-open the artifacts and run
the project's applicable validators before calling the result `verified`.

The full-atlas generator also writes this README from its built-in template.
After any full-atlas bake, re-open this file and confirm that this handoff
guidance is still present; a generated README snapshot is not proof that the
documentation or export itself was verified.

Direction in the page is an entry cue unless a source-specific adapter proves
a baked actor path. GIF and PDF are pre-rendered; they cannot respond to
`prefers-reduced-motion`. Use the poster as a static canonical fallback and
report that limitation explicitly.

## Single-route export and `export-manifest.json`

The generator source contains a focused builder named
`build_single_theme_export(...)` with the intended output directory:

```text
showcase/output/exports/<theme-id>/
  prysai-<theme-id>.gif
  prysai-<theme-id>-poster.png
  prysai-<theme-id>-{blank,spark,arc,bar,monogram,wordmark,canonical}.png
  export-manifest.json
```

The intended command is:

```powershell
python showcase\generate_showcase.py --theme ai-field --background '#0B0D12' --duration-ms 1600 --speed 1.25 --no-particles
```

The checked-in generator exposes `--theme`; `showcase/output/exports/` is
created when the command runs and is not proof of an export before invocation.
Treat this as executable capability, not an already-generated artifact. Return
only paths that exist after the command completes; if execution is skipped,
report the requested output in `not_run` rather than returning a made-up path.

When active, `export-manifest.json` records the source path and SHA-256, theme,
`trajectory_id`, `foreground_variant`, resolved export options, GIF/poster/
checkpoint paths, encoded frame count and duration, canonical final-frame
hash, and `not_run`/`unresolved` gaps. Its expected initial state is
`status: baked`, `evidence_status: candidate`; it is a route delivery ledger,
not semantic role review or browser/accessibility proof. It complements
`output/growth-evidence.json`, `<output>/project.json`, and
`artifact-index.json`.

## Files and generated evidence

- `index.html` - dependency-free 13-card interactive grid and Prompt Lab.
- `app.js` and `styles.css` - local preview controls and presentation shell.
- `assets/animations/prysai-<theme-id>.gif` - one baked image-to-animation
  result per route.
- `assets/animations/prysai-<theme-id>-poster.png` - static canonical final
  frame for loading, static presentation, or reduced-motion substitution.
- `themes.json` - derived display snapshot; it is not the routing authority.
- `output/source-analysis.json` - bounded raster observation and review state.
- `output/growth-evidence.json` - encoded stage frame indices, foreground mask
  metrics, trajectory fingerprints, and cross-theme comparison metadata.
- `output/pdf/motiflux-theme-atlas.pdf` - seven-checkpoint static storyboard;
  it is not a playable timeline or replacement for runtime evidence.

The current generated snapshot is intentionally `candidate` with
`needs-review` raster roles. `growth-evidence.json` reports one shared
canonical mask at the final stage and route-specific trajectory fingerprints;
the shared final mask is expected because every route must land on the same
source identity.

## Regenerate and inspect

From the repository root:

```powershell
python showcase\generate_showcase.py
python scripts\validate_project.py
python -m unittest discover -s tests -p "test_*.py"
```

For a quick read-only evidence summary:

```powershell
python -c "import json; p=json.load(open('showcase/output/growth-evidence.json', encoding='utf-8')); print(p['status'], p['review_status']); print(p['trajectory_comparison'])"
```

For a focused review, inspect one early frame, one active construction frame,
and the canonical final frame for the selected route. Record missing browser,
accessibility, raster-role, or export checks in `not_run`/`unresolved`; do not
upgrade a file merely because it exists or looks plausible.
