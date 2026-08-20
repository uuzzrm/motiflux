#!/usr/bin/env python3
"""Generate the Motiflux theme comparison page and its printable PDF atlas."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import random
import sys
import textwrap
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageSequence


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"
SOURCE = ASSETS / "prysai-logo-white.jpg"
CROP_JPG = ASSETS / "prysai-mark-crop.jpg"
MARK_PNG = ASSETS / "prysai-mark-transparent.png"
ANIMATIONS = ASSETS / "animations"
THEMES = ROOT / "themes.json"
CATALOG = ROOT.parent / "skills" / "motiflux" / "catalog" / "themes.json"
PROJECT_README = ROOT.parent / "README.md"
GITHUB_GALLERY_START = "<!-- GITHUB_GALLERY:START -->"
GITHUB_GALLERY_END = "<!-- GITHUB_GALLERY:END -->"
SOURCE_ANALYSIS = OUTPUT / "source-analysis.json"
GROWTH_EVIDENCE = OUTPUT / "growth-evidence.json"
ANIMATION_SIZE = (900, 302)
ANIMATION_FRAME_COUNT = 39
ANIMATION_FRAME_MS = 90
GROWTH_SEQUENCE = ("blank", "spark", "arc", "bar", "monogram", "wordmark", "canonical")
CANONICAL_HANDOFF_PROGRESS = 1.0
# Reserve the last encoded beat for the clean canonical handoff.  The final
# letter may approach its source pixels, but only the last frame is allowed to
# become the complete lockup.  This keeps "wordmark" visibly distinct from
# "canonical" in a real, optimized GIF rather than only in the renderer.
PRECANONICAL_LOCKUP_LIMIT = .985
PROGRESS_EVIDENCE_POINTS = (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)
EXPORT_OPTIONS = {
    "background": None,
    "duration_ms": None,
    "speed": 1.0,
    "particles": True,
    "guides": True,
}
GROWTH_STAGE_LABELS = {
    "blank": "blank",
    "spark": "origin dot",
    "arc": "circular arc",
    "bar": "horizontal bar",
    "monogram": "P / monogram",
    "wordmark": "Prysai wordmark",
    "canonical": "complete Logo",
}
GROWTH_DISPLAY_SEQUENCE = tuple(GROWTH_STAGE_LABELS[stage] for stage in GROWTH_SEQUENCE)


def _quantized_gif_duration(duration_ms: int) -> int:
    """Return the GIF-compatible total duration used by the player clock."""

    return max(ANIMATION_FRAME_COUNT * 20, round(int(duration_ms) / 10) * 10)


def _gif_frame_durations(duration_ms: int, frame_count: int = ANIMATION_FRAME_COUNT) -> list[int]:
    """Spread centisecond GIF timing units across frames without drift."""

    total_units = max(frame_count * 2, _quantized_gif_duration(duration_ms) // 10)
    base_units, remainder = divmod(total_units, frame_count)
    durations: list[int] = []
    error = 0
    for _ in range(frame_count):
        error += remainder
        units = base_units
        if error >= frame_count:
            units += 1
            error -= frame_count
        durations.append(units * 10)
    return durations


def _read_encoded_gif(path: Path) -> tuple[list[Image.Image], list[int]]:
    """Read encoded frames and metadata by index, avoiding lazy-frame drift."""

    with Image.open(path) as gif:
        frames: list[Image.Image] = []
        durations: list[int] = []
        for index in range(int(getattr(gif, "n_frames", 1))):
            gif.seek(index)
            durations.append(int(gif.info.get("duration", 0)))
            frames.append(gif.convert("RGB").copy())
    return frames, durations


def _foreground_mask_metrics(mask: Image.Image) -> dict[str, object]:
    """Return deterministic geometry and mass evidence for a foreground mask."""

    alpha = mask.convert("L")
    histogram = alpha.histogram()
    alpha_mass = sum(value * count for value, count in enumerate(histogram))
    unique_count = sum(histogram[1:])
    bbox = alpha.getbbox()
    if bbox is None or unique_count == 0:
        return {
            "foreground_mask_sha256": hashlib.sha256(alpha.tobytes()).hexdigest(),
            "alpha_mass": int(alpha_mass),
            "unique_count": 0,
            "bbox": None,
            "centroid": None,
        }

    weighted_x = 0
    weighted_y = 0
    for index, value in enumerate(alpha.getdata()):
        x = index % alpha.width
        y = index // alpha.width
        weighted_x += x * value
        weighted_y += y * value
    return {
        "foreground_mask_sha256": hashlib.sha256(alpha.tobytes()).hexdigest(),
        "alpha_mass": int(alpha_mass),
        "unique_count": int(unique_count),
        "bbox": {
            "x": bbox[0],
            "y": bbox[1],
            "width": bbox[2] - bbox[0],
            "height": bbox[3] - bbox[1],
        },
        "centroid": {
            "x": round(weighted_x / alpha_mass, 4),
            "y": round(weighted_y / alpha_mass, 4),
        },
    }


def _encoded_identity_mask(frame: Image.Image, canonical: Image.Image) -> Image.Image:
    """Isolate bright encoded identity pixels inside the canonical source mask.

    GIF frames also contain a theme background, guides, and optional particles.
    This bounded measurement deliberately intersects a conservative bright-pixel
    mask with the source-derived canonical mask, so evidence describes the
    actual encoded logo growth rather than secondary atmosphere.
    """

    rgb = frame.convert("RGB")
    bright = Image.new("L", rgb.size, 0)
    # The identity paint is white; the theme palette and guides are deliberately
    # below this threshold so they cannot be mistaken for Logo coverage.
    bright_pixels = [255 if min(pixel) > 235 else 0 for pixel in rgb.getdata()]
    bright.putdata(bright_pixels)
    return ImageChops.multiply(bright, canonical.convert("L"))


def _trajectory_fingerprint(theme: dict, progress: float, render_progress: float, metrics: dict[str, object]) -> str:
    """Fingerprint the selected trajectory and its observed foreground state."""

    payload = {
        "trajectory_id": theme["trajectory_id"],
        "foreground_mode": theme["foreground_mode"],
        "foreground_variant": theme.get("foreground_variant", "default"),
        "foreground_easing": theme["foreground_easing"],
        "foreground_order": list(theme["foreground_order"]),
        "progress": progress,
        "render_progress": render_progress,
        "foreground_mask_sha256": metrics["foreground_mask_sha256"],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _set_export_options(options: dict[str, object] | None = None) -> None:
    """Set optional baked-export controls while keeping the default showcase stable."""

    EXPORT_OPTIONS.update({"background": None, "duration_ms": None, "speed": 1.0, "particles": True, "guides": True})
    if options:
        EXPORT_OPTIONS.update(options)


def _export_duration_ms(theme: dict) -> int:
    requested = EXPORT_OPTIONS.get("duration_ms")
    if requested is None:
        return int(theme["duration_ms"])
    return max(ANIMATION_FRAME_COUNT * 20, int(requested))


def _export_progress(progress: float) -> float:
    """Shape the baked progression without changing the canonical endpoint."""

    speed = max(.25, min(4.0, float(EXPORT_OPTIONS.get("speed") or 1.0)))
    if abs(speed - 1.0) < 1e-9:
        return progress
    # Higher speed reaches the readable construction sooner; the final frame
    # always remains an exact canonical handoff.
    exponent = 1.0 / speed
    return _clamp(progress ** exponent)

# The supplied raster has a stable, readable component layout: the icon sits on
# the left, followed by the six wordmark components. These boxes are used only
# to stage the existing pixels; they do not redraw or alter the supplied mark.
LOGO_COMPONENT_BOXES = {
    "origin_dot": (150, 780, 430, 1090),
    "monogram_raw": (150, 160, 1130, 1150),
    "wordmark_01": (1120, 240, 1760, 1000),
    "wordmark_02": (1730, 380, 2110, 1000),
    "wordmark_03": (2080, 380, 2638, 1160),
    "wordmark_04": (2638, 380, 3070, 1000),
    "wordmark_05": (3033, 380, 3560, 1000),
    "wordmark_06": (3560, 170, 3780, 1000),
}


def _scale_box(
    bounds: dict[str, int],
    source_width: int,
    source_height: int,
    sampled_width: int,
    sampled_height: int,
) -> tuple[int, int, int, int]:
    """Convert sampled raster bounds back into the source image coordinate space."""

    scale_x = source_width / max(1, sampled_width)
    scale_y = source_height / max(1, sampled_height)
    left = max(0, math.floor(bounds["x"] * scale_x))
    top = max(0, math.floor(bounds["y"] * scale_y))
    right = min(source_width, math.ceil((bounds["x"] + bounds["width"]) * scale_x))
    bottom = min(source_height, math.ceil((bounds["y"] + bounds["height"]) * scale_y))
    return left, top, max(left + 1, right), max(top + 1, bottom)


def _union_boxes(boxes: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    if not boxes:
        raise ValueError("cannot union an empty source actor group")
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _stage_mapping(boxes: dict[str, tuple[int, int, int, int]]) -> dict[str, list[str]]:
    """Map observed actor candidates to stable showcase construction stages."""

    wordmark = [name for name in sorted(boxes) if name.startswith("wordmark_")]
    symbol = [name for name in ("monogram_raw", "monogram_p") if name in boxes]
    return {
        "origin_dot": ["origin_dot"] if "origin_dot" in boxes else [],
        "arc": ["monogram_raw"] if "monogram_raw" in boxes else symbol[:1],
        "bar": ["monogram_raw"] if "monogram_raw" in boxes else symbol[:1],
        "monogram": symbol,
        "wordmark": wordmark,
        "canonical": ["final"],
    }


def detect_source_structure(path: Path) -> dict[str, object]:
    """Observe source pixels and return boxes used by the growth renderer.

    This is intentionally a bounded observation adapter: it groups pixels into
    symbol and wordmark candidates, then keeps the result reviewable. It does
    not claim semantic vector reconstruction. The checked-in source boxes remain a safe
    fallback for environments where the optional Pillow adapter is unavailable.
    """

    fallback = {
        "status": "fallback",
        "method": "checked-in source boxes",
        "review_status": "needs-review",
        "recognition": {
            "mode": "checked-in-bounded-observation",
            "review_status": "needs-review",
            "input_boundary": "source boxes are a display fallback; semantic recognition and vector reconstruction are not claimed",
            "component_count": len(LOGO_COMPONENT_BOXES),
            "decision_trace": ["use checked-in boxes", "map supported actors", "retain static-canonical fallback"],
        },
        "boxes": dict(LOGO_COMPONENT_BOXES),
        "actor_groups": {"symbol": ["origin_dot", "monogram_raw"], "wordmark": [f"wordmark_{index:02d}" for index in range(1, 7)]},
        "stage_mapping": _stage_mapping(dict(LOGO_COMPONENT_BOXES)),
        "unresolved": ["pixel structure observation adapter was unavailable"],
        "observation_review": {
            "status": "needs-review",
            "reviewed_components": [],
            "method": "bounded geometric observation; no semantic recognition",
            "notes": "Confirm candidate actor roles before treating them as semantic Logo parts.",
        },
    }
    tools_root = ROOT.parent / "skills" / "motiflux" / "tools"
    try:
        if str(tools_root) not in sys.path:
            sys.path.insert(0, str(tools_root))
        from engine.raster import analyze_raster

        analysis = analyze_raster(path, max_dimension=1024)
        raster = analysis.get("observations", {}).get("raster", {})
        components = {str(item.get("id")): item for item in raster.get("components", []) if isinstance(item, dict) and item.get("id")}
        groups = {str(item.get("id")): list(item.get("component_ids", [])) for item in raster.get("layout_groups", []) if isinstance(item, dict) and item.get("id")}
        symbol = [components[item] for item in groups.get("symbol", []) if item in components]
        wordmark = [components[item] for item in groups.get("wordmark", []) if item in components]
        if not symbol or len(wordmark) < 2:
            return fallback
        # Keep small accents (such as the dot above an i) attached to the
        # nearest glyph actor without letting them become a seventh letter.
        max_wordmark_height = max(int(item.get("bounds", {}).get("height", 0)) for item in wordmark)
        wordmark_bodies = [
            item for item in wordmark
            if int(item.get("bounds", {}).get("height", 0)) >= max(2, round(max_wordmark_height * .62))
        ]
        if len(wordmark_bodies) < 2:
            return fallback
        sampling = raster.get("sampling", {})
        source_record = analysis.get("source", {})
        original_width = int(sampling.get("original_width") or source_record.get("width") or 0)
        original_height = int(sampling.get("original_height") or source_record.get("height") or 0)
        sampled_width = int(sampling.get("width") or 0)
        sampled_height = int(sampling.get("height") or 0)
        if min(original_width, original_height, sampled_width, sampled_height) <= 0:
            return fallback
        source_boxes = {
            str(item.get("id")): _scale_box(
                item["bounds"],
                original_width,
                original_height,
                sampled_width,
                sampled_height,
            )
            for item in [*symbol, *wordmark]
            if isinstance(item.get("bounds"), dict)
        }
        dot = min(symbol, key=lambda item: int(item.get("area", 0)))
        monogram_candidates = [item for item in symbol if item is not dot]
        if not monogram_candidates:
            return fallback
        dot_box = source_boxes[str(dot["id"])]
        ordered_wordmark = sorted(wordmark_bodies, key=lambda item: (source_boxes[str(item["id"])][0], source_boxes[str(item["id"])][1]))
        wordmark_boxes = [source_boxes[str(item["id"])] for item in ordered_wordmark]
        for accent in [item for item in wordmark if item not in wordmark_bodies]:
            accent_box = source_boxes[str(accent["id"])]
            nearest = min(
                range(len(ordered_wordmark)),
                key=lambda index: abs((wordmark_boxes[index][0] + wordmark_boxes[index][2]) / 2 - (accent_box[0] + accent_box[2]) / 2),
            )
            wordmark_boxes[nearest] = _union_boxes([wordmark_boxes[nearest], accent_box])
        ring = max(monogram_candidates, key=lambda item: int(item.get("area", 0)))
        p_candidates = [item for item in monogram_candidates if item is not ring]
        boxes: dict[str, tuple[int, int, int, int]] = {
            "origin_dot": dot_box,
            # The largest symbol candidate is the ring; the other symbol
            # candidate is the P-like monogram and is revealed separately.
            "monogram_raw": source_boxes[str(ring["id"])],
        }
        if p_candidates:
            p_component = max(p_candidates, key=lambda item: int(item.get("area", 0)))
            boxes["monogram_p"] = source_boxes[str(p_component["id"])]
        for index, box in enumerate(wordmark_boxes, start=1):
            boxes[f"wordmark_{index:02d}"] = box
        symbol_ids = {str(item["id"]) for item in symbol}
        group_boxes = {
            "symbol": [boxes[name] for name in ("origin_dot", "monogram_raw", "monogram_p") if name in boxes],
            "wordmark": wordmark_boxes,
        }
        observed_components = [
            {
                "id": str(item["id"]),
                "bounds": source_boxes[str(item["id"])],
                "area": item.get("area"),
                "layout_group": "symbol" if str(item["id"]) in symbol_ids else "wordmark",
                "role": "origin-dot-candidate" if item is dot else ("wordmark-candidate" if item in wordmark else ("ring-candidate" if item is ring else "letter-p-candidate")),
                "role_review": {
                    "proposed_role": "origin-dot" if item is dot else ("wordmark" if item in wordmark else ("arc" if item is ring else "monogram")),
                    "accepted_role": None,
                    "confidence": "medium" if item is dot or item is ring else "low",
                    "review_status": "needs-review",
                    "evidence": "connected-component geometry and layout grouping only",
                },
            }
            for item in [*symbol, *sorted(wordmark, key=lambda value: (source_boxes[str(value["id"])][0], source_boxes[str(value["id"])][1]))]
        ]
        return {
            "status": "candidate",
            "method": "Pillow foreground mask + connected components + layout grouping",
            "review_status": "needs-review",
            "recognition": raster.get("recognition", {}),
            "sampling": raster.get("sampling", {}),
            "boxes": boxes,
            "actor_groups": {
                "symbol": [name for name in ("origin_dot", "monogram_raw", "monogram_p") if name in boxes],
                "wordmark": [f"wordmark_{index:02d}" for index in range(1, len(wordmark_boxes) + 1)],
            },
            "group_bounds": {name: _union_boxes(items) for name, items in group_boxes.items() if items},
            "stage_mapping": _stage_mapping(boxes),
            "observed_components": observed_components,
            "observation_review": {
                "status": "needs-review",
                "reviewed_components": [],
                "method": "Pillow foreground mask + connected components + layout grouping",
                "notes": "Proposed roles are bounded geometric hypotheses; accepted_role remains null until reviewed.",
            },
            "unresolved": ["semantic roles and vector equivalence still require review"],
        }
    except (ImportError, OSError, KeyError, TypeError, ValueError):
        return fallback

# These are animation grammars, not vendor recipes. The same component masks
# are used by every route; trajectory_id decides how those supplied pixels are
# staged. A theme must change the foreground construction, not only the field
# around it.
GROWTH_PROFILES = {
    "system-spatial": {"construction_style": "orthogonal coordinate draw-on", "primary_motion": "grid lock and radial construction", "wordmark_reveal": "left-to-right component stagger", "monogram_mode": "radial", "wordmark_mode": "scan", "arc_start": 205, "arc_direction": 1, "stagger": 0.06},
    "premium-quiet": {"construction_style": "quiet contour tracing", "primary_motion": "slow optical trace with a held pause", "wordmark_reveal": "soft letter-by-letter fade", "monogram_mode": "radial", "wordmark_mode": "fade", "arc_start": 228, "arc_direction": 1, "stagger": 0.09},
    "developer-open": {"construction_style": "inspectable command sequence", "primary_motion": "deterministic scanline draw-on", "wordmark_reveal": "explicit left-to-right scan", "monogram_mode": "scan", "wordmark_mode": "scan", "arc_start": 180, "arc_direction": 1, "stagger": 0.04},
    "ai-field": {"construction_style": "signal convergence into geometry", "primary_motion": "seeded signals converge on each component", "wordmark_reveal": "confidence-ordered component reveal", "monogram_mode": "radial", "wordmark_mode": "diagonal", "arc_start": 250, "arc_direction": 1, "stagger": 0.05},
    "fintech-trust": {"construction_style": "progressive confirmation", "primary_motion": "bounded progress ring then stable lock", "wordmark_reveal": "monotonic component confirmation", "monogram_mode": "radial", "wordmark_mode": "scan", "arc_start": 270, "arc_direction": 1, "stagger": 0.05},
    "security-shield": {"construction_style": "boundary-first construction", "primary_motion": "perimeter trace followed by verified interior", "wordmark_reveal": "protected sequential reveal", "monogram_mode": "scan", "wordmark_mode": "scan", "arc_start": 135, "arc_direction": 1, "stagger": 0.07},
    "commerce-energy": {"construction_style": "anticipation and release", "primary_motion": "compressed spark with a fast stroke release", "wordmark_reveal": "quick readable letter cascade", "monogram_mode": "diagonal", "wordmark_mode": "scan", "arc_start": 200, "arc_direction": 1, "stagger": 0.035},
    "automotive-precision": {"construction_style": "kinematic path tracing", "primary_motion": "single directional scan with velocity continuity", "wordmark_reveal": "track-aligned wordmark draw-on", "monogram_mode": "scan", "wordmark_mode": "scan", "arc_start": 315, "arc_direction": 1, "stagger": 0.045},
    "sports-impact": {"construction_style": "compression, strike, recovery", "primary_motion": "high-velocity arc and controlled settle", "wordmark_reveal": "impact-timed component release", "monogram_mode": "diagonal", "wordmark_mode": "scan", "arc_start": 225, "arc_direction": 1, "stagger": 0.025},
    "cinematic-title": {"construction_style": "dark-field title reveal", "primary_motion": "aperture opens from a single illuminated stroke", "wordmark_reveal": "paced title-card letter reveal", "monogram_mode": "radial", "wordmark_mode": "fade", "arc_start": 225, "arc_direction": 1, "stagger": 0.1},
    "nature-flow": {"construction_style": "continuous organic contour", "primary_motion": "low-frequency flow follows the mark curvature", "wordmark_reveal": "breathing connected reveal", "monogram_mode": "diagonal", "wordmark_mode": "fade", "arc_start": 160, "arc_direction": 1, "stagger": 0.08},
    "gaming-world": {"construction_style": "deterministic particle assembly", "primary_motion": "orbiting sparks assemble the stable silhouette", "wordmark_reveal": "reward-like sequential component reveal", "monogram_mode": "radial", "wordmark_mode": "diagonal", "arc_start": 300, "arc_direction": 1, "stagger": 0.04},
    "accessibility-first": {"construction_style": "low-motion semantic construction", "primary_motion": "short opacity changes with a static-safe landing", "wordmark_reveal": "low-motion component fade", "monogram_mode": "radial", "wordmark_mode": "fade", "arc_start": 205, "arc_direction": 1, "stagger": 0.12},
}

# Foreground construction is intentionally separate from the background
# effect catalog. Each route changes how the supplied alpha components enter,
# while all routes still land on the same canonical pixels.
FOREGROUND_PROFILES = {
    # ``reveal_variant`` is an executable route parameter, not a decorative
    # label. It lets the prompt/router name the path while the renderer keeps
    # the implementation behind the small foreground reveal interface.
    "knowledge-graph-lock": {"mode": "grid", "timing": "standard", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "steps", "reveal_variant": "scan-forward"},
    "contour-etch": {"mode": "contour", "timing": "slow", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "soft", "reveal_variant": "polar-clockwise"},
    "token-commit": {"mode": "token", "timing": "staggered", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "linear", "reveal_variant": "scan-reverse"},
    "signal-convergence": {"mode": "convergence", "timing": "field", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "ease_out", "reveal_variant": "polar-counter"},
    "progress-confirm": {"mode": "radial", "timing": "center", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "smooth", "reveal_variant": "polar-offset"},
    "boundary-unlock": {"mode": "boundary", "timing": "late", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "soft", "reveal_variant": "boundary-reverse"},
    "burst-assembly": {"mode": "burst", "timing": "rapid", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "ease_out", "reveal_variant": "diagonal-forward"},
    "kinematic-lock": {"mode": "track", "timing": "standard", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "ease_out", "reveal_variant": "scan-slope"},
    "impact-release": {"mode": "impact", "timing": "impact", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "ease_out", "reveal_variant": "diagonal-reverse"},
    "aperture-title": {"mode": "aperture", "timing": "title", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "soft", "reveal_variant": "diagonal-center"},
    "organic-current": {"mode": "organic", "timing": "slow", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "soft", "reveal_variant": "wave-phase-a"},
    "orbit-quest": {"mode": "orbit", "timing": "orbit", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "ease_out", "reveal_variant": "polar-orbit"},
    "semantic-fade": {"mode": "fade", "timing": "accessible", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "soft", "reveal_variant": "opacity-stable"},
}

# These descriptions are consumed by the showcase and the prompt lab. Keep
# them tied to executable modes so an AI agent can explain the difference it
# will render instead of selecting a purely decorative label.
TRAJECTORY_METADATA = {
    "knowledge-graph-lock": {"path_strategy": "measured actor-to-actor grid locks", "speed_profile": "hierarchy stagger with a slow final lock"},
    "contour-etch": {"path_strategy": "source contour trace followed by fill", "speed_profile": "slow trace with a deliberate reading pause"},
    "token-commit": {"path_strategy": "deterministic left-to-right actor commits", "speed_profile": "even token cadence with short pauses"},
    "signal-convergence": {"path_strategy": "seeded signals converge into measured actors", "speed_profile": "accelerate into geometry and decelerate at lockup"},
    "progress-confirm": {"path_strategy": "center-outward progress gates the supplied actors", "speed_profile": "steady processing with a bounded confirmation settle"},
    "boundary-unlock": {"path_strategy": "perimeter-first trace then interior unlock", "speed_profile": "guarded boundary, quick verify, deliberate release"},
    "burst-assembly": {"path_strategy": "compressed actors release from a shared origin", "speed_profile": "short anticipation, fast release, rapid settle"},
    "kinematic-lock": {"path_strategy": "single-axis actor travel with velocity continuity", "speed_profile": "heavy forms slow; scan accent remains fast"},
    "impact-release": {"path_strategy": "horizontal compression followed by directional release", "speed_profile": "sharp impact with controlled recovery"},
    "aperture-title": {"path_strategy": "center aperture gates contour and lockup layers", "speed_profile": "slow exposure followed by a long title hold"},
    "organic-current": {"path_strategy": "curvature-following drift into source positions", "speed_profile": "low-frequency flow with damped settle"},
    "orbit-quest": {"path_strategy": "deterministic orbital arrivals into actor targets", "speed_profile": "spawn, accumulate, snap to reward, clear"},
    "semantic-fade": {"path_strategy": "ordered opacity with stable source geometry", "speed_profile": "opacity-first and no overshoot"},
}

PHASE_TIMINGS = {
    # Each next actor starts after the previous actor's source-pixel reveal has
    # finished. The route can still differ through its path and easing, but the
    # public storyboard remains a readable construction sequence.
    "standard": {"dot": (.03, .14), "arc": (.17, .32), "bar": (.35, .49), "stem": (.52, .66), "wordmark": (.70, .96)},
    "slow": {"dot": (.04, .17), "arc": (.20, .38), "bar": (.41, .56), "stem": (.59, .72), "wordmark": (.74, .98)},
    "staggered": {"dot": (.02, .14), "arc": (.17, .32), "bar": (.35, .46), "stem": (.49, .63), "wordmark": (.67, .96)},
    "field": {"dot": (.02, .15), "arc": (.18, .33), "bar": (.36, .48), "stem": (.51, .65), "wordmark": (.69, .97)},
    "center": {"dot": (.04, .17), "arc": (.20, .35), "bar": (.38, .47), "stem": (.50, .64), "wordmark": (.68, .97)},
    "late": {"dot": (.05, .18), "arc": (.22, .39), "bar": (.42, .58), "stem": (.62, .71), "wordmark": (.75, .99)},
    "rapid": {"dot": (.01, .10), "arc": (.13, .24), "bar": (.27, .35), "stem": (.38, .42), "wordmark": (.47, .94)},
    # Sports keeps a short recovery beat between the strike and wordmark so
    # its 0.75 evidence frame cannot collapse into commerce's rapid cascade.
    "impact": {"dot": (.01, .10), "arc": (.13, .27), "bar": (.30, .42), "stem": (.46, .58), "wordmark": (.63, .98)},
    "orbit": {"dot": (.02, .13), "arc": (.16, .30), "bar": (.33, .46), "stem": (.50, .64), "wordmark": (.69, .98)},
    # Start the low-motion wordmark earlier so its semantic fade remains a
    # visibly distinct route at the encoded GIF midpoint.
    "accessible": {"dot": (.03, .14), "arc": (.17, .29), "bar": (.32, .43), "stem": (.46, .48), "wordmark": (.52, .93)},
    "organic": {"dot": (.04, .18), "arc": (.21, .38), "bar": (.41, .56), "stem": (.59, .70), "wordmark": (.74, .98)},
    # The title route keeps the aperture phase visible before exposing the
    # wordmark as a deliberate title-card hold.
    "title": {"dot": (.05, .18), "arc": (.21, .38), "bar": (.41, .58), "stem": (.62, .69), "wordmark": (.73, .99)},
}

IMPLEMENTED_TRAJECTORIES = {
    "knowledge-graph-lock",
    "contour-etch",
    "token-commit",
    "signal-convergence",
    "progress-confirm",
    "boundary-unlock",
    "burst-assembly",
    "kinematic-lock",
    "impact-release",
    "aperture-title",
    "organic-current",
    "orbit-quest",
    "semantic-fade",
}

EFFECT_VISUALS = {
    "grid": {"accent": "#8aa4ff", "background": "#101723"},
    "quiet": {"accent": "#d7c7a7", "background": "#171513"},
    "scan": {"accent": "#79e2a4", "background": "#0d1714"},
    "field": {"accent": "#9c8cff", "background": "#14122b"},
    "ring": {"accent": "#6dd9c0", "background": "#0c1c1b"},
    "shield": {"accent": "#ffb86b", "background": "#1b1510"},
    "burst": {"accent": "#ff6f91", "background": "#24131b"},
    "track": {"accent": "#e2edf1", "background": "#11191e"},
    "speed": {"accent": "#ff5c4d", "background": "#24120f"},
    "curtain": {"accent": "#d7d2ff", "background": "#100f1c"},
    "wave": {"accent": "#b9d8a5", "background": "#132017"},
    "orbit": {"accent": "#62d7ff", "background": "#101b2b"},
    "plain": {"accent": "#f4f1df", "background": "#1b1b19"},
}

BEATS = {
    "grid": ["locate", "draw", "lock"],
    "quiet": ["spark", "trace", "rest"],
    "scan": ["parse", "stroke", "commit"],
    "field": ["seed", "converge", "land"],
    "ring": ["orbit", "close", "confirm"],
    "shield": ["boundary", "verify", "unlock"],
    "burst": ["compress", "release", "idle"],
    "track": ["scan", "draw", "settle"],
    "speed": ["charge", "strike", "recover"],
    "curtain": ["dark", "reveal", "hold"],
    "wave": ["breathe", "grow", "root"],
    "orbit": ["spawn", "assemble", "clear"],
    "plain": ["appear", "form", "rest"],
}


def load_data() -> dict:
    """Build the showcase snapshot from the canonical theme catalog."""

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    themes: list[dict] = []
    for index, profile in enumerate(catalog.get("themes", []), start=1):
        runtime = profile.get("runtime", {})
        effect = str(runtime.get("secondary_effect", "plain"))
        visual = EFFECT_VISUALS.get(effect, EFFECT_VISUALS["plain"])
        tempo = float(runtime.get("tempo", 1.0))
        duration = max(1100, min(2400, round(1800 / tempo)))
        routing = profile.get("routing", {})
        routing_aliases = routing.get("aliases", []) if isinstance(routing, dict) else []
        aliases = list(dict.fromkeys(str(item) for item in (*profile.get("aliases", []), *routing_aliases)))
        controls = [str(item).replace("_", " ") for item in profile.get("controls", [])]
        try:
            growth = GROWTH_PROFILES[profile["id"]]
        except KeyError as error:
            raise ValueError(f"missing growth profile for theme: {profile['id']}") from error
        if profile["trajectory_id"] not in IMPLEMENTED_TRAJECTORIES:
            raise ValueError(f"unimplemented trajectory: {profile['trajectory_id']}")
        try:
            foreground = FOREGROUND_PROFILES[profile["trajectory_id"]]
        except KeyError as error:
            raise ValueError(f"missing foreground profile: {profile['trajectory_id']}") from error
        catalog_foreground = profile.get("foreground_plan", {})
        if not isinstance(catalog_foreground, dict):
            raise ValueError(f"foreground_plan must be an object: {profile['id']}")
        for key in ("mode", "variant", "timing", "easing", "path_strategy", "speed_profile", "fallback"):
            if not str(catalog_foreground.get(key, "")).strip():
                raise ValueError(f"foreground_plan missing {key}: {profile['id']}")
        if catalog_foreground.get("fallback") != "static-canonical":
            raise ValueError(f"foreground_plan fallback must be static-canonical: {profile['id']}")
        foreground = {
            **foreground,
            "mode": str(catalog_foreground["mode"]),
            "timing": str(catalog_foreground["timing"]),
            "easing": str(catalog_foreground["easing"]),
            "reveal_variant": str(catalog_foreground["variant"]),
        }
        trajectory_meta = TRAJECTORY_METADATA[profile["trajectory_id"]]
        themes.append({
            "id": profile["id"],
            "name": profile["name"],
            "number": f"{index:02d}",
            "trigger": ", ".join(aliases[:6]),
            "keywords": aliases,
            "tags": [profile["id"], effect, "logo-growth", *controls[:1]],
            "public_analogue": profile.get("public_analogue", ""),
            "intent": profile.get("design_intent", ""),
            "algorithm": list(profile.get("algorithm_stack", [])),
            "trajectory_id": str(profile["trajectory_id"]),
            "trajectory_summary": str(profile["trajectory_summary"]),
            "result": f"The supplied mark follows this foreground route: {profile['trajectory_summary']}",
            "beats": BEATS.get(effect, BEATS["plain"]),
            "qa": "; ".join(profile.get("qa_focus", [])),
            "accent": visual["accent"],
            "background": visual["background"],
            "pattern": effect,
            "tempo": tempo,
            "duration_ms": duration,
            "playback_duration_ms": _quantized_gif_duration(duration),
            "growth_sequence": list(GROWTH_SEQUENCE),
            "construction_style": growth["construction_style"],
            "primary_motion": growth["primary_motion"],
            "wordmark_reveal": growth["wordmark_reveal"],
            "stagger": float(growth["stagger"]),
            "foreground_mode": foreground["mode"],
            "foreground_timing": foreground["timing"],
            "foreground_order": list(foreground["letter_order"]),
            "foreground_easing": foreground["easing"],
            "foreground_variant": foreground.get("reveal_variant", "default"),
            "path_strategy": str(catalog_foreground["path_strategy"]),
            "speed_profile": str(catalog_foreground["speed_profile"]),
            "arc_start": float(growth["arc_start"]),
            "arc_direction": int(growth["arc_direction"]),
            "animation_file": f"assets/animations/prysai-{profile['id']}.gif",
            "animation_poster": f"assets/animations/prysai-{profile['id']}-poster.png",
            "stage_files": {
                stage: f"assets/animations/prysai-{profile['id']}-{stage}.png"
                for stage in GROWTH_SEQUENCE
            },
        })
    return {
        "schema_version": "1.0",
        "source_catalog": "skills/motiflux/catalog/themes.json",
        "source": {
            "asset": "assets/prysai-logo-white.jpg",
            "label": "Prysai logo / supplied raster source",
            "identity_rule": "Use the same source mark in every theme. Change the foreground trajectory and motion language only.",
            "structure_rule": "Observe raster pixels into candidate actors, map only available roles, and keep semantic/vector review unresolved.",
            "growth_sequence": list(GROWTH_SEQUENCE),
            "growth_sequence_display": list(GROWTH_DISPLAY_SEQUENCE),
        },
        "request_example": {
            "user_says": "I want to make a logo animation for my artificial-intelligence company.",
            "agent_route": "AI-field",
            "routing_explanation": "The phrase artificial intelligence selects AI-field; deterministic signals converge into the supplied Logo pixels, then the Prysai wordmark assembles and holds canonical.",
        },
        "themes": themes,
    }


def _attach_role_reviews(analysis: dict[str, object], source_structure: dict[str, object]) -> None:
    """Attach normalized candidate-role review fields to raster evidence."""

    observations = analysis.get("observations")
    if not isinstance(observations, dict):
        return
    raster = observations.get("raster")
    if not isinstance(raster, dict):
        return
    observed = source_structure.get("observed_components", [])
    by_id = {item.get("id"): item for item in observed if isinstance(item, dict) and item.get("id")}
    for component in raster.get("components", []):
        if not isinstance(component, dict):
            continue
        candidate = by_id.get(component.get("id"), {})
        role_review = candidate.get("role_review") if isinstance(candidate, dict) else None
        if not isinstance(role_review, dict):
            role_review = {
                "proposed_role": component.get("selected_role", "unknown"),
                "accepted_role": None,
                "confidence": "low",
                "review_status": "needs-review",
                "evidence": "raster adapter selection is a hypothesis, not semantic recognition",
            }
        component["role_review"] = role_review
    analysis["observation_review"] = source_structure.get("observation_review", {
        "status": "needs-review",
        "reviewed_components": [],
        "method": "bounded geometric observation",
        "notes": "No semantic or vector reconstruction is claimed.",
    })


def write_snapshot(data: dict) -> None:
    """Persist a readable derived snapshot; never use it as routing input."""

    THEMES.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_source_analysis(source_structure: dict[str, object]) -> None:
    """Persist schema-valid raster evidence plus the showcase actor mapping."""

    SOURCE_ANALYSIS.parent.mkdir(parents=True, exist_ok=True)
    tools_root = ROOT.parent / "skills" / "motiflux" / "tools"
    try:
        if str(tools_root) not in sys.path:
            sys.path.insert(0, str(tools_root))
        from engine.raster import analyze_raster

        analysis = analyze_raster(CROP_JPG, max_dimension=1024)
    except (ImportError, OSError, TypeError, ValueError):
        analysis = {
            "schema_version": "1.0",
            "status": "candidate",
            "source": {
                "path": "showcase/assets/prysai-mark-crop.jpg",
                "format": "jpeg",
                "width": None,
                "height": None,
                "color_mode": None,
                "has_alpha": None,
            },
            "observations": {
                "elements": [],
                "colors": [],
                "landmarks": [],
                "negative_spaces": [],
                "topology": {},
            },
            "review": {
                "status": "needs-review",
                "vector_reconstruction": "not-claimed",
                "reason": "The raster observation adapter was unavailable.",
                "recommended_next_step": "Run the Pillow adapter or provide a vector source.",
            },
            "capabilities": ["raster-header"],
            "not_run": ["pixel-decoding", "connected-components", "layout-grouping"],
            "unresolved": ["pixel structure observation adapter was unavailable"],
        }
    analysis["source"]["path"] = "showcase/assets/prysai-mark-crop.jpg"
    analysis["producer"] = "showcase/generate_showcase.py"
    _attach_role_reviews(analysis, source_structure)
    analysis["showcase_adapter"] = source_structure
    SOURCE_ANALYSIS.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = str(hex_color).removeprefix("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _rgba(hex_color: str, alpha: int) -> tuple[int, int, int, int]:
    return (*_rgb(hex_color), max(0, min(255, alpha)))


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def _smoothstep(value: float) -> float:
    progress = _clamp(value)
    return progress * progress * (3 - 2 * progress)


def _contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    copy = image.copy()
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    return copy


def _center_position(canvas_size: tuple[int, int], image_size: tuple[int, int], offset: tuple[int, int] = (0, 0)) -> tuple[int, int]:
    return (
        (canvas_size[0] - image_size[0]) // 2 + offset[0],
        (canvas_size[1] - image_size[1]) // 2 + offset[1],
    )


def _with_opacity(layer: Image.Image, opacity: float) -> Image.Image:
    result = layer.convert("RGBA")
    alpha = result.getchannel("A").point(lambda value: round(value * _clamp(opacity)))
    result.putalpha(alpha)
    return result


def _sample_logo_targets(mark: Image.Image, size: tuple[int, int], count: int, seed: int) -> list[tuple[int, int]]:
    target = _contain(mark, (int(size[0] * .68), int(size[1] * .76)))
    left, top = _center_position(size, target.size)
    mask = target.getchannel("A")
    pixels = [
        (left + x, top + y)
        for y in range(target.height)
        for x in range(target.width)
        if mask.getpixel((x, y)) > 150
    ]
    if not pixels:
        return []
    rng = random.Random(seed)
    if len(pixels) <= count:
        return pixels
    return rng.sample(pixels, count)


def _starting_points(size: tuple[int, int], count: int, seed: int) -> list[tuple[int, int]]:
    rng = random.Random(seed)
    points: list[tuple[int, int]] = []
    for index in range(count):
        side = index % 4
        if side == 0:
            points.append((rng.randint(-20, size[0] // 5), rng.randint(0, size[1])))
        elif side == 1:
            points.append((rng.randint(size[0] * 4 // 5, size[0] + 20), rng.randint(0, size[1])))
        elif side == 2:
            points.append((rng.randint(0, size[0]), rng.randint(-20, size[1] // 5)))
        else:
            points.append((rng.randint(0, size[0]), rng.randint(size[1] * 4 // 5, size[1] + 20)))
    return points


def _draw_animation_effect(layer: Image.Image, theme: dict, progress: float, points: list[tuple[int, int]], targets: list[tuple[int, int]], seed: int, focus: tuple[int, int] | None = None) -> None:
    """Draw deterministic secondary motion around the unchanged source mark."""

    if progress <= .03:
        return
    width, height = layer.size
    draw = ImageDraw.Draw(layer, "RGBA")
    accent = theme["accent"]
    effect = theme["pattern"]
    p = _smoothstep(progress)
    fade_in = int(255 * _clamp(progress * 1.7))
    fade_out = int(255 * (1 - _clamp((progress - .62) / .38)))
    effect_alpha = min(fade_in, max(32, fade_out))

    if effect == "grid":
        shift = int((1 - p) * 38)
        for x in range(-40 + shift, width + 40, 28):
            draw.line((x, 0, x, height), fill=_rgba(accent, max(22, effect_alpha // 2)), width=1)
        for y in range(-40 + shift, height + 40, 28):
            draw.line((0, y, width, y), fill=_rgba(accent, max(22, effect_alpha // 2)), width=1)
    elif effect == "quiet":
        glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow, "RGBA")
        radius = int(min(width, height) * (.18 + p * .18))
        glow_draw.ellipse((width // 2 - radius, height // 2 - radius, width // 2 + radius, height // 2 + radius), fill=_rgba(accent, max(18, effect_alpha // 2)))
        layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(22)))
    elif effect == "scan":
        offset = int((1 - p) * height)
        for y in range(-height + offset, height * 2, 14):
            draw.line((0, y, width, y), fill=_rgba(accent, max(18, effect_alpha // 2)), width=1)
    elif effect == "field":
        # Keep the signal field attached to the measured actors. The foreground
        # path is the identity event; these few arrivals only explain the AI
        # metaphor and must never become the visual subject.
        for index, (start, target) in enumerate(zip(points[:24], targets[:24])):
            travel = _smoothstep((progress - .04) / .72)
            x = round(start[0] + (target[0] - start[0]) * travel)
            y = round(start[1] + (target[1] - start[1]) * travel)
            radius = 1
            alpha = int(220 * (1 - _clamp((progress - .7) / .3)))
            if alpha > 0:
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=_rgba(accent, max(24, alpha)))
        focus_x, focus_y = focus or (width // 2, height // 2)
        ring = int(min(width, height) * (.12 + (1 - p) * .18))
        draw.ellipse((focus_x - ring, focus_y - ring, focus_x + ring, focus_y + ring), outline=_rgba(accent, max(16, effect_alpha // 3)), width=1)
    elif effect in {"ring", "orbit"}:
        focus_x, focus_y = focus or (width // 2, height // 2)
        ring = int(min(width, height) * (.18 + p * .22))
        draw.ellipse((focus_x - ring, focus_y - ring, focus_x + ring, focus_y + ring), outline=_rgba(accent, max(24, effect_alpha)), width=2)
        ring_2 = int(ring * .64)
        draw.ellipse((focus_x - ring_2, focus_y - ring_2, focus_x + ring_2, focus_y + ring_2), outline=_rgba(accent, max(16, effect_alpha // 2)), width=1)
        angle = math.radians((progress * 360) - 90)
        dot_x = focus_x + int(math.cos(angle) * ring)
        dot_y = focus_y + int(math.sin(angle) * ring)
        draw.ellipse((dot_x - 4, dot_y - 4, dot_x + 4, dot_y + 4), fill=_rgba(accent, max(28, effect_alpha)))
    elif effect == "shield":
        inset = int(min(width, height) * (.08 + (1 - p) * .08))
        points_shape = [(width // 2, inset), (width - inset, int(height * .23)), (width - inset * 2, int(height * .74)), (width // 2, height - inset), (inset * 2, int(height * .74)), (inset, int(height * .23))]
        draw.line(points_shape + [points_shape[0]], fill=_rgba(accent, max(24, effect_alpha)), width=2, joint="curve")
    elif effect in {"burst", "speed"}:
        for index in range(5):
            y = int(height * (.24 + index * .13))
            length = int(width * (.38 + p * .38))
            x = int((1 - p) * -width * .24 + index * 10)
            draw.line((x, y, x + length, y - int(height * .16)), fill=_rgba(accent, max(22, effect_alpha)), width=2)
    elif effect == "track":
        sweep = int((p * 1.7 - .35) * width)
        draw.line((sweep, 0, sweep - width // 5, height), fill=_rgba(accent, max(34, effect_alpha)), width=max(2, width // 120))
        draw.line((0, height // 2, width, height // 2), fill=_rgba(accent, max(20, effect_alpha // 2)), width=1)
    elif effect == "curtain":
        opening = int(width * (.12 + p * .38))
        draw.rectangle((0, 0, width // 2 - opening, height), fill=(0, 0, 0, max(20, fade_out // 2)))
        draw.rectangle((width // 2 + opening, 0, width, height), fill=(0, 0, 0, max(20, fade_out // 2)))
        draw.line((width // 2 - opening, 0, width // 2 - opening, height), fill=_rgba(accent, max(18, effect_alpha)), width=1)
        draw.line((width // 2 + opening, 0, width // 2 + opening, height), fill=_rgba(accent, max(18, effect_alpha)), width=1)
    elif effect == "wave":
        for row in range(4):
            baseline = int(height * (.23 + row * .18))
            wave = ImageDraw.Draw(layer, "RGBA")
            coordinates = []
            for x in range(-20, width + 20, 12):
                y = baseline + int(math.sin(x / 54 + progress * 4 + row) * height * .07)
                coordinates.append((x, y))
            wave.line(coordinates, fill=_rgba(accent, max(20, effect_alpha // 2)), width=1)
    elif effect == "plain":
        draw.line((int(width * (p * 1.4 - .4)), 0, int(width * (p * 1.4 - .4)) + width // 4, height), fill=_rgba(accent, max(18, effect_alpha // 2)), width=2)


def _mask_in_box(alpha: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    """Keep only one supplied-raster component inside its source-space box."""

    result = Image.new("L", alpha.size, 0)
    result.paste(alpha.crop(box), box[:2])
    return result


def _place_mask(mask: Image.Image, size: tuple[int, int], target_size: tuple[int, int], position: tuple[int, int]) -> Image.Image:
    """Scale a source-space mask exactly as the canonical mark is displayed."""

    result = Image.new("L", size, 0)
    result.paste(mask.resize(target_size, Image.Resampling.LANCZOS), position)
    return result


def _line_points(start: tuple[float, float], end: tuple[float, float], count: int) -> list[tuple[int, int]]:
    """Create a deterministic polyline used by the source-pixel reveal cursor."""

    count = max(2, int(count))
    return [
        (round(start[0] + (end[0] - start[0]) * index / (count - 1)), round(start[1] + (end[1] - start[1]) * index / (count - 1)))
        for index in range(count)
    ]


def _trace_points(mask: Image.Image, component: str, center: tuple[int, int]) -> list[tuple[int, int]]:
    """Build reviewable construction traces without converting raster pixels to vectors."""

    bbox = mask.getbbox()
    if not bbox:
        return []
    left, top, right, bottom = bbox
    width = max(1, right - left)
    height = max(1, bottom - top)
    if component == "dot":
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        radius = max(2, min(width, height) * .34)
        return [
            (round(cx + math.cos(math.radians(angle)) * radius), round(cy + math.sin(math.radians(angle)) * radius))
            for angle in range(0, 361, 24)
        ]
    if component == "arc":
        cx, cy = center
        rx = max(4, width * .48)
        ry = max(4, height * .48)
        return [
            (round(cx + math.cos(math.radians(angle)) * rx), round(cy + math.sin(math.radians(angle)) * ry))
            for angle in range(0, 361, 8)
        ]
    if component == "bar":
        y = (top + bottom) / 2
        return _line_points((left, y), (right, y), 28)
    if component in {"stem", "p"}:
        x = (left + right) / 2
        stem = _line_points((x, top), (x, bottom), 24)
        if component == "stem":
            return stem
        bowl = [
            (round(center[0] + math.cos(math.radians(angle)) * width * .34), round(top + height * .34 + math.sin(math.radians(angle)) * height * .28))
            for angle in range(205, 526, 12)
        ]
        return stem + bowl
    if component == "wordmark":
        y = (top + bottom) / 2
        # A shallow zig-zag makes the cursor readable without inventing glyph
        # geometry; the revealed fill still comes exclusively from the mask.
        points = _line_points((left, y), (right, y), 16)
        return [(x, round(y + math.sin(index * math.pi) * height * .18)) for index, (x, _) in enumerate(points)]
    return _line_points((left, (top + bottom) / 2), (right, (top + bottom) / 2), 16)


def _route_trace_points(
    mask: Image.Image,
    component: str,
    mode: str,
    components: dict[str, object],
    theme: dict,
    component_index: int,
) -> list[tuple[int, int]]:
    """Apply route-specific direction to a stable, source-space trace."""

    center = components["monogram_center"]
    stored = components.get("trace_points", {}).get(component, [])
    if component == "wordmark" and isinstance(stored, list) and stored and isinstance(stored[0], list):
        stored = stored[max(0, component_index - 4)] if component_index - 4 < len(stored) else []
    points = list(stored)
    if not points:
        points = _trace_points(mask, component, center)
    if not points:
        return []
    if component == "arc":
        # The observed arc occupies the upper half of the monogram. Trace it
        # around its own source-space bounds; using the monogram centroid here
        # would put the pen below the measured actor and leave only fragments.
        # The route may change the entry side and direction, but the path is
        # always clipped to this measured arc. This keeps “draw a circle” a
        # visible identity event rather than a decorative ring in the field.
        bbox = mask.getbbox() or (center[0] - 1, center[1] - 1, center[0] + 1, center[1] + 1)
        arc_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
        rx = max(4, (bbox[2] - bbox[0]) * .48)
        ry = max(4, (bbox[3] - bbox[1]) * .48)
        variant = str(theme.get("foreground_variant", "default"))
        direction = -1 if int(theme.get("arc_direction", 1)) < 0 else 1
        if "reverse" in variant or "counter" in variant:
            direction = -1
        elif variant in {"polar-clockwise", "diagonal-forward", "scan-forward", "wave-phase-a"}:
            direction = 1
        route_offset = ((float(theme.get("arc_start", 205)) - 205.0) % 31.0) - 15.0
        start = (180.0 if direction > 0 else 360.0) + (route_offset if direction > 0 else -route_offset)
        return [
            (round(arc_center[0] + math.cos(math.radians(start + direction * angle)) * rx), round(arc_center[1] + math.sin(math.radians(start + direction * angle)) * ry))
            for angle in range(0, 181, 5)
        ]
    if component == "bar":
        # The bar is a semantic beat in the public storyboard. Keep its
        # construction cursor horizontal even when the surrounding theme uses
        # polar, diagonal, or boundary language. Routes can still differ by
        # entry side or centre-outward order without turning the bar into a
        # background scan.
        bbox = mask.getbbox() or (center[0] - 1, center[1] - 1, center[0] + 1, center[1] + 1)
        left, top, right, bottom = bbox
        y = (top + bottom) / 2
        variant = str(theme.get("foreground_variant", "default"))
        if variant in {"polar-offset", "diagonal-center"}:
            midpoint = (left + right) / 2
            left_path = _line_points((midpoint, y), (left, y), 14)
            right_path = _line_points((midpoint, y), (right, y), 14)
            points = [*left_path, *right_path[1:]]
        elif variant == "wave-phase-a":
            # Organic flow keeps the measured horizontal stroke, but enters
            # from the opposite side so the baked midpoint carries a visible
            # route difference rather than relying on its background.
            points = _line_points((right, y), (left, y), 28)
        else:
            points = _line_points((right, y), (left, y), 28) if "reverse" in variant or mode in {"boundary", "impact"} else _line_points((left, y), (right, y), 28)
        return points
    if component in {"stem", "p"}:
        # Keep the P construction legible: first draw the stem, then the bowl.
        # Both traces remain clipped to the supplied source mask.
        bbox = mask.getbbox() or (center[0] - 1, center[1] - 1, center[0] + 1, center[1] + 1)
        left, top, right, bottom = bbox
        x = (left + right) / 2
        stem = _line_points((x, top), (x, bottom), 24)
        if component == "stem":
            return stem
        bowl = [
            (round(center[0] + math.cos(math.radians(angle)) * max(4, (right - left) * .34)), round(top + (bottom - top) * .34 + math.sin(math.radians(angle)) * max(4, (bottom - top) * .28)))
            for angle in range(205, 526, 12)
        ]
        return stem + bowl
    if component == "wordmark":
        # Each glyph is already an independent observed actor. The route only
        # changes the cursor's entry grammar; it never changes the glyph
        # order. This makes the same P → r → y → s → a → i reading sequence
        # feel like a scan, convergence, wave, or reverse commit while the
        # painted pixels remain bounded by the supplied actor mask.
        variant = str(theme.get("foreground_variant", "default"))
        if "reverse" in variant:
            points.reverse()
        elif variant.startswith("polar"):
            shift = (component_index * 3) % max(1, len(points))
            points = points[shift:] + points[:shift]
        elif variant.startswith("diagonal") or variant == "scan-slope":
            height = max(2, (mask.getbbox() or (0, 0, 1, 1))[3] - (mask.getbbox() or (0, 0, 1, 1))[1])
            points = [(x, round(y + (index / max(1, len(points) - 1) - .5) * height * .45)) for index, (x, y) in enumerate(points)]
        elif variant.startswith("wave"):
            height = max(2, (mask.getbbox() or (0, 0, 1, 1))[3] - (mask.getbbox() or (0, 0, 1, 1))[1])
            points = [(x, round(y + math.sin(index * .8 + component_index) * height * .5)) for index, (x, y) in enumerate(points)]
        return points
    if mode in {"boundary", "impact"}:
        points.reverse()
    if mode in {"convergence", "radial", "aperture"}:
        pivot = min(points, key=lambda point: (point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2)
        points = [pivot, *points]
    if mode == "organic":
        amplitude = max(2.0, (mask.height * .07))
        points = [(x, round(y + math.sin(index * .52 + component_index) * amplitude)) for index, (x, y) in enumerate(points)]
    if mode == "grid":
        points = [(x, y + ((index % 2) * 2 - 1) * min(5, mask.height // 24)) for index, (x, y) in enumerate(points)]
    return points


def _polyline_prefix(points: list[tuple[int, int]], progress: float) -> list[tuple[int, int]]:
    """Return a prefix at a distance along a polyline, not at a point index."""

    if not points:
        return []
    if len(points) == 1 or progress >= .999:
        return list(points)
    if progress <= 0:
        return [points[0]]
    lengths = [0.0]
    for start, end in zip(points, points[1:]):
        lengths.append(lengths[-1] + math.hypot(end[0] - start[0], end[1] - start[1]))
    target = lengths[-1] * _clamp(progress)
    prefix = [points[0]]
    for index, (start, end) in enumerate(zip(points, points[1:]), start=1):
        if lengths[index] >= target:
            segment_length = max(1e-6, lengths[index] - lengths[index - 1])
            local = _clamp((target - lengths[index - 1]) / segment_length)
            prefix.append((round(start[0] + (end[0] - start[0]) * local), round(start[1] + (end[1] - start[1]) * local)))
            break
        prefix.append(end)
    return prefix


def _trace_brush_width(mask: Image.Image, component: str) -> int:
    """Choose a source-scale brush that makes the actor path visibly grow."""

    bbox = mask.getbbox()
    if not bbox:
        return 2
    width = max(1, bbox[2] - bbox[0])
    height = max(1, bbox[3] - bbox[1])
    if component == "dot":
        return max(3, round(min(width, height) * .58))
    if component == "bar":
        return max(3, round(height * .9))
    if component == "wordmark":
        # A wordmark cursor should draw the glyph, not flood its entire box.
        # A narrower pen keeps the route-specific scan/wave/polar entry visible
        # at the shared comparison checkpoints while the fill still resolves
        # to the exact supplied actor before the canonical handoff.
        return max(3, round(height * .18))
    if component == "arc":
        return max(3, round(min(width, height) * .16))
    return max(3, round(min(width, height) * .14))


def _trace_prefix_mask(mask: Image.Image, points: list[tuple[int, int]], progress: float, width: int = 4) -> Image.Image:
    """Paint only the travelled path, then clip the paint to supplied pixels.

    The path is the construction event. The source mask is only the paint
    boundary, so an intermediate frame cannot appear merely because a scalar
    rank field admitted an entire disconnected region.
    """

    if not points or progress <= 0:
        return Image.new("L", mask.size, 0)
    if progress >= .999:
        return mask.copy()
    prefix = _polyline_prefix(points, progress)
    path = Image.new("L", mask.size, 0)
    draw = ImageDraw.Draw(path)
    brush = max(2, int(width))
    draw.line(prefix, fill=255, width=brush, joint="curve")
    head_x, head_y = prefix[-1]
    head_radius = max(2, round(brush * .62))
    draw.ellipse((head_x - head_radius, head_y - head_radius, head_x + head_radius, head_y + head_radius), fill=255)
    return ImageChops.multiply(mask, path)


def _path_reveal(
    mask: Image.Image,
    local: float,
    mode: str,
    component: str,
    component_index: int,
    components: dict[str, object],
    theme: dict,
) -> Image.Image:
    """Reveal source pixels by a travelled actor path.

    Route modes may alter the path order and the actor's arrival transform, but
    this seam never uses a per-pixel rank gate. That makes the identity-bearing
    pixels obey the same visible construction story as the guides.
    """

    if local <= 0:
        return Image.new("L", mask.size, 0)
    if local >= .999:
        return mask.copy()
    progress = _smoothstep(local)
    points = _route_trace_points(mask, component, mode, components, theme, component_index)
    if mode == "fade":
        # Stable geometry remains the accessibility-first choice, but its
        # opacity still follows the same actor-local schedule as other routes.
        return mask.point(lambda value: round(value * progress))
    return _trace_prefix_mask(mask, points, progress, width=_trace_brush_width(mask, component))


def _build_growth_components(
    mark: Image.Image,
    size: tuple[int, int],
    source_structure: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build source-derived actor masks, using reviewed observations when available."""

    target = _contain(mark, (int(size[0] * .68), int(size[1] * .76)))
    position = _center_position(size, target.size)
    alpha = mark.getchannel("A")
    boxes: dict[str, tuple[int, int, int, int]] = dict(LOGO_COMPONENT_BOXES)
    observed_boxes = source_structure.get("boxes") if isinstance(source_structure, dict) else None
    if isinstance(observed_boxes, dict):
        for name, value in observed_boxes.items():
            if not isinstance(name, str) or not isinstance(value, (list, tuple)) or len(value) != 4:
                continue
            try:
                candidate = tuple(int(item) for item in value)
            except (TypeError, ValueError):
                continue
            if candidate[2] > candidate[0] and candidate[3] > candidate[1]:
                boxes[name] = candidate
    raw = {name: _mask_in_box(alpha, box) for name, box in boxes.items()}
    empty = Image.new("L", alpha.size, 0)
    raw["monogram_p"] = raw.get("monogram_p", empty)
    # Keep the dot independent so the construction can begin with one exact
    # source pixel cluster instead of a background-only flash.
    raw["monogram"] = ImageChops.subtract(raw["monogram_raw"], raw["origin_dot"])

    origin_dot = _place_mask(raw["origin_dot"], size, target.size, position)
    monogram = _place_mask(raw["monogram"], size, target.size, position)
    observed_p = _place_mask(raw["monogram_p"], size, target.size, position)
    bbox = monogram.getbbox() or (size[0] // 2 - 70, size[1] // 2 - 70, size[0] // 2 + 70, size[1] // 2 + 70)
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2

    # The arc and bar are measured gates over the original monogram. The
    # remainder is the stem/bowl phase, so every intermediate pixel still
    # belongs to the supplied raster.
    radius = max(24, min(bbox[2] - bbox[0], bbox[3] - bbox[1]) // 2)
    ring = Image.new("L", size, 0)
    ring_draw = ImageDraw.Draw(ring)
    outer = (cx - radius, cy - radius, cx + radius, cy + radius)
    inner_radius = max(8, int(radius * .58))
    inner = (cx - inner_radius, cy - inner_radius, cx + inner_radius, cy + inner_radius)
    ring_draw.ellipse(outer, fill=255)
    ring_draw.ellipse(inner, fill=0)
    arc_gate = Image.new("L", size, 0)
    ImageDraw.Draw(arc_gate).rectangle((0, 0, size[0], cy + max(4, (bbox[3] - bbox[1]) // 20)), fill=255)
    arc = ImageChops.multiply(monogram, ImageChops.multiply(ring, arc_gate))

    bar_height = max(5, (bbox[3] - bbox[1]) // 15)
    bar_gate = Image.new("L", size, 0)
    ImageDraw.Draw(bar_gate).rectangle((bbox[0], cy - bar_height, bbox[2], cy + bar_height), fill=255)
    bar = ImageChops.multiply(monogram, bar_gate)
    arc = ImageChops.subtract(arc, bar)
    stem = ImageChops.subtract(ImageChops.subtract(monogram, arc), bar)

    # The raster observer may not be able to separate the stylized P from its
    # ring. Keep the P actor source-bounded, but expose only the pixels that are
    # new after the public bar beat. The bar is already on the canvas when the
    # monogram is introduced; reusing it as a second P actor made the stage
    # appear to jump instead of grow.
    p_full = observed_p
    if p_full.getbbox() is None:
        p_full = ImageChops.lighter(bar, stem)
    else:
        p_full = ImageChops.lighter(p_full, ImageChops.lighter(bar, stem))
    p_component = ImageChops.subtract(p_full, bar)

    # Keep the compatibility key, but make it source-preserving. The moving
    # bar cursor is now clipped to this measured actor instead of adding pixels
    # outside the supplied Logo.
    bar_stroke = bar.copy()

    components: dict[str, object] = {
        "origin_dot": origin_dot,
        "arc": arc,
        "bar": bar,
        "bar_stroke": bar_stroke,
        "stem": stem,
        "p_component": p_component,
        "p_full": p_full,
        "monogram": monogram,
        "wordmark": [
            _place_mask(raw.get(name, empty), size, target.size, position)
            for name in (
                "wordmark_01",
                "wordmark_02",
                "wordmark_03",
                "wordmark_04",
                "wordmark_05",
                "wordmark_06",
            )
        ],
        "final": _place_mask(alpha, size, target.size, position),
        "position": position,
        "target_size": target.size,
        "monogram_center": (cx, cy),
        "monogram_bbox": bbox,
        "trace_points": {},
    }
    components["trace_points"] = {
        name: _trace_points(mask, name, (cx, cy))
        for name, mask in (
            ("dot", origin_dot),
            ("arc", arc),
            ("bar", bar),
            ("stem", stem),
            ("p", p_component),
        )
    }
    components["trace_points"]["wordmark"] = []
    for wordmark_mask in components["wordmark"]:
        points = _trace_points(wordmark_mask, "wordmark", (cx, cy))
        components["trace_points"].setdefault("wordmark", []).append(points)
    return components


def _sector_mask(size: tuple[int, int], center: tuple[int, int], radius: int, start: float, sweep: float) -> Image.Image:
    """Create a deterministic angular reveal mask for a contour-like stage."""

    mask = Image.new("L", size, 0)
    if sweep >= 359:
        ImageDraw.Draw(mask).ellipse((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), fill=255)
        return mask
    ImageDraw.Draw(mask).pieslice((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), start=start, end=start + sweep, fill=255)
    return mask


def _progressive_mask(mask: Image.Image, progress: float, mode: str, *, center: tuple[int, int] | None = None, start: float = 0.0, direction: int = 1) -> Image.Image:
    """Reveal existing pixels by scan, diagonal, fade, or angular trace."""

    p = _smoothstep(progress)
    if p <= 0:
        return Image.new("L", mask.size, 0)
    if p >= 1:
        return mask.copy()
    if mode == "fade":
        return mask.point(lambda value: round(value * p))
    bbox = mask.getbbox() or (0, 0, mask.width, mask.height)
    gate = Image.new("L", mask.size, 0)
    draw = ImageDraw.Draw(gate)
    if mode == "scan":
        x = round(bbox[0] + (bbox[2] - bbox[0]) * p)
        draw.rectangle((0, 0, x, mask.height), fill=255)
    elif mode == "diagonal":
        x = round((mask.width + mask.height) * p)
        draw.polygon([(0, 0), (x, 0), (0, x)], fill=255)
    else:
        if center is None:
            center = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
        radius = max(mask.width, mask.height)
        sweep = 360 * p * direction
        if direction < 0:
            # Keep the clockwise/counter-clockwise sector anchored at one
            # endpoint. Moving both endpoints made successive frames
            # non-nested, which reads as a flicker instead of a cumulative
            # draw-on.
            sweep = abs(sweep)
            start = start - sweep
        gate = _sector_mask(mask.size, center, radius, start, sweep)
    return ImageChops.multiply(mask, gate)


def _projection_gate(
    size: tuple[int, int],
    bbox: tuple[int, int, int, int],
    progress: float,
    *,
    axis: str = "x",
    reverse: bool = False,
    skew: float = 0.0,
) -> Image.Image:
    """Build a directional draw-on gate without changing source pixels."""

    p = _smoothstep(progress)
    left, top, right, bottom = bbox
    gate = Image.new("L", size, 0)
    draw = ImageDraw.Draw(gate)
    if axis == "center":
        center_x = (left + right) / 2
        half_width = max(1.0, (right - left) * p / 2)
        draw.rectangle(
            (round(center_x - half_width), 0, round(center_x + half_width), size[1]),
            fill=255,
        )
        return ImageChops.multiply(gate, Image.new("L", size, 255))
    if axis == "y":
        boundary = round((bottom - (bottom - top) * p) if reverse else (top + (bottom - top) * p))
        if reverse:
            draw.rectangle((0, boundary, size[0], size[1]), fill=255)
        else:
            draw.rectangle((0, 0, size[0], boundary), fill=255)
        return gate
    if axis == "diagonal":
        width, height = size
        distance = (width + height) * (1.0 - p if reverse else p)
        if distance <= 0:
            return gate
        if distance >= width + height:
            return Image.new("L", size, 255)
        # The forward polygon is the clipped half-plane x + y <= distance.
        # Inverting the same construction gives a genuinely growing
        # bottom-right reveal for reverse routes; the old rectangle-like gate
        # started full and then shrank, which made the Logo appear to flicker.
        forward = Image.new("L", size, 0)
        points: list[tuple[int, int]] = [(0, 0)]
        points.append((round(min(width, distance)), 0))
        if distance > width:
            points.append((width, round(min(height, distance - width))))
        if distance > height:
            points.append((round(max(0, distance - height)), height))
        points.append((0, round(min(height, distance))))
        ImageDraw.Draw(forward).polygon(points, fill=255)
        return ImageChops.invert(forward) if reverse else forward

    boundary = (right - (right - left) * p) if reverse else (left + (right - left) * p)
    if skew:
        # A slanted front reads as a path entering the actor, not as a scaled
        # actor. Keep the front bounded to avoid leaking adjacent wordmark pixels.
        if reverse:
            draw.polygon([(boundary, 0), (size[0], 0), (size[0], size[1]), (boundary + skew, size[1])], fill=255)
        else:
            draw.polygon([(0, 0), (boundary, 0), (boundary + skew, size[1]), (0, size[1])], fill=255)
    elif reverse:
        draw.rectangle((round(boundary), 0, size[0], size[1]), fill=255)
    else:
        draw.rectangle((0, 0, round(boundary), size[1]), fill=255)
    return gate


def _wave_gate(
    size: tuple[int, int],
    bbox: tuple[int, int, int, int],
    progress: float,
    *,
    amplitude: float = 18.0,
    phase: float = 0.0,
    reverse: bool = False,
) -> Image.Image:
    """Build a bounded, low-frequency draw-on front for organic routes."""

    left, top, right, bottom = bbox
    p = _smoothstep(progress)
    boundary = left + (right - left) * p
    points = []
    for y in range(0, size[1] + 8, 8):
        offset = math.sin(y / 31.0 + phase) * amplitude * (1.0 - p * .55)
        points.append((round(boundary + offset), y))
    gate = Image.new("L", size, 0)
    if reverse:
        polygon = points + [(size[0], size[1]), (size[0], 0)]
    else:
        polygon = [(0, 0), (0, size[1]), *reversed(points)]
    ImageDraw.Draw(gate).polygon(polygon, fill=255)
    return gate


def _source_fill_reveal(
    mask: Image.Image,
    local: float,
    strategy: str,
    *,
    center: tuple[int, int],
    start: float,
    direction: int,
    component: str,
    component_index: int,
) -> Image.Image:
    """Reveal a cumulative source-pixel fill behind the moving construction pen.

    A narrow cursor alone makes letters and thick strokes appear as disconnected
    fragments. This gate is the second half of the draw-on contract: it admits
    only source pixels, accumulates monotonically, and never moves or scales a
    completed actor. The route changes the gate geometry while the source mask
    remains the only paint boundary.
    """

    if local <= 0:
        return Image.new("L", mask.size, 0)
    if local >= .999:
        return mask.copy()

    variant = str(strategy or "scan-forward")
    # The small origin dot reads best as an inside-out signal, regardless of the
    # wider route grammar around it.
    if component == "dot":
        return _progressive_mask(mask, local, "radial", center=center, start=start, direction=direction)

    bbox = mask.getbbox() or (center[0], center[1], center[0] + 1, center[1] + 1)
    if variant.startswith("polar"):
        return _progressive_mask(mask, local, "radial", center=center, start=start, direction=direction)
    if variant.startswith("wave"):
        # A wave front may bend, but its admitted region must still grow. Use
        # the cumulative maximum of the sampled front positions so no source
        # pixel disappears merely because the decorative phase changed.
        left, top, right, bottom = bbox
        p = _smoothstep(local)
        gate = Image.new("L", mask.size, 0)
        front_by_y: list[tuple[int, int]] = []
        for y in range(0, mask.height + 8, 8):
            front = left
            for sample in range(1, 25):
                q = p * sample / 24
                front = max(front, left + (right - left) * q + math.sin(y / 31.0 + component_index * .6) * (10 + component_index * 2) * (1.0 - q * .55))
            front_by_y.append((round(front), y))
        polygon = [(0, 0), (0, mask.height), *reversed(front_by_y)]
        ImageDraw.Draw(gate).polygon(polygon, fill=255)
        return ImageChops.multiply(mask, gate)
    if variant.startswith("boundary"):
        return ImageChops.multiply(
            mask,
            _projection_gate(mask.size, bbox, local, axis="y", reverse="reverse" in variant),
        )
    if variant in {"diagonal-forward", "diagonal-reverse", "diagonal-center"}:
        return ImageChops.multiply(
            mask,
            _projection_gate(
                mask.size,
                bbox,
                local,
                axis="center" if variant == "diagonal-center" else "diagonal",
                reverse=variant == "diagonal-reverse",
                skew=component_index * 7,
            ),
        )
    return ImageChops.multiply(
        mask,
        _projection_gate(mask.size, bbox, local, axis="x", reverse="reverse" in variant, skew=component_index * 4 if variant == "scan-slope" else 0),
    )


def _draw_on_reveal(
    mask: Image.Image,
    local: float,
    strategy: str,
    *,
    center: tuple[int, int],
    start: float,
    direction: int,
    component: str,
    component_index: int,
) -> Image.Image:
    """Trace a source-derived contour, then lay in its measured fill."""

    bbox = mask.getbbox() or (center[0], center[1], center[0] + 1, center[1] + 1)
    # These identity beats have an authored pen path. Keep them separate from
    # the broader route grammars below so a diagonal or radial theme cannot
    # make the public arc/bar/P sequence look like a generic opacity mask.
    if component in {"arc", "bar", "stem", "p", "wordmark"}:
        points = _route_trace_points(mask, component, "source-draw", {"monogram_center": center, "trace_points": {}}, {"foreground_variant": strategy, "arc_direction": direction, "arc_start": start}, component_index)
        if points:
            brush = _trace_brush_width(mask, component)
            stroke = _trace_prefix_mask(mask, points, _clamp(local * 1.12), width=brush)
            fill = _source_fill_reveal(
                mask,
                local,
                strategy,
                center=center,
                start=start,
                direction=direction,
                component=component,
                component_index=component_index,
            )
            return ImageChops.lighter(stroke, fill)
    outline = _mask_outline(mask, 5 if mask.width > 300 else 3)
    trace_progress = _clamp(local * 1.28)
    if strategy.startswith("polar"):
        polar_start = start
        polar_direction = direction
        if strategy == "polar-clockwise":
            polar_direction = 1
        elif strategy == "polar-counter":
            polar_direction = -1
        elif strategy == "polar-offset":
            polar_start += 78
        elif strategy == "polar-orbit":
            polar_start += 137 + component_index * 11
        trace = _progressive_mask(outline, trace_progress, "radial", center=center, start=polar_start, direction=polar_direction)
        fill_gate = _progressive_mask(mask, _clamp((local - .38) / .62), "radial", center=center, start=polar_start, direction=polar_direction)
    elif strategy.startswith("diagonal"):
        if strategy == "diagonal-reverse":
            diagonal_reverse = True
            diagonal_axis = "diagonal"
        elif strategy == "diagonal-center":
            diagonal_reverse = False
            diagonal_axis = "center"
        else:
            diagonal_reverse = False
            diagonal_axis = "diagonal"
        trace = ImageChops.multiply(
            outline,
            _projection_gate(
                mask.size,
                bbox,
                trace_progress,
                axis=diagonal_axis,
                reverse=diagonal_reverse,
                skew=component_index * 7,
            ),
        )
        fill_gate = ImageChops.multiply(
            mask,
            _projection_gate(
                mask.size,
                bbox,
                _clamp((local - .32) / .68),
                axis=diagonal_axis,
                reverse=diagonal_reverse,
                skew=component_index * 7,
            ),
        )
    elif strategy.startswith("wave"):
        phase = component_index * .6 + (.24 if strategy == "wave-phase-a" else 0.0)
        trace = ImageChops.multiply(
            outline,
            _wave_gate(mask.size, bbox, trace_progress, amplitude=16 + component_index * 2, phase=phase),
        )
        fill_gate = ImageChops.multiply(
            mask,
            _wave_gate(mask.size, bbox, _clamp((local - .30) / .70), amplitude=16 + component_index * 2, phase=phase),
        )
    elif strategy.startswith("boundary"):
        boundary_reverse = strategy == "boundary-reverse" or component_index % 2 == 1
        trace = ImageChops.multiply(outline, _projection_gate(mask.size, bbox, trace_progress, axis="y", reverse=boundary_reverse))
        fill_gate = ImageChops.multiply(mask, _projection_gate(mask.size, bbox, _clamp((local - .45) / .55), axis="y", reverse=boundary_reverse))
    elif strategy == "scan-reverse":
        trace = ImageChops.multiply(outline, _projection_gate(mask.size, bbox, trace_progress, axis="x", reverse=True))
        fill_gate = ImageChops.multiply(mask, _projection_gate(mask.size, bbox, _clamp((local - .36) / .64), axis="x", reverse=True))
    elif strategy == "scan-slope":
        skew = 18 + component_index * 4
        trace = ImageChops.multiply(outline, _projection_gate(mask.size, bbox, trace_progress, axis="x", skew=skew))
        fill_gate = ImageChops.multiply(mask, _projection_gate(mask.size, bbox, _clamp((local - .36) / .64), axis="x", skew=skew))
    else:
        trace = ImageChops.multiply(outline, _projection_gate(mask.size, bbox, trace_progress, axis="x", reverse=component_index % 2 == 1))
        fill_gate = ImageChops.multiply(mask, _projection_gate(mask.size, bbox, _clamp((local - .36) / .64), axis="x", reverse=component_index % 2 == 1))
    # A contour is a temporary drawing aid, never a new identity pixel. Clip
    # it back to the supplied actor before compositing so the intermediate
    # frame stays source-pixel bounded as well as the final handoff.
    trace = ImageChops.multiply(trace, mask)
    return ImageChops.lighter(trace, fill_gate)


def _reveal_strategy(mode: str, component: str, variant: str = "default") -> str:
    """Choose the actual source-pixel draw-on grammar for a route.

    The route must remain visible when particles and guides are removed. These
    strategies therefore change the foreground mask itself: angular contour,
    orthogonal scan, diagonal aperture, bounded perimeter, or organic wave.
    They never redraw the mark or replace it with a complete-mark transform.
    """

    if mode == "fade":
        return "fade"
    if variant != "default":
        return variant
    if component == "dot":
        return "polar"
    if component == "bar":
        return "boundary" if mode == "boundary" else "diagonal" if mode in {"burst", "impact", "aperture"} else "scan"
    if mode in {"contour", "convergence", "radial", "orbit"}:
        return "polar"
    if mode in {"boundary"}:
        return "boundary"
    if mode in {"organic"}:
        return "wave"
    if mode in {"burst", "impact", "aperture"}:
        return "diagonal"
    return "scan"


def _route_reveal(
    mask: Image.Image,
    local: float,
    mode: str,
    component: str,
    component_index: int,
    components: dict,
    theme: dict,
) -> Image.Image:
    """Select a visible foreground construction strategy for one route."""

    if local <= 0 or local >= .999:
        return _path_reveal(mask, local, mode, component, component_index, components, theme)
    strategy = _reveal_strategy(mode, component, str(theme.get("foreground_variant", "default")))
    if strategy == "fade":
        return _path_reveal(mask, local, mode, component, component_index, components, theme)
    bbox = mask.getbbox() or (0, 0, mask.width, mask.height)
    actor_center = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
    direction = -1 if int(theme.get("arc_direction", 1)) < 0 else 1
    start = float(theme.get("arc_start", 205)) + component_index * 17
    return _draw_on_reveal(
        mask,
        local,
        strategy,
        center=actor_center,
        start=start,
        direction=direction,
        component=component,
        component_index=component_index,
    )


def _composite_logo_mask(canvas: Image.Image, mask: Image.Image, opacity: float = 1.0, glow: bool = False) -> None:
    """Composite white pixels selected from the supplied mark mask."""

    alpha = mask.point(lambda value: round(value * _clamp(opacity)))
    layer = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    layer.putalpha(alpha)
    if glow:
        glow_layer = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
        glow_layer.putalpha(alpha.point(lambda value: round(value * .45)))
        canvas.alpha_composite(glow_layer.filter(ImageFilter.GaussianBlur(8)))
    canvas.alpha_composite(layer)


def _mask_outline(mask: Image.Image, width: int = 5) -> Image.Image:
    """Derive a temporary contour from supplied alpha; never replace its fill."""

    size = max(3, width if width % 2 else width + 1)
    expanded = mask.filter(ImageFilter.MaxFilter(size))
    contracted = mask.filter(ImageFilter.MinFilter(size))
    return ImageChops.subtract(expanded, contracted)


def _radial_gate(size: tuple[int, int], center: tuple[int, int], radius: float, *, vertical: float = 1.0) -> Image.Image:
    gate = Image.new("L", size, 0)
    rx = max(1, int(radius))
    ry = max(1, int(radius * vertical))
    ImageDraw.Draw(gate).ellipse((center[0] - rx, center[1] - ry, center[0] + rx, center[1] + ry), fill=255)
    return gate


def _resize_mask_about_center(mask: Image.Image, center: tuple[int, int], scale_x: float = 1.0, scale_y: float = 1.0) -> Image.Image:
    """Scale a source-derived actor around its measured center for an intermediate frame."""

    bbox = mask.getbbox()
    result = Image.new("L", mask.size, 0)
    if not bbox:
        return result
    crop = mask.crop(bbox)
    scaled = crop.resize((max(1, round(crop.width * scale_x)), max(1, round(crop.height * scale_y))), Image.Resampling.BICUBIC)
    position = (round(center[0] - scaled.width / 2), round(center[1] - scaled.height / 2))
    result.paste(scaled, position, scaled)
    return result


def _transform_mask(
    mask: Image.Image,
    progress: float,
    *,
    start_offset: tuple[float, float] = (0, 0),
    start_scale: tuple[float, float] = (1.0, 1.0),
    wave: tuple[float, float, float] | None = None,
    rotation: float = 0.0,
    target_center: tuple[float, float] | None = None,
) -> Image.Image:
    """Move a supplied component toward its canonical position for one route."""

    bbox = mask.getbbox()
    result = Image.new("L", mask.size, 0)
    if not bbox:
        return result
    if progress >= 1:
        # Preserve the source mask byte-for-byte at every completed actor.
        return mask.copy()
    t = _smoothstep(progress)
    scale_x = start_scale[0] + (1 - start_scale[0]) * t
    scale_y = start_scale[1] + (1 - start_scale[1]) * t
    crop = mask.crop(bbox)
    transformed = crop.resize((max(1, round(crop.width * scale_x)), max(1, round(crop.height * scale_y))), Image.Resampling.BICUBIC)
    if rotation and progress < 1:
        transformed = transformed.rotate(rotation * (1 - t), resample=Image.Resampling.BICUBIC, expand=True)
    canonical_center = target_center or ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    dx = start_offset[0] * (1 - t)
    dy = start_offset[1] * (1 - t)
    if wave:
        amplitude_x, amplitude_y, phase = wave
        dx += math.sin(t * math.pi * 2 + phase) * amplitude_x * (1 - t)
        dy += math.cos(t * math.pi * 2 + phase) * amplitude_y * (1 - t)
    position = (
        round(canonical_center[0] + dx - transformed.width / 2),
        round(canonical_center[1] + dy - transformed.height / 2),
    )
    result.paste(transformed, position, transformed)
    return result


def _actor_sequence(components: dict) -> list[Image.Image]:
    return [components["origin_dot"], components["monogram"], components.get("p_component", components["monogram"]), *components["wordmark"]]


def _composite_actor_sequence(
    canvas: Image.Image,
    actors: list[Image.Image],
    progress: float,
    *,
    order: list[int] | None = None,
    start_offsets: list[tuple[float, float]] | None = None,
    start_scales: list[tuple[float, float]] | None = None,
    wave: tuple[float, float, float] | None = None,
    opacity: float = 1.0,
    rotation: float = 0.0,
    stagger: float = .055,
) -> None:
    """Assemble independent supplied actors in a declared semantic order."""

    order = order or list(range(len(actors)))
    start_offsets = start_offsets or [(0, 0)] * len(actors)
    start_scales = start_scales or [(1, 1)] * len(actors)
    for position, actor_index in enumerate(order):
        # Keep the last semantic actor in motion until the canonical landing;
        # otherwise several routes become identical well before their final frame.
        local = _clamp((progress - position * stagger) / max(.25, 1 - position * stagger))
        if local <= .002:
            continue
        actor_wave = wave
        if wave and wave[2] != 0:
            actor_wave = (wave[0], wave[1], wave[2] + position * .45)
        moved = _transform_mask(
            actors[actor_index],
            local,
            start_offset=start_offsets[actor_index],
            start_scale=start_scales[actor_index],
            wave=actor_wave,
            rotation=rotation,
        )
        _composite_logo_mask(canvas, moved, opacity=min(1.0, opacity * (.82 + .18 * local)), glow=local < .36)


def _ease(value: float, name: str) -> float:
    """Apply a named bounded easing used by the foreground contract."""

    t = _clamp(value)
    if name == "linear":
        return t
    if name == "steps":
        return round(t * 6) / 6
    if name == "ease_out":
        return 1 - (1 - t) ** 3
    if name == "soft":
        return t * t * (3 - 2 * t)
    return _smoothstep(t)


def _phase_progress(progress: float, start: float, end: float, easing: str) -> float:
    """Map global progress into one semantic construction phase."""

    if end <= start:
        return 1.0 if progress >= end else 0.0
    return _ease((progress - start) / (end - start), easing)


def _growth_stage(progress: float, theme: dict | None = None) -> str:
    """Return the public storyboard stage for a normalized frame position."""

    if isinstance(theme, dict):
        checkpoints = _storyboard_progress(theme)
        for stage in ("blank", "spark", "arc", "bar", "monogram", "wordmark"):
            if progress <= checkpoints[stage]:
                return stage
        return "canonical"
    if progress <= 0:
        return "blank"
    if progress < .16:
        return "spark"
    if progress < .33:
        return "arc"
    if progress < .47:
        return "bar"
    if progress < .64:
        return "monogram"
    if progress < CANONICAL_HANDOFF_PROGRESS:
        return "wordmark"
    return "canonical"


def _phase_windows(theme: dict) -> dict[str, tuple[float, float]]:
    timing = str(theme.get("foreground_timing", "standard"))
    return dict(PHASE_TIMINGS.get(timing, PHASE_TIMINGS["standard"]))


def _storyboard_progress(theme: dict) -> dict[str, float]:
    """Derive public checkpoint positions from the selected phase timing.

    The old fixed checkpoints could land in the middle of a route-specific
    actor window. Deriving them from the same timing table used by the renderer
    gives the HTML, PDF, GIF evidence, and tests one readable boundary source.
    """

    windows = _phase_windows(theme)
    dot_start, dot_end = windows["dot"]
    arc_start, arc_end = windows["arc"]
    bar_start, bar_end = windows["bar"]
    stem_start, stem_end = windows["stem"]
    word_start, word_end = windows["wordmark"]
    return {
        "blank": 0.0,
        "spark": dot_end,
        "arc": arc_end,
        "bar": bar_end,
        "monogram": stem_end,
        "wordmark": min(PRECANONICAL_LOCKUP_LIMIT, word_end),
        "canonical": CANONICAL_HANDOFF_PROGRESS,
    }


def _component_motion(
    mask: Image.Image,
    local: float,
    mode: str,
    component_index: int,
    components: dict,
    anchor_mask: Image.Image | None = None,
) -> Image.Image:
    """Move an exact component through a route-specific construction path."""

    cx, cy = components["monogram_center"]
    # A partial path has a moving bbox. Deriving the transform anchor from it
    # makes the actor's origin drift as the path grows, which reads as a whole
    # Logo sliding or scaling. Always derive the canonical anchor from the
    # complete source actor and transform only the partial paint.
    anchor = anchor_mask if isinstance(anchor_mask, Image.Image) else mask
    bbox = anchor.getbbox() or (cx, cy, cx + 1, cy + 1)
    actor_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    if mode == "grid":
        # Lock components from measured grid cells; the source actors settle
        # without rotating, so the construction reads as spatial assembly.
        column = component_index % 3
        row = component_index // 3
        return _transform_mask(
            mask,
            local,
            start_offset=((column - 1) * 92, (row - 1) * 54),
            start_scale=(.72, .72),
            target_center=actor_center,
        )
    if mode == "contour":
        return _transform_mask(mask, local, start_offset=(0, 34), start_scale=(.88, .88), target_center=actor_center)
    if mode == "convergence":
        angle = math.radians(component_index * 53 - 118)
        radius = 168 + (component_index % 3) * 26
        return _transform_mask(
            mask,
            local,
            start_offset=(cx - actor_center[0] + math.cos(angle) * radius, cy - actor_center[1] + math.sin(angle) * radius),
            start_scale=(.27, .27),
            target_center=actor_center,
        )
    if mode == "radial":
        return _transform_mask(
            mask,
            local,
            start_offset=(cx - actor_center[0], cy - actor_center[1]),
            start_scale=(.34, .34),
            target_center=actor_center,
        )
    if mode == "boundary":
        angle = math.radians(component_index * 45 - 90)
        radius = 62 + (component_index % 2) * 24
        return _transform_mask(
            mask,
            local,
            start_offset=(math.cos(angle) * radius, math.sin(angle) * radius),
            start_scale=(.76, .76),
            target_center=actor_center,
        )
    if mode == "aperture":
        return _transform_mask(mask, local, start_offset=(0, 0), start_scale=(.46, .46), target_center=actor_center)
    if mode == "burst":
        angle = math.radians(component_index * 42 - 120)
        radius = 122 + component_index * 18
        return _transform_mask(
            mask,
            local,
            start_offset=(cx - actor_center[0] + math.cos(angle) * radius, cy - actor_center[1] + math.sin(angle) * radius),
            start_scale=(.22, .22),
            target_center=actor_center,
        )
    if mode == "impact":
        return _transform_mask(
            mask,
            local,
            start_offset=(-210 - component_index * 24, 0),
            start_scale=(.06, 1.0),
            target_center=actor_center,
        )
    if mode == "track":
        return _transform_mask(mask, local, start_offset=(-330 - component_index * 30, 0), start_scale=(.92, .92), target_center=actor_center)
    if mode == "organic":
        return _transform_mask(
            mask,
            local,
            start_offset=(0, 96 - component_index * 16),
            wave=(32, 20, .4 + component_index * .38),
            target_center=actor_center,
        )
    if mode == "orbit":
        angle = math.radians(component_index * 58 - 86)
        radius = 158 + (component_index % 3) * 38
        return _transform_mask(
            mask,
            local,
            start_offset=(cx - actor_center[0] + math.cos(angle) * radius, cy - actor_center[1] + math.sin(angle) * radius),
            start_scale=(.48, .48),
            target_center=actor_center,
        )
    if mode == "token":
        return _transform_mask(mask, local, start_offset=(-86 - component_index * 16, (component_index % 2) * 28 - 14), start_scale=(.84, .84), target_center=actor_center)
    return mask


def _aperture_mask(mask: Image.Image, local: float, center_x: int) -> Image.Image:
    opening = int(mask.width * (.025 + .66 * _clamp(local)))
    gate = Image.new("L", mask.size, 0)
    ImageDraw.Draw(gate).rectangle((center_x - opening, 0, center_x + opening, mask.height), fill=255)
    return ImageChops.multiply(mask, gate)


def _component_reveal(
    mask: Image.Image,
    local: float,
    mode: str,
    component: str,
    component_index: int,
    components: dict,
    theme: dict,
    anchor_mask: Image.Image | None = None,
) -> tuple[Image.Image, float, bool]:
    """Return a source-derived reveal mask, opacity, and glow flag."""

    if local <= .002:
        return Image.new("L", mask.size, 0), 0.0, False
    if local >= .999:
        # A completed source actor must stop carrying a temporary outline,
        # clip, or transform. This keeps stage comparisons exact and prevents
        # the bar beat from becoming larger than the measured monogram.
        return mask.copy(), 1.0, False
    # First draw a source-space path prefix, then move that partial actor when
    # the route calls for arrival motion. This keeps the reveal path stable and
    # makes the motion strategy visible in the identity-bearing pixels.
    reveal = _route_reveal(mask, local, mode, component, component_index, components, theme)
    # Raster showcase output is identity-first: the source actor is drawn in
    # place and the route difference comes from the measured path grammar.
    # Actor travel remains an explicit opt-in for a future source-specific
    # adapter, so a theme cannot accidentally degrade into a moving whole mark.
    if bool(theme.get("foreground_travel", False)) and component not in {"arc", "bar"} and mode != "fade":
        reveal = _component_motion(
            reveal,
            local,
            mode,
            component_index,
            components,
            anchor_mask=anchor_mask if isinstance(anchor_mask, Image.Image) else mask,
        )
    opacity = 1.0 if mode != "fade" else .18 + .82 * local
    return reveal, opacity, local < .38 and mode not in {"fade", "boundary"}


def _compose_growth_foreground(
    canvas: Image.Image,
    theme: dict,
    progress: float,
    components: dict,
    component_limit: str | None = None,
) -> None:
    """Render dot, arc, bar, monogram remainder, and letters as separate phases."""

    profile = FOREGROUND_PROFILES.get(
        str(theme.get("trajectory_id", "")),
        {"mode": "grid", "timing": "standard", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "smooth"},
    )
    mode = str(theme.get("foreground_mode", profile["mode"]))
    easing = str(theme.get("foreground_easing", profile["easing"]))
    windows = _phase_windows(theme)
    p_mask = components.get("p_component")
    has_p_component = isinstance(p_mask, Image.Image) and p_mask.getbbox() is not None
    # The monogram beat paints only the P pixels that are new after the bar.
    # Keep `stem` as a compatibility observation, but use the P actor as the
    # executable phase so the animation visibly grows into the monogram before
    # the wordmark begins.
    p_phase_mask = p_mask if has_p_component else components["stem"]
    p_phase_name = "p" if has_p_component else "stem"
    phase_components = (
        ("dot", "dot", components["origin_dot"]),
        ("arc", "arc", components["arc"]),
        ("bar", "bar", components["bar"]),
        (p_phase_name, "stem", p_phase_mask),
    )
    for component_index, (name, window_name, mask) in enumerate(phase_components):
        start, end = windows[window_name]
        local = _phase_progress(progress, start, end, easing)
        reveal, opacity, glow = _component_reveal(mask, local, mode, name, component_index, components, theme, anchor_mask=mask)
        # Identity growth stays source-pixel bounded. Any atmosphere belongs to
        # the separate secondary field layer; a blurred actor would create
        # non-source pixels and make alpha mass appear to shrink when the glow
        # switches off.
        _composite_logo_mask(canvas, reveal, opacity=opacity, glow=False)
        if component_limit == name or (component_limit == "stem" and name == "p"):
            return

    if component_limit in {"dot", "arc", "bar", "stem", "p"}:
        return

    wordmarks = components["wordmark"]
    order = list(theme.get("foreground_order", profile["letter_order"]))
    if sorted(order) != list(range(len(wordmarks))):
        # Letter order is a readability invariant. Theme identity comes from
        # path, easing, and entry behavior, never from spelling the wordmark
        # out of order.
        order = list(range(len(wordmarks)))
    word_start, word_end = windows["wordmark"]
    # Give each glyph a bounded independent window with a small overlap. This
    # makes the intermediate lockup readable while preserving route-specific
    # motion in the way each glyph enters and settles.
    span = max(.12, word_end - word_start)
    overlap = min(.018, span * .08)
    step = span / max(1, len(order) - 1)
    letter_window = min(span, step + overlap)
    for position, letter_index in enumerate(order):
        letter_start = word_start + position * (span - letter_window) / max(1, len(order) - 1)
        letter_end = min(word_end, letter_start + letter_window)
        # A route-specific cursor phase is part of the foreground contract.
        # Keep the authored P → r → y → s → a → i order, but let polar and
        # wave routes breathe at a different point inside each glyph window.
        variant = str(theme.get("foreground_variant", "default"))
        if variant.startswith("polar"):
            phase_offset = ((position % 3) - 1) * .012
            letter_start = max(word_start, letter_start + phase_offset)
            letter_end = min(word_end, letter_end + phase_offset)
        elif variant.startswith("wave"):
            phase_offset = math.sin(position * .9) * .014
            letter_start = max(word_start, letter_start + phase_offset)
            letter_end = min(word_end, letter_end + phase_offset)
        local = _phase_progress(progress, letter_start, letter_end, easing)
        # Keep the pre-canonical lockup visibly in progress. The last frame is
        # the only place where the exact source pixels are handed off, so an
        # optimized GIF cannot settle into a visually complete wordmark one
        # frame early.
        if progress < CANONICAL_HANDOFF_PROGRESS:
            local = min(local, .94)
        reveal, opacity, glow = _component_reveal(wordmarks[letter_index], local, mode, "wordmark", 4 + position, components, theme, anchor_mask=wordmarks[letter_index])
        _composite_logo_mask(canvas, reveal, opacity=opacity, glow=glow)

    # Accessibility-first intentionally keeps geometry stable. GIF palette
    # quantization can nevertheless collapse its opacity frame with another
    # low-motion route. Keep a tiny, source-bounded alpha signature on this
    # route only; it disappears at the canonical handoff and cannot invent
    # pixels outside the measured wordmark actors.
    if mode == "fade" and 0.42 < progress < CANONICAL_HANDOFF_PROGRESS:
        nudge = Image.new("L", canvas.size, 0)
        for index, letter_index in enumerate(order):
            if index % 2 == 0:
                letter = wordmarks[letter_index]
                nudge = ImageChops.lighter(nudge, letter.point(lambda value: round(value * 0.035)))
        _composite_logo_mask(canvas, nudge, opacity=1.0, glow=False)


def build_growth_components(
    mark: Image.Image,
    size: tuple[int, int],
    source_structure: dict[str, object] | None = None,
) -> dict[str, object]:
    """Public pure seam for tests and downstream render adapters."""

    return _build_growth_components(mark, size, source_structure)


def render_growth_progress(
    components: dict[str, object],
    theme: dict,
    progress: float,
) -> Image.Image:
    """Render a foreground-only progress sample for tests and audits."""

    final = components.get("final")
    if not isinstance(final, Image.Image):
        raise TypeError("growth components['final'] must be an image")
    result = Image.new("RGBA", final.size, (0, 0, 0, 0))
    _compose_growth_foreground(result, theme, _clamp(progress), components)
    return result.getchannel("A")


def render_growth_stage(
    components: dict[str, object],
    theme: dict,
    stage: str,
    progress: float = 1.0,
) -> Image.Image:
    """Render one foreground-only storyboard stage as an L mask."""

    if stage not in {"blank", "spark", "arc", "bar", "monogram", "wordmark", "canonical"}:
        raise ValueError(f"unknown growth stage: {stage}")
    final = components["final"]
    if not isinstance(final, Image.Image):
        raise TypeError("growth components['final'] must be an image")
    if stage == "canonical":
        return final.copy()
    result = Image.new("RGBA", final.size, (0, 0, 0, 0))
    if stage == "blank":
        return result.getchannel("A")
    if stage == "spark":
        _compose_growth_foreground(result, theme, 1.0, components, component_limit="dot")
    elif stage == "arc":
        _compose_growth_foreground(result, theme, 1.0, components, component_limit="arc")
    elif stage == "bar":
        _compose_growth_foreground(result, theme, 1.0, components, component_limit="bar")
    elif stage == "monogram":
        _compose_growth_foreground(result, theme, 1.0, components, component_limit="stem")
    else:
        _compose_growth_foreground(result, theme, _clamp(progress), components)
    return result.getchannel("A")


def _draw_trajectory_guides(layer: Image.Image, theme: dict, progress: float, components: dict, seed: int) -> None:
    """Draw the guide that explains the active foreground trajectory."""

    if progress <= .03:
        return
    draw = ImageDraw.Draw(layer, "RGBA")
    accent = theme["accent"]
    p = _smoothstep(progress)
    cx, cy = components["monogram_center"]
    bbox = components["monogram_bbox"]
    trajectory = theme.get("trajectory_id", "")
    if trajectory == "knowledge-graph-lock":
        actors = _actor_sequence(components)
        nodes = [(cx - 120, cy - 42), (cx - 28, cy + 60), (cx + 82, cy - 58), (cx + 166, cy + 58), (cx + 260, cy - 42), (cx + 350, cy + 55), (cx + 440, cy - 35)]
        for index in range(1, len(nodes)):
            if p > index / (len(nodes) + 1):
                draw.line((nodes[index - 1][0], nodes[index - 1][1], nodes[index][0], nodes[index][1]), fill=_rgba(accent, 115), width=1)
        for index, node in enumerate(nodes):
            alpha = int(180 * _clamp((p - index * .06) / .25))
            if alpha:
                radius = 3 if index < len(actors) else 2
                draw.ellipse((node[0] - radius, node[1] - radius, node[0] + radius, node[1] + radius), fill=_rgba(accent, alpha))
    elif trajectory == "contour-etch":
        radius = max(18, min(bbox[2] - bbox[0], bbox[3] - bbox[1]) // 2)
        sweep = 360 * _clamp((progress - .06) / .70)
        draw.arc((cx - radius, cy - radius, cx + radius, cy + radius), 210, 210 + sweep, fill=_rgba(accent, 170), width=2)
    elif trajectory == "token-commit":
        for index in range(7):
            x = int(58 + index * 112)
            if p > index * .075:
                draw.rectangle((x, 18, x + 72, 23), fill=_rgba(accent, 130), outline=None)
                draw.line((x, 26, x + int(72 * _clamp((p - index * .075) / .32)), 26), fill=_rgba(accent, 210), width=2)
    elif trajectory == "signal-convergence":
        rng = random.Random(seed + 91)
        for _ in range(8):
            x = int(cx + (rng.random() - .5) * layer.width * .72)
            y = int(cy + (rng.random() - .5) * layer.height * .56)
            radius = 1 + (rng.randrange(3) == 0)
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=_rgba(accent, int(90 * (1 - p))))
    elif trajectory == "progress-confirm":
        radius = max(24, min(layer.size) * .27)
        sweep = 360 * _clamp((progress - .04) / .86)
        draw.arc((cx - radius, cy - radius, cx + radius, cy + radius), -90, -90 + sweep, fill=_rgba(accent, 210), width=3)
        if p > .86:
            draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=_rgba(accent, 220))
    elif trajectory == "boundary-unlock":
        # Keep the boundary guide scoped to the currently constructed symbol;
        # outlining the entire final wordmark before its stage leaks the end
        # state and weakens the blank-to-lockup story.
        outline = _mask_outline(components["monogram"], 3)
        _composite_logo_mask(layer, _progressive_mask(outline, _clamp((progress - .06) / .52), "scan"), opacity=.62)
        draw.rectangle((bbox[0], bbox[1], bbox[2], bbox[3]), outline=_rgba(accent, 110), width=1)
    elif trajectory == "burst-assembly":
        for index in range(12):
            angle = math.radians(index * 30)
            length = layer.width * (.08 + .31 * p)
            x0, y0 = cx + math.cos(angle) * length * .25, cy + math.sin(angle) * length * .25
            x1, y1 = cx + math.cos(angle) * length, cy + math.sin(angle) * length
            draw.line((x0, y0, x1, y1), fill=_rgba(accent, int(155 * (1 - p))), width=2)
    elif trajectory == "kinematic-lock":
        sweep = int((p * 1.42 - .24) * layer.width)
        draw.line((sweep, 0, sweep - layer.width // 6, layer.height), fill=_rgba(accent, 225), width=max(2, layer.width // 180))
        draw.line((0, cy, layer.width, cy), fill=_rgba(accent, 95), width=1)
    elif trajectory == "impact-release":
        for offset in (-22, -11, 0, 11, 22):
            x = int(cx - (1 - p) * layer.width * .42)
            draw.line((x, cy + offset, x + int((.18 + p) * layer.width * .38), cy + offset), fill=_rgba(accent, int(150 * (1 - p))), width=2)
    elif trajectory == "aperture-title":
        opening = int(layer.width * (.035 + .54 * p))
        draw.line((layer.width // 2 - opening, 0, layer.width // 2 - opening, layer.height), fill=_rgba(accent, 170), width=1)
        draw.line((layer.width // 2 + opening, 0, layer.width // 2 + opening, layer.height), fill=_rgba(accent, 170), width=1)
    elif trajectory == "organic-current":
        for row in range(3):
            coords = []
            for x in range(-20, layer.width + 20, 12):
                y = int(cy + (row - 1) * 42 + math.sin(x / 58 + progress * 4 + row) * 15)
                coords.append((x, y))
            draw.line(coords, fill=_rgba(accent, 95), width=1)
    elif trajectory == "orbit-quest":
        for radius, alpha in ((72, 135), (112, 95), (152, 65)):
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=_rgba(accent, alpha), width=1)
        for index in range(5):
            angle = math.radians(progress * 320 + index * 72)
            radius = 72 + (index % 3) * 40
            x = cx + int(math.cos(angle) * radius)
            y = cy + int(math.sin(angle) * radius)
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=_rgba(accent, 180))
    elif trajectory == "semantic-fade":
        draw.line((cx - 88, cy + 78, cx + 88, cy + 78), fill=_rgba(accent, 95), width=1)


def _render_trajectory_mask(
    canvas: Image.Image,
    theme: dict,
    progress: float,
    components: dict,
) -> None:
    """Render the theme-specific foreground construction from supplied masks."""

    trajectory = str(theme.get("trajectory_id", ""))
    if trajectory not in IMPLEMENTED_TRAJECTORIES:
        raise ValueError(f"unimplemented trajectory: {trajectory}")
    _compose_growth_foreground(canvas, theme, _clamp(progress), components)


def _draw_growth_guides(layer: Image.Image, theme: dict, progress: float, components: dict, seed: int) -> None:
    """Keep trajectory guides secondary to the source-derived foreground."""

    _draw_trajectory_guides(layer, theme, progress, components, seed)


def _render_animation_frame(theme: dict, progress: float, mark: Image.Image, source: Image.Image, components: dict, points: list[tuple[int, int]], targets: list[tuple[int, int]], seed: int) -> Image.Image:
    """Render a theme-specific source-to-canonical frame for the portable GIF."""

    del source  # The source is shown in the left comparison cell; the GIF grows it from blank.
    size = ANIMATION_SIZE
    requested_background = EXPORT_OPTIONS.get("background")
    background_color = requested_background or theme["background"]
    background = Image.new("RGBA", size, (*_rgb(background_color), 255))
    progress = _export_progress(progress)
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    # Secondary atmosphere must remain legible but subordinate to the supplied
    # identity pixels. Omit it from the canonical landing so the final frame
    # reads as a clean, reviewable source mark.
    if requested_background is None and .03 < progress < .88:
        glow_draw.ellipse((size[0] * .18, -size[1] * .45, size[0] * .82, size[1] * 1.45), fill=_rgba(theme["accent"], 11))
        background = Image.alpha_composite(background, _with_opacity(glow.filter(ImageFilter.GaussianBlur(42)), .34))

    if progress < .84 and bool(EXPORT_OPTIONS.get("particles", True)):
        effects = Image.new("RGBA", size, (0, 0, 0, 0))
        _draw_animation_effect(effects, theme, progress, points, targets, seed, focus=components["monogram_center"])
        # Keep the theme signal visible without allowing the secondary field
        # to compete with the source-derived logo construction.
        background.alpha_composite(_with_opacity(effects, .30))

    # Preserve a clean canonical final frame for comparison and downstream use.
    # Do not leave a transformed actor or guide underneath anti-aliased source
    # pixels; the last frame must be the supplied mark, not a composite variant.
    if progress >= CANONICAL_HANDOFF_PROGRESS:
        final = _contain(mark, (int(size[0] * .68), int(size[1] * .76)))
        background.alpha_composite(final, _center_position(size, final.size))
    else:
        _render_trajectory_mask(background, theme, progress, components)
        if bool(EXPORT_OPTIONS.get("guides", True)):
            guides = Image.new("RGBA", size, (0, 0, 0, 0))
            _draw_growth_guides(guides, theme, progress, components, seed)
            background.alpha_composite(_with_opacity(guides, .24))
    return background.convert("RGB")


def build_animation_exports(data: dict, source_structure: dict[str, object] | None = None) -> None:
    """Export one portable animated render for every routed theme."""

    ANIMATIONS.mkdir(parents=True, exist_ok=True)
    mark = Image.open(MARK_PNG).convert("RGBA")
    source = Image.open(CROP_JPG).convert("RGB")
    components = _build_growth_components(mark, ANIMATION_SIZE, source_structure)
    evidence: dict[str, object] = {
        "schema_version": "1.0",
        "status": "candidate",
        "source": "showcase/assets/prysai-mark-crop.jpg",
        "source_sha256": hashlib.sha256(CROP_JPG.read_bytes()).hexdigest(),
        "renderer": "source-pixel actor-path reveal + route-specific foreground grammar; optional secondary guides",
        "canonical_handoff_progress": CANONICAL_HANDOFF_PROGRESS,
        "export_options": {
            "background": EXPORT_OPTIONS.get("background"),
            "duration_ms": EXPORT_OPTIONS.get("duration_ms"),
            "speed": EXPORT_OPTIONS.get("speed"),
            "particles": EXPORT_OPTIONS.get("particles"),
            "guides": EXPORT_OPTIONS.get("guides"),
        },
        "review_status": "needs-review",
        # Filled after encoding when all themes share a count. Optimized GIFs
        # can coalesce identical frames, so each theme also records its own
        # encoded_frame_count and stage indices below.
        "frame_count": None,
        "frame_count_scope": "per-theme; see themes[].encoded_frame_count",
        "stage_order": list(GROWTH_SEQUENCE),
        "themes": [],
        "unresolved": ["raster role semantics and browser pixel review require human or adapter review"],
    }
    encoded_frame_counts: list[int] = []
    for theme in data["themes"]:
        stage_progress = _storyboard_progress(theme)
        seed = sum((index + 1) * ord(character) for index, character in enumerate(theme["id"]))
        targets = _sample_logo_targets(mark, ANIMATION_SIZE, 110, seed)
        starts = _starting_points(ANIMATION_SIZE, len(targets), seed + 17)
        frames = [
            _render_animation_frame(theme, index / (ANIMATION_FRAME_COUNT - 1), mark, source, components, starts, targets, seed)
            for index in range(ANIMATION_FRAME_COUNT)
        ]
        gif_path = ANIMATIONS / Path(theme["animation_file"]).name
        frame_durations = _gif_frame_durations(_export_duration_ms(theme))
        theme["playback_duration_ms"] = sum(frame_durations)
        frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=frame_durations, loop=0, optimize=True, disposal=2)
        poster_path = ANIMATIONS / Path(theme["animation_poster"]).name
        frames[-1].save(poster_path, format="PNG", optimize=True)
        encoded_frames, encoded_durations = _read_encoded_gif(gif_path)
        if not encoded_frames:
            raise ValueError(f"encoded GIF has no frames: {gif_path}")
        encoded_frame_counts.append(len(encoded_frames))
        theme["playback_duration_ms"] = sum(encoded_durations)
        for stage, stage_value in stage_progress.items():
            stage_path = ANIMATIONS / Path(theme["stage_files"][stage]).name
            stage_index = round(stage_value * (len(encoded_frames) - 1))
            encoded_frames[stage_index].save(stage_path, format="PNG", optimize=True)
        stage_records = {}
        for stage, stage_value in stage_progress.items():
            frame_index = round(stage_value * (len(encoded_frames) - 1))
            frame = encoded_frames[frame_index]
            bright_pixels = sum(1 for pixel in frame.getdata() if min(pixel) > 190)
            render_progress = _export_progress(stage_value)
            stage_mask = render_growth_stage(components, theme, stage, progress=render_progress)
            alpha_histogram = stage_mask.histogram()
            encoded_identity = _encoded_identity_mask(frame, components["final"])
            encoded_identity_metrics = _foreground_mask_metrics(encoded_identity)
            actor_ids = {
                "blank": [],
                "spark": ["origin_dot"],
                "arc": ["origin_dot", "arc"],
                "bar": ["origin_dot", "arc", "bar"],
                "monogram": ["origin_dot", "arc", "bar", "p_component"],
                "wordmark": ["origin_dot", "arc", "bar", "p_component", "wordmark_01", "wordmark_02", "wordmark_03", "wordmark_04", "wordmark_05", "wordmark_06"],
                "canonical": ["final"],
            }[stage]
            stage_records[stage] = {
                "frame_index": frame_index,
                "progress": stage_value,
                "render_progress": render_progress,
                "label": GROWTH_STAGE_LABELS[stage],
                "bright_pixel_count": bright_pixels,
                "source_actor_ids": actor_ids,
                "path_strategy": theme["path_strategy"],
                "speed_profile": theme["speed_profile"],
                "foreground_alpha_mass": sum(index * count for index, count in enumerate(alpha_histogram)),
                "encoded_identity_alpha_mass": encoded_identity_metrics["alpha_mass"],
                "encoded_identity_unique_count": encoded_identity_metrics["unique_count"],
                "encoded_identity_coverage": round(
                    encoded_identity_metrics["unique_count"] / max(1, sum(components["final"].histogram()[1:])),
                    6,
                ),
            }
        progress_records = []
        for progress in PROGRESS_EVIDENCE_POINTS:
            frame_index = round(progress * (len(encoded_frames) - 1))
            render_progress = _export_progress(progress)
            if progress >= CANONICAL_HANDOFF_PROGRESS:
                progress_mask = render_growth_stage(components, theme, "canonical")
            else:
                progress_mask = render_growth_progress(components, theme, render_progress)
            metrics = _foreground_mask_metrics(progress_mask)
            encoded_metrics = _foreground_mask_metrics(_encoded_identity_mask(encoded_frames[frame_index], components["final"]))
            progress_records.append({
                "frame_index": frame_index,
                "progress": progress,
                "render_progress": render_progress,
                **metrics,
                "encoded_identity_alpha_mass": encoded_metrics["alpha_mass"],
                "encoded_identity_unique_count": encoded_metrics["unique_count"],
                "encoded_identity_coverage": round(
                    encoded_metrics["unique_count"] / max(1, sum(components["final"].histogram()[1:])),
                    6,
                ),
                "trajectory_fingerprint": _trajectory_fingerprint(theme, progress, render_progress, metrics),
            })
        evidence["themes"].append({
            "id": theme["id"],
            "gif": str(gif_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(gif_path.read_bytes()).hexdigest(),
            "encoded_frame_count": len(encoded_frames),
            "encoded_duration_ms": sum(encoded_durations),
            "canonical_frame_sha256": hashlib.sha256(encoded_frames[-1].tobytes()).hexdigest(),
            "stages": stage_records,
            "progress_points": progress_records,
            "canonical_frame": len(encoded_frames) - 1,
        })
    if encoded_frame_counts and len(set(encoded_frame_counts)) == 1:
        evidence["frame_count"] = encoded_frame_counts[0]
    # Compare source-derived foreground masks at the same progress points
    # across all routes. The canonical endpoint is intentionally identical
    # for every theme; route identity remains in the trajectory fingerprints.
    themes_evidence = evidence["themes"]
    if isinstance(themes_evidence, list) and themes_evidence:
        comparison_points = []
        for point_index, progress in enumerate(PROGRESS_EVIDENCE_POINTS):
            masks = {
                str(theme["progress_points"][point_index]["foreground_mask_sha256"])
                for theme in themes_evidence
                if isinstance(theme, dict) and len(theme.get("progress_points", [])) > point_index
            }
            fingerprints = {
                str(theme["progress_points"][point_index]["trajectory_fingerprint"])
                for theme in themes_evidence
                if isinstance(theme, dict) and len(theme.get("progress_points", [])) > point_index
            }
            comparison_points.append({
                "progress": progress,
                "theme_count": len(themes_evidence),
                "unique_foreground_mask_count": len(masks),
                "unique_trajectory_fingerprint_count": len(fingerprints),
            })
        evidence["trajectory_comparison"] = {
            "progress_points": comparison_points,
            "canonical_note": "The canonical mask is intentionally shared; route identity remains in trajectory fingerprints.",
        }
    GROWTH_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    GROWTH_EVIDENCE.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_single_theme_export(data: dict, source_structure: dict[str, object], theme_id: str) -> Path:
    """Bake one route into an isolated export directory without rewriting the atlas."""

    theme = next((item for item in data["themes"] if item.get("id") == theme_id), None)
    if theme is None:
        available = ", ".join(str(item.get("id")) for item in data["themes"])
        raise ValueError(f"unknown showcase theme {theme_id!r}; choose one of: {available}")
    export_dir = OUTPUT / "exports" / theme_id
    export_dir.mkdir(parents=True, exist_ok=True)
    mark = Image.open(MARK_PNG).convert("RGBA")
    source = Image.open(CROP_JPG).convert("RGB")
    components = _build_growth_components(mark, ANIMATION_SIZE, source_structure)
    seed = sum((index + 1) * ord(character) for index, character in enumerate(theme["id"]))
    targets = _sample_logo_targets(mark, ANIMATION_SIZE, 110, seed)
    starts = _starting_points(ANIMATION_SIZE, len(targets), seed + 17)
    frames = [
        _render_animation_frame(theme, index / (ANIMATION_FRAME_COUNT - 1), mark, source, components, starts, targets, seed)
        for index in range(ANIMATION_FRAME_COUNT)
    ]
    filename = f"prysai-{theme_id}.gif"
    gif_path = export_dir / filename
    frame_durations = _gif_frame_durations(_export_duration_ms(theme))
    theme["playback_duration_ms"] = sum(frame_durations)
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=frame_durations, loop=0, optimize=True, disposal=2)
    encoded_frames, encoded_durations = _read_encoded_gif(gif_path)
    theme["playback_duration_ms"] = sum(encoded_durations)
    poster_path = export_dir / f"prysai-{theme_id}-poster.png"
    encoded_frames[-1].save(poster_path, format="PNG", optimize=True)
    stage_files = {}
    stage_progress = _storyboard_progress(theme)
    for stage, stage_value in stage_progress.items():
        stage_path = export_dir / f"prysai-{theme_id}-{stage}.png"
        encoded_frames[round(stage_value * (len(encoded_frames) - 1))].save(stage_path, format="PNG", optimize=True)
        stage_files[stage] = str(stage_path.relative_to(ROOT.parent)).replace("\\", "/")
    manifest = {
        "schema_version": "1.0",
        "status": "baked",
        "evidence_status": "candidate",
        "source": str(CROP_JPG.relative_to(ROOT.parent)).replace("\\", "/"),
        "source_sha256": hashlib.sha256(CROP_JPG.read_bytes()).hexdigest(),
        "theme": theme_id,
        "trajectory_id": theme["trajectory_id"],
        "foreground_variant": theme["foreground_variant"],
        "export_options": dict(EXPORT_OPTIONS),
        "outputs": {
            "gif": str(gif_path.relative_to(ROOT.parent)).replace("\\", "/"),
            "poster": str(poster_path.relative_to(ROOT.parent)).replace("\\", "/"),
            "stage_checkpoints": stage_files,
        },
        "encoded_frame_count": len(encoded_frames),
        "encoded_duration_ms": sum(encoded_durations),
        "canonical_frame_sha256": hashlib.sha256(encoded_frames[-1].tobytes()).hexdigest(),
        "not_run": ["browser-pixel-review", "human-raster-role-review", "raster-to-vector-reconstruction"],
        "unresolved": ["raster role semantics remain candidate hypotheses"],
    }
    manifest_path = export_dir / "export-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def theme_card(theme: dict) -> str:
    algorithms = "".join(f"<li>{esc(item)}</li>" for item in theme["algorithm"])
    tags = "".join(f"<span class=\"tag\">{esc(item)}</span>" for item in [*theme["tags"], theme["trajectory_id"], theme["foreground_mode"], theme["foreground_variant"]])
    beats = "<span>" + "</span><span>".join(esc(item) for item in theme["beats"]) + "</span>"
    display_sequence = [GROWTH_STAGE_LABELS[stage] for stage in theme["growth_sequence"]]
    display_sequence_attr = " / ".join(display_sequence)
    stage_files_attr = esc(json.dumps(theme.get("stage_files", {}), separators=(",", ":")))
    stage_progress_attr = esc(json.dumps(_storyboard_progress(theme), separators=(",", ":")))
    stage_markup = "".join(
        f'<span data-growth-stage="{esc(stage)}">{index:02d} {esc(GROWTH_STAGE_LABELS[stage])}</span>'
        for index, stage in enumerate(theme["growth_sequence"])
    )
    letter_names = ("P", "r", "y", "s", "a", "i")
    letter_order = " > ".join(letter_names[index] for index in theme["foreground_order"])
    search_terms = [theme["name"], theme["trigger"], *theme["keywords"], *theme["tags"], theme["foreground_mode"], theme["foreground_variant"], theme["foreground_timing"], theme["path_strategy"], theme["speed_profile"]]
    return f'''<article class="theme-card" data-theme="{esc(theme["id"])}" data-search="{esc(" ".join(search_terms))}" style="--accent:{esc(theme["accent"])};--stage-bg:{esc(theme["background"])};--theme-index:{esc(theme["number"])}">
  <header class="card-head">
    <span class="card-number">{esc(theme["number"])}</span>
    <div>
      <h2>{esc(theme["name"])}</h2>
      <p class="trigger">{esc(theme["trigger"])}</p>
    </div>
    <span class="route-state">ROUTE</span>
  </header>
  <div class="comparison" aria-label="The same source image compared with its {esc(theme["name"])} animated result">
    <div class="source-cell">
      <span class="cell-label">INPUT / SAME IMAGE</span>
      <img src="assets/prysai-mark-crop.jpg" alt="Supplied Prysai logo raster source" loading="lazy">
      <span class="cell-foot">source frame</span>
    </div>
     <div class="result-cell motion-output pattern-{esc(theme["pattern"])}">
       <span class="cell-label">OUTPUT / LOGO GROWTH GIF</span>
          <div class="motion-stage" data-motion-card data-theme-id="{esc(theme["id"])}" data-effect="{esc(theme["pattern"])}" data-duration-ms="{esc(theme["playback_duration_ms"])}" data-tempo="{esc(theme["tempo"])}" data-beats="{esc(" / ".join(theme["beats"]))}" data-animation-src="{esc(theme["animation_file"])}" data-poster-src="{esc(theme["animation_poster"])}" data-stage-files="{stage_files_attr}" data-stage-progress="{stage_progress_attr}" data-growth-sequence="{esc(" / ".join(theme["growth_sequence"]))}" data-growth-display="{esc(display_sequence_attr)}" data-trajectory="{esc(theme["trajectory_id"])}" data-foreground-mode="{esc(theme["foreground_mode"])}" data-foreground-variant="{esc(theme["foreground_variant"])}" data-path-strategy="{esc(theme["path_strategy"])}" data-speed-profile="{esc(theme["speed_profile"])}" data-review-status="needs-review" data-state="blank" data-playback="poster">
         <div class="motion-effect motion-effect-a" aria-hidden="true"></div>
         <div class="motion-effect motion-effect-b" aria-hidden="true"></div>
         <div class="motion-effect motion-effect-c" aria-hidden="true"></div>
           <img class="growth-gif" src="{esc(theme["animation_poster"])}" data-gif-src="{esc(theme["animation_file"])}" alt="{esc(theme["name"])} static canonical fallback before the logo growth animation plays" loading="lazy">
          <img class="motion-canonical" hidden src="{esc(theme["animation_poster"])}" alt="Canonical {esc(theme["name"])} logo frame">
           <img class="motion-freeze" hidden src="" alt="Paused or reduced-motion frame of the logo growth animation">
          <span class="motion-loading" hidden role="status">Loading animation frame...</span>
          <div class="growth-storyboard" aria-label="Logo construction stages">
            {stage_markup}
          </div>
           <span class="motion-phase" data-motion-phase role="status" aria-live="polite">blank</span>
           <span class="motion-beat" data-motion-beat aria-hidden="true">{esc(theme["beats"][0])}</span>
       </div>
      <div class="motion-controls" role="group" aria-label="{esc(theme["name"])} animation controls">
        <button type="button" data-card-action="play">Play</button>
        <button type="button" data-card-action="pause">Pause</button>
        <button type="button" data-card-action="replay">Replay</button>
          <div class="motion-timeline" aria-hidden="true"><span data-motion-progress></span></div>
        <span class="motion-time" data-motion-time>0.0s</span>
       </div>
       <label class="motion-seek-label"><span>CHECKPOINT TIMELINE</span><input class="motion-seek" data-motion-seek type="range" min="0" max="1" step="0.001" value="0" aria-label="Seek {esc(theme["name"])} animation checkpoints"><small>Shows a baked PNG checkpoint; the downloaded GIF remains a portable looping file.</small></label>
       <a class="download-animation" href="{esc(theme["animation_file"])}" download>Open / download growth GIF</a>
       <p class="motion-route-banner"><span>THEME-SPECIFIC FOREGROUND ROUTE</span><strong>{esc(theme["foreground_mode"])} / {esc(theme["foreground_variant"])}</strong><small>{esc(theme["path_strategy"])}</small></p>
    </div>
  </div>
  <div class="card-copy">
    <div class="tag-row">{tags}</div>
     <p class="intent">{esc(theme["intent"])}</p>
     <p class="trajectory-note"><span>FOREGROUND TRAJECTORY</span>{esc(theme["trajectory_summary"])}</p>
     <p class="construction-note"><span>FOREGROUND CONTRACT</span><strong>{esc(theme["foreground_mode"])} / {esc(theme["foreground_variant"])} / {esc(theme["foreground_timing"])} / {esc(theme["foreground_easing"])}</strong><small>path: {esc(theme["path_strategy"])}<br>speed: {esc(theme["speed_profile"])}<br>stages: {esc(" > ".join(display_sequence))}<br>letter order: {esc(letter_order)}</small></p>
    <div class="detail-grid">
      <div><span class="detail-label">ALGORITHM STACK</span><ul>{algorithms}</ul></div>
      <div><span class="detail-label">BEATS</span><div class="beats">{beats}</div><span class="detail-label qa-label">QA FOCUS</span><p>{esc(theme["qa"])}</p></div>
    </div>
      <p class="result-note"><span>GROWTH RESULT</span>{esc(theme["result"])} <small>{esc(" → ".join(display_sequence))}</small></p>
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
.skip-link { position: fixed; z-index: 20; top: .6rem; left: .8rem; transform: translateY(-180%); padding: .5rem .7rem; color: #080a09; background: var(--accent); font-size: .65rem; text-decoration: none; }
.skip-link:focus { transform: translateY(0); outline: 2px solid var(--ink); outline-offset: 2px; }
.topbar { display: flex; justify-content: space-between; gap: 1rem; align-items: center; padding: 1.2rem 0; border-bottom: 1px solid var(--line); font-size: .72rem; letter-spacing: .05em; text-transform: uppercase; }
.wordmark { display: flex; gap: .65rem; align-items: center; font-weight: 700; }
.wordmark-mark { display: inline-grid; place-items: center; width: 1.5rem; height: 1.5rem; border: 1px solid var(--ink); color: var(--accent); }
.private-badge { color: var(--muted); }
.section-nav { display: flex; flex-wrap: wrap; gap: .8rem 1.2rem; padding: .7rem 0; border-bottom: 1px solid var(--line); color: var(--muted); font-size: .6rem; text-transform: uppercase; letter-spacing: .07em; }
.section-nav a { text-decoration: none; }
.section-nav a:hover, .section-nav a:focus-visible { color: var(--accent); }
.truth-bar { display: flex; flex-wrap: wrap; gap: .45rem .85rem; align-items: center; padding: .7rem .8rem; border: 1px solid var(--line); border-top: 0; color: var(--muted); font-size: .58rem; line-height: 1.4; letter-spacing: .04em; }
.truth-bar strong { color: var(--accent); letter-spacing: .1em; }
.truth-bar span { padding-left: .85rem; border-left: 1px solid var(--line); }
.section-title { margin: 0 0 .35rem; color: var(--ink); font: 700 1.05rem/1.1 Arial, Helvetica, sans-serif; letter-spacing: -.03em; }
.hero { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(250px, .8fr); gap: 4rem; padding: 6rem 0 4rem; border-bottom: 1px solid var(--line); }
.eyebrow { color: var(--accent); font-size: .73rem; letter-spacing: .14em; text-transform: uppercase; margin: 0 0 1.5rem; }
h1 { max-width: 900px; margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: clamp(3.5rem, 8.8vw, 8.9rem); line-height: .88; letter-spacing: -.08em; font-weight: 700; }
 .hero-copy { max-width: 650px; color: #c8cac4; line-height: 1.7; font-family: Arial, Helvetica, sans-serif; font-size: 1.04rem; }
 .hero-reading-guide { max-width: 650px; margin: 1rem 0 0; padding: .75rem .85rem; border-left: 2px solid var(--accent); color: var(--muted); font: .72rem/1.55 "IBM Plex Mono", monospace; }
 .hero-reading-guide strong { color: var(--ink); }
.hero-next-step { max-width: 650px; margin: 1rem 0 0; padding: .75rem .85rem; border: 1px solid color-mix(in srgb, var(--accent) 35%, var(--line)); background: color-mix(in srgb, var(--accent) 7%, transparent); color: #d9dad3; font: .72rem/1.55 "IBM Plex Mono", monospace; }
.hero-next-step strong { color: var(--accent); }
.hero-preview-pair { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center; gap: .65rem; max-width: 650px; margin-top: 1.15rem; }
.hero-preview-pair figure { position: relative; min-width: 0; margin: 0; border: 1px solid var(--line); background: #000; aspect-ratio: 1.75; overflow: hidden; }
.hero-preview-pair img { display: block; width: 100%; height: 100%; object-fit: contain; }
.hero-preview-pair figcaption { position: absolute; left: .55rem; bottom: .45rem; color: rgba(242,241,233,.72); font: .5rem/1.1 "IBM Plex Mono", monospace; letter-spacing: .08em; text-transform: uppercase; }
.hero-preview-arrow { color: var(--accent); font: 1.3rem/1 "IBM Plex Mono", monospace; }
.workflow-guide { margin: 0 0 3.5rem; border: 1px solid var(--line); background: linear-gradient(125deg, rgba(156,140,255,.08), transparent 48%), var(--panel); }
.workflow-guide-head { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(250px, .65fr); gap: 2rem; align-items: end; padding: 1.25rem 1.35rem; border-bottom: 1px solid var(--line); }
.workflow-guide-head .eyebrow { margin-bottom: .6rem; }
.workflow-guide-head h2 { margin: 0; max-width: 760px; font: 700 clamp(1.7rem, 3.6vw, 3.3rem)/.96 Arial, Helvetica, sans-serif; letter-spacing: -.06em; }
.workflow-guide-head > div:first-child > p:not(.eyebrow) { max-width: 760px; margin: .8rem 0 0; color: #c8cac4; font: .9rem/1.55 Arial, Helvetica, sans-serif; }
.guide-live { align-self: stretch; display: grid; align-content: end; border-left: 1px solid var(--line); padding-left: 1rem; }
.guide-live .detail-label { margin-bottom: .35rem; }
.guide-live strong { display: block; color: var(--accent); font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; }
.guide-live small { display: block; max-width: 260px; margin-top: .45rem; color: var(--muted); font-size: .6rem; line-height: 1.5; }
.workflow-rail { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 1px; margin: 0; padding: 0; list-style: none; background: var(--line); }
.workflow-rail li { min-width: 0; background: var(--panel); transition: background .2s ease, color .2s ease; }
.workflow-rail a { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: .55rem; min-height: 118px; padding: .9rem .85rem .72rem; color: inherit; text-decoration: none; }
.workflow-index { color: var(--muted); font-size: .62rem; }
.workflow-rail strong { display: block; color: var(--ink); font: 600 .78rem/1.1 Arial, Helvetica, sans-serif; }
.workflow-rail small { display: block; margin-top: .38rem; color: var(--muted); font-size: .57rem; line-height: 1.4; }
.workflow-rail em { grid-column: 2; align-self: end; color: var(--muted); font-size: .5rem; font-style: normal; letter-spacing: .08em; text-transform: uppercase; }
.workflow-rail li.is-current { background: color-mix(in srgb, var(--accent) 15%, var(--panel)); }
.workflow-rail li.is-current .workflow-index, .workflow-rail li.is-current em { color: var(--accent); }
.workflow-rail li.is-complete { background: color-mix(in srgb, var(--accent) 6%, var(--panel)); }
.workflow-rail li.is-complete .workflow-index { color: #b9b2ff; }
.workflow-rules { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; background: var(--line); }
.workflow-rules article { min-height: 148px; padding: 1rem 1.1rem; background: var(--panel); }
.workflow-rules article > span { color: var(--accent); font-size: .54rem; letter-spacing: .1em; }
.workflow-rules article strong { display: block; margin: .55rem 0 .45rem; color: var(--ink); font: 600 .8rem/1.2 Arial, Helvetica, sans-serif; }
.workflow-rules article p { margin: 0; color: #c1c5bd; font: .65rem/1.5 Arial, Helvetica, sans-serif; }
.workflow-rules code { color: var(--ink); font: .58rem/1.3 "IBM Plex Mono", monospace; }
.state-ladder { border-top: 1px solid var(--line); }
.state-ladder-head { display: flex; justify-content: space-between; gap: 1.5rem; align-items: end; padding: 1rem 1.25rem; }
.state-ladder-head .detail-label { margin-bottom: .45rem; }
.state-ladder-head h3 { margin: 0; color: var(--ink); font: 600 1rem/1.1 Arial, Helvetica, sans-serif; }
.state-ladder-head p { max-width: 510px; margin: 0; color: var(--muted); font-size: .6rem; line-height: 1.5; }
.state-ladder-items { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; margin: 0; padding: 0; list-style: none; background: var(--line); }
.state-card { min-height: 132px; padding: .95rem 1.1rem; background: var(--panel); }
.state-card > span { color: var(--muted); font-size: .54rem; letter-spacing: .1em; }
.state-card strong { display: block; margin: .5rem 0 .4rem; color: var(--ink); font: 600 .8rem/1.1 Arial, Helvetica, sans-serif; }
.state-card small { display: block; color: #bfc2bb; font-size: .6rem; line-height: 1.5; }
.state-preview > span { color: #a8b7ff; }
.state-baked > span { color: #d4b37a; }
.state-verified > span { color: #79e2a4; }
.hero-side { border-left: 1px solid var(--line); padding-left: 1.5rem; display: grid; align-content: end; gap: 1rem; }
.hero-side figure { margin: 0; border: 1px solid var(--line); background: #000; aspect-ratio: 1.2; overflow: hidden; }
.hero-side figure img { width: 100%; height: 100%; object-fit: cover; object-position: center 50%; }
.source-note { color: var(--muted); font-size: .67rem; line-height: 1.6; margin: 0; }
.io-showcase { margin: 3.2rem 0 2.5rem; border: 1px solid var(--line); background: linear-gradient(130deg, rgba(156,140,255,.08), transparent 46%), var(--panel); padding: 1.35rem; }
.io-heading { display: flex; justify-content: space-between; gap: 2rem; align-items: end; border-bottom: 1px solid var(--line); padding-bottom: 1.2rem; }
.io-heading .eyebrow { margin-bottom: .65rem; }
.io-heading h2 { margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: clamp(2rem, 4vw, 4rem); letter-spacing: -.07em; line-height: .95; }
.io-heading p:not(.eyebrow) { max-width: 630px; margin: .8rem 0 0; color: #c8cac4; font: 1rem/1.55 Arial, Helvetica, sans-serif; }
.io-badge { min-width: 145px; border-left: 1px solid var(--line); padding-left: 1rem; color: var(--muted); font-size: .61rem; line-height: 1.7; letter-spacing: .08em; }
.io-badge strong { color: var(--accent); font-size: .9rem; }
.io-badge small { color: var(--muted); font-size: .53rem; letter-spacing: .05em; text-transform: uppercase; }
.io-flow { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(180px, .72fr) auto minmax(0, 1.55fr); gap: 1rem; align-items: center; padding: 1.2rem 0; }
.io-frame { position: relative; min-width: 0; margin: 0; aspect-ratio: 2.62; overflow: hidden; border: 1px solid var(--line); background: #000; display: grid; place-items: center; }
.io-frame img { width: 100%; height: 100%; object-fit: contain; }
.io-output { background: #14122b; }
.io-output img { object-fit: contain; }
.io-arrow { color: var(--accent); font-size: 2rem; }
.io-middle { min-width: 0; padding: .8rem; border-left: 2px solid var(--accent); background: color-mix(in srgb, var(--accent) 7%, transparent); }
.io-middle span { display: block; color: var(--accent); font-size: .53rem; letter-spacing: .1em; }
.io-middle strong { display: block; margin: .45rem 0; color: var(--ink); font: 600 .82rem/1.15 Arial, Helvetica, sans-serif; }
.io-middle small { display: block; color: var(--muted); font: .58rem/1.45 "IBM Plex Mono", monospace; }
 .io-status { position: absolute; right: .8rem; bottom: .7rem; color: #e9e5ff; font-size: .6rem; letter-spacing: .08em; }
 .checked-in-note { margin: .85rem 0 0 !important; padding: .65rem .75rem; border: 1px solid var(--line); color: var(--muted) !important; font: .68rem/1.5 "IBM Plex Mono", monospace !important; }
 .checked-in-note strong { color: var(--accent); }
.io-footer { display: flex; align-items: center; gap: 1rem; border-top: 1px solid var(--line); padding-top: .9rem; color: var(--muted); font-size: .63rem; line-height: 1.5; }
.io-footer span { flex: 1; }
.io-footer a, .download-animation { color: var(--accent); text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--accent) 55%, transparent); }
.io-footer a:hover, .io-footer a:focus-visible, .download-animation:hover, .download-animation:focus-visible { border-color: var(--accent); }
.evidence-key { margin: 0 0 2.5rem; border: 1px solid var(--line); background: linear-gradient(135deg, rgba(156,140,255,.07), transparent 46%), var(--panel); }
.evidence-key-head { display: grid; grid-template-columns: minmax(0, 1fr) minmax(280px, .8fr); gap: 2rem; align-items: end; padding: 1.2rem 1.3rem; border-bottom: 1px solid var(--line); }
.evidence-key-head .eyebrow { margin-bottom: .6rem; }
.evidence-key-head h2 { margin: 0; font: 700 clamp(1.6rem, 3vw, 2.8rem)/.98 Arial, Helvetica, sans-serif; letter-spacing: -.06em; }
.evidence-key-intro { max-width: 500px; margin: 0; color: var(--muted); font: .72rem/1.55 Arial, Helvetica, sans-serif; }
.evidence-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: var(--line); }
.evidence-item { min-height: 185px; padding: 1.15rem 1.25rem; background: var(--panel); }
.evidence-item h3 { margin: .65rem 0 .5rem; font: 600 1rem/1.1 Arial, Helvetica, sans-serif; }
.evidence-item p { margin: 0; color: #c8cac4; font: .74rem/1.5 Arial, Helvetica, sans-serif; }
.evidence-item small { display: block; margin-top: .75rem; color: var(--muted); font-size: .59rem; line-height: 1.45; }
.evidence-item a { color: var(--accent); }
.evidence-token { color: var(--accent); font-size: .56rem; letter-spacing: .12em; }
.evidence-poster { background: linear-gradient(135deg, rgba(215,199,167,.06), transparent 70%), var(--panel); }
.evidence-pdf { background: linear-gradient(135deg, rgba(121,226,164,.06), transparent 70%), var(--panel); }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.stat { padding: 1rem 0; border-right: 1px solid var(--line); }
.stat:last-child { border-right: 0; padding-left: 1rem; }
.stat:not(:first-child) { padding-left: 1rem; }
.stat strong { display: block; font-size: 1.4rem; color: var(--ink); }
.stat span { color: var(--muted); font-size: .65rem; text-transform: uppercase; letter-spacing: .08em; }
.route-brief { margin: 2.5rem 0 1rem; border: 1px solid var(--line); background: var(--panel); display: grid; grid-template-columns: 1fr 1fr 1fr; }
.route-cell { padding: 1.2rem 1.3rem; min-height: 125px; border-right: 1px solid var(--line); }
.route-cell:last-child { border-right: 0; }
.route-label, .detail-label, .cell-label, .result-note span { display: block; color: var(--muted); font-size: .62rem; letter-spacing: .1em; text-transform: uppercase; margin-bottom: .75rem; }
.route-value { margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 1rem; line-height: 1.45; }
.route-value strong { color: var(--accent); }
.how-to { margin: 0 0 3.5rem; border: 1px solid var(--line); background: linear-gradient(120deg, rgba(121,226,164,.06), transparent 46%), var(--panel); }
.how-to-head { display: grid; grid-template-columns: minmax(0, 1fr) minmax(260px, .8fr); gap: 2rem; align-items: end; padding: 1.2rem 1.3rem; border-bottom: 1px solid var(--line); }
.how-to-head .eyebrow { margin-bottom: .6rem; }
.how-to-head h2 { margin: 0; font: 700 clamp(1.6rem, 3vw, 2.8rem)/.98 Arial, Helvetica, sans-serif; letter-spacing: -.06em; }
.how-to-head p:not(.eyebrow) { margin: .65rem 0 0; color: #c8cac4; font: .86rem/1.5 Arial, Helvetica, sans-serif; }
.how-to-head > p { max-width: 420px; color: var(--muted); font-size: .63rem; line-height: 1.55; }
.how-to-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: var(--line); }
.how-to-step { min-height: 180px; padding: 1.15rem 1.25rem; background: var(--panel); }
.how-to-step > span { color: var(--accent); font-size: .58rem; letter-spacing: .12em; }
.how-to-step h3 { margin: .65rem 0 .5rem; color: var(--ink); font: 600 1rem/1.1 Arial, Helvetica, sans-serif; }
.how-to-step p { margin: 0; color: #c8cac4; font: .75rem/1.5 Arial, Helvetica, sans-serif; }
.how-to-step code { display: block; margin-top: .8rem; padding: .55rem; border: 1px solid var(--line); color: var(--ink); background: #080a09; font: .58rem/1.45 "IBM Plex Mono", monospace; white-space: normal; }
.observation-strip { margin: 0 0 3.5rem; border: 1px solid var(--line); background: linear-gradient(120deg, rgba(138,164,255,.06), transparent 48%), var(--panel); }
.observation-head { display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; padding: 1rem 1.2rem; border-bottom: 1px solid var(--line); }
.observation-head p { margin: 0; color: var(--muted); font-size: .62rem; line-height: 1.45; }
.observation-head strong { color: var(--ink); font-weight: 500; }
.observation-grid { display: grid; grid-template-columns: repeat(4, 1fr); }
.observation-cell { min-height: 104px; padding: 1rem 1.2rem; border-right: 1px solid var(--line); }
.observation-cell:last-child { border-right: 0; }
.observation-cell strong { display: block; color: var(--ink); font: 500 .78rem/1.4 Arial, Helvetica, sans-serif; }
.observation-cell small { display: block; margin-top: .4rem; color: var(--muted); font-size: .58rem; line-height: 1.45; }
.observation-cell a { color: var(--accent); }
.recognition-handoff { display: grid; grid-template-columns: 1.15fr 1fr 1fr; gap: 1px; margin: 0 1.2rem; border: 1px solid var(--line); background: var(--line); }
.recognition-handoff > div { min-width: 0; min-height: 112px; padding: .85rem; background: #0b0e0d; }
.recognition-handoff strong { display: block; color: var(--ink); font: 500 .7rem/1.35 Arial, Helvetica, sans-serif; }
.recognition-handoff p { margin: .45rem 0 0; color: var(--muted); font: .59rem/1.45 Arial, Helvetica, sans-serif; }
.observation-map { margin: 0; padding: .8rem 1.2rem; border-top: 1px solid var(--line); color: #d6d7d0; font: .62rem/1.55 "IBM Plex Mono", monospace; }
.observation-map span { margin-right: .75rem; color: var(--accent); font-size: .54rem; letter-spacing: .08em; }
.observation-map small { display: block; margin-top: .35rem; color: var(--muted); font: .58rem/1.45 Arial, Helvetica, sans-serif; }
.prompt-lab { margin: 0 0 3.5rem; border: 1px solid var(--line); background: linear-gradient(135deg, rgba(156,140,255,.08), transparent 45%), var(--panel); }
.prompt-lab-head { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(220px, .65fr); gap: 2rem; padding: 1.35rem; border-bottom: 1px solid var(--line); }
.prompt-lab-head .eyebrow { margin-bottom: .6rem; }
.prompt-lab-head h2 { margin: 0; max-width: 720px; font: 700 clamp(1.7rem, 3.6vw, 3.2rem)/.98 Arial, Helvetica, sans-serif; letter-spacing: -.06em; }
.prompt-lab-head p:not(.eyebrow) { max-width: 720px; margin: .8rem 0 0; color: #c8cac4; font: .92rem/1.55 Arial, Helvetica, sans-serif; }
.prompt-lab-order { align-self: end; border-left: 1px solid var(--line); padding-left: 1rem; color: var(--muted); font-size: .62rem; line-height: 1.55; text-transform: uppercase; }
.prompt-lab-order span { display: block; margin-bottom: .35rem; color: var(--accent); letter-spacing: .1em; }
.prompt-lab-order strong { display: block; color: var(--ink); font-size: .72rem; }
.prompt-lab-order small { display: block; max-width: 240px; margin-top: .65rem; color: var(--muted); font-size: .58rem; line-height: 1.45; text-transform: none; }
.prompt-lab-grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(230px, .6fr); gap: 1px; background: var(--line); }
.prompt-editor, .route-readout { min-width: 0; padding: 1.2rem; background: var(--panel); }
.motion-prompt { display: block; width: 100%; min-height: 185px; resize: vertical; border: 1px solid var(--line); background: #080a09; color: var(--ink); padding: .8rem; font: .7rem/1.55 "IBM Plex Mono", monospace; }
.motion-prompt:focus, .route-readout select:focus, .tuning-grid select:focus, .tuning-grid input:focus { outline: 2px solid var(--accent); outline-offset: 2px; }
.prompt-actions { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .65rem; }
.prompt-actions button { padding: .42rem .55rem; font-size: .58rem; }
.prompt-actions button:last-child { color: var(--accent); }
.copy-status { min-height: 1.1rem; margin: .65rem 0 0; color: var(--muted); font-size: .61rem; line-height: 1.4; }
.evidence-status { margin-top: .8rem; padding: .7rem; border: 1px solid color-mix(in srgb, var(--accent) 42%, var(--line)); background: rgba(156,140,255,.05); }
.evidence-status strong { display: block; margin-top: .35rem; color: var(--ink); font-size: .64rem; font-weight: 500; }
.evidence-status small { display: block; margin-top: .35rem; color: var(--muted); font-size: .56rem; line-height: 1.45; }
.route-readout { background: #0b0e0d; }
.route-readout select, .tuning-grid select { width: 100%; border: 1px solid var(--line); background: #080a09; color: var(--ink); padding: .55rem; font-size: .64rem; }
.route-readout p { margin: .9rem 0 0; color: var(--muted); font-size: .61rem; line-height: 1.45; }
.route-readout p span { display: block; margin-bottom: .25rem; color: var(--accent); font-size: .52rem; letter-spacing: .1em; }
.route-readout p strong { display: block; color: #d9dad3; font-weight: 500; }
.route-preview { margin: 1rem 0 0; padding-top: .75rem; border-top: 1px solid var(--line); }
.route-preview .detail-label { margin-bottom: .45rem; }
.route-preview img { display: block; width: 100%; aspect-ratio: 900 / 302; object-fit: contain; border: 1px solid var(--line); background: #080a09; }
.route-preview img + img { margin-top: .4rem; }
.route-preview figcaption { margin-top: .45rem; color: var(--muted); font-size: .56rem; line-height: 1.4; }
.route-gif-link { display: inline-block; margin-top: 1rem; color: var(--accent); font-size: .62rem; text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--accent) 55%, transparent); }
.tuning-panel { padding: 1.2rem; border-top: 1px solid var(--line); }
.tuning-head { display: flex; justify-content: space-between; gap: 1rem; align-items: start; }
.tuning-head p { max-width: 760px; margin: -.35rem 0 .9rem; color: var(--muted); font-size: .63rem; line-height: 1.5; }
.tuning-boundary { color: var(--accent); border: 1px solid color-mix(in srgb, var(--accent) 45%, transparent); padding: .3rem .4rem; font-size: .55rem; text-transform: uppercase; white-space: nowrap; }
.recipe-row { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem; margin: .1rem 0 .9rem; padding-bottom: .8rem; border-bottom: 1px solid var(--line); }
.recipe-row .detail-label { margin: 0 .35rem 0 0; }
.recipe-row button { padding: .42rem .55rem; font-size: .57rem; }
.tuning-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .7rem; }
.tuning-grid label { display: grid; gap: .35rem; color: var(--muted); font-size: .58rem; }
.tuning-grid input[type="range"] { width: 100%; accent-color: var(--accent); }
.tuning-grid input[type="color"] { width: 100%; height: 2rem; padding: .15rem; border: 1px solid var(--line); background: #080a09; }
.tuning-grid output { color: var(--ink); font-size: .56rem; }
.tuning-grid .check-label { display: flex; align-items: center; gap: .45rem; padding-top: 1.35rem; }
.tuning-grid .check-label input { accent-color: var(--accent); }
.request-summary { display: flex; flex-wrap: wrap; gap: .5rem .8rem; align-items: baseline; margin-top: 1rem; padding: .7rem; border: 1px solid var(--line); color: var(--muted); font-size: .61rem; }
.request-summary span { color: var(--accent); font-size: .53rem; letter-spacing: .1em; }
.request-summary strong { color: var(--ink); font-weight: 500; }
.static-boundary { margin: .75rem 0 0; color: var(--muted); font-size: .6rem; line-height: 1.5; }
.static-boundary strong { color: #d9dad3; }
.static-boundary code { color: var(--ink); }
.static-boundary a { color: var(--accent); }
.export-details { margin-top: .8rem; border-top: 1px solid var(--line); padding-top: .7rem; color: var(--muted); font-size: .6rem; line-height: 1.5; }
.export-details summary { cursor: pointer; color: var(--accent); }
.export-details pre { overflow-x: auto; margin: .7rem 0 .4rem; padding: .7rem; border: 1px solid var(--line); background: #080a09; color: var(--ink); font: .58rem/1.55 "IBM Plex Mono", monospace; }
.route-export-command { margin-top: .8rem; padding: .75rem; border: 1px solid color-mix(in srgb, var(--accent) 42%, var(--line)); background: rgba(156,140,255,.04); }
.route-export-command pre { overflow-x: auto; margin: .45rem 0 .55rem; padding: .6rem; border: 1px solid var(--line); background: #080a09; color: var(--ink); font: .58rem/1.5 "IBM Plex Mono", monospace; white-space: pre-wrap; word-break: break-word; }
.route-export-command button { font-size: .56rem; padding: .35rem .5rem; }
.route-export-command small { display: block; margin-top: .45rem; color: var(--muted); font-size: .52rem; line-height: 1.4; }
.export-plan { margin: .55rem 0; color: #c8cac4; font: .61rem/1.5 "IBM Plex Mono", monospace; }
.export-approval-state { margin: .45rem 0; color: var(--accent); font: .58rem/1.4 "IBM Plex Mono", monospace; }
.export-approval-state[data-state="declined"] { color: #ff8b82; }
.route-export-command button:disabled { cursor: not-allowed; opacity: .48; }
.export-details p { margin: .4rem 0 0; }
.controls { display: flex; gap: .7rem; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 1.1rem; }
.controls-copy { color: var(--muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; }
.controls-actions { display: flex; gap: .5rem; flex-wrap: wrap; }
.filter { min-width: 240px; color: var(--ink); background: var(--panel); border: 1px solid var(--line); padding: .7rem .8rem; }
.filter:focus { outline: 2px solid var(--accent); outline-offset: 2px; }
.theme-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; padding-bottom: 5rem; }
.theme-card { border: 1px solid var(--line); background: linear-gradient(155deg, rgba(255,255,255,.025), transparent 35%), var(--panel); min-width: 0; overflow: hidden; transition: border-color .2s ease, box-shadow .2s ease; }
.theme-card.route-selected { border-color: color-mix(in srgb, var(--accent) 75%, var(--line)); box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 28%, transparent); }
.theme-card.route-selected .card-head { background: color-mix(in srgb, var(--accent) 8%, transparent); }
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
.cell-foot { position: absolute; z-index: 5; bottom: .65rem; left: .7rem; right: .7rem; color: rgba(242,241,233,.55); font-size: .52rem; text-transform: uppercase; letter-spacing: .07em; pointer-events: none; }
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
 .intent { margin: 0 0 .7rem; color: #d6d7d0; font-family: Arial, Helvetica, sans-serif; font-size: .82rem; line-height: 1.48; }
 .trajectory-note { margin: 0 0 1rem; padding-left: .65rem; border-left: 2px solid var(--accent); color: #bfc2bb; font: .68rem/1.45 Arial, Helvetica, sans-serif; }
 .trajectory-note span { display: block; margin-bottom: .25rem; color: var(--accent); font: .56rem/1.2 "IBM Plex Mono", monospace; letter-spacing: .08em; }
 .construction-note { margin: 0 0 1rem; padding: .55rem .65rem; border: 1px solid color-mix(in srgb, var(--accent) 35%, var(--line)); color: #c9cbc4; font: .63rem/1.45 "IBM Plex Mono", monospace; }
 .construction-note span { display: block; margin-bottom: .25rem; color: var(--accent); font-size: .54rem; letter-spacing: .08em; }
 .construction-note strong { display: block; color: #f2f1e9; font-weight: 600; }
 .construction-note small { display: block; margin-top: .25rem; color: var(--muted); font-size: .58rem; }
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
@media (max-width: 1050px) { .theme-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .hero { gap: 2rem; } }
@media (max-width: 720px) { .shell { width: min(100% - 28px, 640px); } .topbar { font-size: .62rem; } .truth-bar span { padding-left: 0; border-left: 0; } .hero { grid-template-columns: 1fr; padding-top: 4rem; } .hero-side { border-left: 0; padding-left: 0; grid-template-columns: 1fr 1fr; align-items: end; } .io-heading { display: block; } .io-badge { border-left: 0; border-top: 1px solid var(--line); margin-top: 1rem; padding: .8rem 0 0; } .io-flow { grid-template-columns: 1fr; } .io-arrow { transform: rotate(90deg); justify-self: center; } .io-footer { display: block; } .io-footer a { display: inline-block; margin: .6rem .8rem 0 0; } .route-brief { grid-template-columns: 1fr; } .route-cell { border-right: 0; border-bottom: 1px solid var(--line); } .route-cell:last-child { border-bottom: 0; } .how-to-head { display: block; } .how-to-head > p { margin-top: .8rem; } .how-to-grid { grid-template-columns: 1fr; } .how-to-step { min-height: 0; } .observation-head { display: block; } .observation-head p { margin-top: .4rem; } .observation-grid { grid-template-columns: 1fr 1fr; } .observation-cell:nth-child(2) { border-right: 0; } .observation-cell:nth-child(-n + 2) { border-bottom: 1px solid var(--line); } .observation-cell:nth-child(3) { border-right: 1px solid var(--line); } .observation-cell:last-child { border-right: 0; } .recognition-handoff { grid-template-columns: 1fr; margin: 0 .8rem; } .workflow-guide-head { display: block; } .guide-live { margin-top: 1rem; border-left: 0; border-top: 1px solid var(--line); padding: .8rem 0 0; } .workflow-rail, .workflow-rules, .state-ladder-items { grid-template-columns: 1fr; } .workflow-rail a { min-height: 0; } .workflow-rules article, .state-card { min-height: 0; } .state-ladder-head { display: block; } .state-ladder-head p { margin-top: .55rem; } .theme-grid { grid-template-columns: 1fr; } .footer { display: block; } .footer p + p { margin-top: 1rem; } }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
'''


MOTION_CSS = r'''
.motion-output { display: grid; grid-template-rows: 1fr auto; min-height: 205px; background: var(--stage-bg); }
.motion-what-changes { margin: .65rem .65rem 0; padding: .45rem .55rem; border-left: 2px solid var(--accent); color: #c8cac4; font-size: .57rem; line-height: 1.35; }
.motion-what-changes span { display: block; margin-bottom: .16rem; color: var(--accent); font: .5rem/1.1 "IBM Plex Mono", monospace; letter-spacing: .08em; text-transform: uppercase; }
.motion-what-changes strong { color: var(--ink); font-weight: 700; }
.motion-what-changes small { display: block; margin-top: .14rem; color: var(--muted); font-size: .52rem; }
.motion-route-banner { margin: .65rem .65rem 0; padding: .5rem .55rem; border: 1px solid color-mix(in srgb, var(--accent) 58%, var(--line)); background: color-mix(in srgb, var(--accent) 8%, transparent); color: #c8cac4; font-size: .58rem; line-height: 1.35; }
.motion-route-banner span { display: block; margin-bottom: .16rem; color: var(--accent); font: .5rem/1.1 "IBM Plex Mono", monospace; letter-spacing: .08em; text-transform: uppercase; }
.motion-route-banner strong { display: block; color: var(--ink); font-weight: 700; }
.motion-route-banner small { display: block; margin-top: .14rem; color: var(--muted); font-size: .52rem; }
.motion-stage { position: relative; width: 100%; aspect-ratio: 900 / 302; min-height: 145px; display: grid; place-items: center; isolation: isolate; overflow: hidden; --motion-progress: 0; --motion-x: 0; --motion-y: 0; --motion-scale: .72; --motion-rotate: 0deg; --motion-opacity: .05; }
.motion-stage::after { content: ""; position: absolute; z-index: 2; left: 16%; right: 16%; top: 50%; height: 1px; pointer-events: none; opacity: 0; background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 70%, transparent), transparent); transform: translateX(var(--preview-entry-x, 0)); transition: opacity .2s ease, transform .25s ease; }
.motion-stage[data-direction="left-to-right"]::after, .motion-stage[data-direction="right-to-left"]::after { opacity: .16; }
.motion-stage[data-direction="right-to-left"]::after { --preview-entry-x: 8%; }
.motion-stage[data-direction="left-to-right"]::after { --preview-entry-x: -8%; }
.growth-gif { position: relative; z-index: 3; width: 100%; height: 100%; object-fit: contain; image-rendering: auto; }
.motion-canonical, .motion-freeze { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; }
.motion-canonical { z-index: 4; }
.motion-freeze { z-index: 5; }
.motion-loading { position: absolute; z-index: 6; inset: auto 0 2.15rem; text-align: center; color: var(--muted); font-size: .52rem; letter-spacing: .06em; text-transform: uppercase; }
.motion-effect { position: absolute; z-index: 1; pointer-events: none; opacity: 0; will-change: transform, opacity, background-position; }
.motion-effect-a { inset: 0; }
.motion-effect-b { inset: 12%; }
.motion-effect-c { inset: 20%; }
.motion-phase { position: absolute; z-index: 5; bottom: 2.15rem; right: .65rem; color: rgba(242,241,233,.72); font-size: .52rem; text-transform: uppercase; letter-spacing: .08em; }
.motion-beat { position: absolute; z-index: 5; top: 2.15rem; right: .65rem; color: color-mix(in srgb, var(--accent) 82%, var(--ink)); font-size: .48rem; text-transform: uppercase; letter-spacing: .08em; }
.pattern-grid .motion-effect-a { background-image: linear-gradient(rgba(138,164,255,.2) 1px, transparent 1px), linear-gradient(90deg, rgba(138,164,255,.2) 1px, transparent 1px); background-size: 20px 20px; opacity: calc(var(--motion-progress) * .55); transform: translate3d(calc((1 - var(--motion-progress)) * -18%), 0, 0); }
.pattern-quiet .motion-effect-a { background: radial-gradient(circle at 50% 58%, color-mix(in srgb, var(--accent) 24%, transparent), transparent 65%); opacity: calc(var(--motion-progress) * .66); transform: scale(calc(.7 + var(--motion-progress) * .32)); }
.pattern-scan .motion-effect-a { background: repeating-linear-gradient(0deg, transparent 0 6px, color-mix(in srgb, var(--accent) 20%, transparent) 7px 8px); opacity: calc(var(--motion-progress) * .68); transform: translateY(calc((1 - var(--motion-progress)) * -35%)); }
.pattern-field .motion-effect-a { background: radial-gradient(circle at 20% 30%, var(--accent) 0 1px, transparent 2px), radial-gradient(circle at 76% 65%, var(--accent) 0 1px, transparent 2px), radial-gradient(circle at 48% 20%, #fff 0 1px, transparent 2px), radial-gradient(circle at 88% 38%, var(--accent) 0 1px, transparent 2px); background-size: 48px 42px, 61px 58px, 73px 71px, 54px 63px; opacity: calc((1 - var(--motion-progress)) * .58); transform: translate3d(calc((1 - var(--motion-progress)) * -12%), calc((1 - var(--motion-progress)) * 16%), 0) scale(calc(1.2 - var(--motion-progress) * .22)); }
.pattern-field .motion-effect-b { border: 1px solid color-mix(in srgb, var(--accent) 56%, transparent); border-radius: 50%; opacity: calc((1 - var(--motion-progress)) * .46); transform: scale(calc(1.35 - var(--motion-progress) * .45)); }
.pattern-ring .motion-effect-a { inset: 14%; border: 1px solid color-mix(in srgb, var(--accent) 66%, transparent); border-radius: 50%; opacity: calc(var(--motion-progress) * .74); transform: rotate(calc(var(--motion-progress) * 150deg)) scale(calc(.45 + var(--motion-progress) * .55)); }
.pattern-ring .motion-effect-b { inset: 27%; border: 1px dashed color-mix(in srgb, var(--accent) 48%, transparent); border-radius: 50%; opacity: calc(var(--motion-progress) * .68); transform: rotate(calc(var(--motion-progress) * -210deg)); }
.pattern-shield .motion-effect-a { clip-path: polygon(50% 3%, 92% 18%, 84% 72%, 50% 98%, 16% 72%, 8% 18%); border: 1px solid color-mix(in srgb, var(--accent) 68%, transparent); background: color-mix(in srgb, var(--accent) 8%, transparent); opacity: calc(var(--motion-progress) * .65); transform: scale(calc(.72 + var(--motion-progress) * .28)); }
.pattern-shield .motion-effect-b { inset: 25% 12%; border-top: 1px solid var(--accent); border-bottom: 1px solid var(--accent); opacity: calc(var(--motion-progress) * .7); transform: translateY(calc((1 - var(--motion-progress)) * 40%)); }
.pattern-burst .motion-effect-a { inset: 36% 9%; border-top: 1px solid var(--accent); border-bottom: 1px solid var(--accent); opacity: calc(var(--motion-progress) * .72); transform: rotate(-20deg) scaleX(calc(.28 + var(--motion-progress) * .72)); }
.pattern-burst .motion-effect-b { inset: 9% 36%; border-left: 1px solid var(--accent); border-right: 1px solid var(--accent); opacity: calc(var(--motion-progress) * .58); transform: rotate(-20deg) scaleY(calc(.25 + var(--motion-progress) * .75)); }
.pattern-track .motion-effect-a { inset: 0; width: 35%; background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 80%, transparent), transparent); opacity: calc(var(--motion-progress) * .75); transform: translateX(calc((var(--motion-progress) * 180% - 80%))); }
.pattern-track .motion-effect-b { top: 48%; left: 0; right: 0; height: 1px; background: var(--accent); opacity: calc(var(--motion-progress) * .55); box-shadow: 0 -34px 0 color-mix(in srgb, var(--accent) 25%, transparent), 0 34px 0 color-mix(in srgb, var(--accent) 25%, transparent); }
.pattern-speed .motion-effect-a { inset: 28% 0; background: repeating-linear-gradient(165deg, transparent 0 12px, color-mix(in srgb, var(--accent) 64%, transparent) 13px 14px); opacity: calc((1 - var(--motion-progress)) * .75); transform: translateX(calc((1 - var(--motion-progress)) * -24%)); }
.pattern-speed .motion-effect-b { inset: 42% -20%; height: 1px; background: var(--accent); opacity: calc((1 - var(--motion-progress)) * .85); transform: rotate(-14deg) translateX(calc((1 - var(--motion-progress)) * -28%)); }
.pattern-curtain .motion-effect-a { inset: 0; background: linear-gradient(90deg, #000 0 43%, transparent 44% 56%, #000 57%); opacity: calc((1 - var(--motion-progress)) * .82); transform: scaleX(calc(1 - var(--motion-progress) * .5)); }
.pattern-curtain .motion-effect-b { inset: 0; background: radial-gradient(ellipse at center, color-mix(in srgb, var(--accent) 28%, transparent), transparent 65%); opacity: calc(var(--motion-progress) * .65); }
.pattern-wave .motion-effect-a { inset: 0; background: repeating-radial-gradient(ellipse at 20% 80%, transparent 0 16px, color-mix(in srgb, var(--accent) 28%, transparent) 17px 18px); opacity: calc(var(--motion-progress) * .55); transform: rotate(calc(-9deg + var(--motion-progress) * 13deg)) scale(calc(1.3 - var(--motion-progress) * .08)); }
.pattern-wave .motion-effect-b { inset: 0; background: linear-gradient(150deg, transparent 20%, color-mix(in srgb, var(--accent) 12%, transparent), transparent 75%); opacity: calc(var(--motion-progress) * .6); transform: translateX(calc((1 - var(--motion-progress)) * -12%)); }
.pattern-orbit .motion-effect-a { inset: 14%; border: 1px dotted color-mix(in srgb, var(--accent) 76%, transparent); border-radius: 50%; opacity: calc(var(--motion-progress) * .7); transform: rotate(calc(var(--motion-progress) * 360deg)); }
.pattern-orbit .motion-effect-b { inset: 29%; border: 1px solid color-mix(in srgb, var(--accent) 48%, transparent); border-radius: 50%; opacity: calc(var(--motion-progress) * .52); transform: rotate(calc(var(--motion-progress) * -260deg)); }
.pattern-orbit .motion-effect-c { width: 7px; height: 7px; top: 16%; left: 50%; border-radius: 50%; background: var(--accent); box-shadow: 0 0 13px var(--accent); opacity: calc(var(--motion-progress) * .9); transform: rotate(calc(var(--motion-progress) * 360deg)); transform-origin: 0 190%; }
.pattern-plain .motion-effect-a { background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 24%, transparent), transparent); opacity: calc(var(--motion-progress) * .55); transform: scale(calc(.7 + var(--motion-progress) * .3)); }
.growth-storyboard { position: absolute; z-index: 6; left: .65rem; right: .65rem; bottom: .58rem; display: flex; gap: .18rem; align-items: center; pointer-events: none; }
.growth-storyboard span { padding: .18rem .22rem; color: rgba(242,241,233,.48); border: 1px solid transparent; font-size: .43rem; line-height: 1; letter-spacing: .03em; text-transform: uppercase; white-space: nowrap; }
.growth-storyboard span.is-active { color: var(--ink); border-color: color-mix(in srgb, var(--accent) 72%, transparent); background: color-mix(in srgb, var(--accent) 16%, #000); }
.motion-controls { display: flex; align-items: center; gap: .3rem; padding: .45rem .55rem .55rem; background: color-mix(in srgb, #000 20%, transparent); }
.motion-controls button { padding: .3rem .42rem; font-size: .55rem; }
.download-animation { display: block; padding: .45rem .55rem .6rem; background: color-mix(in srgb, #000 20%, transparent); font-size: .57rem; }
.motion-timeline { flex: 1; min-width: 26px; height: 2px; background: color-mix(in srgb, var(--accent) 22%, transparent); overflow: hidden; }
.motion-timeline span { display: block; width: 0; height: 100%; background: var(--accent); transition: width .08s linear; }
.motion-time { color: rgba(242,241,233,.65); font-size: .52rem; min-width: 2.1rem; text-align: right; }
.motion-seek-label { display: block; padding: .42rem .55rem .5rem; color: var(--muted); background: color-mix(in srgb, #000 14%, transparent); font-size: .48rem; line-height: 1.3; letter-spacing: .04em; text-transform: uppercase; }
.motion-seek-label > span { display: block; margin-bottom: .22rem; color: var(--accent); }
.motion-seek-label input { display: block; width: 100%; margin: 0; accent-color: var(--accent); }
.motion-seek-label small { display: block; margin-top: .2rem; color: var(--muted); font-size: .48rem; letter-spacing: 0; text-transform: none; }
body[data-motion="paused"] .motion-stage { outline: 1px solid color-mix(in srgb, var(--accent) 42%, transparent); outline-offset: -1px; }
body[data-motion="reduced"] .motion-effect { display: none; }
body[data-motion="reduced"] .growth-gif { filter: none; }
.motion-stage[data-playback="paused"] .motion-effect,
.motion-stage[data-playback="loading"] .motion-effect { animation-play-state: paused; }
body[data-preview-background="dark"] .result-cell { background: #0b0d12 !important; }
body[data-preview-background="solid"] .result-cell { background: var(--preview-solid-bg, #0b0d12) !important; }
body[data-preview-background="transparent"] .result-cell { background: transparent !important; }
body[data-particles="off"] .motion-effect { display: none; }
body[data-motion="reduced"] .motion-stage::after { display: none; }
@media (max-width: 720px) { .motion-stage { min-height: 155px; } .motion-controls { flex-wrap: wrap; } .motion-timeline { flex-basis: 100%; order: 5; } }
@media (max-width: 720px) {
  .prompt-lab-head, .prompt-lab-grid { grid-template-columns: 1fr; }
  .prompt-lab-order { border-left: 0; border-top: 1px solid var(--line); padding: .9rem 0 0; }
  .tuning-head { flex-wrap: wrap; }
  .tuning-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 420px) {
  .tuning-grid { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  body[data-motion="auto"] .growth-gif,
  body[data-motion="reduced"] .growth-gif { display: none; }
  body[data-motion="auto"] .motion-canonical[hidden],
  body[data-motion="reduced"] .motion-canonical[hidden] { display: block !important; }
  body[data-motion="running"] .growth-gif { display: block; }
  body[data-motion="running"] .motion-canonical { display: none; }
}
'''


JS = r'''(() => {
  "use strict";
  const body = document.body;
  body.dataset.runtimeState = "booting";
  body.dataset.runtimeContract = "showcase-controls";
  const cards = [...document.querySelectorAll(".theme-card")];
  const stages = [...document.querySelectorAll("[data-motion-card]")];
  const filter = document.querySelector("[data-filter]");
  const status = document.querySelector("[data-filter-status]");
  const guideLive = document.querySelector("[data-guide-live]");
  const guideDetail = document.querySelector("[data-guide-detail]");
  const guideStatus = document.querySelector("[data-guide-status]");
  const guideSteps = [...document.querySelectorAll("[data-guide-step]")];
  const guideCopy = {
    source: {
      live: "01 / SOURCE · start here",
      detail: "Confirm the supplied image and the parts that must remain unchanged.",
      status: "Current session: identity is locked to the supplied source; no route or file change has been made."
    },
    theme: {
      live: "02 / THEME · choose a route",
      detail: "Select the design intention; the route must change the foreground reveal, not only the background.",
      status: "Theme selected: the route changes the identity-bearing construction path while the canonical source handoff remains fixed."
    },
    tune: {
      live: "03 / TUNE · make it measurable",
      detail: "Set background, duration, speed, direction, particles, and motion policy in words the exporter can reproduce.",
      status: "Preview only: controls changed the local shell and request summary; no media file has been written."
    },
    bake: {
      live: "04 / BAKE · run the exporter",
      detail: "Copy the command, run it from the project root, then inspect the generated GIF, checkpoints, manifest, and PDF.",
      status: "Command prepared: the browser copied or displayed an export command; it did not execute the shell or claim a new bake."
    },
    verify: {
      live: "05 / VERIFY · inspect evidence",
      detail: "Confirm source identity, final-frame equality, runtime behavior, accessibility, fingerprints, and human review.",
      status: "Verification remains an evidence step: browser interaction alone cannot promote a preview or baked file to verified."
    }
  };
  let guideState = "source";
  function setGuide(next) {
    if (!guideCopy[next]) return;
    guideState = next;
    const copy = guideCopy[next];
    const currentIndex = guideSteps.findIndex((step) => step.dataset.guideStep === next);
    if (guideLive) guideLive.textContent = copy.live;
    if (guideDetail) guideDetail.textContent = copy.detail;
    if (guideStatus) guideStatus.textContent = copy.status;
    guideSteps.forEach((step, index) => {
      step.classList.toggle("is-current", index === currentIndex);
      step.classList.toggle("is-complete", currentIndex > index);
      const state = step.querySelector("[data-guide-step-status]");
      if (state) state.textContent = index < currentIndex ? "complete" : index === currentIndex ? "current" : "next";
    });
  }
  const motionPreference = window.matchMedia?.("(prefers-reduced-motion: reduce)");
  const systemPrefersReduced = () => Boolean(motionPreference?.matches);
  const CANONICAL_HANDOFF_PROGRESS = 1;
  const STAGE_ORDER = ["blank", "spark", "arc", "bar", "monogram", "wordmark", "canonical"];
  const DEFAULT_STAGE_PROGRESS = Object.freeze({ blank: 0, spark: .16, arc: .33, bar: .47, monogram: .64, wordmark: .985, canonical: 1 });
  const presets = {
    grid: [-28, 16, -6, .78], quiet: [0, 10, 0, .9], scan: [-26, 0, 0, .8],
    field: [-10, 22, -8, .72], ring: [0, 0, -22, .78], shield: [0, 24, 0, .74],
    burst: [0, 0, -18, .76], track: [-42, 0, 0, .8], speed: [-48, 6, -10, .7],
    curtain: [0, 0, 0, .84], wave: [16, 22, 8, .76], orbit: [0, -16, 16, .78],
    plain: [0, 12, 0, .86]
  };
  const players = [];
  let motion = systemPrefersReduced() ? "reduced" : "running";
  let motionOverride = null;
  const tuning = { duration: 1.8, speed: 1, direction: "radial", background: "theme", color: "#0B0D12", particles: true, surface: "brand identity" };
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const ease = (value, effect) => {
    const p = clamp(value, 0, 1);
    if (effect === "speed" || effect === "burst") return 1 - Math.pow(1 - p, 3);
    if (effect === "quiet" || effect === "curtain") return p * p * (3 - 2 * p);
    if (effect === "wave" || effect === "orbit") return p < .78 ? p / .78 : 1 - Math.pow((1 - p) / .22, 2) * .035;
    return 1 - Math.pow(1 - p, 2.4);
  };
  function readStageProgress(stage) {
    let parsed = {};
    try { parsed = JSON.parse(stage.dataset.stageProgress || "{}"); } catch (error) { parsed = {}; }
    const result = { blank: 0 };
    let previous = 0;
    STAGE_ORDER.slice(1, -1).forEach((name) => {
      const candidate = Number(parsed[name]);
      const fallback = DEFAULT_STAGE_PROGRESS[name];
      const value = Number.isFinite(candidate) ? clamp(candidate, previous, 1) : fallback;
      result[name] = Math.max(previous, value);
      previous = result[name];
    });
    result.canonical = 1;
    return result;
  }
  function phaseFor(progress, stageProgress = DEFAULT_STAGE_PROGRESS) {
    const p = clamp(progress, 0, 1);
    if (p <= stageProgress.blank) return "blank";
    for (const name of STAGE_ORDER.slice(1, -1)) {
      if (p <= stageProgress[name]) return name;
    }
    return p >= stageProgress.canonical ? "canonical" : "wordmark";
  }
  function beatFor(player, progress) {
    const beats = player.beats || [];
    if (!beats.length) return "";
    if (progress < .34) return beats[0] || "entry";
    if (progress < .68) return beats[1] || beats[0] || "build";
    return beats[2] || beats[beats.length - 1] || "settle";
  }
  function render(player, progress) {
    const p = clamp(progress, 0, 1);
    const phase = phaseFor(p, player.stageProgress);
    player.stage.style.setProperty("--motion-progress", p.toFixed(4));
    player.stage.dataset.state = phase;
    if (player.phase) player.phase.textContent = phase;
    if (player.beat) player.beat.textContent = beatFor(player, p);
    player.stage.querySelectorAll("[data-growth-stage]").forEach((node) => {
      node.classList.toggle("is-active", node.dataset.growthStage === phase);
    });
    if (player.progress) player.progress.style.width = `${p * 100}%`;
    if (player.time) player.time.textContent = `${(p * player.duration / 1000).toFixed(1)}s`;
    if (player.seek && document.activeElement !== player.seek) player.seek.value = p.toFixed(3);
  }
  function showReadyGif(player) {
    if (!player.gif) return;
    player.gif.hidden = false;
    player.stage.dataset.playback = player.playing ? "playing" : "ready";
    if (player.canonical) player.canonical.hidden = true;
    if (player.poster) player.poster.hidden = true;
    if (player.loading) player.loading.hidden = true;
  }
  function showGif(player, restart = false) {
    if (!player.gif) return Promise.resolve(false);
    const currentSource = player.gif.dataset.mediaSrc || "";
    if (!restart && player.gif.dataset.loaded === "true" && currentSource === player.src) {
      showReadyGif(player);
      return Promise.resolve(true);
    }
    const token = (player.loadToken || 0) + 1;
    player.loadToken = token;
    const next = player.gif.cloneNode(false);
    next.hidden = true;
    next.loading = "eager";
    next.removeAttribute("loading");
    next.dataset.loaded = "loading";
    next.dataset.mediaSrc = player.src;
    player.gif.replaceWith(next);
    player.gif = next;
    showLoading(player);
    return new Promise((resolve) => {
      let settled = false;
      const finish = (loaded) => {
        if (settled) return;
        settled = true;
        if (token !== player.loadToken) { resolve(false); return; }
        if (!loaded) { showCanonical(player); resolve(false); return; }
        player.gif.dataset.loaded = "true";
        if (player.playing) showReadyGif(player);
        else if (player.paused) freezeCurrentFrame(player);
        resolve(true);
      };
      next.addEventListener("load", () => finish(true), { once: true });
      next.addEventListener("error", () => finish(false), { once: true });
      next.src = player.src;
    });
  }
  function showPoster(player, source) {
    if (!player.gif) return;
    player.gif.hidden = true;
    player.stage.dataset.playback = source ? "paused" : "poster";
    if (player.canonical) player.canonical.hidden = true;
    if (player.loading) player.loading.hidden = true;
    if (player.poster) {
      player.poster.src = source || player.posterSrc;
      player.poster.alt = source
        ? `${player.name} paused frame of the logo growth animation`
        : `${player.name} static canonical reduced-motion fallback`;
      player.poster.hidden = false;
    }
  }
  function showCheckpoint(player, progress) {
    const p = clamp(progress, 0, 1);
    const stage = phaseFor(p, player.stageProgress);
    if (stage === "canonical") { showCanonical(player); return; }
    const checkpoint = player.stageFiles?.[stage] || player.posterSrc;
    player.current = p * player.duration;
    render(player, p);
    if (player.gif) player.gif.hidden = true;
    player.stage.dataset.playback = "checkpoint";
    if (player.canonical) player.canonical.hidden = true;
    if (player.loading) player.loading.hidden = true;
    if (player.poster) {
      player.poster.src = checkpoint;
      player.poster.alt = `${player.name} baked ${stage} checkpoint of the logo growth animation`;
      player.poster.hidden = false;
    }
  }
  function seekPlayer(player, progress) {
    stop(player);
    player.paused = true;
    showCheckpoint(player, progress);
  }
  function showCanonical(player, preserveClock = false) {
    if (!player.gif) return;
    if (!preserveClock) player.current = player.duration;
    render(player, 1);
    player.gif.hidden = true;
    player.stage.dataset.playback = "canonical";
    if (player.poster) player.poster.hidden = true;
    if (player.loading) player.loading.hidden = true;
    if (player.canonical) {
      player.canonical.src = player.posterSrc;
      player.canonical.hidden = false;
    }
  }
  function showLoading(player) {
    if (player.gif) player.gif.hidden = true;
    player.stage.dataset.playback = "loading";
    if (player.canonical) player.canonical.hidden = true;
    if (player.poster) player.poster.hidden = true;
    if (player.loading) player.loading.hidden = false;
  }
  function freezeCurrentFrame(player) {
    if (!player.gif || player.gif.dataset.loaded !== "true" || !player.gif.complete || !player.gif.naturalWidth) { showCanonical(player); return; }
    const canvas = document.createElement("canvas");
    canvas.width = player.gif.naturalWidth;
    canvas.height = player.gif.naturalHeight;
    try {
      canvas.getContext("2d").drawImage(player.gif, 0, 0);
      showPoster(player, canvas.toDataURL("image/png"));
    } catch (error) {
      showCanonical(player);
    }
  }
  function stop(player) {
    player.playing = false;
    player.loadToken = (player.loadToken || 0) + 1;
    if (player.frame) cancelAnimationFrame(player.frame);
    player.frame = 0;
  }
  function tick(player, timestamp) {
    if (!player.playing || motion === "paused" || motion === "reduced") return;
    if (player.last === null) player.last = timestamp;
    player.current += (timestamp - player.last) * tuning.speed;
    player.last = timestamp;
    const progress = clamp(player.current / player.duration, 0, 1);
    render(player, progress);
    // Hold a separate canonical overlay so the native GIF cannot loop back to
    // its blank frame while the storyboard is still reporting the final state.
    // showCanonical() clamps the visible state to the exact final frame. Call
    // it only once at the handoff so the separate final hold can advance.
    if (player.current >= player.duration && player.stage.dataset.playback !== "canonical") showCanonical(player, true);
    if (player.current >= player.duration + player.finalHoldMs) {
      player.current = 0;
      render(player, 0);
      player.last = null;
      player.frame = 0;
      void showGif(player, true).then((loaded) => {
        if (loaded && player.playing && motion === "running" && !player.frame) {
          player.frame = requestAnimationFrame((next) => tick(player, next));
        }
      });
      return;
    }
    player.frame = requestAnimationFrame((next) => tick(player, next));
  }
  async function play(player, forceRestart = false) {
    if (motion === "reduced") { stop(player); player.current = player.duration; render(player, 1); showCanonical(player); return; }
    // A portable GIF cannot seek. A paused player therefore restarts the
    // checked-in GIF from frame zero; the status text makes that limitation
    // explicit instead of presenting a false resume guarantee.
    const restart = forceRestart || player.current > 0 || player.paused || player.current >= player.duration;
    if (restart) { player.current = 0; render(player, 0); }
    player.paused = false;
    player.playing = true;
    const loaded = await showGif(player, restart);
    if (!loaded || !player.playing || motion !== "running") return;
    player.last = null;
    if (!player.frame) player.frame = requestAnimationFrame((next) => tick(player, next));
  }
  function pause(player) {
    stop(player);
    player.paused = true;
    player.stage.dataset.playback = "paused";
    if (player.current >= player.duration) showCanonical(player); else freezeCurrentFrame(player);
  }
  function replay(player) { stop(player); player.current = 0; player.paused = false; render(player, 0); play(player, true); }
  stages.forEach((stage) => {
     let stageFiles = {};
     try { stageFiles = JSON.parse(stage.dataset.stageFiles || "{}"); } catch (error) { stageFiles = {}; }
     const player = { stage, stageProgress: readStageProgress(stage), id: stage.dataset.themeId || "", autoPlay: stage.dataset.themeId === "ai-field", name: stage.closest(".theme-card")?.querySelector("h2")?.textContent.trim() || "Logo", effect: stage.dataset.effect || "plain", beats: (stage.dataset.beats || "").split(" / ").filter(Boolean), stageFiles, baseDuration: Number(stage.dataset.durationMs || 1800), duration: Number(stage.dataset.durationMs || 1800), finalHoldMs: 720, current: 0, last: null, playing: false, paused: false, frame: 0, loadToken: 0, src: stage.dataset.animationSrc || "", posterSrc: stage.dataset.posterSrc || "", gif: stage.querySelector(".growth-gif"), canonical: stage.querySelector(".motion-canonical"), poster: stage.querySelector(".motion-freeze"), loading: stage.querySelector(".motion-loading"), phase: stage.querySelector("[data-motion-phase]"), beat: stage.querySelector("[data-motion-beat]"), progress: stage.closest(".motion-output")?.querySelector("[data-motion-progress]"), time: stage.closest(".motion-output")?.querySelector("[data-motion-time]"), seek: stage.closest(".motion-output")?.querySelector("[data-motion-seek]") };
    player.playButton = stage.closest(".motion-output")?.querySelector('[data-card-action="play"]');
    player.pauseButton = stage.closest(".motion-output")?.querySelector('[data-card-action="pause"]');
    player.replayButton = stage.closest(".motion-output")?.querySelector('[data-card-action="replay"]');
    player.playButton?.addEventListener("click", () => { setMotion("running"); play(player); });
    player.pauseButton?.addEventListener("click", () => pause(player));
    player.replayButton?.addEventListener("click", () => { setMotion(motion === "reduced" ? "reduced" : "running"); replay(player); });
    player.seek?.addEventListener("input", () => seekPlayer(player, Number(player.seek.value)));
    player.seek?.addEventListener("change", () => seekPlayer(player, Number(player.seek.value)));
    players.push(player);
     render(player, systemPrefersReduced() || !player.autoPlay ? 1 : 0);
     if (systemPrefersReduced()) showCanonical(player); else if (player.autoPlay) play(player); else showCanonical(player);
  });
  function setMotion(next, forceReducedOverride = null, syncPlayers = false) {
    if (forceReducedOverride !== null) motionOverride = forceReducedOverride;
    const previous = motion;
     if (next === "running" && (systemPrefersReduced() || motionOverride === true) && motionOverride !== false) next = "reduced";
    motion = next;
    body.dataset.motion = next;
    document.querySelectorAll("[data-motion-label]").forEach((node) => {
      node.textContent = next === "reduced" ? "REDUCED" : next.toUpperCase();
    });
    if (routeAnimation && routeAnimationPoster) {
      routeAnimation.hidden = next === "reduced";
      routeAnimationPoster.hidden = next !== "reduced";
    }
    if (routePreviewState) routePreviewState.textContent = next === "reduced"
      ? "Static poster · reduced-motion fallback · checked-in asset"
      : "GIF evidence · checked-in route asset · browser tuning is preview-only until the generator is rerun.";
    if (!syncPlayers) return;
    if (next === "paused") players.forEach(pause);
    if (next === "reduced") players.forEach(play);
    if (next === "running" && previous !== "running") players.forEach(play);
  }
  function replayAll() {
    setMotion(motion === "reduced" ? "reduced" : "running");
    players.forEach(replay);
  }
  document.querySelector("[data-action=play]")?.addEventListener("click", () => { setMotion("running"); players.forEach(play); });
  document.querySelector("[data-action=pause]")?.addEventListener("click", () => { setMotion("paused"); players.forEach(pause); });
  document.querySelector("[data-action=replay]")?.addEventListener("click", replayAll);
  filter?.addEventListener("input", () => {
    const query = filter.value.trim().toLowerCase();
    let visible = 0;
    cards.forEach((card) => {
      const terms = query.split(/\s+/).filter(Boolean);
      const searchable = card.dataset.search.toLowerCase().split(/[\s,;|/]+/).filter(Boolean);
      const match = !terms.length || terms.every((term) => searchable.includes(term));
      const player = players.find((candidate) => candidate.stage.closest(".theme-card") === card);
      card.hidden = !match;
      if (!match && player?.playing) { player.filteredPlaying = true; pause(player); }
      if (match && player?.filteredPlaying && motion === "running") { player.filteredPlaying = false; play(player); }
      if (match) visible += 1;
    });
    if (status) status.textContent = `${visible} of ${cards.length} routes shown`;
  });

  const prompt = document.querySelector("[data-motion-prompt]");
  const routeSelect = document.querySelector("[data-route-select]");
  const routeName = document.querySelector("[data-route-name]");
  const routeTrigger = document.querySelector("[data-route-trigger]");
  const routeTrajectory = document.querySelector("[data-route-trajectory]");
  const routeConstruction = document.querySelector("[data-route-construction]");
  const routeSpeed = document.querySelector("[data-route-speed]");
  const routeSequence = document.querySelector("[data-route-sequence]");
  const routeGif = document.querySelector("[data-route-gif]");
  const routeAnimation = document.querySelector("[data-route-animation]");
  const routeAnimationPoster = document.querySelector("[data-route-animation-poster]");
  const routePreviewState = document.querySelector("[data-preview-state]");
  const routeExportCommand = document.querySelector("[data-route-export-command]");
  const copyExportCommandButton = document.querySelector("[data-copy-export-command]");
  const requestSummary = document.querySelector("[data-config-summary]");
  const copyStatus = document.querySelector("[data-copy-status]");
   const syncPromptButton = document.querySelector("[data-sync-prompt]");
   const exportPlan = document.querySelector("[data-export-plan]");
   const exportApprovalState = document.querySelector("[data-export-approval-state]");
   const exportApproveButton = document.querySelector("[data-export-approve]");
   const exportCorrectButton = document.querySelector("[data-export-correct]");
   const exportDeclineButton = document.querySelector("[data-export-decline]");
   const routeExportNote = document.querySelector("[data-route-export-note]");
   let exportApproval = "pending";
   let promptDirty = false;
  const routeCards = new Map(cards.map((card) => {
    const stage = card.querySelector("[data-motion-card]");
    return [card.dataset.theme, {
      id: card.dataset.theme,
      card,
      name: card.querySelector("h2")?.textContent.trim() || card.dataset.theme,
      trigger: card.querySelector(".trigger")?.textContent.trim() || "",
      intent: card.querySelector(".intent")?.textContent.trim() || "",
       trajectory: card.querySelector(".trajectory-note")?.textContent.replace(/^FOREGROUND TRAJECTORY\s*/i, "").trim() || "The supplied mark follows the selected route.",
       mode: stage?.dataset.foregroundMode || "source-derived",
       variant: stage?.dataset.foregroundVariant || "default",
       pathStrategy: stage?.dataset.pathStrategy || "source-derived draw-on path",
       speedProfile: stage?.dataset.speedProfile || "declared route timing",
       construction: stage?.dataset.foregroundMode ? `${stage.dataset.foregroundMode} / ${stage.dataset.foregroundVariant || "default"} / ${stage.dataset.pathStrategy || "source-derived draw-on path"}` : card.querySelector(".motion-route-banner")?.textContent.replace(/^THEME-SPECIFIC FOREGROUND ROUTE\s*/i, "").replace(/\s+/g, " ").trim() || "Source-derived draw-on path.",
       sequence: (stage?.dataset.growthDisplay || "blank / origin dot / circular arc / horizontal bar / P / monogram / Prysai wordmark / complete Logo").replace(/\s*\/\s*/g, " → "),
        gif: card.querySelector(".download-animation")?.getAttribute("href") || "",
        poster: stage?.dataset.posterSrc || card.querySelector(".motion-canonical")?.getAttribute("src") || "",
        beats: (stage?.dataset.beats || "").split(" / ").filter(Boolean)
    }];
  }));
  const promptPresets = {
     ai: { route: "ai-field", controls: { background: "solid", "background-color": "#0B0D12", duration: "1.6", speed: "1.25", direction: "radial", particles: false, "reduced-motion": "respect", format: "gif" }, text: "Animate this supplied logo for an AI technology company. Route it to ai-field. Preserve the supplied source geometry and grow only observed actors in this order: blank → origin dot → circular arc → horizontal bar → P / monogram → Prysai wordmark → complete Logo. Execute the source-pixel foreground route convergence / polar-counter / seeded signals converge into measured actors. Treat raster roles as candidates, use a solid #0B0D12 background, 1600ms, speed 1.25x, center outward, no particles, respect reduced motion, and export GIF." },
     education: { route: "system-spatial", controls: { background: "solid", "background-color": "#F4F1E8", duration: "2.4", speed: "0.75", direction: "left-to-right", particles: false, "reduced-motion": "respect", format: "gif" }, text: "Animate this supplied logo for an education product. Route it to system-spatial. Preserve the source geometry and place observed actors on a clear spatial grid: blank → origin dot → circular arc → horizontal bar → P / monogram → Prysai wordmark → complete Logo. Execute the source-pixel foreground route grid / scan-forward / measured actor-to-actor grid locks. Use a solid #F4F1E8 background, 2400ms, speed 0.75x, left to right entry, no particles, respect reduced motion, and export GIF." },
     premium: { route: "premium-quiet", controls: { background: "solid", "background-color": "#0B0D12", duration: "2.8", speed: "0.75", direction: "radial", particles: false, "reduced-motion": "respect", format: "gif" }, text: "Animate this supplied logo for a premium editorial brand. Route it to premium-quiet. Preserve the source geometry and execute the source-pixel foreground route contour / polar-clockwise / source contour trace followed by fill before the Prysai wordmark. Use a solid #0B0D12 background, 2800ms, speed 0.75x, center outward, no particles, respect reduced motion, and export GIF. Request HTML/SVG only if an accepted SVG source or approved raster reconstruction adapter is available."
    }
  };
  const recipes = {
    solid: { background: "solid", "background-color": "#F4F1E8", particles: false },
    quiet: { duration: "2.4", speed: "0.75" },
    clean: { particles: false },
    accessible: { "reduced-motion": "reduced" }
  };
  function setCopyStatus(message) { if (copyStatus) copyStatus.textContent = message; }
  function setExportApproval(next, message = "") {
    exportApproval = next;
    if (exportApprovalState) {
      exportApprovalState.textContent = next === "approved"
        ? "approved · this exact route and tuning may now be exported"
        : next === "declined"
          ? "declined · export is blocked until the plan is reviewed again"
          : "pending · review the source, candidate actor map, tuning, output, and open gaps";
      exportApprovalState.dataset.state = next;
    }
    if (exportApproveButton) exportApproveButton.disabled = next === "approved";
    if (message) setCopyStatus(message);
  }
  function invalidateExportApproval() {
    if (exportApproval === "approved") setExportApproval("pending", "The export plan changed. Review and approve the updated configuration before copying a command.");
  }
  function readTuningFromControls() {
    tuning.background = document.querySelector('[data-param="background"]')?.value || tuning.background;
    tuning.color = (document.querySelector('[data-param="background-color"]')?.value || tuning.color).toUpperCase();
    tuning.duration = Number(document.querySelector('[data-param="duration"]')?.value) || tuning.duration;
    tuning.speed = Number(document.querySelector('[data-param="speed"]')?.value) || tuning.speed;
    tuning.direction = document.querySelector('[data-param="direction"]')?.value || tuning.direction;
    tuning.particles = Boolean(document.querySelector('[data-param="particles"]')?.checked);
  }
  function applyPresetControls(preset) {
    Object.entries(preset.controls || {}).forEach(([param, value]) => {
      const control = document.querySelector(`[data-param="${param}"]`);
      if (!control) return;
      if (control.type === "checkbox") control.checked = Boolean(value);
      else control.value = String(value);
    });
    readTuningFromControls();
    const motionControl = document.querySelector('[data-param="reduced-motion"]')?.value || "respect";
    motionOverride = motionControl === "reduced" ? true : motionControl === "full" ? false : null;
    setMotion(motionControl === "reduced" || (motionControl === "respect" && systemPrefersReduced()) ? "reduced" : "running");
    applyPreviewTuning();
  }
  async function copyPrompt() {
    const value = prompt?.value.trim();
    if (!value) { setCopyStatus("Write a prompt first."); return; }
    let copied = false;
    try { if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(value); copied = true; } } catch (error) { copied = false; }
    if (!copied) {
      const fallback = document.createElement("textarea"); fallback.value = value; fallback.setAttribute("readonly", ""); fallback.style.position = "fixed"; fallback.style.opacity = "0"; document.body.appendChild(fallback); fallback.select();
      try { copied = document.execCommand("copy"); } catch (error) { copied = false; }
      fallback.remove();
    }
    setCopyStatus(copied ? "Prompt copied. Paste it into the skill request." : "Select the prompt text and copy it manually.");
  }
  function selectedLabel(name) { return document.querySelector(`[data-param="${name}"]`)?.selectedOptions?.[0]?.textContent.trim() || ""; }
  function selectedFormat() {
    const value = document.querySelector('[data-param="format"]')?.value || "gif";
    return value === "html-svg" ? "HTML/SVG" : value === "pdf" ? "PDF atlas" : "GIF";
  }
  function routeCommand() {
    const route = routeCards.get(routeSelect?.value) || routeCards.values().next().value;
    const format = document.querySelector('[data-param="format"]')?.value || "gif";
    const parts = ["python showcase/generate_showcase.py"];
    if (format === "gif") parts.push(`--theme ${route?.id || "ai-field"}`);
    if (tuning.background === "solid") parts.push(`--background '${tuning.color}'`);
    if (tuning.duration) parts.push(`--duration-ms ${Math.round(tuning.duration * 1000)}`);
    if (tuning.speed !== 1) parts.push(`--speed ${tuning.speed}`);
    if (!tuning.particles) parts.push("--no-particles");
    if (format === "pdf") return `${parts.join(" ")}  # writes showcase/output/pdf/motiflux-theme-atlas.pdf`;
    if (format === "html-svg") return "NOT_RUN: HTML/SVG export requires an accepted SVG source or approved raster reconstruction adapter.";
    return parts.join(" ");
  }
  async function copyExportCommand() {
    if (exportApproval !== "approved") {
      setGuide("bake");
      setCopyStatus("Approve the export plan first. The browser will not copy an unreviewed route or candidate actor mapping.");
      return;
    }
    const value = routeCommand();
    if (value.startsWith("NOT_RUN:")) {
      setGuide("bake");
      setCopyStatus(value);
      return;
    }
    let copied = false;
    try { if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(value); copied = true; } } catch (error) { copied = false; }
    setGuide("bake");
    setCopyStatus(copied ? "Export command copied. Run it from the project root; the browser does not execute it." : `Export command: ${value}`);
  }
  function composePrompt() {
    const route = routeCards.get(routeSelect?.value) || routeCards.values().next().value;
    const background = tuning.background === "solid" ? `solid ${tuning.color}` : tuning.background === "dark" ? "plain dark" : tuning.background === "transparent" ? "transparent stage shell" : "the theme background";
    const surface = selectedLabel("surface") || tuning.surface || "brand identity";
    const direction = (selectedLabel("direction") || "center outward").toLowerCase();
    const particles = tuning.particles ? "allow secondary particles" : "no particles";
    const motionControl = document.querySelector('[data-param="reduced-motion"]')?.value || "respect";
    const motionText = motionControl === "reduced" ? "use a static canonical reduced-motion fallback" : motionControl === "full" ? "allow the full motion preview" : "respect reduced motion";
    const stages = (route?.sequence || "blank -> origin dot -> circular arc -> horizontal bar -> P / monogram -> Prysai wordmark -> complete Logo").replace(/→/g, "->");
    const pathStrategy = route?.pathStrategy || "the declared source-derived path";
    const speedProfile = route?.speedProfile || "the declared route timing";
    return `Animate this supplied logo for the selected brand context. Surface: ${surface}. Route it to ${route?.id || "the selected theme"}. Preserve the source geometry and grow only observed actors in this order: ${stages}. Execute the source-pixel foreground route ${route?.construction || "with the declared theme variant"}. Path strategy: ${pathStrategy}. Speed profile: ${speedProfile}. This variant must change the identity-bearing reveal, not only the background, particles, or whole-logo transform. Treat raster role labels as candidates and keep a static canonical fallback. Use ${background}, ${Math.round(tuning.duration * 1000)}ms, speed ${tuning.speed}x, ${direction} direction, ${particles}, ${motionText}, and export ${selectedFormat()}. Lifecycle: browser changes are preview-only; a named generator creates baked files; call the result verified only after source identity, frame, runtime, accessibility, and human-review checks pass. Evidence required: report actual output paths plus candidate, needs-review, not_run, and unresolved items.`;
  }
  function syncPrompt(message = "Request synced from the selected route and controls.") {
    if (!prompt) return;
    prompt.value = composePrompt();
    promptDirty = false;
    setCopyStatus(message);
  }
  function updateRequestSummary() {
    const route = routeCards.get(routeSelect?.value) || routeCards.values().next().value;
    const duration = `${tuning.duration.toFixed(1)} s`;
    const speed = `${tuning.speed}x`;
    const direction = selectedLabel("direction") || "Center outward";
    const background = tuning.background === "solid" ? `solid ${tuning.color}` : tuning.background === "dark" ? "plain dark" : tuning.background === "transparent" ? "transparent shell" : "theme background";
    const particles = tuning.particles ? "particles on" : "particles off";
    const motionControl = document.querySelector('[data-param="reduced-motion"]')?.value || "respect";
    const motionText = motionControl === "reduced" ? "reduced motion" : motionControl === "full" ? "full motion preview" : "respect system motion";
    const format = document.querySelector('[data-param="format"]')?.value === "html-svg" ? "HTML/SVG" : document.querySelector('[data-param="format"]')?.value === "pdf" ? "PDF atlas" : "GIF";
    const surface = selectedLabel("surface") || tuning.surface || "Brand identity";
    if (requestSummary) requestSummary.textContent = `${route?.name || "Selected route"} · ${surface} · ${background} · ${duration} · ${speed} · ${direction.toLowerCase()} · ${particles} · ${motionText} · ${format}`;
    const durationOutput = document.querySelector('[data-value-for="duration"]'); if (durationOutput) durationOutput.textContent = duration;
    const colorOutput = document.querySelector("[data-background-swatch]"); if (colorOutput) colorOutput.textContent = tuning.color;
    if (prompt && !promptDirty) prompt.value = composePrompt();
    if (routeExportCommand) routeExportCommand.textContent = routeCommand();
    if (routeExportNote) routeExportNote.textContent = selectedFormat() === "HTML/SVG"
      ? "not_run · requires accepted SVG or an approved raster reconstruction adapter"
      : selectedFormat() === "PDF atlas"
        ? "baked target · regenerates the seven-stage atlas and repository showcase outputs"
        : "baked target · writes the selected route export manifest and GIF";
    if (exportPlan) exportPlan.textContent = `source: supplied Prysai JPG · route: ${route?.name || "selected"} · actor map: candidate / needs-review · tuning: ${surface}, ${background}, ${duration}, ${speed}, ${direction.toLowerCase()}, ${particles} · output: ${selectedFormat()} · gaps: raster role acceptance and browser/accessibility proof remain open`;
  }
  function applyPreviewTuning() {
    body.dataset.previewBackground = tuning.background;
    body.dataset.particles = tuning.particles ? "on" : "off";
    body.style.setProperty("--preview-solid-bg", tuning.color);
    const entry = tuning.direction === "left-to-right" ? "-8%" : tuning.direction === "right-to-left" ? "8%" : "0%";
    stages.forEach((stage) => { stage.dataset.direction = tuning.direction; stage.style.setProperty("--preview-entry-x", entry); });
    players.forEach((player) => {
      const progress = player.duration ? player.current / player.duration : 0;
      player.duration = player.baseDuration * (tuning.duration / 1.8);
      const isStaticCanonical = player.stage.dataset.playback === "canonical" && !player.playing;
      player.current = isStaticCanonical ? player.duration : clamp(progress, 0, 1) * player.duration;
      if (isStaticCanonical) showCanonical(player); else render(player, clamp(progress, 0, 1));
    });
    updateRequestSummary();
  }
  function applyRecipe(name) {
    const recipe = recipes[name];
    if (!recipe) return;
    Object.entries(recipe).forEach(([param, value]) => {
      const control = document.querySelector(`[data-param="${param}"]`);
      if (!control) return;
      if (control.type === "checkbox") control.checked = Boolean(value);
      else control.value = String(value);
    });
    tuning.background = document.querySelector('[data-param="background"]')?.value || tuning.background;
    tuning.color = (document.querySelector('[data-param="background-color"]')?.value || tuning.color).toUpperCase();
    tuning.duration = Number(document.querySelector('[data-param="duration"]')?.value) || tuning.duration;
    tuning.speed = Number(document.querySelector('[data-param="speed"]')?.value) || tuning.speed;
     tuning.particles = Boolean(document.querySelector('[data-param="particles"]')?.checked);
     tuning.surface = document.querySelector('[data-param="surface"]')?.value || tuning.surface;
     invalidateExportApproval();
    const motionControl = document.querySelector('[data-param="reduced-motion"]')?.value || "respect";
    motionOverride = motionControl === "reduced" ? true : motionControl === "full" ? false : null;
    if (motionControl === "reduced") {
      setMotion("reduced");
      players.forEach(play);
    }
    setGuide("tune");
    applyPreviewTuning();
    setCopyStatus(`${name} recipe applied to the local preview. Sync controls to copy it into the request.`);
  }
  function updateRoute(value, focusCard = false) {
    const route = routeCards.get(value) || routeCards.values().next().value;
    if (!route) return;
    if (routeSelect && routeSelect.value !== value) routeSelect.value = value;
    if (routeName) routeName.textContent = route.name;
    if (routeTrigger) routeTrigger.textContent = route.trigger;
    if (routeTrajectory) routeTrajectory.textContent = route.trajectory;
    if (routeConstruction) routeConstruction.textContent = route.construction;
    if (routeSpeed) routeSpeed.textContent = route.speedProfile;
    if (routeSequence) routeSequence.textContent = route.sequence;
    if (routeGif) { routeGif.href = route.gif; routeGif.textContent = `Open selected ${route.name} GIF`; }
    if (routeAnimation) {
      routeAnimation.src = route.gif;
      routeAnimation.alt = `${route.name} selected route preview: source logo growth animation`;
    }
    if (routeAnimationPoster) {
      const poster = route.poster || route.gif.replace(/\.gif$/i, "-poster.png");
      routeAnimationPoster.src = poster;
      routeAnimationPoster.alt = `${route.name} static canonical fallback for reduced motion`;
      routeAnimationPoster.hidden = motion !== "reduced";
    }
    if (routePreviewState) routePreviewState.textContent = motion === "reduced" ? "Static poster · reduced-motion fallback · checked-in asset" : "GIF evidence · checked-in route asset · browser tuning is preview-only until the generator is rerun.";
    routeCards.forEach((candidate) => candidate.card.classList.toggle("route-selected", candidate === route));
     if (focusCard) route.card.scrollIntoView({ behavior: systemPrefersReduced() ? "auto" : "smooth", block: "center" });
    updateRequestSummary();
  }
  document.querySelectorAll("[data-prompt-preset]").forEach((button) => button.addEventListener("click", () => {
    const preset = promptPresets[button.dataset.promptPreset];
    if (!preset || !prompt) return;
     promptDirty = true; invalidateExportApproval(); updateRoute(preset.route); setGuide("theme"); applyPresetControls(preset); promptDirty = false; prompt.value = composePrompt(); setCopyStatus(`${button.textContent.trim()} loaded. Preview controls now match this request. Review the export plan before copying a command.`); prompt.focus();
  }));
  document.querySelectorAll("[data-recipe]").forEach((button) => button.addEventListener("click", () => applyRecipe(button.dataset.recipe)));
  document.querySelector("[data-copy-prompt]")?.addEventListener("click", copyPrompt);
  copyExportCommandButton?.addEventListener("click", copyExportCommand);
  syncPromptButton?.addEventListener("click", () => syncPrompt());
  prompt?.addEventListener("input", () => { promptDirty = true; setCopyStatus("Prompt edited. The preview stays on the selected route; sync controls only when you want to replace it."); });
  routeSelect?.addEventListener("change", () => {
    invalidateExportApproval();
    updateRoute(routeSelect.value, true);
    setGuide("theme");
    setCopyStatus(promptDirty ? "Route preview changed. Your edited prompt is unchanged; sync controls only if you want to replace it." : "Route preview changed. The request text follows the selected route until you edit it.");
  });
  document.querySelectorAll("[data-param]").forEach((control) => {
    const update = () => {
      const name = control.dataset.param;
      if (name === "duration") tuning.duration = Number(control.value) || 1.8;
      if (name === "speed") tuning.speed = Number(control.value) || 1;
      if (name === "direction") tuning.direction = control.value;
      if (name === "background") tuning.background = control.value;
       if (name === "background-color") tuning.color = control.value.toUpperCase();
       if (name === "surface") tuning.surface = control.value;
       if (name === "particles") tuning.particles = control.checked;
       invalidateExportApproval();
       if (["duration", "speed", "direction", "background", "background-color", "particles", "reduced-motion", "format"].includes(name)) setGuide("tune");
       if (name === "reduced-motion") {
        const nextMotion = control.value === "reduced" || (control.value === "respect" && systemPrefersReduced()) ? "reduced" : "running";
        motionOverride = control.value === "reduced" ? true : control.value === "full" ? false : null;
        setMotion(nextMotion);
        players.forEach(play);
      }
      applyPreviewTuning();
    };
    control.addEventListener("input", update); control.addEventListener("change", update);
  });
   exportApproveButton?.addEventListener("click", () => setExportApproval("approved", "Export plan approved. The command is now eligible to copy; the browser still does not execute it."));
   exportCorrectButton?.addEventListener("click", () => setExportApproval("pending", "Actor mapping correction requested. Keep raster roles as candidate hypotheses until source or human review accepts them."));
   exportDeclineButton?.addEventListener("click", () => setExportApproval("declined", "Export declined. No command was copied."));
   updateRoute(routeSelect?.value || "ai-field");
  applyPreviewTuning();
   setExportApproval("pending");
   setGuide(guideState);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      players.forEach((player) => { player.wasPlaying = player.playing; if (player.playing) pause(player); });
      return;
    }
    if (motion === "running") players.forEach((player) => { if (player.wasPlaying) { player.wasPlaying = false; play(player); } });
  });
  setMotion(motion);
  motionPreference?.addEventListener?.("change", (event) => {
    if (motionOverride !== null) return;
    setMotion(event.matches ? "reduced" : "running", null, true);
  });
  function seek(milliseconds) {
    const target = Number.isFinite(Number(milliseconds)) ? Math.max(0, Number(milliseconds)) : 0;
    players.forEach((player) => {
      stop(player);
      player.current = clamp(target, 0, player.duration);
      player.paused = true;
      render(player, player.duration ? player.current / player.duration : 1);
      if (player.current >= player.duration) showCanonical(player); else showPoster(player);
    });
  }
  function finish() {
    players.forEach((player) => {
      stop(player);
      player.current = player.duration;
      player.paused = true;
      render(player, 1);
      showCanonical(player);
    });
    setMotion("paused");
  }
  function setTempo(value) {
    tuning.speed = clamp(Number(value) || 1, .25, 4);
    const control = document.querySelector('[data-param="speed"]');
    if (control) control.value = String([.75, 1, 1.25, 1.5].reduce((best, option) => Math.abs(option - tuning.speed) < Math.abs(best - tuning.speed) ? option : best, 1));
    updateRequestSummary();
  }
  const runtimeControl = { play: () => { setMotion("running", null, true); }, pause: () => { setMotion("paused", null, true); }, replay: replayAll, seek, finish, setTempo, setMotion: (next) => setMotion(next, null, true) };
  body.dataset.runtimeState = "ready";
  body.dataset.runtimeReady = "true";
  window.__motifluxReady = true;
  window.__motifluxControl = runtimeControl;
  window.__motifluxShowcaseReady = true;
  window.__motifluxShowcaseControl = runtimeControl;
})();
'''


def build_html(data: dict) -> None:
    theme_markup = "\n".join(theme_card(theme) for theme in data["themes"])
    route_options = "".join(
        f'<option value="{esc(theme["id"])}"{" selected" if theme["id"] == "ai-field" else ""}>{esc(theme["name"])}</option>'
        for theme in data["themes"]
    )
    source_label = esc(data["source"]["label"])
    observation = data["source"].get("structure_observation", {})
    observation_status = esc(observation.get("status", "candidate"))
    observation_method = esc(observation.get("method", "bounded raster observation"))
    observation_review = esc(observation.get("review_status", "needs-review"))
    observation_components = len(observation.get("observed_components", [])) if isinstance(observation.get("observed_components", []), list) else 0
    observation_groups = len(observation.get("actor_groups", {})) if isinstance(observation.get("actor_groups", {}), dict) else 0
    recognition = observation.get("recognition", {}) if isinstance(observation.get("recognition", {}), dict) else {}
    recognition_mode = esc(recognition.get("mode", "bounded-geometric-observation"))
    recognition_boundary = esc(recognition.get("input_boundary", "geometry candidates only; semantic recognition is not claimed"))
    recognition_steps = recognition.get("decision_trace", []) if isinstance(recognition.get("decision_trace", []), list) else []
    recognition_step_text = esc(" → ".join(str(item) for item in recognition_steps[:4]) or "mask → components → candidate actors → motion binding")
    mapping = observation.get("stage_mapping", {}) if isinstance(observation.get("stage_mapping", {}), dict) else {}
    mapping_parts = []
    for stage in ("origin_dot", "arc", "bar", "monogram", "wordmark"):
        actors = mapping.get(stage, [])
        if isinstance(actors, list) and actors:
            mapping_parts.append(f"{stage}: {', '.join(str(actor) for actor in actors)}")
    observation_mapping = esc(" · ".join(mapping_parts) or "stage mapping unavailable")
    html_doc = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="Motiflux V1 theme atlas: one supplied Prysai mark routed through thirteen logo-motion systems.">
  <title>Motiflux V1 / Theme Atlas</title>
  <link rel="icon" type="image/jpeg" href="assets/prysai-logo-white.jpg">
  <link rel="stylesheet" href="styles.css?v=motiflux-v1-20260820">
</head>
<body data-motion="auto">
  <div class="shell">
    <a class="skip-link" href="#input-output">Skip to the image-to-animation result</a>
    <header class="topbar">
      <div class="wordmark"><span class="wordmark-mark">M</span><span>Motiflux / V1</span></div>
      <div class="private-badge">Public preview / source-preserving showcase</div>
    </header>
    <div class="truth-bar" role="status"><strong>CHECKED-IN EXAMPLE</strong><span>Input: supplied Prysai JPG</span><span>Analysis: offline candidate</span><span>Output: baked GIF/PDF</span><span>Browser does not generate new media</span></div>
    <nav class="section-nav" aria-label="Showcase sections"><a href="#workflow-guide">How to use</a><a href="#input-output">Image → animation</a><a href="#prompt-lab">Prompt lab</a><a href="#theme-atlas">13 routes</a><a href="output/pdf/motiflux-theme-atlas.pdf">PDF atlas</a></nav>
    <main>
      <section class="hero" aria-labelledby="page-title">
        <div>
          <p class="eyebrow">Brand motion routing / comparative study</p>
          <h1 id="page-title">One image.<br>Thirteen animations.</h1>
           <p class="hero-copy">The source stays fixed. The output grows. Motiflux observes the supplied raster's foreground components and turns those candidate actors into thirteen playable logo-construction results. The visible distinction is the logo's growth path; algorithm notes explain the result rather than replacing it.</p>
           <p class="hero-reading-guide"><strong>How to read this page:</strong> left is the unchanged input image; right is the selected theme's generated GIF. Start with AI-field, pause all cards, then replay one route to compare its foreground draw-on path.</p>
           <p class="hero-next-step"><strong>Start here:</strong> view AI-field → pause → choose a route → copy the prompt → run the skill on your own source.</p>
           <div class="hero-preview-pair" aria-label="Quick static image to animated GIF comparison"><figure><img src="assets/prysai-mark-crop.jpg" alt="Supplied Prysai logo static source"><figcaption>source / JPG</figcaption></figure><span class="hero-preview-arrow" aria-hidden="true">→</span><figure><img src="assets/animations/prysai-ai-field.gif" alt="AI-field logo growth GIF preview"><figcaption>result / GIF</figcaption></figure></div>
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
      <section id="workflow-guide" class="workflow-guide" aria-labelledby="workflow-guide-title">
        <div class="workflow-guide-head">
          <div>
            <p class="eyebrow">Operator guide / five-step contract</p>
            <h2 id="workflow-guide-title">From logo file to defensible motion result.</h2>
            <p>Read the showcase in order. The source fixes the identity, the theme selects the foreground choreography, tuning describes measurable changes, the generator creates files, and evidence determines what you can call verified.</p>
          </div>
          <div class="guide-live" role="status" aria-live="polite">
            <span class="detail-label">NEXT ACTION</span>
            <strong data-guide-live>01 / SOURCE · start here</strong>
            <small data-guide-detail>Confirm the supplied image and the parts that must remain unchanged.</small>
          </div>
        </div>
        <ol class="workflow-rail" aria-label="Motiflux logo animation workflow">
          <li data-guide-step="source" class="is-current"><a href="#input-output"><span class="workflow-index">01</span><span><strong>Source</strong><small>Keep identity fixed</small></span><em data-guide-step-status>current</em></a></li>
          <li data-guide-step="theme"><a href="#prompt-lab"><span class="workflow-index">02</span><span><strong>Theme</strong><small>Choose one route</small></span><em data-guide-step-status>next</em></a></li>
          <li data-guide-step="tune"><a href="#prompt-lab"><span class="workflow-index">03</span><span><strong>Tune</strong><small>State measurable controls</small></span><em data-guide-step-status>next</em></a></li>
          <li data-guide-step="bake"><a href="#prompt-lab"><span class="workflow-index">04</span><span><strong>Bake</strong><small>Run the exporter</small></span><em data-guide-step-status>next</em></a></li>
          <li data-guide-step="verify"><a href="#evidence-key"><span class="workflow-index">05</span><span><strong>Verify</strong><small>Check evidence and review</small></span><em data-guide-step-status>next</em></a></li>
        </ol>
        <div class="workflow-rules">
          <article><span>THEME CUE</span><strong>One context + one motion intention.</strong><p>“AI technology” routes to <code>ai-field</code>; “education” routes to <code>system-spatial</code>. The route changes the identity-bearing foreground path, not only the background.</p></article>
          <article><span>TUNING CUE</span><strong>Use values the generator can reproduce.</strong><p>Say <code>solid #0B0D12</code>, <code>1600ms</code>, <code>speed 1.25x</code>, or <code>no particles</code>. The controls below teach this vocabulary and update the local shell only.</p></article>
          <article><span>EVIDENCE CUE</span><strong>Preview, baked, and verified are different states.</strong><p>A checked-in GIF/PDF is baked. A browser preview or copied command is not a new bake. Call it verified only after file, frame, runtime, source-identity, accessibility, and review checks pass.</p></article>
        </div>
        <div class="state-ladder" aria-labelledby="state-ladder-title">
          <div class="state-ladder-head"><div><span class="detail-label">STATUS LADDER</span><h3 id="state-ladder-title">What the page can prove right now.</h3></div><p data-guide-status>Current session: browser controls are preview-only; checked-in GIF/PDF assets are baked reference outputs; verified is not claimed.</p></div>
          <ol class="state-ladder-items">
            <li class="state-card state-preview"><span>01 / PREVIEW</span><strong>Browser shell</strong><small>Route, tuning, playback, and prompt edits change the local view or request text. No media file is written.</small></li>
            <li class="state-card state-baked"><span>02 / BAKED</span><strong>Generator output</strong><small>The exporter has run and produced the GIF, poster, checkpoint, PDF, manifest, or package being discussed.</small></li>
            <li class="state-card state-verified"><span>03 / VERIFIED</span><strong>Evidence passed</strong><small>Only after the relevant files, fingerprints, frame/runtime checks, source identity, accessibility, and human review are recorded.</small></li>
          </ol>
        </div>
      </section>
      <section id="input-output" class="io-showcase" aria-labelledby="io-title">
        <div class="io-heading">
          <div>
            <p class="eyebrow">Actual rendered output / AI-field route</p>
            <h2 id="io-title">From image to animation.</h2>
           <p>Give the skill one logo image and a request such as “make an AI company logo animation.” Motiflux observes candidate dot, monogram, and wordmark regions, routes the request to AI-field, and returns a portable GIF that grows the supplied pixels from a blank field to a complete logo.</p>
           <p class="checked-in-note"><strong>Checked-in showcase:</strong> this GIF is already generated and stored in the repository. The page controls preview wording and playback; they do not regenerate media in the browser.</p>
          </div>
          <div class="io-badge">INPUT → OUTPUT<br><strong>JPG → GIF</strong><br><small>auto replay / final hold</small></div>
        </div>
         <div class="io-flow">
           <figure class="io-frame io-source"><span class="cell-label">01 / INPUT IMAGE</span><img src="assets/prysai-mark-crop.jpg" alt="Supplied Prysai logo image"></figure>
           <div class="io-arrow" aria-hidden="true">→</div>
           <div class="io-middle"><span>02 / FOREGROUND ROUTE</span><strong>Theme-specific growth path</strong><small>Same source actors, different draw-on grammar, timing, and settle behavior.</small></div>
           <div class="io-arrow" aria-hidden="true">→</div>
           <figure class="io-frame io-output"><span class="cell-label">03 / OUTPUT GIF</span><img src="assets/animations/prysai-ai-field.gif" alt="Prysai logo growing from blank through the AI-field theme"><span class="io-status">AI-FIELD / PLAYING GIF</span></figure>
         </div>
         <div class="io-footer"><span>Observed source actors / origin dot → circular arc → horizontal bar → P / monogram → Prysai wordmark → complete Logo</span><a href="assets/animations/prysai-ai-field.gif" download>Download AI-field GIF</a><a href="#theme-atlas">Compare all 13 routes</a></div>
      </section>
      <section class="evidence-key" aria-labelledby="evidence-key-title">
        <div class="evidence-key-head">
          <div>
            <p class="eyebrow">How to read the deliverables</p>
            <h2 id="evidence-key-title">Three files, three kinds of evidence.</h2>
          </div>
          <p class="evidence-key-intro">The media are related, but they do not prove the same thing. Use the GIF to inspect the complete motion path, the poster to land safely on the canonical final frame, and the PDF to review the seven checkpoints.</p>
        </div>
        <div class="evidence-grid">
          <article class="evidence-item evidence-gif">
            <span class="evidence-token">GIF / FULL TRAJECTORY</span>
            <h3>Complete generation evidence</h3>
            <p>The baked GIF records the playable blank → origin dot → circular arc → horizontal bar → P / monogram → Prysai wordmark → complete Logo sequence. It is the evidence for how the supplied pixels become the final mark over time.</p>
            <small>Use Play, Pause, and Replay to compare the route; a GIF is portable, but the browser player cannot author a new GIF.</small>
          </article>
          <article class="evidence-item evidence-poster">
            <span class="evidence-token">POSTER / CANONICAL FALLBACK</span>
            <h3>Canonical final frame</h3>
            <p>The poster is a static canonical final-frame fallback. It appears for reduced motion, loading, an unavailable GIF, or the final reading hold; it does not prove the intermediate trajectory or human role acceptance.</p>
            <small>Compare it with the source identity and final-frame evidence before calling the result verified.</small>
          </article>
          <article class="evidence-item evidence-pdf">
            <span class="evidence-token">PDF / SEVEN-STAGE STORYBOARD</span>
            <h3>Static inspection atlas</h3>
            <p>The PDF captures seven static checkpoints for each route. It is useful for review, export, and print; it is not a playable GIF, a seekable timeline, or proof of every in-between frame.</p>
            <small><a href="output/pdf/motiflux-theme-atlas.pdf">Open the seven-stage PDF atlas</a> · pair it with the GIF when motion behavior matters.</small>
          </article>
        </div>
      </section>
      <section class="route-brief" aria-labelledby="route-title">
        <div class="route-cell"><span id="route-title" class="route-label">Example request</span><p class="route-value">“I want to make a logo animation for my artificial-intelligence company.”</p></div>
        <div class="route-cell"><span class="route-label">AI-field animation</span><p class="route-value"><strong>AI-field</strong><br>the supplied image becomes a signal-convergence reveal</p></div>
         <div class="route-cell"><span class="route-label">What the viewer sees</span><p class="route-value">Blank field → origin dot → circular arc → horizontal bar → P / monogram → Prysai wordmark → complete Logo. Each card is a direct GIF output.</p></div>
      </section>
      <section class="how-to" aria-labelledby="how-to-title">
        <div class="how-to-head">
          <div><p class="eyebrow">Three-step request pattern</p><h2 id="how-to-title">Give the agent a usable brief.</h2><p>Keywords select the foreground route. Tuning phrases change measurable controls. Export words select an actual delivery path.</p></div>
          <p>Keep identity constraints first. Keep one primary theme. Ask for proof when a file or behavior matters.</p>
        </div>
        <div class="how-to-grid">
          <article class="how-to-step"><span>01 / SOURCE</span><h3>Protect the mark</h3><p>Attach the image and state what must stay unchanged. For raster input, ask the agent to observe candidate actors and keep a static canonical fallback.</p><code>preserve source geometry; use only observed actors</code></article>
          <article class="how-to-step"><span>02 / KEYWORD</span><h3>Choose one route</h3><p>Say the context in plain language. For example, “AI technology” routes to <strong>ai-field</strong>; “education” routes to <strong>system-spatial</strong>. Add no more than two modifiers.</p><code>AI technology -> ai-field -> signal convergence</code></article>
          <article class="how-to-step"><span>03 / TUNE + EXPORT</span><h3>Make the output explicit</h3><p>Use measurable phrases for color, timing, effects, and accessibility. Preview controls are not a baked export; rerun the generator to create GIF or PDF files.</p><code>solid #0B0D12 background; no particles; 1600ms; export GIF</code></article>
        </div>
      </section>
      <section class="observation-strip" aria-labelledby="observation-title">
        <div class="observation-head"><strong id="observation-title">Source structure observation</strong><p>Geometry candidates drive the growth staging; semantic roles remain reviewable.</p></div>
        <div class="observation-grid">
          <div class="observation-cell"><span class="detail-label">METHOD</span><strong>{observation_method}</strong><small>{observation_status} / {observation_components} measured components</small></div>
          <div class="observation-cell"><span class="detail-label">GROUPING</span><strong>{observation_groups} actor groups</strong><small>symbol and wordmark candidates are staged from the supplied pixels</small></div>
          <div class="observation-cell"><span class="detail-label">REVIEW BOUNDARY</span><strong>{observation_review}</strong><small>candidate geometry is not semantic recognition or equivalent editable SVG</small></div>
          <div class="observation-cell"><span class="detail-label">EVIDENCE</span><strong><a href="output/source-analysis.json">Open source analysis</a> · <a href="output/growth-evidence.json">Growth evidence</a></strong><small>inspect masks, bounds, stage frame indices, GIF hashes, and unresolved items</small></div>
        </div>
        <div class="recognition-handoff" aria-label="Automatic structure recognition handoff"><div><span class="detail-label">AUTOMATIC STRUCTURE HANDOFF</span><strong>{recognition_mode}</strong><p>{recognition_boundary}</p></div><div><span class="detail-label">DECISION TRACE</span><p>{recognition_step_text}</p></div><div><span class="detail-label">SAFE ACTION</span><p>Bind only observed actors; keep uncertain roles behind the static-canonical fallback.</p></div></div>
        <p class="observation-map"><span>STAGED ACTOR MAP</span>{observation_mapping}<small>These names are deterministic candidate bindings used by the showcase; review them before treating a raster role as semantic truth.</small></p>
      </section>
      <section id="prompt-lab" class="prompt-lab" aria-labelledby="prompt-lab-title">
        <div class="prompt-lab-head">
          <div>
            <p class="eyebrow">Prompt lab / agent guidance</p>
            <h2 id="prompt-lab-title">Describe the identity. Motiflux chooses the route.</h2>
            <p>Give the skill the source image, surface, industry, foreground growth order, visual controls, accessibility behavior, and output. The controls below update this local preview and the copyable request; they do not regenerate or rewrite the committed GIF pixels in the browser. Editing the request is text-only: it does not automatically reroute the preview. Choose a route or preset explicitly, then use “Sync controls to request” only when you want to replace the text. The stage labels below are candidate descriptions for this checked-in raster; review them before treating them as semantic roles. Use the storyboard chips to read the active construction phase.</p>
          </div>
           <div class="prompt-lab-order"><span>RECOMMENDED ORDER</span><strong>source → theme → growth → tuning → output → proof</strong><small>Say what must stay unchanged first. Then name one route and one measurable refinement.</small></div>
        </div>
        <div class="prompt-lab-grid">
          <div class="prompt-editor">
            <label class="detail-label" for="motion-prompt">COPYABLE REQUEST</label>
            <textarea id="motion-prompt" class="motion-prompt" data-motion-prompt rows="8">Animate this supplied logo for an AI technology company. Surface: brand identity. Route it to ai-field. Preserve the source geometry and grow only observed actors in this order: blank → origin dot → circular arc → horizontal bar → P / monogram → Prysai wordmark → complete Logo. Execute the source-pixel foreground route convergence / polar-counter / seeded signals converge into measured actors. Path strategy: seeded signals converge into measured actors. Speed profile: accelerate into geometry and decelerate at lockup. Treat raster stage labels as candidates and keep a static canonical fallback. Use a solid #0B0D12 background, 1600ms, speed 1.25x, center outward direction, no particles, respect reduced motion, and export GIF. Lifecycle: browser changes are preview-only; the named generator creates baked files; call the result verified only after source identity, frame, runtime, accessibility, and human-review checks pass. Evidence required: report actual output paths plus candidate, needs-review, not_run, and unresolved items.</textarea>
            <div class="prompt-actions"><button type="button" data-prompt-preset="ai">AI technology preset</button><button type="button" data-prompt-preset="education">Education preset</button><button type="button" data-prompt-preset="premium">Premium preset</button><button type="button" data-sync-prompt>Sync controls to request</button><button type="button" data-copy-prompt>Copy request</button></div>
            <p class="copy-status" data-copy-status aria-live="polite">Edit the request, then copy it into the skill.</p>
          <div class="evidence-status" aria-label="Current evidence status"><span class="detail-label">CURRENT EVIDENCE</span><strong>GIF/PDF: baked · evidence: candidate · review: needs-review</strong><small>not_run: raster-to-vector reconstruction, human role review, browser render analysis · unresolved: candidate role semantics</small></div>
          </div>
          <div class="route-readout" aria-live="polite">
            <label class="detail-label" for="route-select">ROUTE PREVIEW</label>
            <select id="route-select" data-route-select>
              {route_options}
            </select>
            <p><span>SELECTED THEME</span><strong data-route-name>AI-field</strong></p>
             <p><span>TRIGGER TAGS</span><strong data-route-trigger>AI, artificial intelligence</strong></p>
             <p><span>FOREGROUND TRAJECTORY</span><strong data-route-trajectory>Signal convergence into the measured source pixels.</strong></p>
             <p><span>DRAW-ON IMPLEMENTATION</span><strong data-route-construction>convergence / seeded signals converge into measured actors</strong></p>
             <p><span>SPEED PROFILE</span><strong data-route-speed>accelerate into geometry and decelerate at lockup</strong></p>
             <p><span>STAGE ORDER</span><strong data-route-sequence>blank → origin dot → circular arc → horizontal bar → P / monogram → Prysai wordmark → complete Logo</strong></p>
             <figure class="route-preview"><span class="detail-label">BAKED ROUTE OUTPUT / GIF OR POSTER</span><img data-route-animation src="assets/animations/prysai-ai-field.gif" alt="AI-field selected route preview: source logo growth animation"><img data-route-animation-poster hidden src="assets/animations/prysai-ai-field-poster.png" alt="AI-field static canonical fallback for reduced motion"><figcaption>Changing the route changes this checked-in GIF. Reduced motion shows its static canonical poster. Tuning controls below change only the local shell simulation until the generator is rerun.</figcaption><p class="preview-state" data-preview-state role="status" aria-live="polite">GIF evidence · checked-in route asset · browser tuning is preview-only until the generator is rerun.</p></figure>
             <a class="route-gif-link" data-route-gif href="assets/animations/prysai-ai-field.gif" download>Open selected AI-field GIF</a>
          </div>
        </div>
        <div class="tuning-panel parameter-panel">
           <div class="tuning-head"><div><span class="detail-label">PROMPT COMPOSER / LOCAL PREVIEW ONLY</span><p>Use these controls to learn precise tuning language. Background, particles, duration, speed, direction, and reduced motion change this page preview only. Downloaded GIF/PDF pixels remain unchanged until the named generator is run.</p></div><span class="tuning-boundary">PREVIEW ONLY</span></div>
          <div class="recipe-row" aria-label="Common tuning recipes"><span class="detail-label">QUICK RECIPES</span><button type="button" data-recipe="solid">Pure color</button><button type="button" data-recipe="quiet">Slow reading</button><button type="button" data-recipe="clean">No particles</button><button type="button" data-recipe="accessible">Low motion</button></div>
          <div class="tuning-grid">
             <label>Surface<select data-param="surface"><option value="brand identity" selected>Brand identity</option><option value="product interface">Product interface</option><option value="campaign title">Campaign title</option><option value="social reveal">Social reveal</option></select></label>
             <label>Background<select data-param="background"><option value="theme" selected>Theme background</option><option value="dark">Plain dark</option><option value="solid">Solid color</option><option value="transparent">Transparent shell</option></select></label>
            <label>Solid color<input data-param="background-color" type="color" value="#0B0D12"><output data-background-swatch>#0B0D12</output><small class="control-note">used only when Background = Solid color</small></label>
            <label>Duration<input data-param="duration" type="range" min="0.8" max="3.2" step="0.1" value="1.8"><output data-value-for="duration">1.8 s</output></label>
            <label>Speed<select data-param="speed"><option value="0.75">0.75x / slow</option><option value="1" selected>1x / medium</option><option value="1.25">1.25x / fast</option><option value="1.5">1.5x / very fast</option></select></label>
           <label>Direction<select data-param="direction"><option value="radial" selected>Center outward</option><option value="left-to-right">Left to right</option><option value="right-to-left">Right to left</option></select><small class="control-note">preview entry cue; not a baked showcase flag</small></label>
             <label class="check-label"><input data-param="particles" type="checkbox" checked> Auxiliary particles<small class="control-note">shell preview; bake with <code>--no-particles</code></small></label>
             <label>Motion<select data-param="reduced-motion"><option value="respect" selected>Respect system setting</option><option value="full">Full motion preview</option><option value="reduced">Reduced / canonical</option></select><small class="control-note">page preview only; GIF remains animated</small></label>
            <label>Output<select data-param="format"><option value="gif" selected>GIF / existing asset</option><option value="html-svg">HTML + SVG / run skill</option><option value="pdf">PDF atlas / existing asset</option></select><small class="control-note">selection changes the request only; no exporter runs here</small></label>
          </div>
          <div class="request-summary" aria-live="polite"><span>REQUEST SUMMARY</span><strong data-config-summary>AI-field · theme background · 1.8 s · medium · center outward · particles on · respect system motion · GIF</strong></div>
          <div class="route-export-command"><span class="detail-label">EXPORT CONFIRMATION GATE</span><p class="export-plan" data-export-plan>source: supplied Prysai JPG · route: AI-field · actor map: candidate / needs-review · tuning: brand identity, theme background, 1.8 s, 1x, center outward, particles · output: GIF · gaps: raster role acceptance and browser/accessibility proof remain open</p><p class="export-approval-state" data-export-approval-state aria-live="polite">pending · review the source, candidate actor map, tuning, output, and open gaps</p><div class="prompt-actions"><button type="button" data-export-approve>Approve plan</button><button type="button" data-export-correct>Correct actor mapping</button><button type="button" data-export-decline>Decline export</button></div><span class="detail-label">CURRENT CONFIGURATION / BAKED EXPORT COMMAND</span><pre><code data-route-export-command>python showcase/generate_showcase.py --theme ai-field --duration-ms 1800</code></pre><button type="button" data-copy-export-command>Copy export command</button><small data-route-export-note>baked target · writes the selected route export manifest and GIF</small><small>Displayed for copying only. Run it from the project root; browser controls never execute shell commands.</small></div>
           <p class="static-boundary"><strong>Preview:</strong> browser controls only. <strong>Baked:</strong> run <code>python showcase/generate_showcase.py</code> for the 13 checked-in GIFs and PDF, or the skill's <code>project</code> + <code>build</code> path for a source-specific HTML/SVG package. <strong>Verified:</strong> only after files, frame evidence, runtime checks, and source identity checks pass. <a href="https://github.com/uuzzrm/motiflux/blob/main/skills/motiflux/guides/prompting.md">Prompt guide</a> · <a href="https://github.com/uuzzrm/motiflux/blob/main/skills/motiflux/guides/export-and-tuning.md">Export and tuning guide</a> · <a href="output/pdf/motiflux-theme-atlas.pdf">Download PDF atlas</a> · <a href="output/source-analysis.json">View source observation</a> · <a href="output/growth-evidence.json">View growth evidence</a></p>
            <details class="export-details"><summary>Show exact export commands</summary><pre><code>python showcase/generate_showcase.py --theme ai-field --background '#0B0D12' --duration-ms 1600 --speed 1.25 --no-particles
python showcase/generate_showcase.py --background '#F4F1E8' --duration-ms 2200 --speed 0.75 --no-particles
 python skills/motiflux/tools/motiflux.py project path/to/logo.svg "AI logo animation, export HTML SVG" work/motiflux-project
python skills/motiflux/tools/motiflux.py validate motion-plan work/motiflux-project/motion-plan.yaml
python skills/motiflux/tools/motiflux.py build path/to/logo.svg work/motiflux-project/motion-plan.yaml work/motiflux-package</code></pre><p>For a JPG or PNG, the showcase GIF is source-pixel based and remains a reviewable candidate. Provide SVG when editable vector actors are required.</p></details>
        </div>
      </section>
      <section id="theme-atlas" aria-labelledby="grid-title">
        <div class="controls">
           <div><h2 id="grid-title" class="section-title">Theme animation atlas</h2><div data-filter-status class="controls-copy">13 of 13 animations shown · same stages, different foreground paths</div></div>
          <div class="controls-actions"><input class="filter" data-filter type="search" placeholder="Filter by theme or keyword" aria-label="Filter themes"><button type="button" data-action="play">Play all</button><button type="button" data-action="pause">Pause</button><button type="button" data-action="replay">Replay</button><span class="route-state" data-motion-label>RUNNING</span></div>
        </div>
        <div class="theme-grid">{theme_markup}</div>
      </section>
    </main>
     <footer class="footer"><p>Motiflux V1 is an AI skill for source-aware logo growth: the source image stays recognizable while the selected theme changes the construction choreography.</p><p>The HTML and GitHub README expose portable GIF outputs. The PDF is a static storyboard of the same image-to-animation sequences. Public design systems are principle analogues only; no private vendor recipe is claimed.</p></footer>
  </div>
  <script src="app.js?v=motiflux-v1-20260820"></script>
</body>
</html>
'''
    (ROOT / "index.html").write_text(html_doc, encoding="utf-8")
    (ROOT / "styles.css").write_text(CSS + MOTION_CSS, encoding="utf-8")
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


# Checkpoints are deliberately taken inside each semantic beat. The public
# labels describe the visible stage, so a `spark` checkpoint must not already
# contain a partial arc and a `wordmark` checkpoint must show a readable but
# unfinished lockup.
# Kept as a compatibility fallback for PDF callers that do not have a theme
# record. Normal showcase/PDF generation uses _storyboard_progress(theme), so
# the renderer and presentation checkpoints share one timing source.
STORYBOARD_PROGRESS = {"blank": 0.0, "spark": .15, "arc": .33, "bar": .48, "monogram": .65, "wordmark": PRECANONICAL_LOCKUP_LIMIT, "canonical": 1.0}
_GIF_FRAME_CACHE: dict[Path, tuple[Image.Image, ...]] = {}


def _load_animation_frames(path: Path) -> tuple[Image.Image, ...]:
    """Read the rendered GIF frames once so PDF pages use the real animation."""

    resolved = path.resolve()
    if resolved not in _GIF_FRAME_CACHE:
        with Image.open(resolved) as gif:
            frames = tuple(frame.convert("RGB").copy() for frame in ImageSequence.Iterator(gif))
        if not frames:
            raise ValueError(f"animation has no frames: {path}")
        _GIF_FRAME_CACHE[resolved] = frames
    return _GIF_FRAME_CACHE[resolved]


def _draw_pil_contained(canvas, image: Image.Image, x: float, y: float, width: float, height: float) -> None:
    from reportlab.lib.utils import ImageReader

    image_width, image_height = image.size
    scale = min(width / image_width, height / image_height)
    draw_width = image_width * scale
    draw_height = image_height * scale
    canvas.drawImage(
        ImageReader(image),
        x + (width - draw_width) / 2,
        y + (height - draw_height) / 2,
        draw_width,
        draw_height,
    )


def draw_storyboard_frame(canvas, x: float, y: float, width: float, height: float, *, frame: str, theme: dict) -> None:
    """Draw a normalized keyframe directly from the theme's generated GIF."""

    if frame not in STORYBOARD_PROGRESS:
        raise ValueError(f"unknown storyboard frame: {frame}")
    gif_path = ANIMATIONS / Path(theme["animation_file"]).name
    frames = _load_animation_frames(gif_path)
    frame_index = round(_storyboard_progress(theme).get(frame, STORYBOARD_PROGRESS[frame]) * (len(frames) - 1))
    image = frames[frame_index]
    canvas.saveState()
    _draw_pil_contained(canvas, image, x, y, width, height)
    canvas.setStrokeColor(pdf_color(theme["accent"]))
    canvas.setLineWidth(.6)
    canvas.rect(x, y, width, height, stroke=1, fill=0)
    canvas.restoreState()


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
    canvas.setFillColor(muted); canvas.setFont("Courier", 5.7); canvas.drawRightString(x + width - 10, y + height - 14, "PLAYABLE IN HTML")
    # Seven checkpoints read more clearly as two compact rows than as seven
    # compressed thumbnails. This keeps arc/bar evidence legible in the PDF.
    stage_y = y + height - header_h - 105
    stage_h = 58
    gap = 4
    frames_to_draw = tuple(GROWTH_SEQUENCE)
    frame_width = (width - 5 * gap) / 4
    for frame_index, frame in enumerate(frames_to_draw):
        row, col = divmod(frame_index, 4)
        frame_x = x + gap + col * (frame_width + gap)
        frame_y = stage_y - row * (stage_h + 18)
        draw_storyboard_frame(canvas, frame_x, frame_y, frame_width, stage_h, frame=frame, theme=theme)
        canvas.setFillColor(muted); canvas.setFont("Courier", 4.1); canvas.drawCentredString(frame_x + frame_width/2, frame_y - 8, GROWTH_STAGE_LABELS[frame].upper())
    canvas.setStrokeColor(line); canvas.line(x, stage_y - 2 * (stage_h + 18) + 4, x + width, stage_y - 2 * (stage_h + 18) + 4)
    text_y = stage_y - 2 * (stage_h + 18) - 10
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
    pdf.setTitle("Motiflux V1 / Image to Animation Atlas")
    pdf.setAuthor("uuzzrm / Motiflux")
    ink = HexColor("#f2f1e9"); muted = HexColor("#a2a69f"); line = HexColor("#303532"); accent = HexColor("#9c8cff")

    # Cover / route explanation page.
    pdf.setFillColor(HexColor("#070908")); pdf.rect(0, 0, page_width, page_height, stroke=0, fill=1)
    pdf.setFillColor(accent); pdf.setFont("Courier-Bold", 8); pdf.drawString(38, page_height - 42, "MOTIFLUX / V1 / IMAGE TO ANIMATION ATLAS")
    pdf.setStrokeColor(line); pdf.line(38, page_height - 53, page_width - 38, page_height - 53)
    pdf.setFillColor(ink); pdf.setFont("Helvetica-Bold", 40); pdf.drawString(38, page_height - 125, "One image.")
    pdf.drawString(38, page_height - 168, "Thirteen playable animations.")
    pdf.setFillColor(muted); pdf.setFont("Helvetica", 11)
    cover_lines = [
        "A source-preserving storyboard of the same supplied Prysai image growing",
        "through Motiflux V1 design themes. The source stays recognizable while",
        "construction order, motion language, and algorithm explanation change.",
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
        "Route: signal convergence / component growth / progressive disclosure.",
         "Animation: blank field -> origin dot -> circular arc -> horizontal bar",
         "-> P / monogram -> Prysai wordmark -> complete Logo. The HTML and GIF",
         "are playable; this PDF records growth frames for the same supplied image.",
    ]
    for offset, line_text in enumerate(route_lines): pdf.drawString(334, 198 - offset*14, line_text)
    pdf.setStrokeColor(line); pdf.line(334, 116, 782, 116)
    pdf.setFillColor(muted); pdf.setFont("Courier", 6.5); pdf.drawString(334, 84, "13 routable themes / 1 identity source / 0 geometry edits")
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
        pdf.setFillColor(muted); pdf.setFont("Courier", 6); pdf.drawString(margin_x, 14, "Same source image / seven-stage growth storyboards")
        pdf.drawRightString(page_width - margin_x, 14, f"PAGE {2 + page_start//4:02d}")
        pdf.showPage()
    pdf.save()
    return pdf_path


def write_readme(data: dict) -> None:
    text = f'''# Motiflux V1 showcase

This showcase uses one supplied raster source - `assets/prysai-logo-white.jpg` -
to make a direct visual comparison across {len(data["themes"])} playable Motiflux logo-growth animations.

Open `index.html` locally for the interactive comparison grid. Each card keeps
the same source image on the left and runs a real blank-to-canonical construction
sequence on the right: blank, origin dot, circular arc, horizontal bar, P / monogram,
Prysai wordmark, and complete Logo. Each theme changes construction timing and motion language; it does not redraw or
rename the Prysai identity.

## Read the comparison correctly

The left cell is the unchanged source image. The right cell is a checked-in
image-to-animation result. The foreground route is the design difference:
each theme moves the observed source actors through a different construction
path, then hands off to the same canonical source-derived mark. Background
color, particles, and atmosphere are secondary signals and must not be
mistaken for a new logo design.

The source observer uses decoded pixels, a foreground mask, connected
components, and layout grouping to propose actor candidates. It does not claim
OCR, semantic recognition, or an editable-vector reconstruction. The generated
source analysis therefore stays `candidate` / `needs-review` until a human or
an appropriate adapter accepts the role mapping.

## Prompt Lab and export controls

Prompt Lab is a local review surface. Route selection, direction, solid color,
duration, speed, particles, and reduced-motion controls update the player,
preview shell, summary, and copyable request. They do not rewrite the checked-in
GIF or PDF. This keeps a browser experiment visibly separate from a baked export.

To bake a new set of GIFs and the PDF from the repository root, use explicit
controls such as:

```powershell
python showcase\\generate_showcase.py --theme ai-field --background '#0B0D12' --duration-ms 1600 --speed 1.25 --no-particles
python showcase\\generate_showcase.py --background '#F4F1E8' --duration-ms 2200 --speed 0.75 --no-particles
```

Omit an option to keep the default theme value. The generator writes all 13
theme GIFs, canonical poster PNGs, the HTML grid, machine-readable evidence,
and (unless `--skip-pdf` is supplied) the seven-stage PDF atlas. Re-run the
project and artifact validators after a bake. A local preview is `preview`; a
file written by the generator is `baked`; `verified` additionally requires the
applicable file, frame, runtime, accessibility, and source-identity checks.

Evidence remains separate from file lifecycle: `candidate`, `complete`,
`needs-review`, `not_run`, and `unresolved` describe proof maturity and open
gaps. A baked file can remain `candidate` when browser, raster-role, or
accessibility evidence is still missing.

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
- `output/pdf/motiflux-theme-atlas.pdf` - printable seven-stage growth storyboard atlas.
- `output/growth-evidence.json` - machine-readable progress-point frame indices, stage labels, foreground mask hashes, alpha/bounds metrics, trajectory fingerprints, cross-theme foreground uniqueness, and review status.

## Regenerate

From the repository root:

```powershell
python showcase\\generate_showcase.py
```

The HTML presents the actual image-to-animation result first. For one route,
use `--theme <theme-id>`; it writes `showcase/output/exports/<theme-id>/` with
the GIF, canonical poster, seven PNG checkpoints, and `export-manifest.json`.
The PDF includes
the route example `artificial-intelligence` -> `AI-field` and records all seven
growth stages of each playable animation: blank, origin dot, circular arc,
horizontal bar, P / monogram, Prysai wordmark, and complete Logo. Public design
systems are principle analogues only; this material does not claim private vendor
algorithms.
'''
    # Keep the showcase guide hand-authored. The root README gallery is the
    # generated surface; overwriting this guide would discard the AI usage,
    # export-state, and single-route instructions maintained beside the page.
    readme_path = ROOT / "README.md"
    if readme_path.is_file():
        existing = readme_path.read_text(encoding="utf-8")
        for required in ("## Prompt Lab", "## Single-route export", "export-manifest.json"):
            if required not in existing:
                raise ValueError(f"showcase README is missing maintained section: {required}")
        return
    readme_path.write_text(text, encoding="utf-8")


def github_gallery(data: dict) -> str:
    """Build a GitHub-native two-column card grid of source image -> GIF."""

    image_path = "showcase/assets/prysai-mark-crop.jpg"
    cards: list[str] = []
    for theme in data["themes"]:
        theme_id = esc(theme["id"])
        name = esc(theme["name"])
        animation_path = f"showcase/{theme['animation_file']}"
        keywords = " ".join(f"<code>{esc(keyword)}</code>" for keyword in theme["keywords"])
        cards.append(
            f'''<td width="50%" valign="top">
<h3>{esc(theme["number"])} · {name}</h3>
<table>
<tr>
<td align="center" valign="top" width="36%"><img src="{image_path}" alt="Static Prysai source mark for {name}" width="150"><br><sub>STATIC SOURCE</sub></td>
<td align="center" valign="top" width="64%"><img src="{animation_path}" alt="{name} Prysai logo animation GIF" width="270"><br><sub>PLAYING GIF</sub></td>
</tr>
</table>
<p><code>{theme_id}</code><br><sub>TRIGGER KEYWORDS</sub><br>{keywords}</p>
<p><sub>{esc(theme["intent"])}</sub></p>
</td>'''
        )

    rows = [
        "## GitHub-native image → animation gallery",
        "",
        "Every card uses the same supplied Prysai source on the left and the portable GIF generated for that theme on the right. The GIF is a real checked-in output, so GitHub can play it directly without JavaScript or a separate deployment.",
        "",
        '<table class="motiflux-gallery">',
    ]
    for index in range(0, len(cards), 2):
        rows.append("<tr>")
        rows.extend(cards[index:index + 2])
        if index + 1 == len(cards):
            rows.append('<td width="50%" valign="top"></td>')
        rows.append("</tr>")
    rows.extend(["</table>", "", "<sub>LEFT = unchanged source image · RIGHT = generated animated result</sub>"])
    return "\n".join(rows)


def write_github_gallery(data: dict) -> None:
    """Replace only the generated gallery in the project README."""

    readme = PROJECT_README.read_text(encoding="utf-8")
    if readme.count(GITHUB_GALLERY_START) != 1 or readme.count(GITHUB_GALLERY_END) != 1:
        raise ValueError("project README must contain exactly one GitHub gallery marker pair")
    start = readme.index(GITHUB_GALLERY_START)
    end = readme.index(GITHUB_GALLERY_END, start)
    if end < start:
        raise ValueError("project README GitHub gallery markers are out of order")
    replacement = f"{GITHUB_GALLERY_START}\n\n{github_gallery(data)}\n\n{GITHUB_GALLERY_END}"
    updated = readme[:start] + replacement + readme[end + len(GITHUB_GALLERY_END):]
    PROJECT_README.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-pdf", action="store_true", help="write HTML assets only")
    parser.add_argument("--theme", metavar="THEME_ID", help="bake one route into showcase/output/exports/<theme-id>")
    parser.add_argument("--background", metavar="#RRGGBB", help="bake one solid background color into every GIF")
    parser.add_argument("--duration-ms", type=int, metavar="MS", help="bake one duration in milliseconds into every GIF")
    parser.add_argument("--speed", type=float, default=1.0, metavar="X", help="bake a bounded progression speed from 0.25x to 4x")
    parser.add_argument("--no-particles", action="store_true", help="omit secondary particle/field effects from baked GIFs")
    parser.add_argument("--no-guides", action="store_true", help="omit secondary trajectory guides from baked GIFs; keep source-pixel growth")
    args = parser.parse_args()
    if args.background is not None:
        normalized_background = args.background.upper()
        if not (len(normalized_background) == 7 and normalized_background.startswith("#")):
            raise SystemExit("--background must be a hex color such as #0B0D12")
        try:
            _rgb(normalized_background)
        except (TypeError, ValueError):
            raise SystemExit("--background must be a hex color such as #0B0D12")
    if args.duration_ms is not None and args.duration_ms < ANIMATION_FRAME_COUNT * 20:
        raise SystemExit(f"--duration-ms must be at least {ANIMATION_FRAME_COUNT * 20}")
    if not .25 <= args.speed <= 4.0:
        raise SystemExit("--speed must be between 0.25 and 4.0")
    _set_export_options({
        "background": args.background.upper() if args.background else None,
        "duration_ms": args.duration_ms,
        "speed": args.speed,
        "particles": not args.no_particles,
        "guides": not args.no_guides,
    })
    derive_preview_assets()
    source_structure = detect_source_structure(CROP_JPG)
    data = load_data()
    if len(data.get("themes", [])) != 13:
        raise ValueError("showcase requires exactly 13 theme records")
    data["source"]["structure_observation"] = source_structure
    write_source_analysis(source_structure)
    if args.theme:
        manifest_path = build_single_theme_export(data, source_structure, args.theme)
        print(f"Generated {manifest_path}")
        return
    build_animation_exports(data, source_structure)
    data["export_options"] = dict(EXPORT_OPTIONS)
    write_snapshot(data)
    build_html(data)
    write_readme(data)
    write_github_gallery(data)
    if not args.skip_pdf:
        pdf_path = build_pdf(data)
        print(f"Generated {pdf_path}")
    print(f"Generated {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
