"""Compare two SVG scenes and return semantic geometry evidence."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION, svg_scene, write_json


def relative_error(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    denominator = max(abs(left), abs(right), 1.0)
    return abs(left - right) / denominator


def compare(candidate_path: Path, canonical_path: Path, tolerance: float = 1e-6) -> dict[str, Any]:
    candidate = svg_scene(candidate_path)
    canonical = svg_scene(canonical_path)
    candidate_fp = candidate["canonical"]
    canonical_fp = canonical["canonical"]
    viewbox_errors = [
        relative_error(left, right)
        for left, right in zip(candidate["viewbox"], canonical["viewbox"])
    ]
    viewbox_errors = [value for value in viewbox_errors if value is not None]
    actor_ids_match = candidate_fp["actor_ids"] == canonical_fp["actor_ids"]
    path_hashes_match = candidate_fp["path_data_hashes"] == canonical_fp["path_data_hashes"]
    paint_match = candidate_fp["paint_attributes"] == canonical_fp["paint_attributes"]
    transforms_match = candidate_fp["transform_matrices"] == canonical_fp["transform_matrices"]
    layer_order_match = candidate_fp["layer_order"] == canonical_fp["layer_order"]
    bounds_errors = compare_bounds(candidate["records"], canonical["records"])
    semantic_equal = (
        viewbox_errors
        and max(viewbox_errors, default=0.0) <= tolerance
        and actor_ids_match
        and path_hashes_match
        and paint_match
        and transforms_match
        and layer_order_match
    )
    unresolved: list[str] = []
    if not candidate["records"] or not canonical["records"]:
        unresolved.append("one or both SVG scenes contain no supported vector actors")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "complete" if semantic_equal and not unresolved else "candidate",
        "candidate": str(candidate_path),
        "canonical": str(canonical_path),
        "geometry_metrics": {
            "semantic_equal": bool(semantic_equal),
            "viewbox_relative_error": max(viewbox_errors, default=None),
            "actor_count": {"candidate": len(candidate["records"]), "canonical": len(canonical["records"])},
            "actor_ids_match": actor_ids_match,
            "path_data_hashes_match": path_hashes_match,
            "paint_attributes_match": paint_match,
            "transforms_match": transforms_match,
            "layer_order_match": layer_order_match,
            "max_actor_bounds_relative_error": max(bounds_errors, default=None),
            "topology_match": candidate["topology"] == canonical["topology"],
        },
        "canonical_fingerprint": canonical_fp,
        "candidate_fingerprint": candidate_fp,
        "not_run": ["raster-contour-distance", "negative-space-area", "browser-pixel-diff"],
        "unresolved": unresolved,
    }


def compare_bounds(candidate_records: list[dict[str, Any]], canonical_records: list[dict[str, Any]]) -> list[float]:
    errors: list[float] = []
    for left, right in zip(candidate_records, canonical_records):
        left_bounds, right_bounds = left.get("bounds"), right.get("bounds")
        if not left_bounds or not right_bounds:
            continue
        for left_value, right_value in zip(left_bounds, right_bounds):
            error = relative_error(float(left_value), float(right_value))
            if error is not None:
                errors.append(error)
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("canonical", type=Path)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    write_json(args.output, compare(args.candidate.resolve(), args.canonical.resolve(), args.tolerance))


if __name__ == "__main__":
    main()

