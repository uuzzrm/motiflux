# Motiflux V1 showcase

This showcase uses one supplied raster source - `assets/prysai-logo-white.jpg` -
to make a direct visual comparison across 13 playable Motiflux theme animations.

Open `index.html` locally for the interactive comparison grid. Each card keeps
the same source image on the left and runs a real source-to-animation sequence
on the right: source, reveal, transform, settle, and canonical hold. The
animation changes motion language and secondary visual treatment; it does not
redraw or rename the Prysai identity.

## Files

- `index.html` - dependency-free interactive grid with filtering and motion controls.
- `assets/animations/prysai-ai-field.gif` - the primary image-to-animation output
  for the example request; every theme also has a portable GIF export.
- The repository root `README.md` contains a generated GitHub-native gallery:
  every row places the same static source image beside its theme GIF and trigger
  keywords, so the image-to-animation result is visible without opening HTML.
- `themes.json` - derived display snapshot generated from the canonical catalog;
  it is not used for routing.
- `assets/prysai-logo-white.jpg` - supplied source image, copied unchanged.
- `assets/prysai-mark-crop.jpg` and `assets/prysai-mark-transparent.png` - display-only derivatives made from the same source; no geometry edits.
- `output/pdf/motiflux-theme-atlas.pdf` - printable four-frame storyboard atlas.

## Regenerate

From the repository root:

```powershell
python showcase\generate_showcase.py
```

The HTML presents the actual image-to-animation result first. The PDF includes
the route example `artificial-intelligence` -> `AI-field` and records four key
frames of each playable animation. Public design systems are principle analogues
only; this material does not claim private vendor algorithms.
