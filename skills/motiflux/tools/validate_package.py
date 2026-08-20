"""Validate a generated Motiflux delivery package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION, contract_errors, evidence_semantic_errors, load_document, write_json


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


def validate_package(package_dir: Path) -> dict[str, Any]:
    required_files = (
        "mark.svg",
        "motion.html",
        "motion-plan.yaml",
        "evidence.json",
        "evidence/source-analysis.json",
    )
    required_dirs = ("evidence", "evidence/geometry", "evidence/motion", "evidence/accessibility")
    errors: list[str] = []
    for relative in required_files:
        if not (package_dir / relative).is_file():
            errors.append(f"missing file: {relative}")
    for relative in required_dirs:
        if not (package_dir / relative).is_dir():
            errors.append(f"missing directory: {relative}")
    if errors:
        return result(package_dir, errors)

    checks = (
        ("motion-plan.schema.json", "motion-plan", package_dir / "motion-plan.yaml"),
        ("evidence.schema.json", "evidence", package_dir / "evidence.json"),
        ("source-analysis.schema.json", "source-analysis", package_dir / "evidence/source-analysis.json"),
    )
    for schema_name, label, artifact_path in checks:
        schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
        artifact = load_document(artifact_path)
        contract_failures = contract_errors(artifact, schema)
        errors.extend(f"{label}: {item}" for item in contract_failures)
        if label == "evidence" and not contract_failures:
            errors.extend(f"{label}: {item}" for item in evidence_semantic_errors(artifact))

    html = (package_dir / "motion.html").read_text(encoding="utf-8")
    runtime = (package_dir / "motion.js").read_text(encoding="utf-8")
    for marker in ("data-motiflux-root", "data-motiflux-mark", "data-motiflux-controls"):
        if marker not in html:
            errors.append(f"motion.html missing runtime marker: {marker}")
    for marker in ("__motifluxReady", "__motifluxControl", "finish()", "prefers-reduced-motion"):
        if marker not in runtime and marker != "prefers-reduced-motion":
            errors.append(f"motion.js missing runtime contract: {marker}")
    if "prefers-reduced-motion" not in html + runtime + (package_dir / "motion.css").read_text(encoding="utf-8"):
        errors.append("package does not declare reduced-motion behavior")
    plan = load_document(package_dir / "motion-plan.yaml")
    foreground = plan.get("foreground_plan", {}) if isinstance(plan, dict) else {}
    actor_ids = foreground.get("source_actors", []) if isinstance(foreground, dict) else []
    if actor_ids:
        for actor_id in actor_ids:
            marker = f'data-motiflux-actor="{actor_id}"'
            if marker not in html and f'id="{actor_id}"' not in html:
                errors.append(f"motion.html missing source actor binding: {actor_id}")
    return result(package_dir, errors)


def result(package_dir: Path, errors: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "package": str(package_dir),
        "valid": not errors,
        "errors": errors,
        "status": "complete" if not errors else "candidate",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_package(args.package.resolve())
    write_json(args.output, report)
    raise SystemExit(0 if report["valid"] else 1)


if __name__ == "__main__":
    main()
