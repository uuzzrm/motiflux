"""Compile a motion plan into a deterministic dependency-free runtime."""

from __future__ import annotations

import html
import json
import re
from typing import Any


EFFECT_CSS = {
    "grid": ".motiflux-secondary{background-image:linear-gradient(rgba(138,164,255,.18) 1px,transparent 1px),linear-gradient(90deg,rgba(138,164,255,.18) 1px,transparent 1px);background-size:22px 22px}",
    "quiet": ".motiflux-secondary{background:radial-gradient(circle,color-mix(in srgb,var(--motiflux-accent) 18%,transparent),transparent 68%)}",
    "scan": ".motiflux-secondary{background:repeating-linear-gradient(0deg,transparent 0 7px,color-mix(in srgb,var(--motiflux-accent) 15%,transparent) 8px 9px)}",
    "field": ".motiflux-secondary{background:radial-gradient(circle at 18% 32%,var(--motiflux-accent) 0 1px,transparent 2px),radial-gradient(circle at 76% 62%,var(--motiflux-accent) 0 1px,transparent 2px);background-size:47px 43px,61px 58px}",
    "ring": ".motiflux-secondary{border:1px solid color-mix(in srgb,var(--motiflux-accent) 60%,transparent);border-radius:50%;inset:14%}",
    "shield": ".motiflux-secondary{clip-path:polygon(50% 3%,92% 18%,84% 72%,50% 98%,16% 72%,8% 18%);border:1px solid color-mix(in srgb,var(--motiflux-accent) 60%,transparent)}",
    "burst": ".motiflux-secondary{inset:36% 8%;border-top:1px solid var(--motiflux-accent);border-bottom:1px solid var(--motiflux-accent);transform:rotate(-20deg)}",
    "track": ".motiflux-secondary{inset:0;background:linear-gradient(90deg,transparent,color-mix(in srgb,var(--motiflux-accent) 70%,transparent),transparent);width:35%}",
    "speed": ".motiflux-secondary{inset:25% 0;background:repeating-linear-gradient(165deg,transparent 0 12px,color-mix(in srgb,var(--motiflux-accent) 55%,transparent) 13px 14px)}",
    "curtain": ".motiflux-secondary{inset:0;background:linear-gradient(90deg,#000 0 43%,transparent 44% 56%,#000 57%)}",
    "wave": ".motiflux-secondary{inset:0;background:repeating-radial-gradient(ellipse at 20% 80%,transparent 0 16px,color-mix(in srgb,var(--motiflux-accent) 25%,transparent) 17px 18px);transform:rotate(-9deg) scale(1.3)}",
    "orbit": ".motiflux-secondary{inset:14%;border:1px dotted color-mix(in srgb,var(--motiflux-accent) 70%,transparent);border-radius:50%}",
    "plain": ".motiflux-secondary{background:linear-gradient(90deg,transparent,color-mix(in srgb,var(--motiflux-accent) 18%,transparent),transparent)}",
}

