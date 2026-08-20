"""Build a small dependency-free Motiflux browser delivery package."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION, contract_errors, load_document, write_json
from engine.planner import foreground_evidence
from engine.runtime import compile_runtime


RUNTIME_JS = r'''(() => {
  "use strict";
  const root = document.querySelector("[data-motiflux-root]");
  const mark = document.querySelector("[data-motiflux-mark]");
  const playButton = document.querySelector("[data-motiflux-play]");
  const pauseButton = document.querySelector("[data-motiflux-pause]");
  const replayButton = document.querySelector("[data-motiflux-replay]");
  const tempoInput = document.querySelector("[data-motiflux-tempo]");
  const duration = Number(root?.dataset.durationMs || 1200);
  const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  let current = reduceMotion ? duration : 0;
  let tempo = Number(root?.dataset.tempo || 1);
  let playing = !reduceMotion;
  let frame = 0;
  let lastTime = null;
  function clamp(value, low, high) { return Math.min(high, Math.max(low, value)); }
  function render(time) {
    current = clamp(time, 0, duration);
    const progress = duration ? current / duration : 1;
    root?.style.setProperty("--motiflux-progress", String(progress));
    root?.setAttribute("data-motiflux-state", progress >= 1 ? "canonical" : "playing");
    if (mark) mark.style.setProperty("--motiflux-progress", String(progress));
  }
  function tick(timestamp) {
    if (lastTime === null) lastTime = timestamp;
    if (playing && !document.hidden && !reduceMotion) {
      current += (timestamp - lastTime) * tempo;
      if (current >= duration) { current = duration; playing = false; }
      render(current);
    }
    lastTime = timestamp;
    frame = requestAnimationFrame(tick);
  }
  const control = {
    seek(milliseconds) { playing = false; render(Number(milliseconds) || 0); },
    finish() { playing = false; render(duration); },
    play() { if (!reduceMotion) { playing = true; lastTime = null; } },
    pause() { playing = false; },
    replay() { current = 0; playing = !reduceMotion; lastTime = null; render(current); },
    setTempo(value) { tempo = clamp(Number(value) || 1, 0.25, 4); }
  };
  window.__motifluxControl = control;
  window.__motifluxReady = true;
  playButton?.addEventListener("click", control.play);
  pauseButton?.addEventListener("click", control.pause);
  replayButton?.addEventListener("click", control.replay);
  tempoInput?.addEventListener("input", event => control.setTempo(event.target.value));
  document.addEventListener("visibilitychange", () => { lastTime = null; });
  render(current);
  frame = requestAnimationFrame(tick);
  window.addEventListener("unload", () => cancelAnimationFrame(frame), { once: true });
})();
'''


RUNTIME_CSS = r''':root {
  color-scheme: light dark;
  --motiflux-stage-size: min(72vw, 22rem);
  --motiflux-progress: 0;
  font-family: system-ui, sans-serif;
}
[data-motiflux-root] { display: grid; gap: 1rem; justify-items: center; }
[data-motiflux-stage] { width: var(--motiflux-stage-size); aspect-ratio: 1; display: grid; place-items: center; }
[data-motiflux-mark] { width: 100%; height: 100%; opacity: calc(.25 + var(--motiflux-progress) * .75); }
[data-motiflux-controls] { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; }
button, input { font: inherit; }
@media (prefers-reduced-motion: reduce) {
  [data-motiflux-mark] { opacity: 1; }
}
'''


def build(mark_path: Path, plan_path: Path, output_dir: Path) -> dict[str, Any]:
    plan = load_document(plan_path)
    if not isinstance(plan, dict):
        raise ValueError("motion plan must be a mapping")
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "motion-plan.schema.json"
    plan_schema = load_document(schema_path)
    plan_errors = contract_errors(plan, plan_schema)
    if plan_errors:
        raise ValueError("motion plan contract failed: " + "; ".join(plan_errors))
    runtime = plan.get("runtime", {}) if isinstance(plan.get("runtime"), dict) else {}
    duration = int(runtime.get("duration_ms", 1200))
    tempo = float(runtime.get("tempo", 1))
    mark = mark_path.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "mark.svg").write_text(mark, encoding="utf-8")
    (output_dir / "motion-plan.yaml").write_text(plan_path.read_text(encoding="utf-8"), encoding="utf-8")
    for relative in ("evidence", "evidence/geometry", "evidence/motion", "evidence/accessibility"):
        (output_dir / relative).mkdir(parents=True, exist_ok=True)
    title = html.escape(str(plan.get("project", {}).get("name", "Motiflux mark")))
    document = f'''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><link rel="stylesheet" href="motion.css"></head>
<body>
<main data-motiflux-root data-duration-ms="{duration}" data-tempo="{tempo}">
  <div data-motiflux-stage aria-label="Animated brand mark">{mark.replace('<svg', '<svg data-motiflux-mark', 1)}</div>
  <div data-motiflux-controls aria-label="Animation controls">
    <button type="button" data-motiflux-play>Play</button>
    <button type="button" data-motiflux-pause>Pause</button>
    <button type="button" data-motiflux-replay>Replay</button>
    <label>Tempo <input data-motiflux-tempo type="range" min="0.25" max="4" step="0.25" value="{tempo}"></label>
  </div>
</main>
<script src="motion.js"></script>
</body>
</html>
'''
    # Keep this compatibility adapter on the same runtime seam as the project
    # pipeline so trajectory metadata changes executable foreground behavior.
    runtime_files = compile_runtime(mark, plan)
    document = runtime_files["motion.html"]
    css = runtime_files["motion.css"]
    js = runtime_files["motion.js"]
    (output_dir / "motion.html").write_text(document, encoding="utf-8")
    (output_dir / "motion.css").write_text(css, encoding="utf-8")
    (output_dir / "motion.js").write_text(js, encoding="utf-8")
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate",
        "source": {"mark": str(mark_path), "plan": str(plan_path)},
        "constraint_summary": {"builder": "dependency-free-runtime-adapter"},
        "geometry_metrics": {},
        "motion_metrics": {"duration_ms": duration, "tempo": tempo},
        "foreground_evidence": foreground_evidence(plan),
        "canonical_fingerprint": {},
        "pixel_tolerance": {"status": "not-run"},
        "accessibility": {"reduced_motion": "static-canonical-css-fallback", "controls": ["play", "pause", "replay", "tempo"]},
        "substituted_tools": [],
        "not_run": ["browser-runtime-check", "canonical-fingerprint-check", "pixel-diff", "accessibility-tree-check"],
        "unresolved": ["brand-specific choreography and browser evidence remain to be supplied by the consuming project"],
    }
    write_json(output_dir / "evidence.json", evidence)
    write_json(output_dir / "evidence" / "source-analysis.json", {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate",
        "source": {"path": str(mark_path), "format": "svg"},
        "observations": {"elements": [], "colors": [], "landmarks": [], "negative_spaces": [], "topology": {}},
        "capabilities": ["builder-input"],
        "not_run": ["source-measurement"],
        "unresolved": ["run measure before geometry acceptance"],
    })
    return {"status": "candidate", "output": str(output_dir), "files": ["mark.svg", "motion.html", "motion-plan.yaml", "motion.css", "motion.js", "evidence.json", "evidence/"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mark", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    write_json(None, build(args.mark.resolve(), args.plan.resolve(), args.output.resolve()))


if __name__ == "__main__":
    main()
