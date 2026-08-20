"""Offline runtime probes for a generated Motiflux package."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION


def probe_runtime(package_dir: Path, *, node_executable: str | None = None) -> dict[str, Any]:
    """Check static runtime contracts and optionally execute a local Node harness.

    The harness uses a tiny fake DOM to exercise readiness, controls, seek, and
    canonical finish state. It deliberately does not claim layout, pixels, or
    accessibility-tree evidence; those remain explicit browser gaps.
    """

    package_dir = package_dir.resolve()
    required = ("motion.html", "motion.css", "motion.js", "mark.svg")
    missing = [relative for relative in required if not (package_dir / relative).is_file()]
    if missing:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "blocked",
            "scope": "offline-runtime-contract",
            "package": str(package_dir),
            "checks": {},
            "capabilities": {"node-runtime": bool(node_executable)},
            "not_run": ["static-runtime-contract", *[f"missing:{item}" for item in missing]],
            "unresolved": ["generated package is missing required runtime files"],
        }

    html = (package_dir / "motion.html").read_text(encoding="utf-8")
    css = (package_dir / "motion.css").read_text(encoding="utf-8")
    javascript = (package_dir / "motion.js").read_text(encoding="utf-8")
    checks: dict[str, Any] = {}
    static_markers = (
        "data-motiflux-root",
        "data-motiflux-mark",
        "data-motiflux-controls",
        "data-motiflux-play",
        "data-motiflux-pause",
        "data-motiflux-replay",
    )
    missing_markers = [marker for marker in static_markers if marker not in html]
    runtime_markers = (
        "__motifluxReady",
        "__motifluxControl",
        "finish()",
        "prefers-reduced-motion",
        "document.hidden",
        "visibilitychange",
    )
    missing_runtime_markers = [marker for marker in runtime_markers if marker not in javascript and marker not in css]
    growth_markers = (
        'data-growth-mode="staged-source-actors"',
        "data-motiflux-role",
        "actorProgress",
        "strokeDashoffset",
    )
    missing_growth_markers = [marker for marker in growth_markers if marker not in javascript and marker not in html]
    checks["static-contract"] = {
        "passed": not missing_markers and not missing_runtime_markers and not missing_growth_markers,
        "missing_html_markers": missing_markers,
        "missing_runtime_markers": missing_runtime_markers,
        "missing_growth_markers": missing_growth_markers,
    }

    unresolved: list[str] = []
    if missing_markers or missing_runtime_markers:
        unresolved.append("runtime package is missing required static contract markers")
    if missing_growth_markers:
        unresolved.append("runtime package is missing the staged source-actor growth contract")
    not_run = ["browser-runtime-check", "accessibility-tree-check", "browser-pixel-diff"]
    if node_executable:
        syntax = _node_syntax_check(node_executable, package_dir / "motion.js")
        checks["node-syntax"] = syntax
        harness = _node_harness(node_executable, package_dir / "motion.js")
        checks["node-runtime-harness"] = harness
        if not syntax.get("passed") or not harness.get("passed"):
            unresolved.append("local Node runtime probe failed")
    else:
        not_run.append("node-runtime-harness")
        unresolved.append("Node runtime is unavailable; only static contract checks ran")

    status = "complete" if checks["static-contract"]["passed"] and not unresolved else "candidate"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "scope": "offline-runtime-contract",
        "package": str(package_dir),
        "checks": checks,
        "capabilities": {"node-runtime": bool(node_executable), "browser-runtime": False},
        "not_run": not_run,
        "unresolved": unresolved,
    }


def _node_syntax_check(node: str, javascript_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [node, "--check", str(javascript_path)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return {
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "stderr": result.stderr.strip(),
    }


def _node_harness(node: str, javascript_path: Path) -> dict[str, Any]:
    path_literal = json.dumps(str(javascript_path))
    script = f"""
const fs = require('fs');
const vm = require('vm');
const nodes = new Map();
function node(selector, dataset={{}}) {{
  return {{ dataset, style: {{ setProperty() {{}} }},
    setAttribute(name, value) {{ this[name] = value; }},
    addEventListener(name, handler) {{ this['on' + name] = handler; }} }};
}}
nodes.set('[data-motiflux-root]', node('root', {{durationMs:'1200', tempo:'1'}}));
nodes.set('[data-motiflux-mark]', node('mark'));
for (const selector of ['[data-motiflux-play]','[data-motiflux-pause]','[data-motiflux-replay]','[data-motiflux-tempo]']) nodes.set(selector, node(selector));
globalThis.window = {{ matchMedia: () => ({{ matches: false }}), addEventListener() {{}} }};
globalThis.document = {{ hidden: false, querySelector: selector => nodes.get(selector) || null, addEventListener() {{}} }};
globalThis.requestAnimationFrame = () => 1;
globalThis.cancelAnimationFrame = () => {{}};
vm.runInThisContext(fs.readFileSync({path_literal}, 'utf8'));
if (!window.__motifluxReady || !window.__motifluxControl) throw new Error('runtime readiness contract failed');
window.__motifluxControl.finish();
const state = nodes.get('[data-motiflux-root]').dataMotifluxState || nodes.get('[data-motiflux-root]')['data-motiflux-state'];
if (state !== 'canonical') throw new Error('finish did not reach canonical state');
window.__motifluxControl.replay();
window.__motifluxControl.pause();
process.stdout.write(JSON.stringify({{passed:true, final_state:state}}));
"""
    result = subprocess.run(
        [node, "-e", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    parsed: dict[str, Any] = {}
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            parsed = {}
    return {
        "passed": result.returncode == 0 and parsed.get("passed") is True,
        "returncode": result.returncode,
        "result": parsed,
        "stderr": result.stderr.strip(),
    }