TRAJECTORY_CSS = {
    "knowledge-graph-lock": '[data-trajectory="knowledge-graph-lock"] [data-motiflux-mark]{clip-path:inset(0 calc((1 - var(--motiflux-progress)) * 100%) 0 0)}',
    "contour-etch": '[data-trajectory="contour-etch"] [data-motiflux-mark]{clip-path:circle(calc(var(--motiflux-progress) * 80%) at 50% 50%)}',
    "token-commit": '[data-trajectory="token-commit"] [data-motiflux-mark]{clip-path:inset(0 0 calc((1 - var(--motiflux-progress)) * 100%) 0)}',
    "signal-convergence": '[data-trajectory="signal-convergence"] [data-motiflux-mark]{clip-path:circle(calc(var(--motiflux-progress) * 100%) at 50% 50%);filter:saturate(calc(.4 + var(--motiflux-progress) * .6))}',
    "progress-confirm": '[data-trajectory="progress-confirm"] [data-motiflux-mark]{clip-path:polygon(0 0,calc(var(--motiflux-progress) * 100%) 0,calc(var(--motiflux-progress) * 100%) 100%,0 100%)}',
    "boundary-unlock": '[data-trajectory="boundary-unlock"] [data-motiflux-mark]{clip-path:inset(calc((1 - var(--motiflux-progress)) * 18%) round 12%)}',
    "burst-assembly": '[data-trajectory="burst-assembly"] [data-motiflux-mark]{clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%)}',
    "kinematic-lock": '[data-trajectory="kinematic-lock"] [data-motiflux-mark]{clip-path:inset(0 calc((1 - var(--motiflux-progress)) * 100%) 0 0);transform:translateX(calc((1 - var(--motiflux-progress)) * -14%)) scale(calc(.96 + var(--motiflux-progress) * .04))}',
    "impact-release": '[data-trajectory="impact-release"] [data-motiflux-mark]{clip-path:inset(0 calc((1 - var(--motiflux-progress)) * 100%) 0 0);transform:translateX(calc((1 - var(--motiflux-progress)) * -20%)) scaleX(calc(.78 + var(--motiflux-progress) * .22))}',
    "aperture-title": '[data-trajectory="aperture-title"] [data-motiflux-mark]{clip-path:inset(0 calc((1 - var(--motiflux-progress)) * 48%) round 3%)}',
    "organic-current": '[data-trajectory="organic-current"] [data-motiflux-mark]{clip-path:ellipse(calc(var(--motiflux-progress) * 72%) 100% at 50% 50%);transform:translateY(calc((1 - var(--motiflux-progress)) * 8px)) rotate(calc((1 - var(--motiflux-progress)) * -2deg))}',
    "orbit-quest": '[data-trajectory="orbit-quest"] [data-motiflux-mark]{clip-path:circle(calc(var(--motiflux-progress) * 84%) at 50% 50%);transform:scale(calc(.8 + var(--motiflux-progress) * .2)) rotate(calc((1 - var(--motiflux-progress)) * 8deg))}',
    "semantic-fade": '[data-trajectory="semantic-fade"] [data-motiflux-mark]{clip-path:none;opacity:calc(.35 + var(--motiflux-progress) * .65)}',
}


# The theme CSS remains an auxiliary field. The source-growth runtime below
# reveals addressable source actors one at a time so the mark itself carries
# the animation story.
ACTOR_GROWTH_CSS = r'''
[data-motiflux-root][data-growth-mode="staged-source-actors"] [data-motiflux-mark]{clip-path:none!important;filter:none!important;transform:none!important;opacity:1!important}
[data-motiflux-root][data-growth-mode="staged-source-actors"] [data-motiflux-mark] [data-motiflux-actor]{opacity:0;transform-box:fill-box;transform-origin:center;will-change:opacity,transform,clip-path,stroke-dashoffset}
[data-motiflux-root][data-growth-mode="staged-source-actors"] .motiflux-secondary{opacity:calc(var(--motiflux-progress) * .55)}
@media (prefers-reduced-motion:reduce){[data-motiflux-root][data-growth-mode="staged-source-actors"] [data-motiflux-mark] [data-motiflux-actor]{opacity:1!important;transform:none!important;clip-path:none!important;stroke-dasharray:none!important;stroke-dashoffset:none!important}}
'''


