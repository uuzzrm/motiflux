"""Internal Motiflux project-kernel modules.

The package is intentionally private to the tool adapters. Consumers use the
unified command seam and the artifacts it writes, not these implementation
modules.
"""

from .catalog import ThemeCatalog, ThemeProfile, load_catalog
from .domain import (
    ArtifactRef,
    CapabilityReport,
    MotionBeat,
    MotionEdge,
    MotionGraph,
    ProjectManifest,
    SceneActor,
    SceneGraph,
    StageResult,
)
from .pipeline import PipelineContext, PipelineRunner, StageDefinition

__all__ = [
    "ArtifactRef",
    "CapabilityReport",
    "MotionBeat",
    "MotionEdge",
    "MotionGraph",
    "PipelineContext",
    "PipelineRunner",
    "ProjectManifest",
    "SceneActor",
    "SceneGraph",
    "StageDefinition",
    "StageResult",
    "ThemeCatalog",
    "ThemeProfile",
    "load_catalog",
]
