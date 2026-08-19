# Motiflux V1 showcase

This showcase uses one supplied raster source - `assets/prysai-logo-white.jpg` -
to make a direct visual comparison across 13 playable Motiflux logo-growth animations.

Open `index.html` locally for the interactive comparison grid. Each card keeps
the same source image on the left and runs a real blank-to-canonical construction
sequence on the right: blank, spark (source dot), arc, bar, monogram, wordmark,
and canonical. Each theme changes construction timing and motion language; it does not redraw or
rename the Prysai identity.

## Files

- `index.html` - dependency-free interactive grid with filtering and motion controls.
- `assets/animations/prysai-ai-field.gif` - the primary image-to-animation output
  for the example request; every theme also has a portable GIF export.
- The repository root `README.md` contains a generated GitHub-native card grid:
  every card places the same static source image on the left beside its theme GIF
  on the right, with the route trigger keywords below.
- `themes.json` - derived display snapshot generated from the canonical catalog;
  it is not used for routing.
- `assets/prysai-logo-white.jpg` - supplied source image, copied unchanged.
- `assets/prysai-mark-crop.jpg` and `assets/prysai-mark-transparent.png` - display-only derivatives made from the same source; no geometry edits.
- `output/pdf/motiflux-theme-atlas.pdf` - printable five-frame growth storyboard atlas.

## Regenerate

From the repository root:

```powershell
python showcase\generate_showcase.py
```

The HTML presents the actual image-to-animation result first. The PDF includes
the route example `artificial-intelligence` -> `AI-field` and records five growth
frames of each playable animation. Public design systems are principle analogues
only; this material does not claim private vendor algorithms.