ACTOR_GROWTH_JS = r'''(() => {
  "use strict";
  const root = document.querySelector("[data-motiflux-root]");
  const mark = document.querySelector("[data-motiflux-mark]");
  const duration = Number(root?.dataset.durationMs || 1400);
  const trajectory = root?.dataset.trajectory || "semantic-fade";
  const directionVector = (() => {
    try {
      const value = JSON.parse(root?.dataset.directionVector || "[0,0]");
      return Array.isArray(value) && value.length === 2 ? value.map(Number) : [0, 0];
    } catch (error) { return [0, 0]; }
  })();
  const stageOrder = JSON.parse(root?.dataset.foregroundStageOrder || '["seed","trace","assemble","lockup","canonical"]');
  const actorStages = JSON.parse(root?.dataset.foregroundActorStages || "{}");
  const stageStrategies = JSON.parse(root?.dataset.foregroundStageStrategies || "{}");
  const sourceNodes = Array.from(mark?.querySelectorAll?.("[data-motiflux-actor]") || []);
  const actorNodes = Object.entries(actorStages).map(([id, index]) => {
    const node = sourceNodes.find(candidate => candidate.getAttribute("data-motiflux-actor") === id);
    return node ? { node, stage: Number(index), role: node.getAttribute("data-motiflux-role") || "unknown" } : null;
  }).filter(Boolean);
  const expectedActorCount = Object.keys(actorStages).length;
  const dynamicActors = expectedActorCount > 0 && actorNodes.length === expectedActorCount;
  const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  let current = reduced ? duration : 0;
  let tempo = Number(root?.dataset.tempo || 1);
  let playing = !reduced && dynamicActors;
  let frame = 0;
  let last = null;

  function clamp(value, low = 0, high = 1) { return Math.min(high, Math.max(low, value)); }
  function ease(value) { const p = clamp(value); return p * p * (3 - 2 * p); }
  function actorProgress(progress, stage) {
    const count = Math.max(1, stageOrder.length);
    let start = stage / count;
    let span = 1.45 / count;
    if (trajectory === "contour-etch" && stage === 1) start -= .06;
    if (trajectory === "burst-assembly") start -= .08;
    if (trajectory === "aperture-title" && stage >= 3) start += .05;
    if (trajectory === "semantic-fade") span = 1.1 / count;
    start = clamp(start, 0, 1);
    const end = clamp(start + span, 0, 1);
    return ease((progress - start) / Math.max(.1, end - start));
  }
  function trajectoryTransform(progress, role, actorIndex) {
    const remaining = 1 - progress;
    const side = actorIndex % 2 === 0 ? -1 : 1;
    if (trajectory === "signal-convergence") return `translate(${side * remaining * 34}px,${remaining * (role === "wordmark" ? 18 : -18)}px)`;
    if (trajectory === "progress-confirm") return `translateX(${remaining * -18}px)`;
    if (trajectory === "boundary-unlock") return `scale(${.88 + progress * .12})`;
    if (trajectory === "burst-assembly") return `translate(${side * remaining * -24}px,${remaining * 12}px)`;
    if (trajectory === "kinematic-lock") return `translateX(${remaining * -42}px)`;
    if (trajectory === "impact-release") return `translateX(${remaining * -58}px) scaleX(${.86 + progress * .14})`;
    if (trajectory === "aperture-title") return `translateY(${remaining * 10}px)`;
    if (trajectory === "organic-current") return `translate(${side * remaining * 12}px,${Math.sin(progress * Math.PI) * remaining * -10}px) rotate(${side * remaining * -2}deg)`;
    if (trajectory === "orbit-quest") return `rotate(${side * remaining * 18}deg) translateX(${remaining * 16}px)`;
    if (trajectory === "contour-etch") return `scale(${.98 + progress * .02})`;
    if (trajectory === "token-commit") return `translateX(${remaining * -8}px)`;
    return "";
  }
  function directionTransform(progress) {
    const remaining = 1 - progress;
    const x = Number.isFinite(directionVector[0]) ? directionVector[0] : 0;
    const y = Number.isFinite(directionVector[1]) ? directionVector[1] : 0;
    if (!x && !y) return "";
    return `translate(${x * remaining * 16}px,${y * remaining * 16}px)`;
  }
  function revealActor(entry, progress, actorIndex) {
    const node = entry.node;
    const p = actorProgress(progress, entry.stage);
    const role = entry.role;
    if (progress >= 1) {
      node.style.opacity = "1";
      node.style.transform = "";
      node.style.clipPath = "none";
      node.style.strokeDasharray = "";
      node.style.strokeDashoffset = "";
      return;
    }
    node.style.opacity = p <= .001 ? "0" : String(.14 + p * .86);
    let roleTransform = "";
    if (role === "origin-dot") {
      roleTransform = `scale(${.2 + p * .8})`;
      node.style.clipPath = "circle(50% at 50% 50%)";
    } else if (role === "bar") {
      node.style.transformOrigin = "left center";
      roleTransform = `scaleX(${.08 + p * .92})`;
      node.style.clipPath = `inset(0 ${100 - p * 100}% 0 0)`;
    } else if (role === "arc") {
      const length = typeof node.getTotalLength === "function" ? node.getTotalLength() : 0;
      const stroke = node.getAttribute("stroke") || getComputedStyle(node).stroke;
      if (length > 0 && stroke && stroke !== "none") {
        node.style.strokeDasharray = String(length);
        node.style.strokeDashoffset = String(length * (1 - p));
        node.style.clipPath = "none";
      } else {
        node.style.clipPath = `circle(${Math.max(4, p * 80)}% at 50% 50%)`;
      }
    } else if (role === "wordmark") {
      node.style.transformOrigin = "left center";
      roleTransform = `translateX(${(1 - p) * -8}%) scaleX(${.96 + p * .04})`;
      node.style.clipPath = `inset(0 ${100 - p * 100}% 0 0)`;
    } else {
      roleTransform = `scale(${.72 + p * .28})`;
      node.style.clipPath = `circle(${Math.max(4, p * 100)}% at 50% 50%)`;
    }
    node.style.transform = [directionTransform(p), trajectoryTransform(p, role, actorIndex), roleTransform].filter(Boolean).join(" ");
    node.setAttribute("data-motiflux-actor-progress", p.toFixed(3));
    node.setAttribute("data-motiflux-actor-order", String(actorIndex));
  }
  function renderForeground(progress) {
    const index = Math.min(stageOrder.length - 1, Math.floor(progress * stageOrder.length));
    const stage = stageOrder[index];
    root?.setAttribute("data-motiflux-foreground-stage", stage);
    root?.setAttribute("data-motiflux-path-strategy", stageStrategies[stage] || "source-derived");
    actorNodes.forEach((entry, actorIndex) => revealActor(entry, progress, actorIndex));
  }
  function render(milliseconds) {
    current = clamp(milliseconds, 0, duration);
    const progress = duration ? current / duration : 1;
    root?.style.setProperty("--motiflux-progress", String(progress));
    root?.setAttribute("data-motiflux-runtime", dynamicActors ? "actor-growth" : "static-canonical");
    root?.setAttribute("data-motiflux-state", progress >= 1 || !dynamicActors ? "canonical" : "playing");
    root?.setAttribute("data-motiflux-beat", progress < .25 ? root?.dataset.beatStart : progress < .75 ? root?.dataset.beatMiddle : root?.dataset.beatEnd);
    mark?.style.setProperty("--motiflux-progress", String(progress));
    renderForeground(progress);
  }
  function tick(timestamp) {
    if (last === null) last = timestamp;
    if (playing && !document.hidden && !reduced) {
      current += (timestamp - last) * tempo;
      if (current >= duration) { current = duration; playing = false; }
      render(current);
    }
    last = timestamp;
    frame = requestAnimationFrame(tick);
  }
  const control = {
    seek(milliseconds) { playing = false; render(Number(milliseconds) || 0); },
    finish() { playing = false; render(duration); },
    play() { if (!reduced && dynamicActors) { playing = true; last = null; } },
    pause() { playing = false; },
    replay() { current = 0; playing = !reduced && dynamicActors; last = null; render(current); },
    setTempo(value) { tempo = clamp(Number(value) || 1, .25, 4); root?.setAttribute("data-tempo", String(tempo)); },
  };
  window.__motifluxControl = control;
  window.__motifluxReady = true;
  document.querySelector("[data-motiflux-play]")?.addEventListener("click", control.play);
  document.querySelector("[data-motiflux-pause]")?.addEventListener("click", control.pause);
  document.querySelector("[data-motiflux-replay]")?.addEventListener("click", control.replay);
  document.querySelector("[data-motiflux-tempo]")?.addEventListener("input", event => control.setTempo(event.target.value));
  document.addEventListener("visibilitychange", () => { last = null; if (document.hidden) control.pause(); });
  render(current);
  frame = requestAnimationFrame(tick);
  window.addEventListener("unload", () => cancelAnimationFrame(frame), { once: true });
})();'''


