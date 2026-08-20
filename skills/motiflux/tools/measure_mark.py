"""Measure a Motiflux source mark without mutating it."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION, parse_raster_header, source_format, svg_scene, write_json
from engine.raster import analyze_raster


def measure(path: Path) -> dict[str, Any]:
    fmt = source_format(path)
    if fmt == "svg":
        scene = svg_scene(path)
        records = scene["records"]
        bounds = [item["bounds"] for item in records if item["bounds"]]
        capabilities = ["svg-xml", "semantic-elements", "vector-fingerprint"]
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "candidate",
            "source": {
                "path": str(path),
                "format": "svg",
                "width": scene["viewbox"][2],
                "height": scene["viewbox"][3],
                "color_mode": "vector",
                "has_alpha": None,
            },
            "observations": {
                "elements": records,
                "colors": [{"value": color} for color in scene["colors"]],
                "landmarks": landmark_observations(scene["viewbox"], bounds),
                "negative_spaces": [],
                "topology": scene["topology"],
                "canonical_fingerprint": scene["canonical"],
            },
            "capabilities": capabilities,
            "not_run": ["raster-pixel-analysis", "browser-render-analysis"],
            "unresolved": ["negative-space geometry requires raster or explicit scene regions"],
        }

    return analyze_raster(path)


def landmark_observations(viewbox: list[float], bounds: list[list[float]]) -> list[dict[str, Any]]:
    if not bounds:
        return []
    min_x = min(item[0] for item in bounds)
    min_y = min(item[1] for item in bounds)
    max_x = max(item[0] + item[2] for item in bounds)
    max_y = max(item[1] + item[3] for item in bounds)
    return [
        {"id": "mark-left", "kind": "extremum", "x": min_x, "y": (min_y + max_y) / 2, "importance": "structural"},
        {"id": "mark-right", "kind": "extremum", "x": max_x, "y": (min_y + max_y) / 2, "importance": "structural"},
        {"id": "mark-top", "kind": "extremum", "x": (min_x + max_x) / 2, "y": min_y, "importance": "structural"},
        {"id": "mark-bottom", "kind": "extremum", "x": (min_x + max_x) / 2, "y": max_y, "importance": "structural"},
        {"id": "mark-center", "kind": "center", "x": (min_x + max_x) / 2, "y": (min_y + max_y) / 2, "importance": "identity"},
        {"id": "source-viewbox", "kind": "container", "value": viewbox, "importance": "structural"},
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    write_json(args.output, measure(args.input.resolve()))


if __name__ == "__main__":
    main()
