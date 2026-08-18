"""Small domain records shared by the Motiflux project pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Status = Literal["complete", "candidate", "blocked"]


@dataclass(frozen=True)
class StageResult:
    """The observable result of one pipeline stage.

    The interface is deliberately small: callers need a stage name, status,
    artifact paths, and explicit missing/uncertain evidence. Implementation
    details remain behind the stage adapter.
    """

    stage: str
    status: Status
    artifacts: tuple[str, ...] = ()
    not_run: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "artifacts": list(self.artifacts),
            "not_run": list(self.not_run),
            "unresolved": list(self.unresolved),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ProjectManifest:
    """Serializable project-level trace for one source/request pair."""

    schema_version: str
    project_id: str
    request: str
    source: dict[str, Any]
    stages: tuple[StageResult, ...]
    artifacts: dict[str, str]
    status: Status
    not_run: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "request": self.request,
            "source": self.source,
            "stages": [stage.to_dict() for stage in self.stages],
            "artifacts": self.artifacts,
            "status": self.status,
            "not_run": list(self.not_run),
            "unresolved": list(self.unresolved),
        }


def aggregate_status(stages: list[StageResult]) -> Status:
    if any(stage.status == "blocked" for stage in stages):
        return "blocked"
    if any(stage.status == "candidate" for stage in stages):
        return "candidate"
    return "complete"
