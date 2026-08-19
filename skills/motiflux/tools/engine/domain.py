"""Small domain records shared by the Motiflux project pipeline.

These records are the internal language of the kernel.  Command adapters may
continue to return dictionaries for compatibility, but stage orchestration,
artifact indexing, and evidence aggregation use these records so the seams do
not depend on ad-hoc mapping keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Status = Literal["complete", "candidate", "blocked"]


@dataclass(frozen=True)
class CapabilityReport:
    """Report whether an optional local capability is available."""

    id: str
    available: bool
    provider: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "available": self.available,
            "provider": self.provider,
            "details": self.details,
        }


@dataclass(frozen=True)
class ArtifactRef:
    """Content-addressed metadata for one emitted project artifact."""

    path: str
    sha256: str
    bytes: int
    producer: str
    media_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "producer": self.producer,
            "media_type": self.media_type,
        }


@dataclass(frozen=True)
class SceneActor:
    """One identity-bearing or supporting actor in a normalized scene."""

    id: str
    tag: str
    role: str
    layer: int
    bounds: tuple[float, ...] = ()
    parent: str | None = None
    paint: dict[str, Any] = field(default_factory=dict)
    transform: str = ""
    geometry_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tag": self.tag,
            "role": self.role,
            "layer": self.layer,
            "bounds": list(self.bounds),
            "parent": self.parent,
            "paint": self.paint,
            "transform": self.transform,
            "geometry_ref": self.geometry_ref,
        }


@dataclass(frozen=True)
class SceneGraph:
    """Normalized source scene consumed by planning and geometry verification."""

    schema_version: str
    status: Status
    source_format: str
    viewbox: tuple[float, ...] = ()
    actors: tuple[SceneActor, ...] = ()
    canonical_fingerprint: dict[str, Any] = field(default_factory=dict)
    capabilities: tuple[str, ...] = ()
    not_run: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "source": {"format": self.source_format, "viewbox": list(self.viewbox)},
            "actors": [actor.to_dict() for actor in self.actors],
            "canonical_fingerprint": self.canonical_fingerprint,
            "capabilities": list(self.capabilities),
            "not_run": list(self.not_run),
            "unresolved": list(self.unresolved),
        }


@dataclass(frozen=True)
class MotionBeat:
    """A named temporal intent in a motion graph."""

    id: str
    intent: str
    duration_weight: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "intent": self.intent,
            "duration_weight": self.duration_weight,
        }


@dataclass(frozen=True)
class MotionEdge:
    """An actor-to-beat dependency and its property channels."""

    actor: str
    beat: str
    starts_after: tuple[str, ...] = ()
    may_overlap: tuple[str, ...] = ()
    must_finish_before: tuple[str, ...] = ()
    property_channels: tuple[str, ...] = ()
    anchor: str = "source-bounds"

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor": self.actor,
            "beat": self.beat,
            "starts_after": list(self.starts_after),
            "may_overlap": list(self.may_overlap),
            "must_finish_before": list(self.must_finish_before),
            "property_channels": list(self.property_channels),
            "anchor": self.anchor,
        }


@dataclass(frozen=True)
class MotionGraph:
    """Typed, source-aware motion graph passed to a renderer."""

    schema_version: str
    status: Status
    project: dict[str, Any]
    theme_selection: dict[str, Any]
    motion_language: dict[str, Any]
    constraints: tuple[dict[str, Any], ...]
    actor_ids: tuple[str, ...]
    beats: tuple[MotionBeat, ...]
    edges: tuple[MotionEdge, ...]
    runtime: dict[str, Any]
    actors: tuple[SceneActor, ...] = ()
    source_fingerprint: dict[str, Any] = field(default_factory=dict)
    not_run: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "project": self.project,
            "theme_selection": self.theme_selection,
            "motion_language": self.motion_language,
            "constraints": list(self.constraints),
            "actor_ids": list(self.actor_ids),
            "actors": [actor.to_dict() for actor in self.actors],
            "beats": [beat.to_dict() for beat in self.beats],
            "dependencies": [edge.to_dict() for edge in self.edges],
            "runtime": self.runtime,
            "source_fingerprint": self.source_fingerprint,
            "not_run": list(self.not_run),
            "unresolved": list(self.unresolved),
        }

    def to_plan(self) -> dict[str, Any]:
        """Return a renderer-compatible plan without exposing graph internals."""

        actor_records = [actor.to_dict() for actor in self.actors]
        if not actor_records:
            actor_records = [{"id": actor_id} for actor_id in self.actor_ids]
        return {
            "schema_version": self.schema_version,
            "project": self.project,
            "theme_selection": self.theme_selection,
            "motion_language": self.motion_language,
            "constraints": list(self.constraints),
            "actors": actor_records,
            "beats": [beat.to_dict() for beat in self.beats],
            "dependencies": [edge.to_dict() for edge in self.edges],
            "runtime": self.runtime,
        }


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
    requires: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "artifacts": list(self.artifacts),
            "not_run": list(self.not_run),
            "unresolved": list(self.unresolved),
            "metadata": self.metadata,
            "requires": list(self.requires),
            "provides": list(self.provides),
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
    architecture_version: str = "1.1"
    artifact_index: str = "artifact-index.json"
    capabilities: dict[str, dict[str, Any]] = field(default_factory=dict)
    execution: dict[str, Any] = field(default_factory=dict)

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
            "architecture_version": self.architecture_version,
            "artifact_index": self.artifact_index,
            "capabilities": self.capabilities,
            "execution": self.execution,
        }


def aggregate_status(stages: list[StageResult]) -> Status:
    if any(stage.status == "blocked" for stage in stages):
        return "blocked"
    if any(stage.status == "candidate" for stage in stages):
        return "candidate"
    return "complete"
