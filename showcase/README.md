# Motiflux V1 showcase

This showcase uses one supplied raster source - `assets/prysai-logo-white.jpg` -
to make a direct visual comparison across 13 Motiflux theme routes.

Open `index.html` locally for the interactive comparison grid. Each card keeps
the source mark on the left and shows a theme-specific representative output
stage on the right. The output stage changes motion language and secondary
visual treatment; it does not redraw or rename the Prysai identity.

## Files

- `index.html` - dependency-free interactive grid with filtering and motion controls.
- `themes.json` - structured theme records used by the page and PDF generator.
- `assets/prysai-logo-white.jpg` - supplied source image, copied unchanged.
- `assets/prysai-mark-crop.jpg` and `assets/prysai-mark-transparent.png` - display-only derivatives made from the same source; no geometry edits.
- `output/pdf/motiflux-theme-atlas.pdf` - printable comparison atlas.

## Regenerate

From the repository root:

```powershell
python showcase\generate_showcase.py
```

The PDF includes a route example for the phrase `artificial-intelligence` ->
`AI-field`. Public design systems are principle analogues only; this material
does not claim private vendor algorithms or browser-runtime validation.
