#!/usr/bin/env python3
"""Generate the Motiflux theme comparison page and its printable PDF atlas."""

from __future__ import annotations

import argparse
import html
import json
import math
import textwrap
from pathlib import Path
from typing import Iterable

from PIL import Image


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"
SOURCE = ASSETS / "prysai-logo-white.jpg"
CROP_JPG = ASSETS / "prysai-mark-crop.jpg"
MARK_PNG = ASSETS / "prysai-mark-transparent.png"
THEMES = ROOT / "themes.json"


def load_data() -> dict:
    return json.loads(THEMES.read_text(encoding="utf-8"))


def derive_preview_assets() -> None:
    """Create display-only derivatives without changing the supplied mark geometry."""

    source = Image.open(SOURCE).convert("RGB")
    luminance = source.convert("L")
    binary = luminance.point(lambda value: 255 if value >= 180 else 0)
    bbox = binary.getbbox()
    if bbox is None:
        raise ValueError("supplied source contains no bright logo pixels")
    margin = 220
    left = max(0, bbox[0] - margin)
    top = max(0, bbox[1] - margin)
    right = min(source.width, bbox[2] + margin)
    bottom = min(source.height, bbox[3] + margin)
    crop = source.crop((left, top, right, bottom))
    crop.save(CROP_JPG, quality=95, optimize=True)

    gray = crop.convert("L")
    alpha = gray.point(lambda value: max(0, min(255, int((value - 8) * 255 / 247))))
    transparent = Image.new("RGBA", crop.size, (255, 255, 255, 0))
    transparent.putalpha(alpha)
    transparent.save(MARK_PNG, optimize=True)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def theme_card(theme: dict) -> str:
    algorithms = "".join(f"<li>{esc(item)}</li>" for item in theme["algorithm"])
    tags = "".join(f"<span class=\"tag\">{esc(item)}</span>" for item in theme["tags"])
    beats = "<span>" + "</span><span>".join(esc(item) for item in theme["beats"]) + "</span>"
    return f'''<article class="theme-card" data-theme="{esc(theme["id"])}" data-search="{esc(" ".join([theme["name"], theme["trigger"], *theme["tags"]]))}" style="--accent:{esc(theme["accent"])};--stage-bg:{esc(theme["background"])};--theme-index:{esc(theme["number"])}">
  <header class="card-head">
    <span class="card-number">{esc(theme["number"])}</span>
    <div>
      <h2>{esc(theme["name"])}</h2>
      <p class="trigger">{esc(theme["trigger"])}</p>
    </div>
    <span class="route-state">ROUTE</span>
  </header>
  <div class="comparison" aria-label="Source mark compared with the {esc(theme["name"])} generated result">
    <div class="source-cell">
      <span class="cell-label">INPUT / SAME SOURCE</span>
      <img src="assets/prysai-mark-crop.jpg" alt="Supplied Prysai logo raster source" loading="lazy">
      <span class="cell-foot">identity locked</span>
    </div>
    <div class="result-cell pattern-{esc(theme["pattern"])}">
      <span class="cell-label">OUTPUT / {esc(theme["name"]).upper()}</span>
      <div class="effect effect-a" aria-hidden="true"></div>
      <div class="effect effect-b" aria-hidden="true"></div>
      <div class="effect effect-c" aria-hidden="true"></div>
      <img class="output-mark" src="assets/prysai-mark-transparent.png" alt="Prysai logo in the {esc(theme["name"])} motion study" loading="lazy">
      <span class="cell-foot">representative landing frame</span>
    </div>
  </div>
  <div class="card-copy">
    <div class="tag-row">{tags}</div>
    <p class="intent">{esc(theme["intent"])}</p>
    <div class="detail-grid">
      <div><span class="detail-label">ALGORITHM STACK</span><ul>{algorithms}</ul></div>
      <div><span class="detail-label">BEATS</span><div class="beats">{beats}</div><span class="detail-label qa-label">QA FOCUS</span><p>{esc(theme["qa"])}</p></div>
    </div>
    <p class="result-note"><span>GENERATED RESULT</span>{esc(theme["result"])}</p>
  </div>
</article>'''


