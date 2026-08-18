from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "skills" / "motiflux" / "tools"
sys.path.insert(0, str(TOOLS))

from audit_motion import audit  # noqa: E402
from build_web_package import build  # noqa: E402
from compare_shape import compare  # noqa: E402
from measure_mark import measure  # noqa: E402
from route_theme import parse_themes, route  # noqa: E402
from engine.artifacts import ArtifactStore  # noqa: E402
from engine.catalog import load_catalog  # noqa: E402
from engine.planner import build_plan, validate_references  # noqa: E402
from engine.project_pipeline import run_project  # noqa: E402
from validate_artifact import validate  # noqa: E402


EXAMPLE = ROOT / "examples" / "basic-mark"


class MotifluxToolTests(unittest.TestCase):
    def test_measure_svg_produces_semantic_observations(self) -> None:
        result = measure(EXAMPLE / "mark.svg")
        self.assertEqual(result["status"], "candidate")
        self.assertEqual(result["observations"]["topology"]["element_count"], 2)
        self.assertEqual(len(result["observations"]["canonical_fingerprint"]["actor_ids"]), 2)

    def test_compare_equal_scene_is_semantically_complete(self) -> None:
        result = compare(EXAMPLE / "mark.svg", EXAMPLE / "mark.svg")
        self.assertEqual(result["status"], "complete")
        self.assertTrue(result["geometry_metrics"]["semantic_equal"])

    def test_audit_preserves_missing_browser_evidence(self) -> None:
        result = audit(EXAMPLE / "telemetry.json", duration_ms=1200)
        self.assertEqual(result["status"], "candidate")
        self.assertIn("canonical-end-state-fingerprint", result["not_run"])
        self.assertIn("accessibility-browser-check", result["not_run"])

    def test_build_emits_runtime_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "package"
            result = build(EXAMPLE / "mark.svg", EXAMPLE / "motion-plan.yaml", output)
            self.assertEqual(result["status"], "candidate")
            html = (output / "motion.html").read_text(encoding="utf-8")
            runtime = (output / "motion.js").read_text(encoding="utf-8")
            self.assertIn("__motifluxReady", runtime)
            self.assertIn("__motifluxControl", runtime)
            self.assertIn("data-motiflux-mark", html)
            evidence = json.loads((output / "evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(evidence["status"], "candidate")

    def test_theme_router_excludes_composition_guidance(self) -> None:
        guide = (ROOT / "skills" / "motiflux" / "guides" / "motion-themes.md").read_text(encoding="utf-8")
        themes = parse_themes(guide)
        self.assertEqual(len(themes), 13)
        self.assertNotIn("Theme composition", {theme["name"] for theme in themes})
        selection = route("AI security startup")["theme_selection"]
        self.assertEqual(selection["primary"], "AI-field")
        self.assertNotIn("Theme composition", selection["scores"])

    def test_canonical_catalog_has_thirteen_unique_profiles(self) -> None:
        catalog = load_catalog()
        self.assertEqual(len(catalog.profiles), 13)
        self.assertEqual(len({profile.id for profile in catalog.profiles}), 13)

    def test_ai_request_routes_to_catalog_ai_field(self) -> None:
        selection = load_catalog().route("I want a logo animation for my artificial intelligence company")
        self.assertEqual(selection["theme_selection"]["primary_id"], "ai-field")
        self.assertIn("artificial intelligence", selection["theme_selection"]["matched_tags"])

    def test_plan_references_reject_dangling_actor_beat_and_theme(self) -> None:
        plan = {
            "theme_selection": {"primary_id": "missing-theme"},
            "actors": [{"id": "mark", "parent": "missing-parent"}],
            "beats": [{"id": "form", "intent": "form"}],
            "dependencies": [{"actor": "missing-actor", "beat": "missing-beat", "starts_after": ["missing-beat"]}],
        }
        errors = validate_references(plan, theme_ids={"ai-field"})
        self.assertTrue(any("unknown theme" in error for error in errors))
        self.assertTrue(any("unknown parent" in error for error in errors))
        self.assertTrue(any("unknown actor" in error for error in errors))
        self.assertTrue(any("unknown beat" in error for error in errors))

    def test_artifact_store_rejects_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ArtifactStore(Path(temp_dir) / "project")
            with self.assertRaises(ValueError):
                store.path("..\\outside.json")

    def test_project_pipeline_writes_manifest_and_package_for_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_project(EXAMPLE / "mark.svg", "AI logo animation", Path(temp_dir) / "project")
            self.assertEqual(result["status"], "candidate")
            self.assertEqual(result["source"]["format"], "svg")
            self.assertTrue((Path(temp_dir) / "project" / "project.json").is_file())
            self.assertTrue((Path(temp_dir) / "project" / "package" / "motion.html").is_file())
            self.assertEqual(result["stages"][1]["metadata"]["primary"], "ai-field")
            self.assertEqual(result["stages"][2]["status"], "complete")
            report = validate("project", Path(temp_dir) / "project" / "project.json")
            self.assertTrue(report["valid"], report["errors"])

    def test_project_pipeline_keeps_raster_reconstruction_as_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "mark.jpg"
            source.write_bytes((ROOT / "showcase" / "assets" / "prysai-logo-white.jpg").read_bytes())
            result = run_project(source, "AI logo animation", Path(temp_dir) / "project")
            stages = {stage["stage"]: stage for stage in result["stages"]}
            self.assertEqual(result["source"]["format"], "jpeg")
            self.assertEqual(stages["reconstruct"]["status"], "candidate")
            self.assertIn("reconstruct-raster-source", result["not_run"])
            self.assertEqual(stages["compile"]["status"], "blocked")

    def test_showcase_contains_thirteen_motion_players_and_runtime_contract(self) -> None:
        html = (ROOT / "showcase" / "index.html").read_text(encoding="utf-8")
        runtime = (ROOT / "showcase" / "app.js").read_text(encoding="utf-8")
        self.assertEqual(html.count("data-motion-card"), 13)
        self.assertEqual(html.count('data-card-action="play"'), 13)
        self.assertEqual(html.count('data-card-action="replay"'), 13)
        self.assertIn("requestAnimationFrame", runtime)
        self.assertIn("window.__motifluxShowcaseReady", runtime)
        self.assertIn('setMotion("running")', runtime)

    def test_showcase_exposes_portable_image_to_animation_outputs(self) -> None:
        html = (ROOT / "showcase" / "index.html").read_text(encoding="utf-8")
        animation_dir = ROOT / "showcase" / "assets" / "animations"
        self.assertIn("assets/animations/prysai-ai-field.gif", html)
        self.assertEqual(len(list(animation_dir.glob("prysai-*.gif"))), 13)
        self.assertGreater((animation_dir / "prysai-ai-field.gif").stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
