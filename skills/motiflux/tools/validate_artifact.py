"""Validate a Motiflux artifact against its bundled JSON Schema."""

from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION, contract_errors, evidence_semantic_errors, load_document, write_json


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
SCHEMAS = {
    "source-analysis": SCHEMA_DIR / "source-analysis.schema.json",
    "motion-plan": SCHEMA_DIR / "motion-plan.schema.json",
    "telemetry": SCHEMA_DIR / "telemetry.schema.json",
    "evidence": SCHEMA_DIR / "evidence.schema.json",
    "project": SCHEMA_DIR / "project.schema.json",
    "artifact-index": SCHEMA_DIR / "artifact-index.schema.json",
    "runtime-probe": SCHEMA_DIR / "runtime-probe.schema.json",
}


def validate(kind: str, artifact_path: Path) -> dict[str, Any]:
    schema_path = SCHEMAS[kind]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    artifact = load_document(artifact_path)
    errors = contract_errors(artifact, schema)
    if kind == "evidence" and not errors:
        errors.extend(evidence_semantic_errors(artifact))
    if kind == "artifact-index" and not errors:
        errors.extend(validate_index_integrity(artifact_path, artifact))
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": str(artifact_path),
        "kind": kind,
        "valid": not errors,
        "errors": errors,
    }


def validate_index_integrity(index_path: Path, index: Any) -> list[str]:
    """Verify every indexed file's path, size, and SHA-256 digest."""

    if not isinstance(index, dict):
        return ["artifact index must be an object"]
    errors: list[str] = []
    seen: set[str] = set()
    root = index_path.resolve().parent
    for item in index.get("artifacts", []):
        if not isinstance(item, dict):
            errors.append("artifact index contains a non-object record")
            continue
        relative = str(item.get("path", "")).replace("\\", "/")
        if not relative or relative in seen:
            errors.append(f"artifact index contains duplicate or empty path: {relative!r}")
            continue
        seen.add(relative)
        candidate = (root / relative).resolve()
        if candidate != root and root not in candidate.parents:
            errors.append(f"artifact index path escapes root: {relative}")
            continue
        if not candidate.is_file():
            errors.append(f"indexed artifact is missing: {relative}")
            continue
        payload = candidate.read_bytes()
        if item.get("bytes") != len(payload):
            errors.append(f"indexed artifact size mismatch: {relative}")
        if item.get("sha256") != hashlib.sha256(payload).hexdigest():
            errors.append(f"indexed artifact hash mismatch: {relative}")
    if index.get("count") != len(index.get("artifacts", [])):
        errors.append("artifact index count does not match artifact records")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(SCHEMAS))
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.kind, args.artifact.resolve())
    write_json(args.output, result)
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