CSS = r'''
:root {
  color-scheme: dark;
  --ink: #f2f1e9;
  --muted: #9b9e9b;
  --line: #2b302f;
  --panel: #0d100f;
  --panel-2: #111513;
  --page: #070908;
  --accent: #9c8cff;
  font-family: "IBM Plex Mono", "Cascadia Code", Consolas, monospace;
  background: var(--page);
  color: var(--ink);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; min-width: 320px; background: var(--page); }
body::before {
  content: ""; position: fixed; inset: 0; pointer-events: none; opacity: .15;
  background-image: linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px);
  background-size: 36px 36px; mask-image: linear-gradient(to bottom, #000, transparent 70%);
}
a { color: inherit; }
button, input { font: inherit; }
button { cursor: pointer; color: var(--ink); background: #111513; border: 1px solid var(--line); padding: .7rem .9rem; }
button:hover, button:focus-visible { border-color: var(--accent); outline: 2px solid color-mix(in srgb, var(--accent) 35%, transparent); outline-offset: 2px; }
.shell { width: min(1440px, calc(100% - 44px)); margin: 0 auto; position: relative; }
.topbar { display: flex; justify-content: space-between; gap: 1rem; align-items: center; padding: 1.2rem 0; border-bottom: 1px solid var(--line); font-size: .72rem; letter-spacing: .05em; text-transform: uppercase; }
.wordmark { display: flex; gap: .65rem; align-items: center; font-weight: 700; }
.wordmark-mark { display: inline-grid; place-items: center; width: 1.5rem; height: 1.5rem; border: 1px solid var(--ink); color: var(--accent); }
.private-badge { color: var(--muted); }
.hero { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(250px, .8fr); gap: 4rem; padding: 6rem 0 4rem; border-bottom: 1px solid var(--line); }
.eyebrow { color: var(--accent); font-size: .73rem; letter-spacing: .14em; text-transform: uppercase; margin: 0 0 1.5rem; }
h1 { max-width: 900px; margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: clamp(3.5rem, 8.8vw, 8.9rem); line-height: .88; letter-spacing: -.08em; font-weight: 700; }
.hero-copy { max-width: 650px; color: #c8cac4; line-height: 1.7; font-family: Arial, Helvetica, sans-serif; font-size: 1.04rem; }
.hero-side { border-left: 1px solid var(--line); padding-left: 1.5rem; display: grid; align-content: end; gap: 1rem; }
.hero-side figure { margin: 0; border: 1px solid var(--line); background: #000; aspect-ratio: 1.2; overflow: hidden; }
.hero-side figure img { width: 100%; height: 100%; object-fit: cover; object-position: center 50%; }
.source-note { color: var(--muted); font-size: .67rem; line-height: 1.6; margin: 0; }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.stat { padding: 1rem 0; border-right: 1px solid var(--line); }
.stat:last-child { border-right: 0; padding-left: 1rem; }
.stat:not(:first-child) { padding-left: 1rem; }
.stat strong { display: block; font-size: 1.4rem; color: var(--ink); }
.stat span { color: var(--muted); font-size: .65rem; text-transform: uppercase; letter-spacing: .08em; }
.route-brief { margin: 2.5rem 0 3.5rem; border: 1px solid var(--line); background: var(--panel); display: grid; grid-template-columns: 1fr 1fr 1fr; }
.route-cell { padding: 1.2rem 1.3rem; min-height: 125px; border-right: 1px solid var(--line); }
.route-cell:last-child { border-right: 0; }
.route-label, .detail-label, .cell-label, .result-note span { display: block; color: var(--muted); font-size: .62rem; letter-spacing: .1em; text-transform: uppercase; margin-bottom: .75rem; }
.route-value { margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 1rem; line-height: 1.45; }
.route-value strong { color: var(--accent); }
.controls { display: flex; gap: .7rem; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 1.1rem; }
.controls-copy { color: var(--muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; }
.controls-actions { display: flex; gap: .5rem; flex-wrap: wrap; }
.filter { min-width: 240px; color: var(--ink); background: var(--panel); border: 1px solid var(--line); padding: .7rem .8rem; }
.filter:focus { outline: 2px solid var(--accent); outline-offset: 2px; }
.theme-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; padding-bottom: 5rem; }
.theme-card { border: 1px solid var(--line); background: linear-gradient(155deg, rgba(255,255,255,.025), transparent 35%), var(--panel); min-width: 0; overflow: hidden; }
.theme-card[hidden] { display: none; }
.card-head { display: grid; grid-template-columns: 2.2rem minmax(0, 1fr) auto; gap: .7rem; padding: .85rem .9rem .8rem; align-items: start; border-bottom: 1px solid var(--line); }
.card-number { color: var(--accent); font-size: .7rem; padding-top: .15rem; }
.card-head h2 { margin: 0; font-size: .92rem; letter-spacing: -.02em; }
.trigger { margin: .35rem 0 0; color: var(--muted); font-size: .62rem; line-height: 1.35; }
.route-state { font-size: .57rem; color: var(--accent); border: 1px solid color-mix(in srgb, var(--accent) 50%, transparent); padding: .22rem .3rem; }
.comparison { display: grid; grid-template-columns: 1fr 1fr; min-height: 205px; border-bottom: 1px solid var(--line); }
.source-cell, .result-cell { position: relative; min-width: 0; overflow: hidden; }
.source-cell { display: grid; place-items: center; background: #000; border-right: 1px solid var(--line); }
.source-cell img { width: 84%; height: 84%; object-fit: contain; }
.result-cell { display: grid; place-items: center; isolation: isolate; background: var(--stage-bg); }
.cell-label { position: absolute; z-index: 5; top: .7rem; left: .7rem; margin: 0; color: #c7c8c2; font-size: .53rem; }
.cell-foot { position: absolute; z-index: 5; bottom: .65rem; left: .7rem; right: .7rem; color: rgba(242,241,233,.55); font-size: .52rem; text-transform: uppercase; letter-spacing: .07em; }
.output-mark { position: relative; z-index: 3; width: 84%; max-height: 84%; object-fit: contain; opacity: 1; filter: drop-shadow(0 0 16px color-mix(in srgb, var(--accent) 38%, transparent)); animation: mark-float 4.8s cubic-bezier(.2,.8,.2,1) infinite alternate; }
.effect { position: absolute; pointer-events: none; z-index: 1; }
.effect-a { inset: 0; opacity: .5; }
.effect-b { inset: 12%; opacity: .6; }
.effect-c { inset: 20%; opacity: .65; }
.pattern-grid .effect-a { background-image: linear-gradient(rgba(138,164,255,.17) 1px, transparent 1px), linear-gradient(90deg, rgba(138,164,255,.17) 1px, transparent 1px); background-size: 20px 20px; animation: grid-drift 8s linear infinite; }
.pattern-quiet .effect-a { background: radial-gradient(circle at 50% 58%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 62%); animation: quiet-breathe 5s ease-in-out infinite alternate; }
.pattern-scan .effect-a { background: repeating-linear-gradient(0deg, transparent 0 6px, color-mix(in srgb, var(--accent) 13%, transparent) 7px 8px); animation: scan-pass 4s linear infinite; }
.pattern-field .effect-a { background: radial-gradient(circle at 20% 30%, var(--accent) 0 1px, transparent 2px), radial-gradient(circle at 76% 65%, var(--accent) 0 1px, transparent 2px), radial-gradient(circle at 48% 20%, #fff 0 1px, transparent 2px), radial-gradient(circle at 88% 38%, var(--accent) 0 1px, transparent 2px); background-size: 48px 42px, 61px 58px, 73px 71px, 54px 63px; filter: blur(.1px); animation: field-float 4s ease-in-out infinite alternate; }
.pattern-field .effect-b { border: 1px solid color-mix(in srgb, var(--accent) 50%, transparent); border-radius: 50%; animation: field-ring 5.4s ease-in-out infinite alternate; }
.pattern-ring .effect-a { width: 72%; height: 72%; inset: 14%; border: 1px solid color-mix(in srgb, var(--accent) 60%, transparent); border-radius: 50%; animation: ring-spin 6s linear infinite; }
.pattern-ring .effect-b { width: 45%; height: 45%; inset: 27%; border: 1px dashed color-mix(in srgb, var(--accent) 45%, transparent); border-radius: 50%; animation: ring-spin 4s linear infinite reverse; }
.pattern-shield .effect-a { clip-path: polygon(50% 3%, 92% 18%, 84% 72%, 50% 98%, 16% 72%, 8% 18%); border: 1px solid color-mix(in srgb, var(--accent) 60%, transparent); background: color-mix(in srgb, var(--accent) 6%, transparent); animation: shield-pulse 4s ease-in-out infinite alternate; }
.pattern-shield .effect-b { inset: 25% 12%; border-top: 1px solid var(--accent); border-bottom: 1px solid var(--accent); animation: gate-scan 3.4s ease-in-out infinite alternate; }
.pattern-burst .effect-a { inset: 36% 9%; border-top: 1px solid var(--accent); border-bottom: 1px solid var(--accent); transform: rotate(-20deg); animation: burst-line 3s ease-out infinite alternate; }
.pattern-burst .effect-b { inset: 9% 36%; border-left: 1px solid var(--accent); border-right: 1px solid var(--accent); transform: rotate(-20deg); animation: burst-line 3.4s ease-out infinite alternate-reverse; }
.pattern-track .effect-a { inset: 0; background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 70%, transparent), transparent); width: 35%; animation: light-sweep 3.8s ease-in-out infinite; }
.pattern-track .effect-b { top: 48%; left: 0; right: 0; height: 1px; background: var(--accent); opacity: .5; box-shadow: 0 -34px 0 color-mix(in srgb, var(--accent) 24%, transparent), 0 34px 0 color-mix(in srgb, var(--accent) 24%, transparent); }
.pattern-speed .effect-a { inset: 28% 0; background: repeating-linear-gradient(165deg, transparent 0 12px, color-mix(in srgb, var(--accent) 60%, transparent) 13px 14px); transform: translateX(-20%); animation: speed-lines 2.4s ease-in-out infinite alternate; }
.pattern-speed .effect-b { inset: 42% -20%; background: var(--accent); height: 1px; transform: rotate(-14deg); animation: speed-lines 1.8s ease-in-out infinite alternate-reverse; }
.pattern-curtain .effect-a { inset: 0; background: linear-gradient(90deg, #000 0 43%, transparent 44% 56%, #000 57%); opacity: .75; animation: curtain-open 4.2s ease-in-out infinite alternate; }
.pattern-curtain .effect-b { inset: 0; background: radial-gradient(ellipse at center, color-mix(in srgb, var(--accent) 26%, transparent), transparent 65%); animation: quiet-breathe 5s ease-in-out infinite alternate; }
.pattern-wave .effect-a { inset: 0; background: repeating-radial-gradient(ellipse at 20% 80%, transparent 0 16px, color-mix(in srgb, var(--accent) 25%, transparent) 17px 18px); transform: rotate(-9deg) scale(1.3); animation: wave-flow 7s ease-in-out infinite alternate; }
.pattern-wave .effect-b { inset: 0; background: linear-gradient(150deg, transparent 20%, color-mix(in srgb, var(--accent) 10%, transparent), transparent 75%); animation: wave-light 4.8s ease-in-out infinite alternate; }
.pattern-orbit .effect-a { inset: 14%; border: 1px dotted color-mix(in srgb, var(--accent) 70%, transparent); border-radius: 50%; animation: ring-spin 6s linear infinite; }
.pattern-orbit .effect-b { inset: 29%; border: 1px solid color-mix(in srgb, var(--accent) 45%, transparent); border-radius: 50%; animation: ring-spin 3.8s linear infinite reverse; }
.pattern-orbit .effect-c { width: 7px; height: 7px; top: 16%; left: 50%; border-radius: 50%; background: var(--accent); box-shadow: 0 0 13px var(--accent); animation: orbit-dot 3.2s linear infinite; transform-origin: 0 190%; }
.pattern-plain .effect-a { background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 22%, transparent), transparent); animation: quiet-breathe 4s ease-in-out infinite alternate; }
.card-copy { padding: .95rem .9rem 1rem; }
.tag-row { display: flex; flex-wrap: wrap; gap: .35rem; margin-bottom: .7rem; }
.tag { border: 1px solid var(--line); color: var(--muted); padding: .22rem .35rem; font-size: .55rem; }
.intent { margin: 0 0 1rem; color: #d6d7d0; font-family: Arial, Helvetica, sans-serif; font-size: .82rem; line-height: 1.48; }
.detail-grid { display: grid; grid-template-columns: 1.15fr .85fr; gap: 1rem; border-top: 1px solid var(--line); padding-top: .8rem; }
.detail-grid ul { margin: 0; padding-left: 1rem; color: #c1c5bd; font-size: .61rem; line-height: 1.5; }
.detail-grid li::marker { color: var(--accent); }
.beats { display: flex; flex-wrap: wrap; gap: .25rem; margin-bottom: .75rem; }
.beats span { color: var(--ink); background: color-mix(in srgb, var(--accent) 12%, transparent); border-left: 2px solid var(--accent); padding: .25rem .3rem; font-size: .57rem; }
.qa-label { margin-top: .4rem; }
.detail-grid p { color: var(--muted); font-size: .6rem; line-height: 1.45; margin: 0; }
.result-note { border-top: 1px solid var(--line); margin: .9rem 0 0; padding-top: .75rem; color: #b9bbb5; font-size: .61rem; line-height: 1.45; }
.result-note span { color: var(--accent); margin-bottom: .35rem; }
.footer { border-top: 1px solid var(--line); padding: 1.5rem 0 3rem; display: flex; gap: 2rem; justify-content: space-between; color: var(--muted); font-size: .63rem; line-height: 1.6; }
.footer p { max-width: 650px; margin: 0; }
@keyframes mark-float { 0% { transform: translateY(4px) scale(.98); } 100% { transform: translateY(0) scale(1); } }
@keyframes grid-drift { to { background-position: 20px 20px; } }
@keyframes quiet-breathe { to { opacity: .9; transform: scale(1.08); } }
@keyframes scan-pass { from { transform: translateY(-25%); } to { transform: translateY(25%); } }
@keyframes field-float { to { transform: translate(12px, -7px) scale(1.12); } }
@keyframes field-ring { to { transform: scale(.65) rotate(20deg); opacity: .2; } }
@keyframes ring-spin { to { transform: rotate(360deg); } }
@keyframes shield-pulse { to { transform: scale(.88); opacity: .25; } }
@keyframes gate-scan { to { transform: translateY(25%); opacity: .2; } }
@keyframes burst-line { to { transform: rotate(20deg) scaleX(.68); opacity: .15; } }
@keyframes light-sweep { 0%, 100% { left: -35%; } 50% { left: 100%; } }
@keyframes speed-lines { to { transform: translateX(22%); opacity: .15; } }
@keyframes curtain-open { from { clip-path: inset(0 0 0 0); } to { clip-path: inset(0 23% 0 23%); } }
@keyframes wave-flow { to { transform: rotate(4deg) scale(1.45) translate(-4%, -5%); } }
@keyframes wave-light { to { transform: translateX(12%); opacity: .2; } }
@keyframes orbit-dot { to { transform: rotate(360deg); } }
body[data-motion="paused"] .theme-card *, body[data-motion="reduced"] .theme-card * { animation-play-state: paused !important; }
body[data-motion="reduced"] .theme-card * { animation: none !important; }
body[data-motion="reduced"] .output-mark { opacity: 1; filter: none; transform: none; }
@media (max-width: 1050px) { .theme-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .hero { gap: 2rem; } }
@media (max-width: 720px) { .shell { width: min(100% - 28px, 640px); } .topbar { font-size: .62rem; } .hero { grid-template-columns: 1fr; padding-top: 4rem; } .hero-side { border-left: 0; padding-left: 0; grid-template-columns: 1fr 1fr; align-items: end; } .route-brief { grid-template-columns: 1fr; } .route-cell { border-right: 0; border-bottom: 1px solid var(--line); } .route-cell:last-child { border-bottom: 0; } .theme-grid { grid-template-columns: 1fr; } .footer { display: block; } .footer p + p { margin-top: 1rem; } }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } .theme-card * { animation: none !important; } .output-mark { opacity: 1; filter: none; transform: none; } }
'''


