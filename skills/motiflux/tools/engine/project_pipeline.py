"""The end-to-end Motiflux project pipeline.

``run_project`` is intentionally small: it creates a context, installs the
stage registry, runs it, indexes emitted artifacts, and writes the manifest.
The stage implementations remain local handlers behind ``PipelineRunner`` so
future adapters can replace one capability without rewriting orchestration.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION

from .artifacts import ArtifactStore
from .catalog import ThemeCatalog, load_catalog
from .domain import ProjectManifest, aggregate_status
from .pipeline import PipelineContext, PipelineRunner
from .stages import build_stages, unique_items


def project_id(source: Path, request: str) -> str:
    digest = hashlib.sha256(f"{source.resolve()}\0{request}".encode("utf-8")).hexdigest()[:12]
    return f"motiflux-{digest}"


def run_project(
    source_path: Path,
    request: str,
    output_dir: Path,
    *,
    catalog: ThemeCatalog | None = None,
) -> dict[str, Any]:
    """Run the source-aware project pipeline and write a traceable manifest."""

    source_path = source_path.resolve()
    output_dir = output_dir.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    catalog = catalog or load_catalog()
    store = ArtifactStore(output_dir)
    context = PipelineContext.create(source_path, request, output_dir, store, catalog)
    stages = build_stages()
    stage_results = PipelineRunner(stages).run(context)

    artifact_index_path = store.write_index(exclude=("project.json",))
    artifacts = collect_artifacts(context)
    artifacts["artifact_index"] = artifact_index_path
    artifacts["project"] = "project.json"

    analysis = context.values.get("analysis", {})
    not_run = unique_items(item for stage in stage_results for item in stage.not_run)
    unresolved = unique_items(item for stage in stage_results for item in stage.unresolved)
    execution = {
        "runner": "PipelineRunner",
        "architecture_version": "1.1",
        "stage_order": [stage.name for stage in stages],
        "completed_stages": [stage.stage for stage in stage_results if stage.status == "complete"],
        "candidate_stages": [stage.stage for stage in stage_results if stage.status == "candidate"],
        "blocked_stages": [stage.stage for stage in stage_results if stage.status == "blocked"],
        "artifact_count": len(store.artifact_refs(exclude=("project.json", "artifact-index.json"))),
    }
    capabilities = {key: value.to_dict() for key, value in context.capabilities.items()}
    manifest = ProjectManifest(
        schema_version=SCHEMA_VERSION,
        project_id=project_id(source_path, request),
        request=request,
        source={"path": str(source_path), "format": analysis.get("source", {}).get("format")},
        stages=stage_results,
        artifacts=artifacts,
        status=aggregate_status(list(stage_results)),
        not_run=not_run,
        unresolved=unresolved,
        capabilities=capabilities,
        execution=execution,
    )
    manifest_path = store.write_json("project.json", manifest.to_dict(), producer="project-manifest")
    if manifest_path != "project.json":
        raise ValueError("project manifest path normalization changed unexpectedly")
    return {**manifest.to_dict(), "artifacts": artifacts}


def collect_artifacts(context: PipelineContext) -> dict[str, str]:
    return {
        key.removeprefix("artifact:"): str(value)
        for key, value in context.values.items()
        if key.startswith("artifact:") and isinstance(value, str)
    }
