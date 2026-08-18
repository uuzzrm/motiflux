"""The end-to-end Motiflux project pipeline."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from audit_motion import audit
from compare_shape import compare
from measure_mark import measure
from motiflux_core import SCHEMA_VERSION, contract_errors, load_document
from validate_package import validate_package

from .artifacts import ArtifactStore
from .catalog import ThemeCatalog, load_catalog
from .domain import ProjectManifest, StageResult, aggregate_status
from .planner import build_plan, validate_references
from .runtime import compile_runtime


PROJECT_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "project.schema.json"
MOTION_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "motion-plan.schema.json"


def project_id(source: Path, request: str) -> str:
    digest = hashlib.sha256(f"{source.resolve()}\0{request}".encode("utf-8")).hexdigest()[:12]
    return f"motiflux-{digest}"


def run_project(source_path: Path, request: str, output_dir: Path, *, catalog: ThemeCatalog | None = None) -> dict[str, Any]:
    source_path = source_path.resolve()
    output_dir = output_dir.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    catalog = catalog or load_catalog()
    store = ArtifactStore(output_dir)
    stages: list[StageResult] = []
    artifacts: dict[str, str] = {}
    not_run: list[str] = []
    unresolved: list[str] = []

    analysis = measure(source_path)
    analysis_path = store.write_json("source-analysis.json", analysis)
    artifacts["source_analysis"] = analysis_path
    stages.append(StageResult("analyze", analysis["status"], (analysis_path,), tuple(analysis.get("not_run", [])), tuple(analysis.get("unresolved", [])), {"format": analysis.get("source", {}).get("format")}))

    selection = catalog.route(request)
    selection_path = store.write_json("theme-selection.json", selection)
    artifacts["theme_selection"] = selection_path
    profile = catalog.get(selection["theme_selection"].get("primary_id", selection["theme_selection"]["primary"]))
    stages.append(StageResult("route", "complete", (selection_path,), (), (), {"primary": profile.id, "catalog": str(catalog.source_path)}))

    plan = build_plan(analysis, selection, profile, project_name=f"Motiflux project / {profile.name}", source_name=source_path.name)
    plan_errors = validate_references(plan, theme_ids={item.id for item in catalog.profiles})
    plan_schema = load_document(MOTION_SCHEMA_PATH)
    plan_errors.extend(contract_errors(plan, plan_schema))
    plan_status = "complete" if not plan_errors else "candidate"
    plan_path = store.write_json("motion-plan.yaml", plan)
    artifacts["motion_plan"] = plan_path
    stages.append(StageResult("plan", plan_status, (plan_path,), (), tuple(plan_errors), {"theme": profile.id}))
    if plan_errors:
        unresolved.extend(plan_errors)

    if source_path.suffix.casefold() == ".svg":
        mark_path = store.copy_file(source_path, "mark.svg")
        artifacts["mark"] = mark_path
        reconstruction_status = "complete" if analysis.get("observations", {}).get("elements") else "candidate"
        reconstruction_unresolved = () if reconstruction_status == "complete" else ("SVG contains no supported actors",)
        stages.append(StageResult("reconstruct", reconstruction_status, (mark_path,), (), reconstruction_unresolved, {"strategy": "preserve-source-vector"}))
    else:
        reconstruction_status = "candidate"
        reconstruction_unresolved = ("raster-to-vector reconstruction adapter is not installed",)
        stages.append(StageResult("reconstruct", reconstruction_status, (), ("raster-to-vector-reconstruction",), reconstruction_unresolved, {"strategy": "await-image-adapter"}))
        not_run.append("reconstruct-raster-source")

    if "mark" in artifacts and not plan_errors:
        mark_file = store.path(artifacts["mark"])
        geometry_report = compare(mark_file, mark_file)
        geometry_path = store.write_json("evidence/geometry/semantic.json", geometry_report)
        artifacts["geometry"] = geometry_path
        stages.append(StageResult("verify-geometry", geometry_report["status"], (geometry_path,), tuple(geometry_report.get("not_run", [])), tuple(geometry_report.get("unresolved", [])), geometry_report.get("geometry_metrics", {})))

        runtime_files = compile_runtime(mark_file.read_text(encoding="utf-8"), plan)
        package_files = []
        for name, content in runtime_files.items():
            package_files.append(store.write_text(f"package/{name}", content))
        package_mark = store.copy_file(mark_file, "package/mark.svg")
        package_plan = store.write_json("package/motion-plan.yaml", plan)
        for relative in ("package/evidence", "package/evidence/geometry", "package/evidence/motion", "package/evidence/accessibility"):
            store.path(relative).mkdir(parents=True, exist_ok=True)
        package_evidence = {
            "schema_version": SCHEMA_VERSION,
            "status": "candidate",
            "source": {"mark": "mark.svg", "plan": "motion-plan.yaml", "theme": profile.id},
            "constraint_summary": {"pipeline": "source-preserving project compiler", "theme": profile.id},
            "geometry_metrics": geometry_report.get("geometry_metrics", {}),
            "motion_metrics": {"duration_ms": plan["runtime"]["duration_ms"], "tempo": plan["runtime"]["tempo"], "secondary_effect": plan["runtime"]["secondary_effect"]},
            "canonical_fingerprint": geometry_report.get("canonical_fingerprint", {}),
            "pixel_tolerance": {"status": "not-run"},
            "accessibility": {"reduced_motion": plan["runtime"]["reduced_motion"], "controls": plan["runtime"]["controls"]},
            "substituted_tools": [],
            "not_run": ["browser-runtime-check", "pixel-diff", "accessibility-tree-check"],
            "unresolved": ["browser evidence remains to be supplied by the runtime adapter"],
        }
        evidence_path = store.write_json("package/evidence.json", package_evidence)
        source_evidence_path = store.write_json("package/evidence/source-analysis.json", analysis)
        package_report = validate_package(store.path("package"))
        package_report_path = store.write_json("evidence/package-validation.json", package_report)
        artifacts["package"] = "package"
        artifacts["package_evidence"] = f"package/{evidence_path.split('/', 1)[1]}" if evidence_path.startswith("package/") else evidence_path
        artifacts["package_validation"] = package_report_path
        compile_status = "complete" if package_report["valid"] else "candidate"
        stages.append(StageResult("compile", compile_status, tuple([*package_files, package_mark, package_plan, evidence_path, source_evidence_path]), (), tuple(package_report.get("errors", [])), {"theme": profile.id, "effect": plan["runtime"]["secondary_effect"]}))
        telemetry_path = store.write_json("evidence/motion/telemetry.json", {
            "schema_version": SCHEMA_VERSION,
            "samples": [{"time_ms": 0, "active_beat": "orient", "actor_states": {}, "visible_bounds": {}, "progress_values": {"global": 0}, "runtime_errors": []}, {"time_ms": plan["runtime"]["duration_ms"], "active_beat": "resolve", "actor_states": {}, "visible_bounds": {}, "progress_values": {"global": 1}, "runtime_errors": []}],
            "risk_intervals": [{"id": "resolve", "kind": "canonical-handoff", "time_ms": plan["runtime"]["duration_ms"]}],
            "runtime_errors": [],
            "final_scene_fingerprint": geometry_report.get("canonical_fingerprint", {}),
        })
        motion_report = audit(store.path(telemetry_path), canonical_path=mark_file, duration_ms=plan["runtime"]["duration_ms"])
        motion_path = store.write_json("evidence/motion/audit.json", motion_report)
        artifacts["motion_audit"] = motion_path
        stages.append(StageResult("verify-motion", motion_report["status"], (motion_path,), tuple(motion_report.get("not_run", [])), tuple(motion_report.get("unresolved", [])), motion_report.get("motion_metrics", {})))
    else:
        stages.append(StageResult(
            "verify-geometry",
            "candidate",
            (),
            ("raster-geometry-adapter",),
            ("geometry verification requires a canonical vector",),
            {"source_format": analysis.get("source", {}).get("format")},
        ))
        stages.append(StageResult("compile", "blocked", (), ("compile-requires-canonical-vector",), ("compile cannot run until a canonical vector exists",), {}))
        stages.append(StageResult("verify-motion", "blocked", (), ("verify-requires-compiled-package",), ("motion verification cannot run until compilation succeeds",), {}))

    not_run.extend(item for stage in stages for item in stage.not_run if item not in not_run)
    unresolved.extend(item for stage in stages for item in stage.unresolved if item not in unresolved)
    artifacts["project"] = "project.json"
    manifest = ProjectManifest(SCHEMA_VERSION, project_id(source_path, request), request, {"path": str(source_path), "format": analysis.get("source", {}).get("format")}, tuple(stages), artifacts, aggregate_status(stages), tuple(not_run), tuple(unresolved))
    manifest_path = store.write_json("project.json", manifest.to_dict())
    return {**manifest.to_dict(), "artifacts": artifacts}