JS = r'''(() => {
  "use strict";
  const body = document.body;
  const cards = [...document.querySelectorAll(".theme-card")];
  const filter = document.querySelector("[data-filter]");
  const status = document.querySelector("[data-filter-status]");
  const prefersReduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  let motion = prefersReduced ? "reduced" : "running";
  function setMotion(next) {
    motion = next;
    body.dataset.motion = next;
    document.querySelectorAll("[data-motion-label]").forEach((node) => {
      node.textContent = next === "reduced" ? "REDUCED" : next.toUpperCase();
    });
  }
  function replay() {
    cards.forEach((card) => {
      card.querySelectorAll(".output-mark, .effect").forEach((node) => {
        node.style.animation = "none";
        void node.offsetWidth;
        node.style.animation = "";
      });
    });
    setMotion(prefersReduced ? "reduced" : "running");
  }
  document.querySelector("[data-action=play]")?.addEventListener("click", () => setMotion("running"));
  document.querySelector("[data-action=pause]")?.addEventListener("click", () => setMotion("paused"));
  document.querySelector("[data-action=replay]")?.addEventListener("click", replay);
  filter?.addEventListener("input", () => {
    const query = filter.value.trim().toLowerCase();
    let visible = 0;
    cards.forEach((card) => {
      const match = !query || card.dataset.search.toLowerCase().includes(query);
      card.hidden = !match;
      if (match) visible += 1;
    });
    if (status) status.textContent = `${visible} of ${cards.length} routes shown`;
  });
  setMotion(motion);
  window.__motifluxShowcaseReady = true;
  window.__motifluxShowcaseControl = { play: () => setMotion("running"), pause: () => setMotion("paused"), replay, setMotion };
})();
'''


