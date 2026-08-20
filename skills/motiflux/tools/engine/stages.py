"""Default Motiflux stage handlers.

This module contains the offline adapters that implement the stage graph.  The
runner in ``pipeline.py`` knows only the stage interface; the compatibility
façade in ``project_pipeline.py`` knows only how to assemble the manifest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from audit_motion import audit
from compare_shape import compare
from measure_mark import measure
from motiflux_core import SCHEMA_VERSION, contract_errors, load_document
from validate_package import validate_package

from .catalog import ThemeCatalog
from .domain import StageResult
from .pipeline import PipelineContext, StageDefinition
from .planner import build_plan, foreground_evidence, validate_references
from .runtime import compile_runtime
from .runtime_probe import probe_runtime


MOTION_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "motion-plan.schema.json"


def build_stages() -> tuple[StageDefinition, ...]:
    """Return the stable stage graph in dependency order."""

    return (
        StageDefinition("analyze", ("source",), ("analysis",), stage_analyze),
        StageDefinition("route", ("request", "catalog"), ("selection", "profile"), stage_route),
        StageDefinition("plan", ("analysis", "selection", "profile"), ("plan",), stage_plan),
        StageDefinition("reconstruct", ("source", "analysis", "plan"), ("canonical-mark",), stage_reconstruct),
        StageDefinition("verify-geometry", ("canonical-mark", "plan"), ("geometry-report",), stage_verify_geometry),
        StageDefinition("compile", ("canonical-mark", "plan", "geometry-report"), ("package",), stage_compile),
        StageDefinition("verify-package", ("package",), ("package-report",), stage_verify_package),
        StageDefinition("verify-motion", ("package", "package-report", "canonical-mark", "plan"), ("motion-report", "runtime-report"), stage_verify_motion),
    )


def stage_analyze(context: PipelineContext) -> StageResult:
    analysis = measure(context.get("source"))
    path = context.store.write_json("source-analysis.json", analysis, producer="analyze")
    context.provide("analysis", analysis)
    context.provide("artifact:source_analysis", path)
    return StageResult("analyze", analysis["status"], (path,), tuple(analysis.get("not_run", [])), tuple(analysis.get("unresolved", [])), {"format": analysis.get("source", {}).get("format")})


def stage_route(context: PipelineContext) -> StageResult:
    catalog: ThemeCatalog = context.get("catalog")
    selection = catalog.route(context.get("request"))
    path = context.store.write_json("theme-selection.json", selection, producer="route")
    profile = catalog.get(selection["theme_selection"].get("primary_id", selection["theme_selection"]["primary"]))
    context.provide("selection", selection)
    context.provide("profile", profile)
    context.provide("artifact:theme_selection", path)
    return StageResult("route", "complete", (path,), metadata={"primary": profile.id, "catalog": str(catalog.source_path)})


def stage_plan(context: PipelineContext) -> StageResult:
    source = context.get("source")
    profile = context.get("profile")
    plan = build_plan(context.get("analysis"), context.get("selection"), profile, project_name=f"Motiflux project / {profile.name}", source_name=source.name, request=context.request)
    catalog: ThemeCatalog = context.get("catalog")
    plan_errors = validate_references(plan, theme_ids={item.id for item in catalog.profiles})
    plan_errors.extend(contract_errors(plan, load_document(MOTION_SCHEMA_PATH)))
    path = context.store.write_json("motion-plan.yaml", plan, producer="plan")
    context.provide("artifact:motion_plan", path)
    if not plan_errors:
        context.provide("plan", plan)
    return StageResult("plan", "complete" if not plan_errors else "candidate", (path,), unresolved=tuple(plan_errors), metadata={"theme": profile.id, "valid": not plan_errors})


def stage_reconstruct(context: PipelineContext) -> StageResult:
    source = context.get("source")
    analysis = context.get("analysis")
    if source.suffix.casefold() != ".svg":
        raster_observations = analysis.get("observations", {}).get("raster", {})
        if raster_observations:
            return StageResult("reconstruct", "candidate", not_run=("reconstruct-raster-source", "raster-to-vector-reconstruction", "human-role-review"), unresolved=("raster observations are candidates; vector reconstruction is not claimed",), metadata={"strategy": "pixel-observation-only", "component_count": analysis.get("observations", {}).get("topology", {}).get("component_count", 0)})
        return StageResult("reconstruct", "candidate", not_run=("reconstruct-raster-source", "raster-to-vector-reconstruction"), unresolved=("raster-to-vector reconstruction adapter is not installed",), metadata={"strategy": "await-image-adapter"})
    mark_path = context.store.copy_file(source, "mark.svg", producer="reconstruct")
    status = "complete" if analysis.get("observations", {}).get("elements") else "candidate"
    unresolved = () if status == "complete" else ("SVG contains no supported actors",)
    if status == "complete":
        context.provide("canonical-mark", context.store.path(mark_path))
    context.provide("artifact:mark", mark_path)
    return StageResult("reconstruct", status, (mark_path,), unresolved=unresolved, metadata={"strategy": "preserve-source-vector"})


def stage_verify_geometry(context: PipelineContext) -> StageResult:
    mark_path = context.get("canonical-mark")
    report = compare(mark_path, mark_path)
    path = context.store.write_json("evidence/geometry/semantic.json", report, producer="verify-geometry")
    context.provide("geometry-report", report)
    context.provide("artifact:geometry", path)
    return StageResult("verify-geometry", report["status"], (path,), tuple(report.get("not_run", [])), tuple(report.get("unresolved", [])), report.get("geometry_metrics", {}))


def stage_compile(context: PipelineContext) -> StageResult:
    mark_path = context.get("canonical-mark")
    plan = context.get("plan")
    geometry_report = context.get("geometry-report")
    runtime_files = compile_runtime(mark_path.read_text(encoding="utf-8"), plan)
    package_files = [context.store.write_text(f"package/{name}", content, producer="compile") for name, content in runtime_files.items()]
    package_mark = context.store.copy_file(mark_path, "package/mark.svg", producer="compile")
    package_plan = context.store.write_json("package/motion-plan.yaml", plan, producer="compile")
    for relative in ("package/evidence", "package/evidence/geometry", "package/evidence/motion", "package/evidence/accessibility"):
        context.store.path(relative).mkdir(parents=True, exist_ok=True)
    profile = context.get("profile")
    package_evidence = {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate",
        "source": {"mark": "mark.svg", "plan": "motion-plan.yaml", "theme": profile.id},
        "constraint_summary": {"pipeline": "source-preserving project compiler", "theme": profile.id},
        "geometry_metrics": geometry_report.get("geometry_metrics", {}),
        "motion_metrics": {"duration_ms": plan["runtime"]["duration_ms"], "tempo": plan["runtime"]["tempo"], "secondary_effect": plan["runtime"]["secondary_effect"], "trajectory_id": plan["runtime"]["trajectory_id"]},
        "foreground_evidence": foreground_evidence(plan),
        "canonical_fingerprint": geometry_report.get("canonical_fingerprint", {}),
        "pixel_tolerance": {"status": "not-run"},
        "accessibility": {"reduced_motion": plan["runtime"]["reduced_motion"], "controls": plan["runtime"]["controls"]},
        "substituted_tools": [],
        "not_run": ["browser-runtime-check", "pixel-diff", "accessibility-tree-check"],
        "unresolved": ["browser evidence remains to be supplied by the runtime adapter"],
    }
    evidence_path = context.store.write_json("package/evidence.json", package_evidence, producer="compile")
    source_evidence_path = context.store.write_json("package/evidence/source-analysis.json", context.get("analysis"), producer="compile")
    context.provide("package", context.store.path("package"))
    context.provide("artifact:package", "package")
    context.provide("artifact:package_evidence", evidence_path)
    return StageResult("compile", "complete", tuple([*package_files, package_mark, package_plan, evidence_path, source_evidence_path]), metadata={"theme": profile.id, "effect": plan["runtime"]["secondary_effect"], "trajectory": plan["runtime"]["trajectory_id"]})


def stage_verify_package(context: PipelineContext) -> StageResult:
    report = validate_package(context.get("package"))
    path = context.store.write_json("evidence/package-validation.json", report, producer="verify-package")
    context.provide("package-report", report)
    context.provide("artifact:package_validation", path)
    return StageResult("verify-package", "complete" if report["valid"] else "candidate", (path,), unresolved=tuple(report.get("errors", [])), metadata={"valid": report["valid"]})


def stage_verify_motion(context: PipelineContext) -> StageResult:
    plan = context.get("plan")
    mark_path = context.get("canonical-mark")
    duration = plan["runtime"]["duration_ms"]
    foreground = foreground_evidence(plan)
    beat_ids = [str(beat["id"]) for beat in plan.get("beats", []) if isinstance(beat, dict) and beat.get("id")]
    first_beat, last_beat = (beat_ids[0], beat_ids[-1]) if beat_ids else ("orient", "resolve")
    telemetry_relative = context.store.write_json("evidence/motion/telemetry.json", {"schema_version": SCHEMA_VERSION, "samples": [{"time_ms": 0, "active_beat": first_beat, "actor_states": {}, "visible_bounds": {}, "progress_values": {"global": 0}, "runtime_errors": []}, {"time_ms": duration, "active_beat": last_beat, "actor_states": {}, "visible_bounds": {}, "progress_values": {"global": 1}, "runtime_errors": []}], "stage_snapshots": foreground["stage_snapshots"], "risk_intervals": [{"id": last_beat, "kind": "canonical-handoff", "time_ms": duration}], "runtime_errors": [], "final_scene_fingerprint": context.get("geometry-report").get("canonical_fingerprint", {})}, producer="verify-motion")
    telemetry_path = context.store.path(telemetry_relative)
    motion_report = audit(telemetry_path, canonical_path=mark_path, duration_ms=duration)
    motion_path = context.store.write_json("evidence/motion/audit.json", motion_report, producer="verify-motion")
    node_capability = context.capabilities["node-runtime"]
    node = node_capability.details.get("executable") if node_capability.available else None
    runtime_report = probe_runtime(context.get("package"), node_executable=node)
    runtime_path = context.store.write_json("evidence/runtime-probe.json", runtime_report, producer="verify-motion")
    context.provide("motion-report", motion_report)
    context.provide("runtime-report", runtime_report)
    context.provide("artifact:telemetry", telemetry_relative)
    context.provide("artifact:motion_audit", motion_path)
    context.provide("artifact:runtime_probe", runtime_path)
    not_run = unique_items([*motion_report.get("not_run", []), *runtime_report.get("not_run", [])])
    unresolved = unique_items([*motion_report.get("unresolved", []), *runtime_report.get("unresolved", [])])
    status = "complete" if motion_report["status"] == "complete" and runtime_report["status"] == "complete" else "candidate"
    return StageResult("verify-motion", status, (motion_path, runtime_path, telemetry_relative), not_run, unresolved, {"motion": motion_report.get("motion_metrics", {}), "runtime": runtime_report.get("checks", {})})


def unique_items(items: Any) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(item) for item in items if item))
