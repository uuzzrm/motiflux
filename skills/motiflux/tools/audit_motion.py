"""Audit Motiflux telemetry and produce evidence-preserving motion metrics."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION, load_document, svg_scene, write_json


def audit(
    telemetry_path: Path,
    *,
    canonical_path: Path | None = None,
    accessibility_path: Path | None = None,
    duration_ms: float | None = None,
) -> dict[str, Any]:
    telemetry = load_document(telemetry_path)
    if not isinstance(telemetry, dict):
        return failure("telemetry must be a mapping", "telemetry-document")
    samples = telemetry.get("samples")
    if not isinstance(samples, list) or not samples:
        return failure("telemetry.samples must contain at least one sample", "telemetry-samples")
    stage_snapshots = telemetry.get("stage_snapshots")
    if not isinstance(stage_snapshots, list) or not stage_snapshots:
        return failure("telemetry.stage_snapshots must contain foreground evidence", "foreground-stage-snapshots")

    errors: list[str] = []
    times: list[float] = []
    progress_errors: list[str] = []
    channel_values: dict[str, list[float]] = {}
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            errors.append(f"sample {index} is not an object")
            continue
        time_value = sample.get("time_ms")
        if not isinstance(time_value, (int, float)):
            errors.append(f"sample {index} has no numeric time_ms")
        else:
            times.append(float(time_value))
        sample_errors = sample.get("runtime_errors", [])
        if isinstance(sample_errors, list):
            errors.extend(str(item) for item in sample_errors)
        progress = sample.get("progress_values", {})
        if isinstance(progress, dict):
            for channel, value in progress.items():
                if isinstance(value, (int, float)):
                    channel_values.setdefault(str(channel), []).append(float(value))

    if telemetry.get("runtime_errors"):
        errors.extend(str(item) for item in telemetry["runtime_errors"])
    if any(right < left for left, right in zip(times, times[1:])):
        errors.append("sample time_ms is not monotonic")
    for channel, values in channel_values.items():
        if any(right < left - 1e-9 for left, right in zip(values, values[1:])):
            progress_errors.append(f"progress channel is not monotonic: {channel}")
    errors.extend(progress_errors)
    foreground_result = {
        "checked": True,
        "stage_count": len(stage_snapshots),
        "stage_ids": [str(item.get("stage_id")) for item in stage_snapshots if isinstance(item, dict)],
        "source_actor_ids": sorted({str(actor_id) for item in stage_snapshots if isinstance(item, dict) for actor_id in item.get("source_actor_ids", []) or []}),
    }

    canonical_result: dict[str, Any] = {"checked": False}
    not_run: list[str] = []
    if canonical_path is not None:
        canonical = svg_scene(canonical_path)
        reported = telemetry.get("final_scene_fingerprint") or telemetry.get("final_fingerprint")
        expected = canonical["canonical"]["fingerprint"]
        actual = reported.get("fingerprint") if isinstance(reported, dict) else reported
        canonical_result = {
            "checked": True,
            "expected": expected,
            "actual": actual,
            "match": actual == expected,
        }
        if actual != expected:
            errors.append("final scene fingerprint does not match canonical mark")
    else:
        not_run.append("canonical-end-state-fingerprint")

    accessibility_result: dict[str, Any]
    if accessibility_path is not None:
        accessibility = load_document(accessibility_path)
        accessibility_result = accessibility if isinstance(accessibility, dict) else {"valid": False}
        if accessibility_result.get("valid") is False:
            errors.append("accessibility report is invalid")
    else:
        accessibility_result = {"checked": False}
        not_run.append("accessibility-browser-check")

    if duration_ms is not None and times and max(times) < duration_ms:
        not_run.append("full-duration-coverage")
    if not telemetry.get("risk_intervals"):
        not_run.append("risk-interval-coverage")

    required_missing = bool(not_run)
    status = "complete" if not errors and not required_missing else "candidate"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "motion_metrics": {
            "sample_count": len(samples),
            "time_monotonic": not any(right < left for left, right in zip(times, times[1:])),
            "progress_monotonic": not progress_errors,
            "progress_channels": sorted(channel_values),
            "runtime_error_count": len(errors),
            "duration_covered_ms": max(times, default=0.0),
        },
        "canonical_fingerprint": canonical_result,
        "foreground_evidence": foreground_result,
        "accessibility": accessibility_result,
        "not_run": not_run,
        "unresolved": errors,
    }


def failure(message: str, missing: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate",
        "motion_metrics": {},
        "canonical_fingerprint": {"checked": False},
        "foreground_evidence": {"checked": False},
        "accessibility": {"checked": False},
        "not_run": [missing],
        "unresolved": [message],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("telemetry", type=Path)
    parser.add_argument("--canonical", type=Path)
    parser.add_argument("--accessibility", type=Path)
    parser.add_argument("--duration-ms", type=float)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    write_json(
        args.output,
        audit(
            args.telemetry.resolve(),
            canonical_path=args.canonical.resolve() if args.canonical else None,
            accessibility_path=args.accessibility.resolve() if args.accessibility else None,
            duration_ms=args.duration_ms,
        ),
    )


if __name__ == "__main__":
    main()
