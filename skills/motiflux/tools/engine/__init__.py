"""Internal Motiflux project-kernel modules.

The package is intentionally private to the tool adapters. Consumers use the
unified command seam and the artifacts it writes, not these implementation
modules.
"""

from .catalog import ThemeCatalog, ThemeProfile, load_catalog
from .domain import ProjectManifest, StageResult

__all__ = ["ProjectManifest", "StageResult", "ThemeCatalog", "ThemeProfile", "load_catalog"]
