#!/usr/bin/env python3
"""Validate the Motiflux plugin layout and the content-level invariants."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "motiflux"
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".html", ".css", ".js", ".gitignore"}
TOOL_NAMES = {
    "motiflux_core.py",
    "measure_mark.py",
    "compare_shape.py",
    "audit_motion.py",
    "build_web_package.py",
    "motiflux.py",
    "validate_artifact.py",
    "route_theme.py",
    "validate_package.py",
}


def fail(message: str) -> None:
    raise ValueError(message)


def require_file(path: Path) -> None:
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(ROOT)}")


def validate_manifest() -> None:
    path = ROOT / ".codex-plugin" / "plugin.json"
    require_file(path)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"invalid plugin manifest JSON: {error}")
    if manifest.get("name") != "motiflux":
        fail("plugin manifest name must be motiflux")
    if manifest.get("version") != "1.0.0":
        fail("plugin manifest version must be 1.0.0 for the V1 development line")
    if not manifest.get("description"):
        fail("plugin manifest description must be non-empty")
    if manifest.get("skills") != "./skills/":
        fail("plugin manifest skills path must be ./skills/")
    interface = manifest.get("interface", {})
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        if not interface.get(field):
            fail(f"plugin manifest interface.{field} must be non-empty")
    if not isinstance(interface.get("defaultPrompt"), list) or not interface["defaultPrompt"]:
        fail("plugin manifest interface.defaultPrompt must be a non-empty list")


def validate_skill() -> tuple[str, str]:
    skill_path = SKILL_ROOT / "SKILL.md"
    guide_path = SKILL_ROOT / "guides" / "motion-themes.md"
    agent_path = SKILL_ROOT / "agents" / "openai.yaml"
    schema_paths = sorted((SKILL_ROOT / "schemas").glob("*.schema.json"))
    tool_paths = sorted((SKILL_ROOT / "tools").glob("*.py"))
    for path in (skill_path, guide_path, agent_path, *schema_paths, *tool_paths):
        require_file(path)
    if {path.name for path in tool_paths} != TOOL_NAMES:
        fail("skill tools must contain exactly the declared adapter set")
    if {path.name for path in schema_paths} != {
        "source-analysis.schema.json",
        "motion-plan.schema.json",
        "telemetry.schema.json",
        "evidence.schema.json",
        "theme-selection.schema.json",
    }:
        fail("skill schemas must contain the declared artifact contracts")

    skill = skill_path.read_text(encoding="utf-8")
    guide = guide_path.read_text(encoding="utf-8")
    agent = agent_path.read_text(encoding="utf-8")

    if not skill.startswith("---\n") or "\n---" not in skill[4:]:
        fail("skill frontmatter must be present and closed")
    frontmatter = skill[4 : skill.index("\n---", 4)]
    if not re.search(r"^name:\s*motiflux\s*$", frontmatter, re.MULTILINE):
        fail("skill frontmatter name must be motiflux")
    if not re.search(r"^description:\s*.+$", frontmatter, re.MULTILINE):
        fail("skill frontmatter description must be non-empty")
    if len(skill.splitlines()) > 500:
        fail("SKILL.md must remain under 500 lines")

    for required in (
        "constraint_graph",
        "scene_graph",
        "motion_graph",
        "evidence_ledger",
        "OBSERVE",
        "MODEL",
        "RECONSTRUCT",
        "COMPOSE",
        "INSTRUMENT",
        "VALIDATE",
        "DELIVER",
        "semantic fingerprint",
        "guides/output-contract.md",
        "guides/runtime-contract.md",
        "tools/motiflux.py",
        "tools/motiflux.py measure",
        "tools/motiflux.py compare",
        "tools/motiflux.py audit",
        "tools/motiflux.py build",
        "tools/motiflux.py route",
    ):
        if required not in skill:
            fail(f"SKILL.md is missing required concept: {required}")

    theme_count = len(re.findall(r"^##\s+\d+\.\s+", guide, re.MULTILINE))
    if theme_count < 10:
        fail(f"theme atlas must provide at least 10 numbered themes; found {theme_count}")
    for required in ("Theme record", "Theme composition", "Public reference index"):
        if required not in guide:
            fail(f"motion theme atlas is missing section: {required}")

    if not re.search(r"^interface:\s*$", agent, re.MULTILINE):
        fail("skill UI metadata must contain interface")
    for required in ("display_name", "short_description", "default_prompt"):
        if not re.search(rf"^\s+{required}:\s*\".+\"\s*$", agent, re.MULTILINE):
            fail(f"skill UI metadata is missing quoted field: {required}")
    if "$motiflux" not in agent:
        fail("skill UI default prompt must explicitly name $motiflux")

    return skill, guide


def validate_showcase() -> None:
    showcase = ROOT / "showcase"
    required = (
        showcase / "README.md",
        showcase / "index.html",
        showcase / "styles.css",
        showcase / "app.js",
        showcase / "themes.json",
        showcase / "generate_showcase.py",
        showcase / "assets" / "prysai-logo-white.jpg",
        showcase / "assets" / "prysai-mark-crop.jpg",
        showcase / "assets" / "prysai-mark-transparent.png",
        showcase / "output" / "pdf" / "motiflux-theme-atlas.pdf",
    )
    for path in required:
        require_file(path)
    try:
        showcase_data = json.loads((showcase / "themes.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"invalid showcase theme JSON: {error}")
    themes = showcase_data.get("themes")
    if not isinstance(themes, list) or len(themes) != 13:
        fail("showcase must contain exactly 13 theme records")
    theme_ids = [theme.get("id") for theme in themes if isinstance(theme, dict)]
    if len(theme_ids) != 13 or len(set(theme_ids)) != 13:
        fail("showcase theme ids must be present and unique")
    index = (showcase / "index.html").read_text(encoding="utf-8")
    if index.count('class="theme-card"') != 13:
        fail("showcase HTML must contain exactly 13 theme cards")
    if index.count("assets/prysai-mark-crop.jpg") != 13:
        fail("showcase HTML must repeat the same source derivative in every card")
    if index.count("assets/prysai-mark-transparent.png") != 13:
        fail("showcase HTML must provide one output mark per theme card")
    for required_marker in (
        'data-action="play"',
        'data-action="pause"',
        'data-action="replay"',
        'data-filter',
        'prefers-reduced-motion',
        'aria-label=',
    ):
        if required_marker not in index and required_marker not in (showcase / "styles.css").read_text(encoding="utf-8"):
            fail(f"showcase is missing required interaction/accessibility marker: {required_marker}")


def validate_content(skill: str, guide: str) -> None:
    # Construct the comparison strings from pieces so this guard itself does not
    # become a source of the historical identifiers it is designed to reject.
    forbidden = [
        "".join(("P", "2", "M")),
        "".join(("Pixel", "2", "Motion")),
        ":".join(("20", "50", "30")),
        "pathLength=" + "=" + chr(34) + "1" + chr(34),
        "de " + "Casteljau",
        "tip " + "glint",
        "easing " + "probe",
        "continuity " + "sweep",
        "Final Frame " + "exact diff 0",
    ]
    haystack = f"{skill}\n{guide}".casefold()
    for marker in forbidden:
        if marker.casefold() in haystack:
            fail(f"content contains a forbidden historical marker: {marker}")

    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.rstrip() != line:
                    fail(f"trailing whitespace: {path.relative_to(ROOT)}:{line_number}")


def main() -> int:
    try:
        validate_manifest()
        skill, guide = validate_skill()
        validate_showcase()
        validate_content(skill, guide)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Motiflux validation failed: {error}")
        return 1
    print("Motiflux project validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
