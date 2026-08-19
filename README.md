# Motiflux

Motiflux is an AI skill for turning a brand mark into an editable SVG scene and a
responsive, validated motion package. It treats logo animation as a constrained
design-and-verification problem: identity, topology, motion language, runtime
behavior, accessibility, and the canonical final state are all explicit.

Status: private development · Motiflux V1 · plugin release `1.0.0`

## What is included

- `.codex-plugin/plugin.json` — Codex plugin manifest and project metadata.
- `skills/motiflux/SKILL.md` — the core AI workflow and completion contract.
- `skills/motiflux/guides/motion-themes.md` — 13 theme routes with algorithm
  stacks, implementation controls, exclusions, and QA focus.
- `skills/motiflux/agents/openai.yaml` — UI metadata for skill discovery.
- `skills/motiflux/guides/project-kernel.md` — AI-facing stage graph, module
  interfaces, artifact integrity, and extension protocol.
- `skills/motiflux/schemas/` — machine-readable contracts for plans, evidence,
  telemetry, source observations, artifact indexes, and runtime probes.
- `skills/motiflux/catalog/themes.json` — the single machine-readable catalog
  for 13 routable motion themes.
- `skills/motiflux/tools/` — offline `measure`, `route`, `project`, `compare`,
  `audit`, `build`, `probe`, and `validate` command seams.
- `examples/basic-mark/` — a deterministic end-to-end fixture.
- `showcase/` — a source-preserving 13-theme comparison grid, supplied Prysai
  asset, and generated PDF atlas.
- `docs/` and `tasks/` — architecture decisions and the active implementation
  plan.
- `scripts/validate_project.py` — dependency-free repository structure and
  content checks.

The skill keeps its working context focused. Project-level documentation and
validation stay outside the skill directory so they do not become accidental
instructions during an AI task.

## Design model

```text
source mark
    ↓
constraint graph → scene graph → motion graph → runtime package
    ↓                 ↓              ↓               ↓
evidence ledger ← geometry QA ← temporal QA ← accessibility QA
```

Theme selection changes choreography and implementation parameters; it must not
change identity constraints of the source mark. Public design systems are used
only as principle references, never as claims about private vendor algorithms or
copied assets.

## Architecture

The public interface is the unified project command. Internally, a dependency-
checked stage registry keeps the execution graph explicit:

```text
analyze → route → plan → reconstruct → verify-geometry
                                      ↓
                         compile → verify-package → verify-motion
                                      ↓
                         artifact-index + project manifest
```

Each stage declares its prerequisites and products. Missing prerequisites block
dependent stages and remain visible in the manifest. Every generated file is
indexed with SHA-256, byte size, media type, and producing stage. The local
runtime probe can verify static package markers and a Node harness; it does not
claim browser-pixel or accessibility-tree proof. See
[`project-kernel.md`](skills/motiflux/guides/project-kernel.md) and
[`ADR-006`](docs/decisions/ADR-006-dependency-checked-pipeline-and-artifact-index.md).

## Showcase

The source-preserving atlas feeds the same supplied Prysai image into 13 real
logo-growth GIF outputs. The example request `artificial-intelligence logo
animation` routes to `AI-field`, where the mark grows from a blank field through
spark, arc, bar, monogram, and wordmark construction before the canonical hold.
Each card keeps the input image beside a directly playable GIF. Algorithm
stacks, beats, and QA focus remain secondary explanations of the construction
being shown.

[Open the interactive HTML grid](showcase/index.html) · [Download the PDF atlas](showcase/output/pdf/motiflux-theme-atlas.pdf)

![Motiflux V1 theme atlas cover](showcase/output/previews/atlas-cover.png)

<!-- GITHUB_GALLERY:START -->

## GitHub-native image → animation gallery

Every card uses the same supplied Prysai source on the left and the portable GIF generated for that theme on the right. The GIF is a real checked-in output, so GitHub can play it directly without JavaScript or a separate deployment.