def build_html(data: dict) -> None:
    theme_markup = "\n".join(theme_card(theme) for theme in data["themes"])
    source_label = esc(data["source"]["label"])
    html_doc = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="Motiflux V1 theme atlas: one supplied Prysai mark routed through thirteen logo-motion systems.">
  <title>Motiflux V1 / Theme Atlas</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body data-motion="running">
  <div class="shell">
    <header class="topbar">
      <div class="wordmark"><span class="wordmark-mark">M</span><span>Motiflux / V1</span></div>
      <div class="private-badge">Private development / source-preserving showcase</div>
    </header>
    <main>
      <section class="hero" aria-labelledby="page-title">
        <div>
          <p class="eyebrow">Brand motion routing / comparative study</p>
          <h1 id="page-title">One mark.<br>Thirteen motion systems.</h1>
          <p class="hero-copy">The source stays fixed. The design language changes. This atlas shows how Motiflux routes the same Prysai logo through thirteen market-facing motion themes, then explains the algorithm family behind each representative landing frame.</p>
          <div class="stats" aria-label="Showcase summary">
            <div class="stat"><strong>13</strong><span>routable themes</span></div>
            <div class="stat"><strong>1</strong><span>identity source</span></div>
            <div class="stat"><strong>0</strong><span>geometry edits</span></div>
          </div>
        </div>
        <aside class="hero-side">
          <figure><img src="assets/prysai-logo-white.jpg" alt="{source_label}"></figure>
          <p class="source-note">INPUT ASSET<br>{source_label}<br>Display derivatives remove the black surround for legibility only; the logo geometry is unchanged.</p>
        </aside>
      </section>
      <section class="route-brief" aria-labelledby="route-title">
        <div class="route-cell"><span id="route-title" class="route-label">Example request</span><p class="route-value">“I want to make a logo animation for my artificial-intelligence company.”</p></div>
        <div class="route-cell"><span class="route-label">AI field selected</span><p class="route-value"><strong>AI-field</strong><br>signal flow / convergence / progressive disclosure</p></div>
        <div class="route-cell"><span class="route-label">Why this result</span><p class="route-value">Organized signals converge into the real mark, then settle into a quiet canonical state.</p></div>
      </section>
      <section aria-labelledby="grid-title">
        <div class="controls">
          <div><div id="grid-title" class="controls-copy">Theme comparison grid</div><div data-filter-status class="controls-copy">13 of 13 routes shown</div></div>
          <div class="controls-actions"><input class="filter" data-filter type="search" placeholder="Filter by theme or keyword" aria-label="Filter themes"><button type="button" data-action="play">Play all</button><button type="button" data-action="pause">Pause</button><button type="button" data-action="replay">Replay</button><span class="route-state" data-motion-label>RUNNING</span></div>
        </div>
        <div class="theme-grid">{theme_markup}</div>
      </section>
    </main>
    <footer class="footer"><p>Motiflux V1 is an AI skill for source-aware logo motion: measure, route, reconstruct, compose, instrument, validate, deliver.</p><p>Public design systems are principle analogues only. This showcase does not claim private vendor algorithms, copied assets, or browser-runtime proof.</p></footer>
  </div>
  <script src="app.js"></script>
