"""Dependency-checked stage orchestration for the Motiflux project kernel.

The public pipeline interface remains one function in ``project_pipeline``.
This module owns the reusable execution model behind that seam: stages declare
logical prerequisites and products, while handlers own domain work.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable

from .artifacts import ArtifactStore
from .catalog import ThemeCatalog
from .domain import CapabilityReport, StageResult


StageHandler = Callable[["PipelineContext"], StageResult]


@dataclass(frozen=True)
class StageDefinition:
    """The small interface a pipeline stage must satisfy."""

    name: str
    requires: tuple[str, ...]
    provides: tuple[str, ...]
    handler: StageHandler


@dataclass
class PipelineContext:
    """Mutable state shared only inside one pipeline execution."""

    source_path: Path
    request: str
    output_dir: Path
    store: ArtifactStore
    catalog: ThemeCatalog
    capabilities: dict[str, CapabilityReport]
    values: dict[str, Any]

    @classmethod
    def create(
        cls,
        source_path: Path,
        request: str,
        output_dir: Path,
        store: ArtifactStore,
        catalog: ThemeCatalog,
    ) -> "PipelineContext":
        capabilities = detect_capabilities()
        return cls(
            source_path=source_path,
            request=request,
            output_dir=output_dir,
            store=store,
            catalog=catalog,
            capabilities=capabilities,
            values={
                "source": source_path,
                "source_path": source_path,
                "request": request,
                "output_dir": output_dir,
                "store": store,
                "catalog": catalog,
            },
        )

    def provide(self, key: str, value: Any) -> None:
        self.values[key] = value

    def has(self, key: str) -> bool:
        value = self.values.get(key)
        return key in self.values and value is not None

    def get(self, key: str) -> Any:
        if not self.has(key):
            raise KeyError(f"pipeline value is unavailable: {key}")
        return self.values[key]


class PipelineRunner:
    """Run an ordered registry while enforcing stage prerequisites."""

    def __init__(self, stages: tuple[StageDefinition, ...]):
        self.stages = stages
        names = [stage.name for stage in stages]
        if len(names) != len(set(names)):
            raise ValueError("pipeline stage names must be unique")

    def run(self, context: PipelineContext) -> tuple[StageResult, ...]:
        results: list[StageResult] = []
        for definition in self.stages:
            missing = tuple(key for key in definition.requires if not context.has(key))
            if missing:
                result = StageResult(
                    stage=definition.name,
                    status="blocked",
                    not_run=tuple(f"missing-prerequisite:{key}" for key in missing),
                    unresolved=(f"stage requires unavailable values: {', '.join(missing)}",),
                    metadata={"execution": "skipped", "missing": list(missing)},
                    requires=definition.requires,
                    provides=definition.provides,
                )
                results.append(result)
                continue

            try:
                result = definition.handler(context)
            except Exception as error:  # keep the manifest inspectable on adapter failure
                result = StageResult(
                    stage=definition.name,
                    status="blocked",
                    not_run=("stage-handler",),
                    unresolved=(f"{type(error).__name__}: {error}",),
                    metadata={"execution": "failed", "error_type": type(error).__name__},
                )

            if result.stage != definition.name:
                result = replace(result, stage=definition.name)
            result = replace(
                result,
                requires=definition.requires,
                provides=definition.provides,
            )
            missing_products = tuple(key for key in definition.provides if not context.has(key))
            if missing_products and result.status != "blocked":
                result = replace(
                    result,
                    status="candidate",
                    unresolved=tuple(
                        [*result.unresolved, f"stage did not provide: {', '.join(missing_products)}"]
                    ),
                )
            results.append(result)
        return tuple(results)


def detect_capabilities() -> dict[str, CapabilityReport]:
    """Detect only local, offline capabilities used by the kernel."""

    node = shutil.which("node")
    return {
        "svg-semantic": CapabilityReport(
            id="svg-semantic",
            available=True,
            provider="motiflux-python",
            details={"scope": "supported SVG XML and semantic fingerprints"},
        ),
        "raster-pixels": CapabilityReport(
            id="raster-pixels",
            available=False,
            provider="none",
            details={"scope": "requires an approved image decoder adapter"},
        ),
        "node-runtime": CapabilityReport(
            id="node-runtime",
            available=bool(node),
            provider="node" if node else "none",
            details={"executable": node or ""},
        ),
        "browser-runtime": CapabilityReport(
            id="browser-runtime",
            available=False,
            provider="none",
            details={"scope": "browser adapter is not bundled into the offline kernel"},
        ),
    }