<table class="motiflux-gallery">
<tr>
<td width="50%" valign="top">
<h3>01 · System-spatial</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for System-spatial" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-system-spatial.gif" alt="System-spatial Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>system-spatial</code><br><sub>TRIGGER KEYWORDS</sub><br><code>system</code> <code>product</code> <code>saas</code> <code>dashboard</code> <code>enterprise</code> <code>interface</code> <code>structured</code> <code>clear</code> <code>technology</code> <code>education</code> <code>learning</code> <code>teaching</code> <code>course</code> <code>knowledge</code> <code>教育</code> <code>学习</code> <code>课程</code> <code>教学</code> <code>知识</code></p>
<p><sub>Communicate state change, hierarchy, and spatial continuity through semantic movement.</sub></p>
</td>
<td width="50%" valign="top">
<h3>02 · Premium-quiet</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Premium-quiet" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-premium-quiet.gif" alt="Premium-quiet Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>premium-quiet</code><br><sub>TRIGGER KEYWORDS</sub><br><code>premium</code> <code>luxury</code> <code>fashion</code> <code>beauty</code> <code>editorial</code> <code>quiet</code> <code>elegant</code> <code>minimal</code></p>
<p><sub>Create perceived value through restraint, material presence, optical alignment, and deliberate timing.</sub></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<h3>03 · Developer-open</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Developer-open" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-developer-open.gif" alt="Developer-open Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>developer-open</code><br><sub>TRIGGER KEYWORDS</sub><br><code>developer</code> <code>open source</code> <code>opensource</code> <code>api</code> <code>cli</code> <code>code</code> <code>tooling</code> <code>technical</code> <code>precise</code></p>
<p><sub>Make transformation legible to technical users through explicit phases and reproducible state.</sub></p>
</td>
<td width="50%" valign="top">
<h3>04 · AI-field</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for AI-field" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-ai-field.gif" alt="AI-field Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>ai-field</code><br><sub>TRIGGER KEYWORDS</sub><br><code>ai</code> <code>artificial intelligence</code> <code>machine learning</code> <code>ml</code> <code>neural</code> <code>data</code> <code>model</code> <code>generative</code> <code>future</code> <code>intelligent</code></p>
<p><sub>Suggest intelligence through organized transformation rather than science-fiction decoration.</sub></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<h3>05 · Fintech-trust</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Fintech-trust" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-fintech-trust.gif" alt="Fintech-trust Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>fintech-trust</code><br><sub>TRIGGER KEYWORDS</sub><br><code>fintech</code> <code>banking</code> <code>bank</code> <code>payments</code> <code>payment</code> <code>trust</code> <code>finance</code> <code>institutional</code> <code>reliable</code> <code>secure finance</code></p>
<p><sub>Communicate reliability, controlled movement, and successful resolution.</sub></p>
</td>
<td width="50%" valign="top">
<h3>06 · Security-shield</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Security-shield" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-security-shield.gif" alt="Security-shield Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>security-shield</code><br><sub>TRIGGER KEYWORDS</sub><br><code>security</code> <code>privacy</code> <code>identity</code> <code>authentication</code> <code>auth</code> <code>defense</code> <code>shield</code> <code>compliance</code> <code>protection</code></p>
<p><sub>Convey boundary, verification, and controlled access.</sub></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<h3>07 · Commerce-energy</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Commerce-energy" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-commerce-energy.gif" alt="Commerce-energy Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>commerce-energy</code><br><sub>TRIGGER KEYWORDS</sub><br><code>commerce</code> <code>retail</code> <code>shopping</code> <code>marketplace</code> <code>consumer</code> <code>sale</code> <code>conversion</code> <code>friendly</code></p>
<p><sub>Create approachability and action without making the brand feel unstable.</sub></p>
</td>
<td width="50%" valign="top">
<h3>08 · Automotive-precision</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Automotive-precision" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-automotive-precision.gif" alt="Automotive-precision Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>automotive-precision</code><br><sub>TRIGGER KEYWORDS</sub><br><code>automotive</code> <code>mobility</code> <code>transport</code> <code>engineering</code> <code>performance</code> <code>industrial</code> <code>mechanical</code></p>
<p><sub>Express mass, direction, precision, and mechanical confidence.</sub></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<h3>09 · Sports-impact</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Sports-impact" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-sports-impact.gif" alt="Sports-impact Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>sports-impact</code><br><sub>TRIGGER KEYWORDS</sub><br><code>sports</code> <code>fitness</code> <code>competition</code> <code>speed</code> <code>impact</code> <code>bold</code> <code>dynamic</code> <code>athletics</code></p>
<p><sub>Create energy through anticipation, compression, release, and recovery.</sub></p>
</td>
<td width="50%" valign="top">
<h3>10 · Cinematic-title</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Cinematic-title" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-cinematic-title.gif" alt="Cinematic-title Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>cinematic-title</code><br><sub>TRIGGER KEYWORDS</sub><br><code>cinematic</code> <code>film</code> <code>movie</code> <code>title</code> <code>trailer</code> <code>story</code> <code>dramatic</code> <code>suspense</code></p>
<p><sub>Reveal meaning through attention control, scale, silence, and composition.</sub></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<h3>11 · Nature-flow</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Nature-flow" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-nature-flow.gif" alt="Nature-flow Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>nature-flow</code><br><sub>TRIGGER KEYWORDS</sub><br><code>nature</code> <code>organic</code> <code>wellness</code> <code>sustainable</code> <code>water</code> <code>wind</code> <code>growth</code> <code>calm</code> <code>health</code></p>
<p><sub>Imply growth, breath, flow, and connection without losing mark structure.</sub></p>
</td>
<td width="50%" valign="top">
<h3>12 · Gaming-world</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Gaming-world" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-gaming-world.gif" alt="Gaming-world Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>gaming-world</code><br><sub>TRIGGER KEYWORDS</sub><br><code>gaming</code> <code>esports</code> <code>fantasy</code> <code>sci-fi</code> <code>character</code> <code>quest</code> <code>arcade</code> <code>playful</code></p>
<p><sub>Create personality, reward, and world-building around a recognizable mark.</sub></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<h3>13 · Accessibility-first</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="showcase/assets/prysai-mark-crop.jpg" alt="Static Prysai source mark for Accessibility-first" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="showcase/assets/animations/prysai-accessibility-first.gif" alt="Accessibility-first Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>accessibility-first</code><br><sub>TRIGGER KEYWORDS</sub><br><code>accessible</code> <code>accessibility</code> <code>reduced motion</code> <code>calm</code> <code>inclusive</code> <code>low motion</code> <code>keyboard</code> <code>assistive</code></p>
<p><sub>Preserve orientation and feedback while minimizing vestibular, cognitive, and visual load.</sub></p>
</td>
<td width="50%" valign="top"></td>
</tr>
</table>

