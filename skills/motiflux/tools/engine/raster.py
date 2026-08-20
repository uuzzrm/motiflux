"""Deterministic raster observations for the Motiflux source-analysis seam.

This module deliberately stops at image observations.  It can identify a
foreground mask, connected components, and explainable role candidates, but it
does not trace pixels into paths or claim that a raster logo has been
reconstructed as a vector scene.

The public seam is :func:`analyze_raster`.  Lower-level mask and component
functions are exposed for focused callers and tests.  Pillow is an optional
decoder: when it is unavailable, ``analyze_raster`` returns the existing
header-only candidate shape instead of changing the pipeline's dependency
contract.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable, Sequence

try:  # The command adapters import ``motiflux_core`` as a top-level module.
    from motiflux_core import SCHEMA_VERSION, parse_raster_header, source_format
except ImportError:  # pragma: no cover - package import fallback
    from ..motiflux_core import SCHEMA_VERSION, parse_raster_header, source_format


Pixel = tuple[int, int, int, int]
Mask = list[bool]

ROLE_ORDER = ("origin-dot", "arc", "bar", "monogram", "wordmark", "unknown")
ROLE_PRIORITY = {role: index for index, role in enumerate(ROLE_ORDER)}
NEIGHBOURS_8 = (
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
)
NEIGHBOURS_4 = ((0, -1), (-1, 0), (1, 0), (0, 1))


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _rounded(value: float, digits: int = 4) -> float | int:
    rounded = round(float(value), digits)
    return int(rounded) if math.isclose(rounded, round(rounded), abs_tol=1e-9) else rounded


def _median(values: Sequence[int | float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _percentile(values: Sequence[int | float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    position = _clamp(fraction) * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _normalise_pixels(
    pixels: Sequence[Any], width: int | None, height: int | None
) -> tuple[list[Pixel], int, int]:
    """Accept either a flat pixel sequence or height rows of pixels."""

    if width is None or height is None:
        if not pixels or not isinstance(pixels[0], (list, tuple)):
            raise ValueError("width and height are required for flat pixels")
        height = len(pixels)
        width = len(pixels[0])
    if width <= 0 or height <= 0:
        raise ValueError("pixel dimensions must be positive")

    expected = width * height
    first = pixels[0] if pixels else None
    if isinstance(first, (list, tuple)) and len(pixels) == height and (
        not first or isinstance(first[0], (list, tuple))
    ):
        flattened = [pixel for row in pixels for pixel in row]
    else:
        flattened = list(pixels)
    if len(flattened) != expected:
        raise ValueError(f"pixel count {len(flattened)} does not match {width}x{height}")

    normalised: list[Pixel] = []
    for pixel in flattened:
        if not isinstance(pixel, (list, tuple)) or len(pixel) not in {3, 4}:
            raise ValueError("each pixel must contain RGB or RGBA channels")
        channels = tuple(max(0, min(255, int(channel))) for channel in pixel)
        normalised.append((channels[0], channels[1], channels[2], channels[3] if len(channels) == 4 else 255))
    return normalised, width, height


def _border_indices(width: int, height: int) -> list[int]:
    """Return a bounded, row-major border sample without duplicate indices."""

    step = max(1, min(width, height) // 64)
    indices: set[int] = set()
    for x in range(0, width, step):
        indices.add(x)
        indices.add((height - 1) * width + x)
    for y in range(0, height, step):
        indices.add(y * width)
        indices.add(y * width + width - 1)
    return sorted(indices)


def _background_estimate(pixels: Sequence[Pixel], width: int, height: int) -> dict[str, Any]:
    border = [pixels[index] for index in _border_indices(width, height)]
    transparent = [pixel[3] <= 16 for pixel in border]
    transparent_fraction = sum(transparent) / max(1, len(transparent))
    opaque_border = [pixel for pixel in border if pixel[3] > 16]
    colour_source = opaque_border or border
    background_rgb = [int(round(_median([pixel[channel] for pixel in colour_source]))) for channel in range(3)]
    border_distances = [
        max(abs(pixel[channel] - background_rgb[channel]) for channel in range(3))
        for pixel in colour_source
    ]
    noise = _percentile(border_distances, 0.95)
    threshold = int(round(_clamp(max(10.0, noise * 2.0 + 6.0), 10.0, 48.0)))
    if transparent_fraction >= 0.10:
        mode = "transparent"
    elif border_distances and noise <= 6:
        mode = "opaque-solid"
    else:
        mode = "opaque-estimated"
    return {
        "mode": mode,
        "estimated_rgb": background_rgb,
        "border_sample_count": len(border),
        "transparent_border_fraction": _rounded(transparent_fraction),
        "colour_noise_p95": _rounded(noise),
        "colour_distance_threshold": threshold,
    }


def foreground_mask(
    pixels: Sequence[Any],
    width: int | None = None,
    height: int | None = None,
    *,
    alpha_threshold: int = 16,
) -> dict[str, Any]:
    """Build a deterministic foreground mask from RGB/RGBA pixels.

    Transparent borders are treated as the background when present.  For
    opaque images, the background is estimated from border pixels and a fixed
    colour-distance threshold derived from border noise.  The result includes
    the in-memory boolean mask for callers that need it; source-analysis JSON
    uses the compact RLE representation produced by :func:`encode_mask`.
    """

    normalised, width, height = _normalise_pixels(pixels, width, height)
    background = _background_estimate(normalised, width, height)
    background_rgb = background["estimated_rgb"]
    threshold = int(background["colour_distance_threshold"])
    mask: Mask = []
    if background["mode"] == "transparent":
        mask = [pixel[3] > alpha_threshold for pixel in normalised]
    else:
        for pixel in normalised:
            distance = max(abs(pixel[channel] - background_rgb[channel]) for channel in range(3))
            mask.append(distance > threshold)

    foreground_pixels = sum(mask)
    background["alpha_threshold"] = alpha_threshold
    background["foreground_pixels"] = foreground_pixels
    background["foreground_coverage"] = _rounded(foreground_pixels / max(1, width * height))
    return {"mask": mask, "width": width, "height": height, "background": background}


def encode_mask(mask: Sequence[bool], width: int, height: int) -> dict[str, Any]:
    """Encode a row-major mask as deterministic ``start``/``length`` runs."""

    if width <= 0 or height <= 0 or len(mask) != width * height:
        raise ValueError("mask dimensions do not match the supplied pixels")
    runs: list[dict[str, int]] = []
    index = 0
    while index < len(mask):
        if not mask[index]:
            index += 1
            continue
        start = index
        index += 1
        while index < len(mask) and mask[index]:
            index += 1
        runs.append({"start": start, "length": index - start})
    foreground_pixels = sum(run["length"] for run in runs)
    return {
        "encoding": "row-major-rle-v1",
        "width": width,
        "height": height,
        "foreground_pixels": foreground_pixels,
        "background_pixels": width * height - foreground_pixels,
        "coverage": _rounded(foreground_pixels / max(1, width * height)),
        "runs": runs,
    }


def connected_components(
    mask: Sequence[bool],
    width: int,
    height: int,
    *,
    connectivity: int = 8,
) -> list[dict[str, Any]]:
    """Return row-major connected components with pixel geometry metrics."""

    if width <= 0 or height <= 0 or len(mask) != width * height:
        raise ValueError("mask dimensions do not match the supplied pixels")
    if connectivity not in {4, 8}:
        raise ValueError("connectivity must be 4 or 8")
    neighbours = NEIGHBOURS_8 if connectivity == 8 else NEIGHBOURS_4
    visited = bytearray(len(mask))
    components: list[dict[str, Any]] = []
    for start in range(len(mask)):
        if not mask[start] or visited[start]:
            continue
        stack = [start]
        visited[start] = 1
        indices: list[int] = []
        min_x = width
        min_y = height
        max_x = -1
        max_y = -1
        sum_x = 0.0
        sum_y = 0.0
        while stack:
            index = stack.pop()
            indices.append(index)
            x, y = index % width, index // width
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
            sum_x += x + 0.5
            sum_y += y + 0.5
            for dx, dy in neighbours:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    neighbour_index = ny * width + nx
                    if mask[neighbour_index] and not visited[neighbour_index]:
                        visited[neighbour_index] = 1
                        stack.append(neighbour_index)

        area = len(indices)
        component_width = max_x - min_x + 1
        component_height = max_y - min_y + 1
        index_set = set(indices)
        perimeter = 0
        for index in indices:
            x, y = index % width, index // width
            for dx, dy in NEIGHBOURS_4:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < width and 0 <= ny < height) or ny * width + nx not in index_set:
                    perimeter += 1
        bounds_area = component_width * component_height
        circularity = (4.0 * math.pi * area / (perimeter * perimeter)) if perimeter else 0.0
        components.append(
            {
                "scan_order": len(components),
                "pixel_indices": indices,
                "bounds": {"x": min_x, "y": min_y, "width": component_width, "height": component_height},
                "area": area,
                "centroid": {"x": _rounded(sum_x / area), "y": _rounded(sum_y / area)},
                "geometry": {
                    "aspect_ratio": _rounded(component_width / max(1, component_height)),
                    "fill_ratio": _rounded(area / max(1, bounds_area)),
                    "perimeter": perimeter,
                    "circularity": _rounded(_clamp(circularity)),
                    "edge_touching": min_x == 0 or min_y == 0 or max_x == width - 1 or max_y == height - 1,
                },
            }
        )
    return components


def _role_score(value: float) -> float:
    return round(_clamp(value), 4)


def _distance_from_center(component: dict[str, Any], bounds: dict[str, int]) -> float:
    centroid = component["centroid"]
    center_x = bounds["x"] + bounds["width"] / 2.0
    center_y = bounds["y"] + bounds["height"] / 2.0
    diagonal = math.hypot(bounds["width"], bounds["height"]) or 1.0
    return _clamp(math.hypot(centroid["x"] - center_x, centroid["y"] - center_y) / diagonal * 2.0)


def _union_bounds(components: Sequence[dict[str, Any]]) -> dict[str, int] | None:
    if not components:
        return None
    left = min(item["bounds"]["x"] for item in components)
    top = min(item["bounds"]["y"] for item in components)
    right = max(item["bounds"]["x"] + item["bounds"]["width"] for item in components)
    bottom = max(item["bounds"]["y"] + item["bounds"]["height"] for item in components)
    return {"x": left, "y": top, "width": right - left, "height": bottom - top}


def _wordmark_group_score(components: Sequence[dict[str, Any]], content: dict[str, int] | None) -> tuple[set[int], float]:
    if not content or len(components) < 2:
        return set(), 0.0
    # A wordmark is usually a horizontal run on the right of a symbol.  Use
    # that spatial fact before aspect-ratio heuristics: glyphs such as ``r``
    # and ``i`` are not wide, and an isolated i-dot is often its own
    # connected component.  This remains a hypothesis, not semantic truth.
    wordmark_left = content["x"] + content["width"] * 0.27
    candidates = [
        item
        for item in components
        if item["centroid"]["x"] >= wordmark_left
        and max(2, int(content["height"] * 0.24)) <= item["bounds"]["height"] <= max(2, int(content["height"] * 0.84))
    ]
    if len(candidates) < 2:
        return set(), 0.0
    candidates.sort(key=lambda item: (item["centroid"]["x"], item["centroid"]["y"], item["scan_order"]))
    # Glyphs with ascenders (for example a capital P) can have a centroid
    # above the rest of the wordmark. Use the shared bottom edge as the
    # baseline signal so a tall first glyph is not misclassified as a symbol.
    baseline = _median([item["bounds"]["y"] + item["bounds"]["height"] for item in candidates])
    aligned = [
        item
        for item in candidates
        if abs((item["bounds"]["y"] + item["bounds"]["height"]) - baseline)
        <= max(2.0, content["height"] * 0.22)
    ]
    if len(aligned) < 2:
        return set(), 0.0
    left = min(item["bounds"]["x"] for item in aligned)
    right = max(item["bounds"]["x"] + item["bounds"]["width"] for item in aligned)
    height = max(item["bounds"]["height"] for item in aligned)
    span_ratio = (right - left) / max(1, height)
    score = _role_score(0.45 * _clamp((span_ratio - 2.0) / 5.0) + 0.35 * _clamp(len(aligned) / 5.0) + 0.20)
    wordmark_indices = {item["scan_order"] for item in aligned}
    # Attach small accents (for example the dot above ``i``) to the nearest
    # aligned body component when they sit inside the same horizontal run.
    for item in components:
        if item["scan_order"] in wordmark_indices:
            continue
        bounds = item["bounds"]
        if bounds["height"] > max(2, int(content["height"] * 0.30)):
            continue
        if not (left - max(2, height * 0.35) <= item["centroid"]["x"] <= right + max(2, height * 0.35)):
            continue
        if abs((item["bounds"]["y"] + item["bounds"]["height"]) - baseline) <= max(4.0, content["height"] * 0.75):
            wordmark_indices.add(item["scan_order"])
    return wordmark_indices, score


def classify_components(
    components: Sequence[dict[str, Any]],
    width: int,
    height: int,
) -> dict[str, Any]:
    """Attach explainable role candidates and a stable geometric order."""

    content = _union_bounds(components)
    total_pixels = max(1, width * height)
    content_area = max(1, content["width"] * content["height"]) if content else total_pixels
    wordmark_indices, group_score = _wordmark_group_score(components, content)
    symbol_indices = {item["scan_order"] for item in components if item["scan_order"] not in wordmark_indices}
    group_confidence = "medium" if group_score >= 0.60 else "low"
    enriched: list[dict[str, Any]] = []
    for component in components:
        item = {key: value for key, value in component.items() if key != "pixel_indices"}
        bounds = item["bounds"]
        geometry = item["geometry"]
        aspect = float(geometry["aspect_ratio"])
        elongation = max(aspect, 1.0 / max(aspect, 0.001))
        area_share = item["area"] / total_pixels
        content_share = item["area"] / content_area
        compactness = _clamp(1.0 - abs(math.log(max(aspect, 0.001))) / math.log(4.0))
        small = _clamp(1.0 - content_share / 0.12)
        leftness = _clamp(1.0 - (item["centroid"]["x"] - (content["x"] if content else 0)) / max(1, (content["width"] if content else width)))
        central = 1.0 - _distance_from_center(item, content or {"x": 0, "y": 0, "width": width, "height": height})
        thin = _clamp((elongation - 1.0) / 5.0)
        wide = _clamp((aspect - 2.0) / 5.0)
        medium = _clamp(1.0 - abs(math.log(max(aspect, 0.001))) / math.log(3.0))
        scores = {
            "origin-dot": _role_score(0.52 * small + 0.30 * compactness + 0.18 * leftness),
            "arc": _role_score(
                0.42 * _clamp((0.68 - float(geometry["fill_ratio"])) / 0.68)
                + 0.32 * medium
                + 0.16 * float(geometry["circularity"])
                + 0.10 * _clamp(content_share / 0.30)
            ),
            "bar": _role_score(0.68 * thin + 0.20 * float(geometry["fill_ratio"]) + 0.12 * _clamp(area_share / 0.20)),
            "monogram": _role_score(
                0.34 * central
                + 0.28 * _clamp(content_share / 0.45)
                + 0.20 * compactness
                + 0.18 * float(geometry["fill_ratio"])
            ),
            "wordmark": _role_score(0.54 * wide + 0.20 * _clamp(bounds["height"] / max(1, (content["height"] if content else height))) + 0.26 * (group_score if component["scan_order"] in wordmark_indices else 0.0)),
            "unknown": 0.18,
        }
        if component["scan_order"] in wordmark_indices and group_score >= 0.45:
            scores["wordmark"] = max(scores["wordmark"], group_score)
        ordered_roles = sorted(ROLE_ORDER, key=lambda role: (-scores[role], ROLE_PRIORITY[role]))
        selected = ordered_roles[0]
        if selected != "unknown" and scores[selected] < 0.35:
            selected = "unknown"
        candidates = [
            {
                "role": role,
                "score": scores[role],
                "confidence": "medium" if scores[role] >= 0.55 else "low",
            }
            for role in ordered_roles
        ]
        item["role_candidates"] = candidates
        # This adapter may score and order hypotheses, but it never accepts a
        # semantic raster role. The proposal remains in role_candidates and
        # role_review; planner.py performs the same normalization at handoff.
        item["selected_role"] = "unknown"
        item["layout_group"] = "wordmark" if component["scan_order"] in wordmark_indices else "symbol"
        item["group_confidence"] = group_confidence if wordmark_indices else "low"
        item["heuristic_basis"] = {
            "small_relative_to_content": _rounded(small),
            "compactness": _rounded(compactness),
            "elongation": _rounded(elongation),
            "fill_ratio": geometry["fill_ratio"],
            "centrality": _rounded(central),
            "wordmark_group_score": group_score if component["scan_order"] in wordmark_indices else 0,
        }
        selected_candidate = next(
            (candidate for candidate in candidates if candidate["role"] == selected),
            {"confidence": "low"},
        )
        item["role_review"] = {
            "proposed_role": selected,
            "accepted_role": None,
            "confidence": selected_candidate.get("confidence", "low"),
            "review_status": "needs-review",
            "evidence": "connected-component geometry, layout grouping, and deterministic role scores only",
        }
        enriched.append(item)

    enriched.sort(
        key=lambda item: (
            ROLE_PRIORITY.get(selected, ROLE_PRIORITY["unknown"]),
            item["centroid"]["y"],
            item["centroid"]["x"],
            -item["area"],
            item["scan_order"],
        )
    )
    for order, item in enumerate(enriched):
        item["id"] = f"raster-component-{order + 1:03d}"
        item["sort_order"] = order
    return {
        "components": enriched,
        "content_bounds": content,
        "layout_groups": [
            {
                "id": "symbol",
                "role": "identity-symbol-candidate",
                "component_ids": [item["id"] for item in enriched if item["scan_order"] in symbol_indices],
                "confidence": "medium" if symbol_indices else "low",
                "basis": "components outside the horizontal wordmark hypothesis",
            },
            {
                "id": "wordmark",
                "role": "wordmark-candidate",
                "component_ids": [item["id"] for item in enriched if item["scan_order"] in wordmark_indices],
                "confidence": group_confidence,
                "basis": "right-side components aligned on a shared baseline, with nearby small accents attached",
            },
        ],
        "ordering": {
            "strategy": "role-priority, then centroid-y, centroid-x, area-desc, scan-order",
            "component_ids": [item["id"] for item in enriched],
            "role_priority": list(ROLE_ORDER),
            "rationale": "Use geometry only to propose a stable reveal order; review role assignments before animation planning.",
        },
        "role_hypotheses": [
            {
                "role": "wordmark",
                "component_ids": [enriched[index]["id"] for index, item in enumerate(enriched) if item["scan_order"] in wordmark_indices],
                "score": group_score,
                "basis": "multiple short components with a shared baseline and horizontal span",
            }
        ]
        if wordmark_indices
        else [],
    }


def _colour_summary(pixels: Sequence[Pixel], mask: Sequence[bool]) -> list[dict[str, Any]]:
    counts: dict[tuple[int, int, int], int] = {}
    for pixel, visible in zip(pixels, mask):
        if not visible:
            continue
        rgb = tuple((channel // 16) * 16 for channel in pixel[:3])
        counts[rgb] = counts.get(rgb, 0) + 1
    total = sum(counts.values())
    records = []
    for rgb, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:8]:
        records.append({"rgb": list(rgb), "count": count, "share": _rounded(count / max(1, total))})
    return records


def analyze_pixels(
    pixels: Sequence[Any],
    width: int | None = None,
    height: int | None = None,
    *,
    connectivity: int = 8,
    alpha_threshold: int = 16,
) -> dict[str, Any]:
    """Analyse already-decoded pixels without filesystem or decoder effects."""

    normalised, width, height = _normalise_pixels(pixels, width, height)
    mask_result = foreground_mask(normalised, width, height, alpha_threshold=alpha_threshold)
    components = connected_components(mask_result["mask"], width, height, connectivity=connectivity)
    classified = classify_components(components, width, height)
    return {
        "width": width,
        "height": height,
        "background": mask_result["background"],
        "mask": mask_result["mask"],
        "foreground_mask": encode_mask(mask_result["mask"], width, height),
        "components": classified["components"],
        "content_bounds": classified["content_bounds"],
        "ordering": classified["ordering"],
        "role_hypotheses": classified["role_hypotheses"],
        "layout_groups": classified["layout_groups"],
        "recognition": _recognition_summary(classified),
        "colors": _colour_summary(normalised, mask_result["mask"]),
        "topology": {
            "connectivity": connectivity,
            "component_count": len(classified["components"]),
            "foreground_pixels": mask_result["background"]["foreground_pixels"],
            "foreground_coverage": mask_result["background"]["foreground_coverage"],
        },
    }


def _landmarks(width: int, height: int, bounds: dict[str, int] | None) -> list[dict[str, Any]]:
    if not bounds:
        return []
    left, top = bounds["x"], bounds["y"]
    right, bottom = left + bounds["width"], top + bounds["height"]
    center_x, center_y = (left + right) / 2.0, (top + bottom) / 2.0
    return [
        {"id": "raster-left", "kind": "extremum", "x": left, "y": _rounded(center_y), "importance": "structural"},
        {"id": "raster-right", "kind": "extremum", "x": right, "y": _rounded(center_y), "importance": "structural"},
        {"id": "raster-top", "kind": "extremum", "x": _rounded(center_x), "y": top, "importance": "structural"},
        {"id": "raster-bottom", "kind": "extremum", "x": _rounded(center_x), "y": bottom, "importance": "structural"},
        {"id": "raster-center", "kind": "center", "x": _rounded(center_x), "y": _rounded(center_y), "importance": "identity-candidate"},
        {"id": "raster-content-bounds", "kind": "container", "value": [left, top, bounds["width"], bounds["height"]], "importance": "structural"},
        {"id": "raster-image-bounds", "kind": "container", "value": [0, 0, width, height], "importance": "structural"},
    ]


def _elements(components: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for component in components:
        bounds = component["bounds"]
        records.append(
            {
                "id": component["id"],
                "tag": "raster-component",
                "bounds": [bounds["x"], bounds["y"], bounds["width"], bounds["height"]],
                "centroid": component["centroid"],
                "area": component["area"],
                "role": component["selected_role"],
                "role_candidates": component["role_candidates"],
                "role_review": component.get("role_review", {}),
                "layout_group": component.get("layout_group", "unknown"),
                "group_confidence": component.get("group_confidence", "low"),
                "geometry_strategy": "pixel-observation-only",
                "reconstruction_status": "needs-review",
            }
        )
    return records


def _recognition_summary(classified: dict[str, Any]) -> dict[str, Any]:
    """Build the explainable handoff from pixel observations to motion actors.

    The adapter proposes geometry-backed roles; it does not perform semantic
    brand recognition or vector reconstruction. Keeping this decision trace
    beside the observations gives an AI agent a safe planning input.
    """

    components = list(classified.get("components", []))
    role_counts: dict[str, int] = {}
    for component in components:
        role = str(component.get("selected_role", "unknown"))
        role_counts[role] = role_counts.get(role, 0) + 1
    groups = [
        str(item.get("id"))
        for item in classified.get("layout_groups", [])
        if isinstance(item, dict) and item.get("id")
    ]
    return {
        "mode": "bounded-geometric-observation",
        "review_status": "needs-review",
        "input_boundary": "decoded pixels and layout heuristics only; no semantic or vector reconstruction claim",
        "component_count": len(components),
        "role_counts": role_counts,
        "layout_groups": groups,
        "confidence_policy": {
            "high": "not assigned by this adapter",
            "medium": "geometry is suggestive and still requires review",
            "low": "do not use as a semantic role without review",
            "accepted_role": "only an explicit reviewer annotation may promote a role",
        },
        "motion_binding_rules": {
            "origin-dot": "scale-and-opacity reveal from the observed centroid",
            "arc": "ordered angular or contour prefix over the observed source mask",
            "bar": "continuous endpoint-to-endpoint scan over the observed stroke",
            "monogram": "component-local contour or convergence reveal using source pixels",
            "wordmark": "reading-order glyph/component cascade using source pixels",
            "unknown": "static-canonical fallback until a reviewer accepts a role",
        },
        "decision_trace": [
            "estimate border background and foreground mask",
            "extract connected components with deterministic ordering",
            "hypothesize symbol and wordmark groups from layout and geometry",
            "bind supported roles to source-pixel motion strategies",
            "retain unknown or low-confidence actors behind static-canonical fallback",
        ],
    }


def _header_only(path: Path, reason: str, *, decoder_error: bool = False) -> dict[str, Any]:
    header = parse_raster_header(path)
    not_run = ["pixel-decoding", "color-clustering", "landmark-detection", "topology-analysis"]
    unresolved = [reason]
    if decoder_error:
        unresolved.append("raster pixel observations were not produced")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate",
        "source": {
            "path": str(path),
            "format": header["format"],
            "width": header["width"],
            "height": header["height"],
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
            "reason": "Only raster header metadata is available.",
            "recommended_next_step": "Install an approved image decoder or provide a vector source for review.",
        },
        "capabilities": ["raster-header"],
        "not_run": not_run,
        "unresolved": unresolved,
    }


def _load_pixels(path: Path, max_dimension: int) -> tuple[list[Pixel], int, int, int, int, str, bool]:
    try:
        from PIL import Image
    except ImportError as error:  # pragma: no cover - depends on environment
        raise RuntimeError("Pillow is unavailable") from error

    with Image.open(path) as image:
        image.load()
        original_width, original_height = image.size
        original_mode = image.mode
        has_alpha = "A" in image.getbands() or "transparency" in image.info
        rgba = image.convert("RGBA")
        if max_dimension > 0 and max(original_width, original_height) > max_dimension:
            scale = max_dimension / max(original_width, original_height)
            sampled_size = (max(1, round(original_width * scale)), max(1, round(original_height * scale)))
            resampling = getattr(Image, "Resampling", Image).NEAREST
            rgba = rgba.resize(sampled_size, resampling)
        width, height = rgba.size
        pixels = [tuple(int(channel) for channel in pixel) for pixel in rgba.getdata()]
    return pixels, width, height, original_width, original_height, original_mode, has_alpha


def analyze_raster(path: Path, *, max_dimension: int = 512, connectivity: int = 8) -> dict[str, Any]:
    """Decode and analyse a PNG/JPG/WebP into a candidate source-analysis document."""

    path = Path(path)
    fmt = source_format(path)
    if fmt not in {"png", "jpeg", "webp"}:
        return _header_only(path, f"unsupported raster format for pixel analysis: {fmt}")
    try:
        pixels, width, height, original_width, original_height, mode, has_alpha = _load_pixels(path, max_dimension)
    except RuntimeError as error:
        return _header_only(path, str(error))
    except Exception as error:  # Pillow decoder errors remain inspectable candidates.
        return _header_only(path, f"raster decoder failed: {type(error).__name__}: {error}", decoder_error=True)

    pixel_analysis = analyze_pixels(pixels, width, height, connectivity=connectivity)
    raster_observations = {
        "analysis_version": "1.0",
        "coordinate_space": "sampled-raster",
        "sampling": {
            "original_width": original_width,
            "original_height": original_height,
            "width": width,
            "height": height,
            "max_dimension": max_dimension,
            "method": "nearest-neighbour when capped; exact pixels otherwise",
        },
        "decoder": {"provider": "Pillow", "mode": mode, "has_alpha": has_alpha},
        "background": pixel_analysis["background"],
        "foreground_mask": pixel_analysis["foreground_mask"],
        "components": pixel_analysis["components"],
        "content_bounds": pixel_analysis["content_bounds"],
            "ordering": pixel_analysis["ordering"],
            "role_hypotheses": pixel_analysis["role_hypotheses"],
            "layout_groups": pixel_analysis["layout_groups"],
            "recognition": pixel_analysis["recognition"],
            "reconstruction": {
            "status": "needs-review",
            "vector_reconstruction": "not-claimed",
            "reason": "Pixels were segmented into observations; no vector paths were generated or verified.",
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate",
        "source": {
            "path": str(path),
            "format": fmt,
            "width": original_width,
            "height": original_height,
            "color_mode": mode,
            "has_alpha": has_alpha,
        },
        "observations": {
            "elements": _elements(pixel_analysis["components"]),
            "colors": pixel_analysis["colors"],
            "landmarks": _landmarks(width, height, pixel_analysis["content_bounds"]),
            "negative_spaces": [],
            "topology": pixel_analysis["topology"],
            "recognition": pixel_analysis["recognition"],
            "raster": raster_observations,
        },
        "review": {
            "status": "needs-review",
            "vector_reconstruction": "not-claimed",
            "reason": "Raster components and role labels are deterministic geometric candidates, not semantic truth.",
            "recommended_next_step": "Review component roles and compare against the supplied mark before planning motion.",
        },
        "capabilities": [
            "raster-header",
            "raster-pixels",
            "foreground-mask",
            "connected-components",
            "geometric-role-candidates",
        ],
        "not_run": ["raster-to-vector-reconstruction", "human-role-review", "browser-render-analysis"],
        "unresolved": [
            "component roles are heuristic candidates and require review",
            "raster-to-vector reconstruction was not attempted",
        ],
    }


def analyze(path: Path, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for callers that use the concise analysis verb."""

    return analyze_raster(path, **kwargs)


__all__ = [
    "analyze",
    "analyze_pixels",
    "analyze_raster",
    "connected_components",
    "encode_mask",
    "foreground_mask",
]
