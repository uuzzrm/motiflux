"""Safe, deterministic artifact writes for the project pipeline."""

from __future__ import annotations

import json
import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Any

from .domain import ArtifactRef


class ArtifactStore:
    """Write named artifacts below one output root and return relative paths."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._producers: dict[str, str] = {}

    def path(self, relative: str) -> Path:
        # Artifact names can come from a Windows-authored plan even when the
        # validator runs on Linux. Normalize both separator conventions before
        # resolving so traversal checks have the same meaning in every runner.
        normalized = relative.replace("\\", "/")
        candidate = (self.root / normalized).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError(f"artifact path escapes project root: {relative}")
        return candidate

    def _register(self, relative: str, producer: str) -> str:
        normalized = relative.replace("\\", "/")
        self._producers[normalized] = producer
        return normalized

    def write_json(self, relative: str, value: Any, *, producer: str = "unknown") -> str:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, target)
        return self._register(relative, producer)

    def write_text(self, relative: str, value: str, *, producer: str = "unknown") -> str:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(value, encoding="utf-8")
        os.replace(temporary, target)
        return self._register(relative, producer)

    def copy_file(self, source: Path, relative: str, *, producer: str = "unknown") -> str:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(source.read_bytes())
        os.replace(temporary, target)
        return self._register(relative, producer)

    def artifact_refs(self, *, exclude: tuple[str, ...] = ()) -> tuple[ArtifactRef, ...]:
        """Index every file below the root, including unregistered files.

        Scanning the root is intentional: an adapter that writes directly to a
        known project root cannot silently evade the manifest. Such files are
        marked ``unknown`` until their producer is registered.
        """

        excluded = {item.replace("\\", "/") for item in exclude}
        refs: list[ArtifactRef] = []
        for path in sorted(item for item in self.root.rglob("*") if item.is_file()):
            relative = path.relative_to(self.root).as_posix()
            if relative in excluded:
                continue
            payload = path.read_bytes()
            media_type = media_type_for(path)
            refs.append(
                ArtifactRef(
                    path=relative,
                    sha256=hashlib.sha256(payload).hexdigest(),
                    bytes=len(payload),
                    producer=self._producers.get(relative, "unknown"),
                    media_type=media_type,
                )
            )
        return tuple(refs)

    def write_index(
        self,
        *,
        exclude: tuple[str, ...] = (),
        producer: str = "artifact-index",
    ) -> str:
        """Write the deterministic content index after all stages finish."""

        index_path = "artifact-index.json"
        excluded = tuple(dict.fromkeys((index_path, *exclude)))
        refs = self.artifact_refs(exclude=excluded)
        payload = {
            "schema_version": "1.0",
            "index_version": "1.1",
            "root": ".",
            "count": len(refs),
            "excluded": list(excluded),
            "artifacts": [ref.to_dict() for ref in refs],
        }
        return self.write_json(index_path, payload, producer=producer)


def media_type_for(path: Path) -> str:
    """Return a stable media type across Windows and Linux runners."""

    explicit = {
        ".css": "text/css",
        ".gif": "image/gif",
        ".html": "text/html",
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".js": "text/javascript",
        ".json": "application/json",
        ".md": "text/markdown",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".txt": "text/plain",
        ".webp": "image/webp",
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
    }
    return explicit.get(path.suffix.casefold(), mimetypes.guess_type(path.name)[0] or "application/octet-stream")
