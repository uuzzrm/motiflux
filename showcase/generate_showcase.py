#!/usr/bin/env python3
"""Generate the Motiflux theme comparison page and its printable PDF atlas."""

from __future__ import annotations

import argparse
import html
import json
import math
import random
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
ANIMATION_SIZE = (900, 302)
ANIMATION_FRAME_COUNT = 28
ANIMATION_FRAME_MS = 90
GROWTH_SEQUENCE = ("blank", "spark", "arc", "bar", "monogram", "wordmark", "canonical")

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
    "knowledge-graph-lock": {"mode": "grid", "timing": "standard", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "steps"},
    "contour-etch": {"mode": "contour", "timing": "slow", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "soft"},
    "token-commit": {"mode": "token", "timing": "staggered", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "linear"},
    "signal-convergence": {"mode": "convergence", "timing": "field", "letter_order": (1, 0, 2, 4, 3, 5), "easing": "ease_out"},
    "progress-confirm": {"mode": "radial", "timing": "center", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "smooth"},
    "boundary-unlock": {"mode": "boundary", "timing": "late", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "soft"},
    "burst-assembly": {"mode": "burst", "timing": "rapid", "letter_order": (0, 2, 4, 1, 3, 5), "easing": "ease_out"},
    "kinematic-lock": {"mode": "track", "timing": "standard", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "ease_out"},
    "impact-release": {"mode": "impact", "timing": "rapid", "letter_order": (0, 2, 4, 1, 3, 5), "easing": "ease_out"},
    "aperture-title": {"mode": "aperture", "timing": "late", "letter_order": (5, 4, 3, 2, 1, 0), "easing": "soft"},
    "organic-current": {"mode": "organic", "timing": "slow", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "soft"},
    "orbit-quest": {"mode": "orbit", "timing": "staggered", "letter_order": (0, 2, 4, 1, 3, 5), "easing": "ease_out"},
    "semantic-fade": {"mode": "fade", "timing": "late", "letter_order": (0, 1, 2, 3, 4, 5), "easing": "soft"},
}

PHASE_TIMINGS = {
    "standard": {"dot": (.03, .18), "arc": (.13, .40), "bar": (.33, .54), "stem": (.46, .70), "wordmark": (.63, .94)},
    "slow": {"dot": (.04, .22), "arc": (.16, .46), "bar": (.39, .60), "stem": (.53, .76), "wordmark": (.69, .96)},
    "staggered": {"dot": (.02, .18), "arc": (.12, .39), "bar": (.31, .56), "stem": (.48, .73), "wordmark": (.65, .95)},
    "field": {"dot": (.02, .20), "arc": (.11, .40), "bar": (.32, .55), "stem": (.47, .72), "wordmark": (.61, .95)},
    "center": {"dot": (.04, .20), "arc": (.14, .43), "bar": (.35, .57), "stem": (.49, .72), "wordmark": (.64, .95)},
    "late": {"dot": (.05, .23), "arc": (.18, .47), "bar": (.40, .62), "stem": (.54, .79), "wordmark": (.71, .97)},
    "rapid": {"dot": (.01, .13), "arc": (.09, .31), "bar": (.25, .45), "stem": (.38, .61), "wordmark": (.55, .91)},
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
        aliases = [str(item) for item in profile.get("aliases", [])]
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
            "growth_sequence": list(GROWTH_SEQUENCE),
            "construction_style": growth["construction_style"],
            "primary_motion": growth["primary_motion"],
            "wordmark_reveal": growth["wordmark_reveal"],
            "stagger": float(growth["stagger"]),
            "foreground_mode": foreground["mode"],
            "foreground_timing": foreground["timing"],
            "foreground_order": list(foreground["letter_order"]),
            "foreground_easing": foreground["easing"],
            "arc_start": float(growth["arc_start"]),
            "arc_direction": int(growth["arc_direction"]),
            "animation_file": f"assets/animations/prysai-{profile['id']}.gif",
            "animation_poster": f"assets/animations/prysai-{profile['id']}-poster.png",
        })
    return {
        "schema_version": "1.0",
        "source_catalog": "skills/motiflux/catalog/themes.json",
        "source": {
            "asset": "assets/prysai-logo-white.jpg",
            "label": "Prysai logo / supplied raster source",
            "identity_rule": "Use the same source mark in every theme. Change the foreground trajectory and motion language only.",
        },
        "request_example": {
            "user_says": "I want to make a logo animation for my artificial-intelligence company.",
            "agent_route": "AI-field",
            "routing_explanation": "The phrase artificial intelligence selects AI-field; deterministic signals converge into the supplied Logo pixels, then the Prysai wordmark assembles and holds canonical.",
        },
        "themes": themes,
    }


