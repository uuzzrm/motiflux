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
ENGINE_NAMES = {
    "__init__.py",
    "artifacts.py",
    "catalog.py",
    "domain.py",
    "pipeline.py",
    "planner.py",
    "project_pipeline.py",
    "runtime.py",
    "runtime_probe.py",
    "stages.py",
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
    kernel_guide_path = SKILL_ROOT / "guides" / "project-kernel.md"
    agent_path = SKILL_ROOT / "agents" / "openai.yaml"
    schema_paths = sorted((SKILL_ROOT / "schemas").glob("*.schema.json"))
    tool_paths = sorted((SKILL_ROOT / "tools").glob("*.py"))
    engine_paths = sorted((SKILL_ROOT / "tools" / "engine").glob("*.py"))
    for path in (skill_path, guide_path, kernel_guide_path, agent_path, *schema_paths, *tool_paths, *engine_paths):
        require_file(path)
    if {path.name for path in tool_paths} != TOOL_NAMES:
        fail("skill tools must contain exactly the declared adapter set")
    if {path.name for path in schema_paths} != {
        "source-analysis.schema.json",
        "motion-plan.schema.json",
        "telemetry.schema.json",
        "evidence.schema.json",
        "theme-selection.schema.json",
        "project.schema.json",
        "artifact-index.schema.json",
        "runtime-probe.schema.json",
    }:
        fail("skill schemas must contain the declared artifact contracts")
    if {path.name for path in engine_paths} != ENGINE_NAMES:
        fail("project engine must contain the declared internal modules")

    catalog_path = SKILL_ROOT / "catalog" / "themes.json"
    catalog_schema_path = SKILL_ROOT / "catalog" / "themes.schema.json"
    require_file(catalog_path)
    require_file(catalog_schema_path)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog_themes = catalog.get("themes")
    catalog_ids = [item.get("id") for item in catalog_themes if isinstance(item, dict)] if isinstance(catalog_themes, list) else []
    if len(catalog_ids) != 13 or len(set(catalog_ids)) != 13:
        fail("canonical theme catalog must contain exactly 13 unique IDs")

    skill = skill_path.read_text(encoding="utf-8")
    guide = guide_path.read_text(encoding="utf-8")
    kernel_guide = kernel_guide_path.read_text(encoding="utf-8")
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
        "catalog/themes.json",
        "tools/motiflux.py project",
        "project manifest",
        "project pipeline",
        "tools/motiflux.py probe",
        "artifact-index.json",
        "PipelineRunner",
    ):
        if required not in skill:
            fail(f"SKILL.md is missing required concept: {required}")
    for required in ("Stage graph", "requires", "provides", "Artifact index", "runtime-probe"):
        if required not in kernel_guide:
            fail(f"project kernel guide is missing required concept: {required}")

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
    if "engine.catalog" not in (SKILL_ROOT / "tools" / "route_theme.py").read_text(encoding="utf-8"):
        fail("route compatibility adapter must delegate to engine.catalog")

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
        showcase / "assets" / "animations" / "prysai-ai-field.gif",
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
    catalog = json.loads((SKILL_ROOT / "catalog" / "themes.json").read_text(encoding="utf-8"))
    catalog_ids = {theme.get("id") for theme in catalog.get("themes", []) if isinstance(theme, dict)}
    if set(theme_ids) != catalog_ids:
        fail("showcase theme ids must match the canonical catalog")
    generator = (showcase / "generate_showcase.py").read_text(encoding="utf-8")
    if "catalog" not in generator.lower():
        fail("showcase generator must consume the canonical catalog")
    index = (showcase / "index.html").read_text(encoding="utf-8")
    if index.count('class="theme-card"') != 13:
        fail("showcase HTML must contain exactly 13 theme cards")
    if index.count("assets/prysai-mark-crop.jpg") != 14:
        fail("showcase HTML must use the same source derivative in the primary input and every card")
    if index.count("assets/prysai-mark-transparent.png") != 13:
        fail("showcase HTML must provide one output mark per theme card")
    if "assets/animations/prysai-ai-field.gif" not in index:
        fail("showcase must include the primary image-to-animation output")
    animation_paths = sorted((showcase / "assets" / "animations").glob("prysai-*.gif"))
    if len(animation_paths) != 13:
        fail("showcase must export one portable GIF per theme")
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


def validate_github_gallery() -> None:
    """Ensure the root README exposes every canonical theme as static -> GIF."""

    readme_path = ROOT / "README.md"
    require_file(readme_path)
    readme = readme_path.read_text(encoding="utf-8")
    start_marker = "<!-- GITHUB_GALLERY:START -->"
    end_marker = "<!-- GITHUB_GALLERY:END -->"
    if readme.count(start_marker) != 1 or readme.count(end_marker) != 1:
        fail("README must contain exactly one GitHub gallery marker pair")
    start = readme.index(start_marker)
    end = readme.index(end_marker)
    if end <= start:
        fail("README GitHub gallery markers must be in order")
    gallery = readme[start:end]

    catalog = json.loads((SKILL_ROOT / "catalog" / "themes.json").read_text(encoding="utf-8"))
    themes = catalog.get("themes", [])
    if not isinstance(themes, list) or len(themes) != 13:
        fail("GitHub gallery source catalog must contain exactly 13 themes")
    static_path = "showcase/assets/prysai-mark-crop.jpg"
    if gallery.count(static_path) != 13:
        fail("GitHub gallery must show the static source exactly once per theme")
    if not (ROOT / static_path).is_file():
        fail("GitHub gallery static source image is missing")
    for theme in themes:
        theme_id = theme.get("id") if isinstance(theme, dict) else None
        if not theme_id:
            fail("GitHub gallery source catalog contains an invalid theme record")
        animation_path = f"showcase/assets/animations/prysai-{theme_id}.gif"
        if theme_id not in gallery or animation_path not in gallery:
            fail(f"GitHub gallery is missing canonical theme or GIF: {theme_id}")
        if not (ROOT / animation_path).is_file():
            fail(f"GitHub gallery GIF is missing: {animation_path}")
        for keyword in theme.get("aliases", []):
            if str(keyword) not in gallery:
                fail(f"GitHub gallery is missing trigger keyword for {theme_id}: {keyword}")


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
        validate_github_gallery()
        validate_content(skill, guide)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Motiflux validation failed: {error}")
        return 1
    print("Motiflux project validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