SOURCE_ELEMENT_RE = re.compile(
    r"(<(?:circle|ellipse|line|path|polygon|polyline|rect|text|use)\b)([^>]*?)(/?>)",
    re.IGNORECASE,
)


def mark_with_runtime_actor_attributes(mark_svg: str, actor_ids: list[str], actor_roles: dict[str, str] | None = None) -> str:
    """Add non-identity selectors so synthetic source actor IDs remain addressable."""

    actor_roles = actor_roles or {}
    index = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal index
        attributes = match.group(2)
        source_id = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', attributes, re.IGNORECASE)
        if source_id and source_id.group(1) in actor_ids:
            actor_id = source_id.group(1)
        else:
            actor_id = actor_ids[index] if index < len(actor_ids) else None
            index += 1
        if not actor_id:
            return match.group(0)
        escaped = html.escape(str(actor_id), quote=True)
        role = html.escape(str(actor_roles.get(str(actor_id), "unknown")), quote=True)
        if "data-motiflux-actor=" not in attributes:
            attributes += f' data-motiflux-actor="{escaped}"'
        if "data-motiflux-role=" not in attributes:
            attributes += f' data-motiflux-role="{role}"'
        return f'{match.group(1)}{attributes}{match.group(3)}'

    return SOURCE_ELEMENT_RE.sub(replace, mark_svg)


