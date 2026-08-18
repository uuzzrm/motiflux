"""Validate a Motiflux artifact against its bundled JSON Schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION, contract_errors, load_document, write_json


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
SCHEMAS = {
    "source-analysis": SCHEMA_DIR / "source-analysis.schema.json",
    "motion-plan": SCHEMA_DIR / "motion-plan.schema.json",
    "telemetry": SCHEMA_DIR / "telemetry.schema.json",
    "evidence": SCHEMA_DIR / "evidence.schema.json",
    "project": SCHEMA_DIR / "project.schema.json",
}


def validate(kind: str, artifact_path: Path) -> dict[str, Any]:
    schema_path = SCHEMAS[kind]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    artifact = load_document(artifact_path)
    errors = contract_errors(artifact, schema)
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": str(artifact_path),
        "kind": kind,
        "valid": not errors,
        "errors": errors,
    }


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
