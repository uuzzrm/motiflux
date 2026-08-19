"""Compile a motion plan into a deterministic dependency-free runtime."""

from __future__ import annotations

import html
import json
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
    title = html.escape(str(plan.get("project", {}).get("name", "Motiflux mark")))
    beat_ids = [str(beat.get("id")) for beat in plan.get("beats", []) if isinstance(beat, dict) and beat.get("id")]
    beat_ids = beat_ids or ["orient", "form", "resolve"]
    safe_mark = mark_svg.replace("<svg", '<svg data-motiflux-mark="canonical"', 1)
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><link rel="stylesheet" href="motion.css"></head>
<body><main data-motiflux-root data-duration-ms="{duration}" data-tempo="{tempo}" data-theme="{html.escape(str(selection.get("primary", "system-spatial")))}" data-effect="{html.escape(effect)}" data-trajectory="{html.escape(trajectory)}" data-trajectory-summary="{html.escape(trajectory_summary)}" data-beat-start="{html.escape(beat_ids[0])}" data-beat-middle="{html.escape(beat_ids[len(beat_ids) // 2])}" data-beat-end="{html.escape(beat_ids[-1])}"><div data-motiflux-stage aria-label="Animated brand mark"><div class="motiflux-secondary" aria-hidden="true"></div>{safe_mark}</div><div data-motiflux-controls aria-label="Animation controls"><button type="button" data-motiflux-play>Play</button><button type="button" data-motiflux-pause>Pause</button><button type="button" data-motiflux-replay>Replay</button><label>Tempo <input data-motiflux-tempo type="range" min="0.25" max="4" step="0.25" value="{tempo}"></label></div></main><script src="motion.js"></script></body></html>'''
    css = f''':root{{--motiflux-progress:0;--motiflux-accent:{accent};font-family:system-ui,sans-serif;color-scheme:light dark}}[data-motiflux-root]{{display:grid;gap:1rem;justify-items:center}}[data-motiflux-stage]{{position:relative;width:min(72vw,28rem);aspect-ratio:1;display:grid;place-items:center;overflow:hidden}}[data-motiflux-mark]{{position:relative;z-index:2;width:100%;height:100%;opacity:calc(.25 + var(--motiflux-progress) * .75);transform:translateY(calc((1 - var(--motiflux-progress)) * 10px)) scale(calc(.92 + var(--motiflux-progress) * .08))}}.motiflux-secondary{{position:absolute;z-index:1;inset:0;opacity:calc(.15 + var(--motiflux-progress) * .55);transform:scale(calc(.75 + var(--motiflux-progress) * .25));transition:opacity .12s linear,transform .12s linear}}{EFFECT_CSS.get(effect, EFFECT_CSS["plain"])}{TRAJECTORY_CSS[trajectory]}[data-motiflux-controls]{{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center}}button,input{{font:inherit}}@media (prefers-reduced-motion:reduce){{[data-motiflux-mark]{{opacity:1;transform:none;clip-path:none!important}}.motiflux-secondary{{display:none}}}}'''
    js = f'''(() => {{"use strict";const root=document.querySelector("[data-motiflux-root]"),mark=document.querySelector("[data-motiflux-mark]"),duration=Number(root?.dataset.durationMs||{duration}),reduced=window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;let current=reduced?duration:0,tempo=Number(root?.dataset.tempo||{tempo}),playing=!reduced,frame=0,last=null;function clamp(v){{return Math.min(duration,Math.max(0,v))}}function render(ms){{current=clamp(ms);const p=duration?current/duration:1;root?.style.setProperty("--motiflux-progress",String(p));root?.setAttribute("data-motiflux-state",p>=1?"canonical":"playing");root?.setAttribute("data-motiflux-beat",p<.25?root?.dataset.beatStart:p<.75?root?.dataset.beatMiddle:root?.dataset.beatEnd);mark?.style.setProperty("--motiflux-progress",String(p))}}function tick(t){{if(last===null)last=t;if(playing&&!document.hidden&&!reduced){{current+=(t-last)*tempo;if(current>=duration){{current=duration;playing=false}}render(current)}}last=t;frame=requestAnimationFrame(tick)}}const control={{seek(ms){{playing=false;render(Number(ms)||0)}},finish(){{playing=false;render(duration)}},play(){{if(!reduced){{playing=true;last=null}}}},pause(){{playing=false}},replay(){{current=0;playing=!reduced;last=null;render(current)}},setTempo(value){{tempo=Math.min(4,Math.max(.25,Number(value)||1));root?.setAttribute("data-tempo",String(tempo))}}}};window.__motifluxControl=control;window.__motifluxReady=true;document.querySelector("[data-motiflux-play]")?.addEventListener("click",control.play);document.querySelector("[data-motiflux-pause]")?.addEventListener("click",control.pause);document.querySelector("[data-motiflux-replay]")?.addEventListener("click",control.replay);document.querySelector("[data-motiflux-tempo]")?.addEventListener("input",e=>control.setTempo(e.target.value));document.addEventListener("visibilitychange",()=>{{last=null}});render(current);frame=requestAnimationFrame(tick);window.addEventListener("unload",()=>cancelAnimationFrame(frame),{{once:true}})}})();'''
    return {"motion.html": document, "motion.css": css, "motion.js": js}