def compile_runtime(mark_svg: str, plan: dict[str, Any]) -> dict[str, str]:
    runtime = plan.get("runtime", {})
    selection = plan.get("theme_selection", {})
    effect = str(runtime.get("secondary_effect", "plain"))
    trajectory = str(selection.get("trajectory_id", "semantic-fade"))
    trajectory_summary = str(selection.get("trajectory_summary", "stable semantic reveal"))
    if trajectory not in TRAJECTORY_CSS:
        raise ValueError(f"unknown Motiflux trajectory: {trajectory}")
    duration = int(runtime.get("duration_ms", 1400))
    tempo = float(runtime.get("tempo", 1.0))
    damping = float(runtime.get("settle_damping", 0.82))
    accent = str(runtime.get("accent", "#9c8cff"))
    background = runtime.get("background", {}) if isinstance(runtime.get("background"), dict) else {}
    background_mode = str(background.get("mode", "theme"))
    background_color = str(background.get("color") or "transparent")
    if not re.fullmatch(r"(?:#[0-9a-fA-F]{3,8}|transparent|[a-zA-Z]+)", background_color):
        background_color = "transparent"
    particles = bool(runtime.get("particles", True))
    particle_density = str(runtime.get("particle_density", "standard"))
    if particle_density not in {"sparse", "standard", "dense"}:
        particle_density = "standard"
    particle_seed = max(0, min(2147483647, int(runtime.get("seed", 0) or 0)))
    direction_vector = runtime.get("direction_vector", [0, 0])
    if not isinstance(direction_vector, list) or len(direction_vector) != 2:
        direction_vector = [0, 0]
    try:
        direction_x = int(direction_vector[0]) * 12
        direction_y = int(direction_vector[1]) * 12
    except (TypeError, ValueError):
        direction_x, direction_y = 0, 0
    title = html.escape(str(plan.get("project", {}).get("name", "Motiflux mark")))
    beat_ids = [str(beat.get("id")) for beat in plan.get("beats", []) if isinstance(beat, dict) and beat.get("id")]
    beat_ids = beat_ids or ["orient", "form", "resolve"]
    foreground = plan.get("foreground_plan", {})
    foreground_stages = foreground.get("stages", []) if isinstance(foreground, dict) else []
    stage_order = [str(item) for item in foreground.get("stage_order", [])] if isinstance(foreground, dict) else []
    if not stage_order:
        stage_order = ["seed", "trace", "assemble", "lockup", "canonical"]
    stage_indices = {stage_id: index for index, stage_id in enumerate(stage_order)}
    actor_stages: dict[str, int] = {}
    stage_strategies: dict[str, str] = {}
    planned_actor_stages = foreground.get("actor_stage_map", {}) if isinstance(foreground, dict) else {}
    if isinstance(planned_actor_stages, dict):
        for actor_id, stage_value in planned_actor_stages.items():
            if isinstance(stage_value, str) and stage_value in stage_indices:
                actor_stages[str(actor_id)] = stage_indices[stage_value]
            elif isinstance(stage_value, (int, float)):
                actor_stages[str(actor_id)] = max(0, min(len(stage_order) - 1, int(stage_value)))
    for index, stage in enumerate(foreground_stages):
        if not isinstance(stage, dict):
            continue
        stage_id = str(stage.get("id", ""))
        if not stage_id:
            continue
        stage_strategies[stage_id] = str(stage.get("path_strategy", "source-derived"))
        for actor_id in stage.get("source_actors", []) or []:
            actor_stages.setdefault(str(actor_id), stage_indices.get(stage_id, index))
    role_annotations = foreground.get("role_annotations", {}) if isinstance(foreground, dict) else {}
    raster_source = any(
        isinstance(actor, dict) and actor.get("geometry_strategy") == "pixel-observation-only"
        for actor in plan.get("actors", [])
    )
    actor_ids = [str(actor.get("id")) for actor in plan.get("actors", []) if isinstance(actor, dict) and actor.get("id")]
    actor_ids = actor_ids or list(actor_stages)
    raster_actor_ids = {
        str(actor.get("id"))
        for actor in plan.get("actors", [])
        if isinstance(actor, dict)
        and actor.get("id")
        and actor.get("geometry_strategy") == "pixel-observation-only"
    }
    raster_review_open = bool(raster_actor_ids) and any(
        not isinstance(role_annotations, dict)
        or not isinstance(role_annotations.get(actor_id), dict)
        or role_annotations[actor_id].get("review_status") != "accepted"
        or role_annotations[actor_id].get("accepted_role") not in {"origin-dot", "arc", "bar", "monogram", "wordmark"}
        or role_annotations[actor_id].get("role") != role_annotations[actor_id].get("accepted_role")
        for actor_id in raster_actor_ids
    )
    # Unconfirmed raster observations remain available as source evidence, but
    # the generic runtime must keep the canonical mark static until every
    # raster actor has an explicit accepted binding.
    if raster_review_open:
        actor_stages = {}
    if not actor_stages:
        actor_stages = {actor_id: 0 for actor_id in actor_ids}
        if raster_review_open:
            actor_stages = {}
    actor_roles: dict[str, str] = {}
    for actor in plan.get("actors", []):
        if not isinstance(actor, dict) or not actor.get("id"):
            continue
        actor_id = str(actor["id"])
        annotation = role_annotations.get(actor_id, {}) if isinstance(role_annotations, dict) else {}
        annotated_role = annotation.get("role") if isinstance(annotation, dict) else None
        actor_roles[actor_id] = str(annotated_role or actor.get("role") or "unknown")
    direction_vector_json = html.escape(json.dumps([direction_x // 12, direction_y // 12], separators=(",", ":")), quote=True)
    stage_order_json = html.escape(json.dumps(stage_order, separators=(",", ":")), quote=True)
    actor_stages_json = html.escape(json.dumps(actor_stages, separators=(",", ":")), quote=True)
    stage_strategies_json = html.escape(json.dumps(stage_strategies, separators=(",", ":")), quote=True)
    foreground_resolution = "static-canonical" if raster_review_open else "accepted-source-actors"
    review_status = "needs-review" if raster_review_open else "accepted"
    safe_mark = mark_with_runtime_actor_attributes(mark_svg, actor_ids, actor_roles)
    safe_mark = safe_mark.replace("<svg", '<svg data-motiflux-mark="canonical"', 1)
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><link rel="stylesheet" href="motion.css"></head>
<body><main data-motiflux-root data-growth-mode="staged-source-actors" data-duration-ms="{duration}" data-tempo="{tempo}" data-settle-damping="{damping}" data-theme="{html.escape(str(selection.get("primary", "system-spatial")))}" data-effect="{html.escape(effect)}" data-trajectory="{html.escape(trajectory)}" data-trajectory-summary="{html.escape(trajectory_summary)}" data-background-mode="{html.escape(background_mode)}" data-background-color="{html.escape(background_color)}" data-particles="{'on' if particles else 'off'}" data-particle-density="{html.escape(particle_density)}" data-particle-seed="{particle_seed}" data-direction="{html.escape(str(runtime.get('direction', 'radial')))}" data-direction-vector="{direction_vector_json}" data-foreground-stage-order="{stage_order_json}" data-foreground-actor-stages="{actor_stages_json}" data-foreground-stage-strategies="{stage_strategies_json}" data-foreground-resolution="{foreground_resolution}" data-role-review-status="{review_status}" data-foreground-review-open="{'true' if raster_review_open else 'false'}" data-foreground-fallback="static-canonical" data-beat-start="{html.escape(beat_ids[0])}" data-beat-middle="{html.escape(beat_ids[len(beat_ids) // 2])}" data-beat-end="{html.escape(beat_ids[-1])}"><div data-motiflux-stage aria-label="Animated brand mark"><div class="motiflux-secondary" aria-hidden="true"></div>{safe_mark}</div><div data-motiflux-controls aria-label="Animation controls"><button type="button" data-motiflux-play>Play</button><button type="button" data-motiflux-pause>Pause</button><button type="button" data-motiflux-replay>Replay</button><label>Tempo <input data-motiflux-tempo type="range" min="0.25" max="4" step="0.25" value="{tempo}"></label></div></main><script src="motion.js"></script></body></html>'''
    background_css = "transparent" if background_mode == "transparent" else background_color if background_mode == "solid" else "color-mix(in srgb, var(--motiflux-accent) 4%, transparent)"
    css = f''':root{{--motiflux-progress:0;--motiflux-accent:{accent};--motiflux-entry-x:{direction_x}px;--motiflux-entry-y:{direction_y}px;font-family:system-ui,sans-serif;color-scheme:light dark}}[data-motiflux-root]{{display:grid;gap:1rem;justify-items:center}}[data-motiflux-stage]{{position:relative;width:min(72vw,28rem);aspect-ratio:1;display:grid;place-items:center;overflow:hidden;background:{background_css}}}[data-motiflux-mark]{{position:relative;z-index:2;width:100%;height:100%;opacity:calc(.25 + var(--motiflux-progress) * .75);transform:translate(calc((1 - var(--motiflux-progress)) * var(--motiflux-entry-x)),calc((1 - var(--motiflux-progress)) * var(--motiflux-entry-y))) scale(calc(.92 + var(--motiflux-progress) * .08))}}[data-motiflux-mark] [id]{{transition:opacity .12s linear}}.motiflux-secondary{{position:absolute;z-index:1;inset:0;opacity:calc(var(--motiflux-progress) * .55);transform:scale(calc(.75 + var(--motiflux-progress) * .25));transition:opacity .12s linear,transform .12s linear}}[data-motiflux-root][data-particles="off"] .motiflux-secondary{{display:none}}{EFFECT_CSS.get(effect, EFFECT_CSS["plain"])}{TRAJECTORY_CSS[trajectory]}{ACTOR_GROWTH_CSS}[data-motiflux-controls]{{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center}}button,input{{font:inherit}}@media (prefers-reduced-motion:reduce){{[data-motiflux-mark]{{opacity:1;transform:none;clip-path:none!important}}[data-motiflux-mark] [id]{{opacity:1!important}}.motiflux-secondary{{display:none}}}}'''
    js = f'''(() => {{"use strict";const root=document.querySelector("[data-motiflux-root]"),mark=document.querySelector("[data-motiflux-mark]"),duration=Number(root?.dataset.durationMs||{duration}),stageOrder=JSON.parse(root?.dataset.foregroundStageOrder||'["seed","trace","assemble","lockup","canonical"]'),actorStages=JSON.parse(root?.dataset.foregroundActorStages||"{{}}"),stageStrategies=JSON.parse(root?.dataset.foregroundStageStrategies||"{{}}"),sourceNodes=Array.from(mark?.querySelectorAll?.("[data-motiflux-actor]")||[]),actorNodes=Object.entries(actorStages).map(([id,index])=>[sourceNodes.find(node=>node.getAttribute("data-motiflux-actor")===id)||document.getElementById?.(id),Number(index)]).filter(([node])=>node),reduced=window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;let current=reduced?duration:0,tempo=Number(root?.dataset.tempo||{tempo}),playing=!reduced,frame=0,last=null;function clamp(v){{return Math.min(duration,Math.max(0,v))}}function renderForeground(p){{const index=Math.min(stageOrder.length-1,Math.floor(p*stageOrder.length));const stage=stageOrder[index];root?.setAttribute("data-motiflux-foreground-stage",stage);root?.setAttribute("data-motiflux-path-strategy",stageStrategies[stage]||"source-derived");actorNodes.forEach(([node,actorStage])=>{{if(node)node.style.opacity=p>=(actorStage+0.5)/stageOrder.length?"1":"0"}})}}function render(ms){{current=clamp(ms);const p=duration?current/duration:1;root?.style.setProperty("--motiflux-progress",String(p));root?.setAttribute("data-motiflux-state",p>=1?"canonical":"playing");root?.setAttribute("data-motiflux-beat",p<.25?root?.dataset.beatStart:p<.75?root?.dataset.beatMiddle:root?.dataset.beatEnd);mark?.style.setProperty("--motiflux-progress",String(p));renderForeground(p)}}function tick(t){{if(last===null)last=t;if(playing&&!document.hidden&&!reduced){{current+=(t-last)*tempo;if(current>=duration){{current=duration;playing=false}}render(current)}}last=t;frame=requestAnimationFrame(tick)}}const control={{seek(ms){{playing=false;render(Number(ms)||0)}},finish(){{playing=false;render(duration)}},play(){{if(!reduced){{playing=true;last=null}}}},pause(){{playing=false}},replay(){{current=0;playing=!reduced;last=null;render(current)}},setTempo(value){{tempo=Math.min(4,Math.max(.25,Number(value)||1));root?.setAttribute("data-tempo",String(tempo))}}}};window.__motifluxControl=control;window.__motifluxReady=true;document.querySelector("[data-motiflux-play]")?.addEventListener("click",control.play);document.querySelector("[data-motiflux-pause]")?.addEventListener("click",control.pause);document.querySelector("[data-motiflux-replay]")?.addEventListener("click",control.replay);document.querySelector("[data-motiflux-tempo]")?.addEventListener("input",e=>control.setTempo(e.target.value));document.addEventListener("visibilitychange",()=>{{last=null}});render(current);frame=requestAnimationFrame(tick);window.addEventListener("unload",()=>cancelAnimationFrame(frame),{{once:true}})}})();'''
    # Keep the inline compatibility string above for older generated fixtures,
    # but ship the actor-aware runtime as the active implementation.
    js = ACTOR_GROWTH_JS
    return {"motion.html": document, "motion.css": css, "motion.js": js}