def write_snapshot(data: dict) -> None:
    """Persist a readable derived snapshot; never use it as routing input."""

    THEMES.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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
    value = hex_color.removeprefix("#")
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
        for index, (start, target) in enumerate(zip(points, targets)):
            travel = _smoothstep((progress - .04) / .72)
            x = round(start[0] + (target[0] - start[0]) * travel)
            y = round(start[1] + (target[1] - start[1]) * travel)
            radius = 1 + (index % 3 == 0)
            alpha = int(220 * (1 - _clamp((progress - .7) / .3)))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=_rgba(accent, max(24, alpha)))
        focus_x, focus_y = focus or (width // 2, height // 2)
        ring = int(min(width, height) * (.18 + (1 - p) * .3))
        draw.ellipse((focus_x - ring, focus_y - ring, focus_x + ring, focus_y + ring), outline=_rgba(accent, max(20, effect_alpha // 2)), width=1)
        ring_2 = int(ring * .68)
        draw.ellipse((focus_x - ring_2, focus_y - ring_2, focus_x + ring_2, focus_y + ring_2), outline=_rgba(accent, max(14, effect_alpha // 3)), width=1)
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


def _build_growth_components(mark: Image.Image, size: tuple[int, int]) -> dict[str, object]:
    """Build semantic masks from the supplied alpha without redrawing the logo."""

    target = _contain(mark, (int(size[0] * .68), int(size[1] * .76)))
    position = _center_position(size, target.size)
    alpha = mark.getchannel("A")
    raw = {name: _mask_in_box(alpha, box) for name, box in LOGO_COMPONENT_BOXES.items()}
    # Keep the dot independent so the construction can begin with one exact
    # source pixel cluster instead of a background-only flash.
    raw["monogram"] = ImageChops.subtract(raw["monogram_raw"], raw["origin_dot"])

    origin_dot = _place_mask(raw["origin_dot"], size, target.size, position)
    monogram = _place_mask(raw["monogram"], size, target.size, position)
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

    components: dict[str, object] = {
        "origin_dot": origin_dot,
        "arc": arc,
        "bar": bar,
        "stem": stem,
        "monogram": monogram,
        "wordmark": [
            _place_mask(raw[name], size, target.size, position)
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
    }
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
            start = start - sweep
            sweep = abs(sweep)
        gate = _sector_mask(mask.size, center, radius, start, sweep)
    return ImageChops.multiply(mask, gate)


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
) -> Image.Image:
    """Move a supplied component toward its canonical position for one route."""

    bbox = mask.getbbox()
    result = Image.new("L", mask.size, 0)
    if not bbox:
        return result
    t = _smoothstep(progress)
    scale_x = start_scale[0] + (1 - start_scale[0]) * t
    scale_y = start_scale[1] + (1 - start_scale[1]) * t
    crop = mask.crop(bbox)
    transformed = crop.resize((max(1, round(crop.width * scale_x)), max(1, round(crop.height * scale_y))), Image.Resampling.BICUBIC)
    if rotation and progress < 1:
        transformed = transformed.rotate(rotation * (1 - t), resample=Image.Resampling.BICUBIC, expand=True)
    target_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    dx = start_offset[0] * (1 - t)
    dy = start_offset[1] * (1 - t)
    if wave:
        amplitude_x, amplitude_y, phase = wave
        dx += math.sin(t * math.pi * 2 + phase) * amplitude_x * (1 - t)
        dy += math.cos(t * math.pi * 2 + phase) * amplitude_y * (1 - t)
    position = (
        round(target_center[0] + dx - transformed.width / 2),
        round(target_center[1] + dy - transformed.height / 2),
    )
    result.paste(transformed, position, transformed)
    return result


def _actor_sequence(components: dict) -> list[Image.Image]:
    return [components["origin_dot"], components["monogram"], *components["wordmark"]]


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


def _growth_stage(progress: float) -> str:
    """Return the public storyboard stage for a normalized frame position."""

    if progress < .03:
        return "blank"
    if progress < .16:
        return "spark"
    if progress < .33:
        return "arc"
    if progress < .47:
        return "bar"
    if progress < .64:
        return "monogram"
    if progress < .95:
        return "wordmark"
    return "canonical"


def _phase_windows(theme: dict) -> dict[str, tuple[float, float]]:
    timing = str(theme.get("foreground_timing", "standard"))
    return dict(PHASE_TIMINGS.get(timing, PHASE_TIMINGS["standard"]))


def _component_motion(
    mask: Image.Image,
    local: float,
    mode: str,
    component_index: int,
    components: dict,
) -> Image.Image:
    """Move an exact component through a route-specific construction path."""

    cx, cy = components["monogram_center"]
    bbox = mask.getbbox() or (cx, cy, cx + 1, cy + 1)
    actor_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    if mode == "burst":
        angle = math.radians(component_index * 42 - 120)
        radius = 64 + component_index * 12
        return _transform_mask(
            mask,
            local,
            start_offset=(cx - actor_center[0] + math.cos(angle) * radius, cy - actor_center[1] + math.sin(angle) * radius),
            start_scale=(.34, .34),
            rotation=8 if component_index % 2 else -8,
        )
    if mode == "impact":
        return _transform_mask(
            mask,
            local,
            start_offset=(-150 - component_index * 18, 0),
            start_scale=(.12, 1.0),
            rotation=-3 if component_index % 2 else 3,
        )
    if mode == "track":
        return _transform_mask(mask, local, start_offset=(-240 - component_index * 22, 0), start_scale=(.98, .98))
    if mode == "organic":
        return _transform_mask(
            mask,
            local,
            start_offset=(0, 68 - component_index * 12),
            wave=(18, 11, .4 + component_index * .38),
            rotation=2,
        )
    if mode == "orbit":
        angle = math.radians(component_index * 58 - 86)
        radius = 86 + (component_index % 3) * 30
        return _transform_mask(
            mask,
            local,
            start_offset=(cx - actor_center[0] + math.cos(angle) * radius, cy - actor_center[1] + math.sin(angle) * radius),
            start_scale=(.72, .72),
            rotation=12,
        )
    if mode == "token":
        return _transform_mask(mask, local, start_offset=(-24 - component_index * 8, 0), start_scale=(.96, .96))
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
) -> tuple[Image.Image, float, bool]:
    """Return a source-derived reveal mask, opacity, and glow flag."""

    if local <= .002:
        return Image.new("L", mask.size, 0), 0.0, False
    cx, cy = components["monogram_center"]
    moved = _component_motion(mask, local, mode, component_index, components)
    reveal_mode = "scan"
    if component == "arc":
        reveal_mode = "radial" if mode in {"radial", "orbit", "burst", "boundary"} else "scan"
        if mode in {"convergence", "organic"}:
            reveal_mode = "diagonal"
    elif component == "stem":
        reveal_mode = {"radial": "radial", "convergence": "diagonal", "organic": "diagonal"}.get(mode, "scan")
    elif component == "wordmark":
        reveal_mode = {
            "fade": "fade",
            "contour": "scan",
            "boundary": "scan",
            "convergence": "diagonal",
            "organic": "diagonal",
            "radial": "radial",
            "orbit": "radial",
        }.get(mode, "scan")

    if mode == "aperture":
        reveal = _aperture_mask(moved, local, cx)
    elif mode in {"contour", "boundary"}:
        outline = _mask_outline(moved, 5 if component != "wordmark" else 3)
        trace = _progressive_mask(outline, local, "scan", center=(cx, cy))
        fill = _progressive_mask(moved, _clamp((local - .48) / .52), "fade")
        reveal = ImageChops.lighter(trace, fill)
    elif mode == "fade":
        reveal = moved
    elif reveal_mode == "radial":
        start = float(theme.get("arc_start", 205)) + component_index * 17
        direction = int(theme.get("arc_direction", 1))
        reveal = _progressive_mask(moved, local, "radial", center=(cx, cy), start=start, direction=direction)
    else:
        reveal = _progressive_mask(moved, local, reveal_mode, center=(cx, cy), start=float(theme.get("arc_start", 205)), direction=int(theme.get("arc_direction", 1)))
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
    phase_components = (("dot", components["origin_dot"]), ("arc", components["arc"]), ("bar", components["bar"]), ("stem", components["stem"]))
    for component_index, (name, mask) in enumerate(phase_components):
        start, end = windows[name]
        local = _phase_progress(progress, start, end, easing)
        reveal, opacity, glow = _component_reveal(mask, local, mode, name, component_index, components, theme)
        _composite_logo_mask(canvas, reveal, opacity=opacity, glow=glow)
        if component_limit == name:
            return

    if component_limit in {"dot", "arc", "bar", "stem"}:
        return

    wordmarks = components["wordmark"]
    order = list(theme.get("foreground_order", profile["letter_order"]))
    word_start, word_end = windows["wordmark"]
    stagger = min(.05, float(theme.get("stagger", .05)) * .65)
    for position, letter_index in enumerate(order):
        letter_start = word_start + position * stagger
        local = _phase_progress(progress, letter_start, word_end, easing)
        reveal, opacity, glow = _component_reveal(wordmarks[letter_index], local, mode, "wordmark", 4 + position, components, theme)
        _composite_logo_mask(canvas, reveal, opacity=opacity, glow=glow)


def build_growth_components(mark: Image.Image, size: tuple[int, int]) -> dict[str, object]:
    """Public pure seam for tests and downstream render adapters."""

    return _build_growth_components(mark, size)


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
        for _ in range(22):
            x = rng.randrange(max(1, layer.width))
            y = rng.randrange(max(1, layer.height))
            radius = 1 + (rng.randrange(3) == 0)
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=_rgba(accent, int(90 * (1 - p))))
    elif trajectory == "progress-confirm":
        radius = max(24, min(layer.size) * .27)
        sweep = 360 * _clamp((progress - .04) / .86)
        draw.arc((cx - radius, cy - radius, cx + radius, cy + radius), -90, -90 + sweep, fill=_rgba(accent, 210), width=3)
        if p > .86:
            draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=_rgba(accent, 220))
    elif trajectory == "boundary-unlock":
        outline = _mask_outline(components["final"], 3)
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
    points: list[tuple[int, int]],
    targets: list[tuple[int, int]],
    seed: int,
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
    background = Image.new("RGBA", size, (*_rgb(theme["background"]), 255))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.ellipse((size[0] * .18, -size[1] * .45, size[0] * .82, size[1] * 1.45), fill=_rgba(theme["accent"], 20))
    background = Image.alpha_composite(background, glow.filter(ImageFilter.GaussianBlur(42)))

    if progress < .96:
        effects = Image.new("RGBA", size, (0, 0, 0, 0))
        _draw_animation_effect(effects, theme, progress, points, targets, seed, focus=components["monogram_center"])
        background.alpha_composite(effects)

    # Preserve a clean canonical final frame for comparison and downstream use.
    # Do not leave a transformed actor or guide underneath anti-aliased source
    # pixels; the last frame must be the supplied mark, not a composite variant.
    if progress >= .995:
        final = _contain(mark, (int(size[0] * .68), int(size[1] * .76)))
        background.alpha_composite(final, _center_position(size, final.size))
    else:
        _render_trajectory_mask(background, theme, progress, components, points, targets, seed)
        _draw_growth_guides(background, theme, progress, components, seed)
    return background.convert("RGB")


def build_animation_exports(data: dict) -> None:
    """Export one portable animated render for every routed theme."""

    ANIMATIONS.mkdir(parents=True, exist_ok=True)
    mark = Image.open(MARK_PNG).convert("RGBA")
    source = Image.open(CROP_JPG).convert("RGB")
    components = _build_growth_components(mark, ANIMATION_SIZE)
    for theme in data["themes"]:
        seed = sum((index + 1) * ord(character) for index, character in enumerate(theme["id"]))
        targets = _sample_logo_targets(mark, ANIMATION_SIZE, 110, seed)
        starts = _starting_points(ANIMATION_SIZE, len(targets), seed + 17)
        frames = [
            _render_animation_frame(theme, index / (ANIMATION_FRAME_COUNT - 1), mark, source, components, starts, targets, seed)
            for index in range(ANIMATION_FRAME_COUNT)
        ]
        gif_path = ANIMATIONS / Path(theme["animation_file"]).name
        frame_ms = max(20, round(theme["duration_ms"] / ANIMATION_FRAME_COUNT / 10) * 10)
        frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=frame_ms, loop=0, optimize=True, disposal=2)
        poster_path = ANIMATIONS / Path(theme["animation_poster"]).name
        frames[-1].save(poster_path, format="PNG", optimize=True)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def theme_card(theme: dict) -> str:
    algorithms = "".join(f"<li>{esc(item)}</li>" for item in theme["algorithm"])
    tags = "".join(f"<span class=\"tag\">{esc(item)}</span>" for item in [*theme["tags"], theme["trajectory_id"], theme["foreground_mode"]])
    beats = "<span>" + "</span><span>".join(esc(item) for item in theme["beats"]) + "</span>"
    letter_names = ("P", "r", "y", "s", "a", "i")
    letter_order = " > ".join(letter_names[index] for index in theme["foreground_order"])
    search_terms = [theme["name"], theme["trigger"], *theme["tags"], theme["foreground_mode"], theme["foreground_timing"]]
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
       <div class="motion-stage" data-motion-card data-effect="{esc(theme["pattern"])}" data-duration-ms="{esc(theme["duration_ms"])}" data-tempo="{esc(theme["tempo"])}" data-beats="{esc(" / ".join(theme["beats"]))}" data-animation-src="{esc(theme["animation_file"])}" data-poster-src="{esc(theme["animation_poster"])}" data-growth-sequence="{esc(" / ".join(theme["growth_sequence"]))}" data-state="playing">
         <div class="motion-effect motion-effect-a" aria-hidden="true"></div>
         <div class="motion-effect motion-effect-b" aria-hidden="true"></div>
         <div class="motion-effect motion-effect-c" aria-hidden="true"></div>
         <img class="growth-gif" src="{esc(theme["animation_file"])}" alt="{esc(theme["name"])} style: Prysai logo grows from a spark into the complete wordmark" loading="lazy">
         <img class="motion-freeze" hidden src="" alt="Paused frame of the logo growth animation" aria-hidden="true">
         <span class="motion-phase" data-motion-phase>blank</span>
      </div>
      <div class="motion-controls" aria-label="{esc(theme["name"])} animation controls">
        <button type="button" data-card-action="play">Play</button>
        <button type="button" data-card-action="pause">Pause</button>
        <button type="button" data-card-action="replay">Replay</button>
        <div class="motion-timeline" aria-hidden="true"><span data-motion-progress></span></div>
        <span class="motion-time" data-motion-time>0.0s</span>
      </div>
       <a class="download-animation" href="{esc(theme["animation_file"])}" download>Open / download growth GIF</a>
    </div>
  </div>
  <div class="card-copy">
    <div class="tag-row">{tags}</div>
     <p class="intent">{esc(theme["intent"])}</p>
     <p class="trajectory-note"><span>FOREGROUND TRAJECTORY</span>{esc(theme["trajectory_summary"])}</p>
     <p class="construction-note"><span>FOREGROUND CONTRACT</span><strong>{esc(theme["foreground_mode"])} / {esc(theme["foreground_timing"])} / {esc(theme["foreground_easing"])}</strong><small>stages: blank &gt; dot &gt; arc &gt; bar &gt; P &gt; letters &gt; canonical<br>letter order: {esc(letter_order)}</small></p>
    <div class="detail-grid">
      <div><span class="detail-label">ALGORITHM STACK</span><ul>{algorithms}</ul></div>
      <div><span class="detail-label">BEATS</span><div class="beats">{beats}</div><span class="detail-label qa-label">QA FOCUS</span><p>{esc(theme["qa"])}</p></div>
    </div>
     <p class="result-note"><span>GROWTH RESULT</span>{esc(theme["result"])} <small>{esc(" → ".join(theme["growth_sequence"]))}</small></p>
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
.io-showcase { margin: 3.2rem 0 2.5rem; border: 1px solid var(--line); background: linear-gradient(130deg, rgba(156,140,255,.08), transparent 46%), var(--panel); padding: 1.35rem; }
.io-heading { display: flex; justify-content: space-between; gap: 2rem; align-items: end; border-bottom: 1px solid var(--line); padding-bottom: 1.2rem; }
.io-heading .eyebrow { margin-bottom: .65rem; }
.io-heading h2 { margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: clamp(2rem, 4vw, 4rem); letter-spacing: -.07em; line-height: .95; }
.io-heading p:not(.eyebrow) { max-width: 630px; margin: .8rem 0 0; color: #c8cac4; font: 1rem/1.55 Arial, Helvetica, sans-serif; }
.io-badge { min-width: 145px; border-left: 1px solid var(--line); padding-left: 1rem; color: var(--muted); font-size: .61rem; line-height: 1.7; letter-spacing: .08em; }
.io-badge strong { color: var(--accent); font-size: .9rem; }
.io-flow { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1.55fr); gap: 1rem; align-items: center; padding: 1.2rem 0; }
.io-frame { position: relative; min-width: 0; margin: 0; aspect-ratio: 2.62; overflow: hidden; border: 1px solid var(--line); background: #000; display: grid; place-items: center; }
.io-frame img { width: 100%; height: 100%; object-fit: contain; }
.io-output { background: #14122b; }
.io-output img { object-fit: cover; }
.io-arrow { color: var(--accent); font-size: 2rem; }
.io-status { position: absolute; right: .8rem; bottom: .7rem; color: #e9e5ff; font-size: .6rem; letter-spacing: .08em; }
.io-footer { display: flex; align-items: center; gap: 1rem; border-top: 1px solid var(--line); padding-top: .9rem; color: var(--muted); font-size: .63rem; line-height: 1.5; }
.io-footer span { flex: 1; }
.io-footer a, .download-animation { color: var(--accent); text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--accent) 55%, transparent); }
.io-footer a:hover, .io-footer a:focus-visible, .download-animation:hover, .download-animation:focus-visible { border-color: var(--accent); }
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
@media (max-width: 720px) { .shell { width: min(100% - 28px, 640px); } .topbar { font-size: .62rem; } .hero { grid-template-columns: 1fr; padding-top: 4rem; } .hero-side { border-left: 0; padding-left: 0; grid-template-columns: 1fr 1fr; align-items: end; } .io-heading { display: block; } .io-badge { border-left: 0; border-top: 1px solid var(--line); margin-top: 1rem; padding: .8rem 0 0; } .io-flow { grid-template-columns: 1fr; } .io-arrow { transform: rotate(90deg); justify-self: center; } .io-footer { display: block; } .io-footer a { display: inline-block; margin: .6rem .8rem 0 0; } .route-brief { grid-template-columns: 1fr; } .route-cell { border-right: 0; border-bottom: 1px solid var(--line); } .route-cell:last-child { border-bottom: 0; } .theme-grid { grid-template-columns: 1fr; } .footer { display: block; } .footer p + p { margin-top: 1rem; } }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } .theme-card * { animation: none !important; } }
'''


MOTION_CSS = r'''
.motion-output { display: grid; grid-template-rows: 1fr auto; min-height: 205px; background: var(--stage-bg); }
.motion-stage { position: relative; min-height: 145px; display: grid; place-items: center; isolation: isolate; overflow: hidden; --motion-progress: 0; --motion-x: 0; --motion-y: 0; --motion-scale: .72; --motion-rotate: 0deg; --motion-opacity: .05; }
.growth-gif { position: relative; z-index: 3; width: 100%; height: 100%; object-fit: cover; image-rendering: auto; }
.motion-freeze { position: absolute; inset: 0; z-index: 4; width: 100%; height: 100%; object-fit: cover; }
.motion-effect { position: absolute; z-index: 1; pointer-events: none; opacity: 0; will-change: transform, opacity, background-position; }
.motion-effect-a { inset: 0; }
.motion-effect-b { inset: 12%; }
.motion-effect-c { inset: 20%; }
.motion-phase { position: absolute; z-index: 5; bottom: .58rem; right: .65rem; color: rgba(242,241,233,.72); font-size: .52rem; text-transform: uppercase; letter-spacing: .08em; }
.pattern-grid .motion-effect-a { background-image: linear-gradient(rgba(138,164,255,.2) 1px, transparent 1px), linear-gradient(90deg, rgba(138,164,255,.2) 1px, transparent 1px); background-size: 20px 20px; opacity: calc(var(--motion-progress) * .55); transform: translate3d(calc((1 - var(--motion-progress)) * -18%), 0, 0); }
.pattern-quiet .motion-effect-a { background: radial-gradient(circle at 50% 58%, color-mix(in srgb, var(--accent) 24%, transparent), transparent 65%); opacity: calc(var(--motion-progress) * .66); transform: scale(calc(.7 + var(--motion-progress) * .32)); }
.pattern-scan .motion-effect-a { background: repeating-linear-gradient(0deg, transparent 0 6px, color-mix(in srgb, var(--accent) 20%, transparent) 7px 8px); opacity: calc(var(--motion-progress) * .68); transform: translateY(calc((1 - var(--motion-progress)) * -35%)); }
.pattern-field .motion-effect-a { background: radial-gradient(circle at 20% 30%, var(--accent) 0 1px, transparent 2px), radial-gradient(circle at 76% 65%, var(--accent) 0 1px, transparent 2px), radial-gradient(circle at 48% 20%, #fff 0 1px, transparent 2px), radial-gradient(circle at 88% 38%, var(--accent) 0 1px, transparent 2px); background-size: 48px 42px, 61px 58px, 73px 71px, 54px 63px; opacity: calc((1 - var(--motion-progress)) * .9); transform: translate3d(calc((1 - var(--motion-progress)) * -12%), calc((1 - var(--motion-progress)) * 16%), 0) scale(calc(1.2 - var(--motion-progress) * .22)); }
.pattern-field .motion-effect-b { border: 1px solid color-mix(in srgb, var(--accent) 56%, transparent); border-radius: 50%; opacity: calc((1 - var(--motion-progress)) * .7); transform: scale(calc(1.35 - var(--motion-progress) * .45)); }
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
.motion-controls { display: flex; align-items: center; gap: .3rem; padding: .45rem .55rem .55rem; background: color-mix(in srgb, #000 20%, transparent); }
.motion-controls button { padding: .3rem .42rem; font-size: .55rem; }
.download-animation { display: block; padding: .45rem .55rem .6rem; background: color-mix(in srgb, #000 20%, transparent); font-size: .57rem; }
.motion-timeline { flex: 1; min-width: 26px; height: 2px; background: color-mix(in srgb, var(--accent) 22%, transparent); overflow: hidden; }
.motion-timeline span { display: block; width: 0; height: 100%; background: var(--accent); transition: width .08s linear; }
.motion-time { color: rgba(242,241,233,.65); font-size: .52rem; min-width: 2.1rem; text-align: right; }
body[data-motion="paused"] .motion-stage { outline: 1px solid color-mix(in srgb, var(--accent) 42%, transparent); outline-offset: -1px; }
body[data-motion="reduced"] .motion-effect { display: none; }
body[data-motion="reduced"] .growth-gif { filter: none; }
@media (max-width: 720px) { .motion-stage { min-height: 155px; } .motion-controls { flex-wrap: wrap; } .motion-timeline { flex-basis: 100%; order: 5; } }
'''


JS = r'''(() => {
  "use strict";
  const body = document.body;
  const cards = [...document.querySelectorAll(".theme-card")];
  const stages = [...document.querySelectorAll("[data-motion-card]")];
  const filter = document.querySelector("[data-filter]");
  const status = document.querySelector("[data-filter-status]");
  const prefersReduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const presets = {
    grid: [-28, 16, -6, .78], quiet: [0, 10, 0, .9], scan: [-26, 0, 0, .8],
    field: [-10, 22, -8, .72], ring: [0, 0, -22, .78], shield: [0, 24, 0, .74],
    burst: [0, 0, -18, .76], track: [-42, 0, 0, .8], speed: [-48, 6, -10, .7],
    curtain: [0, 0, 0, .84], wave: [16, 22, 8, .76], orbit: [0, -16, 16, .78],
    plain: [0, 12, 0, .86]
  };
  const players = [];
  let motion = prefersReduced ? "reduced" : "running";
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const ease = (value, effect) => {
    const p = clamp(value, 0, 1);
    if (effect === "speed" || effect === "burst") return 1 - Math.pow(1 - p, 3);
    if (effect === "quiet" || effect === "curtain") return p * p * (3 - 2 * p);
    if (effect === "wave" || effect === "orbit") return p < .78 ? p / .78 : 1 - Math.pow((1 - p) / .22, 2) * .035;
    return 1 - Math.pow(1 - p, 2.4);
  };
  function phaseFor(progress) {
    if (progress < .08) return "blank";
    if (progress < .18) return "spark";
    if (progress < .38) return "arc";
    if (progress < .52) return "bar";
    if (progress < .66) return "monogram";
    if (progress < .94) return "wordmark";
    return "canonical";
  }
  function render(player, progress) {
    const p = clamp(progress, 0, 1);
    player.stage.style.setProperty("--motion-progress", p.toFixed(4));
    player.stage.dataset.state = phaseFor(p);
    if (player.phase) player.phase.textContent = phaseFor(p);
    if (player.progress) player.progress.style.width = `${p * 100}%`;
    if (player.time) player.time.textContent = `${(p * player.duration / 1000).toFixed(1)}s`;
  }
  function showGif(player, restart) {
    if (!player.gif) return;
    player.gif.src = restart ? `${player.src}?play=${Date.now()}` : player.src;
    player.gif.hidden = false;
    if (player.poster) player.poster.hidden = true;
  }
  function showPoster(player, source) {
    if (!player.gif) return;
    player.gif.hidden = true;
    if (player.poster) {
      player.poster.src = source || player.posterSrc;
      player.poster.hidden = false;
    }
  }
  function freezeCurrentFrame(player) {
    if (!player.gif || !player.gif.complete || !player.gif.naturalWidth) { showPoster(player); return; }
    const canvas = document.createElement("canvas");
    canvas.width = player.gif.naturalWidth;
    canvas.height = player.gif.naturalHeight;
    try {
      canvas.getContext("2d").drawImage(player.gif, 0, 0);
      showPoster(player, canvas.toDataURL("image/png"));
    } catch (error) {
      // A local GIF should be readable; keep the canonical poster as a safe fallback.
      showPoster(player);
    }
  }
  function stop(player) { player.playing = false; if (player.frame) cancelAnimationFrame(player.frame); player.frame = 0; }
  function tick(player, timestamp) {
    if (!player.playing || motion === "paused" || motion === "reduced") return;
    if (player.last === null) player.last = timestamp;
    player.current += timestamp - player.last;
    player.last = timestamp;
    const progress = clamp(player.current / player.duration, 0, 1);
    render(player, progress);
    if (progress >= 1) { stop(player); render(player, 1); showPoster(player); } else player.frame = requestAnimationFrame((next) => tick(player, next));
  }
  function play(player) {
    if (prefersReduced) { render(player, 1); showPoster(player); return; }
    // A portable GIF cannot seek. Resume by restarting it so the timer and pixels agree.
    const restart = player.current > 0 || player.paused || player.current >= player.duration;
    if (restart) { player.current = 0; render(player, 0); }
    player.paused = false;
    showGif(player, restart);
    player.playing = true; player.last = null; if (!player.frame) player.frame = requestAnimationFrame((next) => tick(player, next));
  }
  function pause(player) { stop(player); player.paused = true; freezeCurrentFrame(player); }
  function replay(player) { stop(player); player.current = 0; player.paused = false; render(player, 0); showGif(player, true); play(player); }
  stages.forEach((stage) => {
    const player = { stage, effect: stage.dataset.effect || "plain", duration: Number(stage.dataset.durationMs || 1800), current: 0, last: null, playing: false, paused: false, frame: 0, src: stage.dataset.animationSrc || "", posterSrc: stage.dataset.posterSrc || "", gif: stage.querySelector(".growth-gif"), poster: stage.querySelector(".motion-freeze"), phase: stage.querySelector("[data-motion-phase]"), progress: stage.closest(".motion-output")?.querySelector("[data-motion-progress]"), time: stage.closest(".motion-output")?.querySelector("[data-motion-time]") };
    player.playButton = stage.closest(".motion-output")?.querySelector('[data-card-action="play"]');
    player.pauseButton = stage.closest(".motion-output")?.querySelector('[data-card-action="pause"]');
    player.replayButton = stage.closest(".motion-output")?.querySelector('[data-card-action="replay"]');
    player.playButton?.addEventListener("click", () => { setMotion("running"); play(player); });
    player.pauseButton?.addEventListener("click", () => pause(player));
    player.replayButton?.addEventListener("click", () => { setMotion("running"); replay(player); });
    players.push(player);
    render(player, prefersReduced ? 1 : 0);
    if (prefersReduced) showPoster(player); else play(player);
  });
  function setMotion(next) {
    motion = next;
    body.dataset.motion = next;
    document.querySelectorAll("[data-motion-label]").forEach((node) => {
      node.textContent = next === "reduced" ? "REDUCED" : next.toUpperCase();
    });
  }
  function replayAll() {
    players.forEach(replay);
    setMotion(prefersReduced ? "reduced" : "running");
  }
  document.querySelector("[data-action=play]")?.addEventListener("click", () => { setMotion("running"); players.forEach(play); });
  document.querySelector("[data-action=pause]")?.addEventListener("click", () => { setMotion("paused"); players.forEach(pause); });
  document.querySelector("[data-action=replay]")?.addEventListener("click", replayAll);
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
  document.addEventListener("visibilitychange", () => { if (document.hidden) players.forEach(pause); });
  setMotion(motion);
  window.__motifluxShowcaseReady = true;
  window.__motifluxShowcaseControl = { play: () => { setMotion("running"); players.forEach(play); }, pause: () => { setMotion("paused"); players.forEach(pause); }, replay: replayAll, setMotion };
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
  <link rel="icon" type="image/jpeg" href="assets/prysai-logo-white.jpg">
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
          <h1 id="page-title">One image.<br>Thirteen animations.</h1>
           <p class="hero-copy">The source stays fixed. The output grows. This atlas shows how Motiflux turns the same supplied Prysai image into thirteen playable logo-construction results. Algorithm families remain available as explanation, not as the thing being displayed.</p>
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
      <section class="io-showcase" aria-labelledby="io-title">
        <div class="io-heading">
          <div>
            <p class="eyebrow">Actual rendered output / AI-field route</p>
            <h2 id="io-title">From image to animation.</h2>
           <p>Give the skill one logo image and a request such as “make an AI company logo animation.” Motiflux routes it to AI-field, keeps the source mark intact, and returns a portable GIF that grows it from a blank field to a complete logo.</p>
          </div>
          <div class="io-badge">INPUT → OUTPUT<br><strong>JPG → GIF</strong></div>
        </div>
        <div class="io-flow">
          <figure class="io-frame io-source"><span class="cell-label">INPUT / SUPPLIED IMAGE</span><img src="assets/prysai-mark-crop.jpg" alt="Supplied Prysai logo image"></figure>
          <div class="io-arrow" aria-hidden="true">→</div>
          <figure class="io-frame io-output"><span class="cell-label">OUTPUT / LOGO GROWTH GIF</span><img src="assets/animations/prysai-ai-field.gif" alt="Prysai logo growing from blank through the AI-field theme"><span class="io-status">AI-FIELD / PLAYING GIF</span></figure>
        </div>
         <div class="io-footer"><span>Same identity source / spark (source dot) → arc → bar → monogram → wordmark → canonical</span><a href="assets/animations/prysai-ai-field.gif" download>Download AI-field GIF</a><a href="#theme-atlas">Compare all 13 routes</a></div>
      </section>
      <section class="route-brief" aria-labelledby="route-title">
        <div class="route-cell"><span id="route-title" class="route-label">Example request</span><p class="route-value">“I want to make a logo animation for my artificial-intelligence company.”</p></div>
        <div class="route-cell"><span class="route-label">AI-field animation</span><p class="route-value"><strong>AI-field</strong><br>the supplied image becomes a signal-convergence reveal</p></div>
         <div class="route-cell"><span class="route-label">What the viewer sees</span><p class="route-value">Blank field → spark (source dot) → arc → bar → P construction → wordmark → stable logo. Each card is a direct GIF output.</p></div>
      </section>
      <section id="theme-atlas" aria-labelledby="grid-title">
        <div class="controls">
          <div><div id="grid-title" class="controls-copy">Theme animation atlas / algorithm notes are secondary</div><div data-filter-status class="controls-copy">13 of 13 animations shown</div></div>
          <div class="controls-actions"><input class="filter" data-filter type="search" placeholder="Filter by theme or keyword" aria-label="Filter themes"><button type="button" data-action="play">Play all</button><button type="button" data-action="pause">Pause</button><button type="button" data-action="replay">Replay</button><span class="route-state" data-motion-label>RUNNING</span></div>
        </div>
        <div class="theme-grid">{theme_markup}</div>
      </section>
    </main>
     <footer class="footer"><p>Motiflux V1 is an AI skill for source-aware logo growth: the source image stays recognizable while the selected theme changes the construction choreography.</p><p>The HTML and GitHub README expose portable GIF outputs. The PDF is a static storyboard of the same image-to-animation sequences. Public design systems are principle analogues only; no private vendor recipe is claimed.</p></footer>
  </div>
  <script src="app.js"></script>
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


STORYBOARD_PROGRESS = {"blank": 0.0, "spark": .16, "monogram": .52, "wordmark": .76, "canonical": 1.0}
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
    frame_index = round(STORYBOARD_PROGRESS[frame] * (len(frames) - 1))
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
    stage_y = y + height - header_h - 105
    stage_h = 95
    gap = 4
    frame_width = (width - 6*gap) / 5
    for frame_index, frame in enumerate(("blank", "spark", "monogram", "wordmark", "canonical")):
        frame_x = x + gap + frame_index * (frame_width + gap)
        draw_storyboard_frame(canvas, frame_x, stage_y, frame_width, stage_h, frame=frame, theme=theme)
        canvas.setFillColor(muted); canvas.setFont("Courier", 4.7); canvas.drawCentredString(frame_x + frame_width/2, stage_y - 8, frame.upper())
    canvas.setStrokeColor(line); canvas.line(x, stage_y - 13, x + width, stage_y - 13)
    text_y = stage_y - 26
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
        "Animation: blank field -> spark (source dot) -> arc -> bar -> monogram -> wordmark",
        "-> canonical. The HTML and GIF are playable; this PDF records growth",
        "frames for the same supplied image.",
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
        pdf.setFillColor(muted); pdf.setFont("Courier", 6); pdf.drawString(margin_x, 14, "Same source image / five-frame growth storyboards")
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
python showcase\\generate_showcase.py
```

The HTML presents the actual image-to-animation result first. The PDF includes
the route example `artificial-intelligence` -> `AI-field` and records five growth
frames of each playable animation. Public design systems are principle analogues
only; this material does not claim private vendor algorithms.
'''
    (ROOT / "README.md").write_text(text, encoding="utf-8")


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
    args = parser.parse_args()
    data = load_data()
    if len(data.get("themes", [])) != 13:
        raise ValueError("showcase requires exactly 13 theme records")
    derive_preview_assets()
    write_snapshot(data)
    build_animation_exports(data)
    build_html(data)
    write_readme(data)
    write_github_gallery(data)
    if not args.skip_pdf:
        pdf_path = build_pdf(data)
        print(f"Generated {pdf_path}")
    print(f"Generated {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