</body>
</html>
'''
    (ROOT / "index.html").write_text(html_doc, encoding="utf-8")
    (ROOT / "styles.css").write_text(CSS, encoding="utf-8")
    (ROOT / "app.js").write_text(JS, encoding="utf-8")


def wrap_text(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [""]


def pdf_color(hex_color: str):
    from reportlab.lib.colors import HexColor

    return HexColor(hex_color)


def draw_pattern(canvas, x: float, y: float, width: float, height: float, theme: dict) -> None:
    """Draw a compact static analogue of each theme's animated secondary layer."""

    accent = pdf_color(theme["accent"])
    canvas.saveState()
    canvas.setStrokeColor(accent)
    canvas.setFillColor(accent)
    canvas.setLineWidth(0.55)
    pattern = theme["pattern"]
    if pattern == "grid":
        for offset in range(0, int(width), 14):
            canvas.line(x + offset, y, x + offset, y + height)
        for offset in range(0, int(height), 14):
            canvas.line(x, y + offset, x + width, y + offset)
        canvas.setStrokeAlpha(0.17)
    elif pattern in {"ring", "orbit"}:
        canvas.setStrokeAlpha(0.45)
        canvas.circle(x + width * .5, y + height * .5, min(width, height) * .33, stroke=1, fill=0)
        canvas.setDash(1, 3)
        canvas.circle(x + width * .5, y + height * .5, min(width, height) * .22, stroke=1, fill=0)
        canvas.setDash()
    elif pattern == "shield":
        canvas.setStrokeAlpha(0.45)
        points = [(x + width*.5, y + height*.91), (x + width*.83, y + height*.76), (x + width*.76, y + height*.27), (x + width*.5, y + height*.08), (x + width*.24, y + height*.27), (x + width*.17, y + height*.76)]
        path = canvas.beginPath()
        path.moveTo(*points[0])
        for point in points[1:]: path.lineTo(*point)
        path.close()
        canvas.drawPath(path, stroke=1, fill=0)
    elif pattern in {"speed", "track"}:
        canvas.setStrokeAlpha(0.35)
        for offset in range(-20, int(height), 20):
            canvas.line(x + width*.1, y + offset, x + width*.95, y + offset + height*.25)
    elif pattern == "burst":
        canvas.setStrokeAlpha(0.42)
        cx, cy = x + width*.5, y + height*.5
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            canvas.line(cx + math.cos(rad)*width*.13, cy + math.sin(rad)*height*.13, cx + math.cos(rad)*width*.47, cy + math.sin(rad)*height*.47)
    elif pattern in {"wave", "field"}:
        canvas.setStrokeAlpha(0.28)
        for row in range(3):
            path = canvas.beginPath()
            path.moveTo(x, y + height*(.28 + row*.18))
            path.curveTo(x + width*.25, y + height*(.48 + row*.1), x + width*.55, y + height*(.02 + row*.2), x + width, y + height*(.3 + row*.17))
            canvas.drawPath(path, stroke=1, fill=0)
    elif pattern == "curtain":
        canvas.setStrokeAlpha(0.28)
        canvas.setLineWidth(3)
        canvas.line(x + width*.08, y, x + width*.34, y + height)
        canvas.line(x + width*.92, y, x + width*.66, y + height)
    elif pattern == "scan":
        canvas.setStrokeAlpha(0.22)
        for offset in range(7, int(height), 11): canvas.line(x, y + offset, x + width, y + offset)
    else:
        canvas.setStrokeAlpha(0.22)
        canvas.circle(x + width*.5, y + height*.5, min(width, height)*.24, stroke=1, fill=0)
    canvas.restoreState()


def draw_image_contained(canvas, path: Path, x: float, y: float, width: float, height: float, mask: str | None = None) -> None:
    from PIL import Image as PILImage

    with PILImage.open(path) as image:
        image_width, image_height = image.size
    scale = min(width / image_width, height / image_height)
    draw_width = image_width * scale
    draw_height = image_height * scale
    canvas.drawImage(str(path), x + (width - draw_width)/2, y + (height - draw_height)/2, draw_width, draw_height, mask=mask)


def draw_card(canvas, x: float, y: float, width: float, height: float, theme: dict, index: int) -> None:
    from reportlab.lib.colors import HexColor

    accent = pdf_color(theme["accent"])
    line = HexColor("#303532")
    ink = HexColor("#f2f1e9")
    muted = HexColor("#a2a69f")
    canvas.saveState()
    canvas.setFillColor(HexColor("#0d100f")); canvas.setStrokeColor(line); canvas.roundRect(x, y, width, height, 5, stroke=1, fill=1)
    header_h = 34
    canvas.setStrokeColor(line); canvas.line(x, y + height - header_h, x + width, y + height - header_h)
    canvas.setFillColor(accent); canvas.setFont("Courier-Bold", 8); canvas.drawString(x + 10, y + height - 15, theme["number"])
    canvas.setFillColor(ink); canvas.setFont("Helvetica-Bold", 10); canvas.drawString(x + 31, y + height - 15, theme["name"])
    canvas.setFillColor(muted); canvas.setFont("Courier", 5.7); canvas.drawRightString(x + width - 10, y + height - 14, "ROUTE")
    stage_y = y + height - header_h - 116
    stage_h = 106
    half = width / 2
    canvas.setFillColor(HexColor("#000000")); canvas.rect(x, stage_y, half, stage_h, stroke=0, fill=1)
    canvas.setFillColor(pdf_color(theme["background"])); canvas.rect(x + half, stage_y, half, stage_h, stroke=0, fill=1)
    canvas.setStrokeColor(line); canvas.line(x + half, stage_y, x + half, stage_y + stage_h); canvas.line(x, stage_y, x + width, stage_y); canvas.line(x, stage_y + stage_h, x + width, stage_y + stage_h)
    draw_pattern(canvas, x + half, stage_y, half, stage_h, theme)
    draw_image_contained(canvas, CROP_JPG, x + 7, stage_y + 13, half - 14, stage_h - 26)
    draw_image_contained(canvas, MARK_PNG, x + half + 7, stage_y + 13, half - 14, stage_h - 26, mask="auto")
    canvas.setFillColor(muted); canvas.setFont("Courier", 5.2); canvas.drawString(x + 7, stage_y + stage_h - 12, "INPUT / SAME SOURCE"); canvas.drawString(x + half + 7, stage_y + stage_h - 12, "OUTPUT / REPRESENTATIVE FRAME")
    text_y = stage_y - 13
    canvas.setFillColor(muted); canvas.setFont("Courier", 5.6); canvas.drawString(x + 10, text_y, theme["trigger"][:68])
    text_y -= 11
    canvas.setFillColor(ink); canvas.setFont("Helvetica", 6.8)
    for line_text in wrap_text(theme["intent"], 82)[:3]:
        canvas.drawString(x + 10, text_y, line_text[:100]); text_y -= 8
    text_y -= 2
    canvas.setFillColor(accent); canvas.setFont("Courier-Bold", 5.4); canvas.drawString(x + 10, text_y, "ALGORITHM")
    canvas.setFillColor(muted); canvas.setFont("Courier", 5.4)
    algorithm_line = " / ".join(theme["algorithm"])
    for line_text in wrap_text(algorithm_line, 86)[:2]:
        text_y -= 7; canvas.drawString(x + 10, text_y, line_text[:105])
    text_y -= 10
    canvas.setFillColor(accent); canvas.setFont("Courier-Bold", 5.4); canvas.drawString(x + 10, text_y, "QA")
    canvas.setFillColor(muted); canvas.setFont("Courier", 5.4); canvas.drawString(x + 28, text_y, theme["qa"][:92])
    canvas.restoreState()


def build_pdf(data: dict) -> Path:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    pdf_path = OUTPUT / "pdf" / "motiflux-theme-atlas.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(str(pdf_path), pagesize=(page_width, page_height), pageCompression=1)
    pdf.setTitle("Motiflux V1 / Theme Atlas")
    pdf.setAuthor("uuzzrm / Motiflux")
    ink = HexColor("#f2f1e9"); muted = HexColor("#a2a69f"); line = HexColor("#303532"); accent = HexColor("#9c8cff")

    # Cover / route explanation page.
    pdf.setFillColor(HexColor("#070908")); pdf.rect(0, 0, page_width, page_height, stroke=0, fill=1)
    pdf.setFillColor(accent); pdf.setFont("Courier-Bold", 8); pdf.drawString(38, page_height - 42, "MOTIFLUX / V1 / THEME ATLAS")
    pdf.setStrokeColor(line); pdf.line(38, page_height - 53, page_width - 38, page_height - 53)
    pdf.setFillColor(ink); pdf.setFont("Helvetica-Bold", 40); pdf.drawString(38, page_height - 125, "One mark.")
    pdf.drawString(38, page_height - 168, "Thirteen motion systems.")
    pdf.setFillColor(muted); pdf.setFont("Helvetica", 11)
    cover_lines = [
        "A source-preserving comparison of the same supplied Prysai logo routed",
        "through Motiflux V1 design themes. The logo geometry stays locked; the",
        "motion language, stage treatment, algorithm family, and QA focus change.",
    ]
    for offset, line_text in enumerate(cover_lines): pdf.drawString(40, page_height - 214 - offset*16, line_text)
    pdf.setFillColor(HexColor("#000000")); pdf.setStrokeColor(line); pdf.roundRect(40, 82, 235, 190, 6, stroke=1, fill=1)
    draw_image_contained(pdf, SOURCE, 48, 91, 219, 172)
    pdf.setFillColor(muted); pdf.setFont("Courier", 6); pdf.drawString(48, 69, "SUPPLIED RASTER SOURCE / IDENTITY LOCKED")
    pdf.setFillColor(HexColor("#0d100f")); pdf.setStrokeColor(line); pdf.roundRect(315, 82, 486, 190, 6, stroke=1, fill=1)
    pdf.setFillColor(accent); pdf.setFont("Courier-Bold", 7); pdf.drawString(334, 246, "ROUTING EXAMPLE")
    pdf.setFillColor(ink); pdf.setFont("Helvetica-Bold", 14); pdf.drawString(334, 222, "AI-field")
    pdf.setFillColor(muted); pdf.setFont("Helvetica", 9)
    route_lines = [
        "Request: I want to make a logo animation for my artificial-intelligence company.",
        "Route: signal flow / convergence / progressive disclosure.",
        "Result: organized signals converge into the real mark, then settle into a",
        "quiet canonical state. This is a representative landing frame, not a claim",
        "of a private vendor's internal algorithm or a browser-runtime pass.",
    ]
    for offset, line_text in enumerate(route_lines): pdf.drawString(334, 198 - offset*14, line_text)
    pdf.setStrokeColor(line); pdf.line(334, 116, 782, 116)
    pdf.setFillColor(muted); pdf.setFont("Courier", 6.5); pdf.drawString(334, 98, "13 routable themes / 1 identity source / 0 geometry edits")
    pdf.setFillColor(muted); pdf.setFont("Courier", 6.5); pdf.drawRightString(page_width - 38, 28, "PAGE 01")
    pdf.showPage()

    margin_x, margin_y = 26, 30
    gap_x, gap_y = 14, 15
    card_width = (page_width - margin_x*2 - gap_x) / 2
    card_height = 247
    for page_start in range(0, len(data["themes"]), 4):
        pdf.setFillColor(HexColor("#070908")); pdf.rect(0, 0, page_width, page_height, stroke=0, fill=1)
        pdf.setFillColor(accent); pdf.setFont("Courier-Bold", 7); pdf.drawString(margin_x, page_height - 22, "MOTIFLUX / COMPARISON GRID")
        pdf.setFillColor(muted); pdf.setFont("Courier", 6); pdf.drawRightString(page_width - margin_x, page_height - 22, f"THEMES {page_start + 1:02d}-{min(page_start + 4, len(data['themes'])):02d}")
        page_themes = data["themes"][page_start:page_start+4]
        if len(page_themes) == 1:
            # The final route gets a larger, centered card so the atlas closes
            # with a deliberate summary frame instead of an empty grid slot.
            theme = page_themes[0]
            x = margin_x
            y = 58
            draw_card(pdf, x, y, page_width - margin_x * 2, 405, theme, page_start)
        else:
            for slot, theme in enumerate(page_themes):
                col, row = slot % 2, slot // 2
                x = margin_x + col*(card_width + gap_x)
                y = page_height - 47 - (row + 1)*card_height - row*gap_y
                draw_card(pdf, x, y, card_width, card_height, theme, page_start + slot)
        pdf.setFillColor(muted); pdf.setFont("Courier", 6); pdf.drawString(margin_x, 14, "Source-preserving theme studies / representative static frames")
        pdf.drawRightString(page_width - margin_x, 14, f"PAGE {2 + page_start//4:02d}")
        pdf.showPage()
    pdf.save()
    return pdf_path


def write_readme(data: dict) -> None:
    text = f'''# Motiflux V1 showcase

This showcase uses one supplied raster source - `assets/prysai-logo-white.jpg` -
to make a direct visual comparison across {len(data["themes"])} Motiflux theme routes.

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
python showcase\\generate_showcase.py
```

The PDF includes a route example for the phrase `artificial-intelligence` ->
`AI-field`. Public design systems are principle analogues only; this material
does not claim private vendor algorithms or browser-runtime validation.
'''
    (ROOT / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-pdf", action="store_true", help="write HTML assets only")
    args = parser.parse_args()
    data = load_data()
    if len(data.get("themes", [])) != 13:
        raise ValueError("showcase requires exactly 13 theme records")
    derive_preview_assets()
    build_html(data)
    write_readme(data)
    if not args.skip_pdf:
        pdf_path = build_pdf(data)
        print(f"Generated {pdf_path}")
    print(f"Generated {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
