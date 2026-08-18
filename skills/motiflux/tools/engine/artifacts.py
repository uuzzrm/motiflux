"""Safe, deterministic artifact writes for the project pipeline."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class ArtifactStore:
    """Write named artifacts below one output root and return relative paths."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, relative: str) -> Path:
        # Artifact names can come from a Windows-authored plan even when the
        # validator runs on Linux. Normalize both separator conventions before
        # resolving so traversal checks have the same meaning in every runner.
        normalized = relative.replace("\\", "/")
        candidate = (self.root / normalized).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError(f"artifact path escapes project root: {relative}")
        return candidate

    def write_json(self, relative: str, value: Any) -> str:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, target)
        return relative.replace("\\", "/")

    def write_text(self, relative: str, value: str) -> str:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(value, encoding="utf-8")
        os.replace(temporary, target)
        return relative.replace("\\", "/")

    def copy_file(self, source: Path, relative: str) -> str:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(source.read_bytes())
        os.replace(temporary, target)
        return relative.replace("\\", "/")
