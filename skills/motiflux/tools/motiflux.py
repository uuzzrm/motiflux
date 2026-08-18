"""Unified command entrypoint for the Motiflux tool seam."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from audit_motion import audit
from build_web_package import build
from compare_shape import compare
from measure_mark import measure
from motiflux_core import write_json
from route_theme import route
from validate_artifact import SCHEMAS, validate
from validate_package import validate_package


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    measure_parser = subparsers.add_parser("measure")
    measure_parser.add_argument("input", type=Path)
    measure_parser.add_argument("--output", type=Path)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("candidate", type=Path)
    compare_parser.add_argument("canonical", type=Path)
    compare_parser.add_argument("--tolerance", type=float, default=1e-6)
    compare_parser.add_argument("--output", type=Path)

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("telemetry", type=Path)
    audit_parser.add_argument("--canonical", type=Path)
    audit_parser.add_argument("--accessibility", type=Path)
    audit_parser.add_argument("--duration-ms", type=float)
    audit_parser.add_argument("--output", type=Path)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("mark", type=Path)
    build_parser.add_argument("plan", type=Path)
    build_parser.add_argument("output", type=Path)

    route_parser = subparsers.add_parser("route")
    route_parser.add_argument("query")
    route_parser.add_argument("--output", type=Path)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("kind", choices=sorted(SCHEMAS))
    validate_parser.add_argument("artifact", type=Path)
    validate_parser.add_argument("--output", type=Path)

    package_parser = subparsers.add_parser("package")
    package_parser.add_argument("package", type=Path)
    package_parser.add_argument("--output", type=Path)

    args = parser.parse_args()
    if args.command == "measure":
        result, output = measure(args.input.resolve()), args.output
    elif args.command == "compare":
        result, output = compare(args.candidate.resolve(), args.canonical.resolve(), args.tolerance), args.output
    elif args.command == "audit":
        result, output = audit(args.telemetry.resolve(), canonical_path=args.canonical.resolve() if args.canonical else None, accessibility_path=args.accessibility.resolve() if args.accessibility else None, duration_ms=args.duration_ms), args.output
    elif args.command == "build":
        result, output = build(args.mark.resolve(), args.plan.resolve(), args.output.resolve()), None
    elif args.command == "route":
        result, output = route(args.query), args.output
    elif args.command == "validate":
        result, output = validate(args.kind, args.artifact.resolve()), args.output
    else:
        result, output = validate_package(args.package.resolve()), args.output
    write_json(output, result)


if __name__ == "__main__":
    main()