<sub>LEFT = unchanged source image · RIGHT = generated animated result</sub>

<!-- GITHUB_GALLERY:END -->

## Local validation

From the repository root:

```powershell
python -m pip install -r requirements-ci.txt
python scripts/validate_project.py
python H:\Codex\home\skills\.system\skill-creator\scripts\quick_validate.py skills\motiflux
python H:\Codex\home\skills\.system\plugin-creator\scripts\validate_plugin.py .
python -m unittest discover -s tests -v
```

The two paths into `H:\Codex\home` are local development helpers. The first
command is the repository's portable check and is the one used by GitHub Actions.

## Tool pipeline

```powershell
python skills\motiflux\tools\motiflux.py measure examples\basic-mark\mark.svg --output work\source-analysis.json
python skills\motiflux\tools\motiflux.py validate source-analysis work\source-analysis.json
python skills\motiflux\tools\motiflux.py compare examples\basic-mark\mark.svg examples\basic-mark\mark.svg
python skills\motiflux\tools\motiflux.py audit examples\basic-mark\telemetry.json --duration-ms 1200
python skills\motiflux\tools\motiflux.py build examples\basic-mark\mark.svg examples\basic-mark\motion-plan.yaml work\basic-package
python skills\motiflux\tools\motiflux.py route "AI security startup"
python skills\motiflux\tools\motiflux.py project examples\basic-mark\mark.svg "AI logo animation" work\project
python skills\motiflux\tools\motiflux.py validate project work\project\project.json
python skills\motiflux\tools\motiflux.py validate artifact-index work\project\artifact-index.json
python skills\motiflux\tools\motiflux.py probe work\project\package
python showcase\generate_showcase.py
```

The project command runs `analyze -> route -> plan -> reconstruct ->
verify-geometry -> compile -> verify-package -> verify-motion` and writes a
traceable `project.json` plus `artifact-index.json`. SVG input can compile
through the deterministic fixture; raster input remains an honest `candidate`
and blocks vector-dependent stages until a real raster-to-vector adapter is
available.

The output is deliberately evidence-preserving. A valid semantic SVG comparison
does not claim browser pixels, raster contours, or accessibility-tree proof.
Those remain explicit `not_run` items until the corresponding adapter runs.

## Development boundary

This repository is intentionally private while Motiflux V1 is being developed.
No public release, GitHub Pages deployment, or production runtime is implied by
the repository itself. A consuming project supplies the source mark and produces
the output package described by the skill contract.

## Showcase boundary

The `showcase/` atlas is a separate demonstration surface inspired by the
source-to-output comparison pattern used by public logo-motion projects. It
uses one supplied Prysai raster source across 13 routed themes. Every checked-in
GIF is a construction sequence, not a complete-logo transform: blank, spark,
arc, bar, monogram, wordmark, canonical. Its HTML output contains dependency-
free players with per-card play, pause, replay, timeline, reduced-motion, and
hidden-page behavior. Its PDF records five representative growth frames, with
algorithm notes kept as context. These materials do not claim private vendor
algorithms, copied assets, or generic-package browser validation.
