from __future__ import annotations

import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageSequence


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
from engine.pipeline import PipelineContext, PipelineRunner, StageDefinition  # noqa: E402
from engine.domain import MotionBeat, MotionEdge, MotionGraph, SceneActor, StageResult  # noqa: E402
from engine.runtime_probe import probe_runtime  # noqa: E402
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

    def test_normalized_routing_handles_hyphens_and_word_boundaries(self) -> None:
        catalog = load_catalog()
        self.assertEqual(catalog.route("machine-learning logo")["theme_selection"]["primary_id"], "ai-field")
        self.assertEqual(catalog.route("artificial-intelligence logo")["theme_selection"]["primary_id"], "ai-field")
        self.assertEqual(catalog.route("email logo")["theme_selection"]["primary_id"], "system-spatial")

    def test_education_alias_routes_to_system_spatial(self) -> None:
        selection = load_catalog().route("我想做一个教育课程 logo 动画")
        self.assertEqual(selection["theme_selection"]["primary_id"], "system-spatial")
        self.assertIn("教育", selection["theme_selection"]["matched_tags"])

    def test_catalog_trajectories_are_unique_and_complete(self) -> None:
        catalog = load_catalog()
        trajectories = [profile.trajectory_id for profile in catalog.profiles]
        self.assertEqual(len(trajectories), 13)
        self.assertEqual(len(set(trajectories)), 13)
        self.assertTrue(all(profile.trajectory_summary for profile in catalog.profiles))

    def test_plans_encode_theme_specific_beats_and_channels(self) -> None:
        catalog = load_catalog()
        analysis = measure(EXAMPLE / "mark.svg")
        ai_selection = catalog.route("AI logo animation")
        system_selection = catalog.route("education logo animation")
        ai_plan = build_plan(analysis, ai_selection, catalog.get("ai-field"), project_name="AI", source_name="mark.svg")
        system_plan = build_plan(analysis, system_selection, catalog.get("system-spatial"), project_name="Education", source_name="mark.svg")
        self.assertNotEqual([beat["id"] for beat in ai_plan["beats"]], [beat["id"] for beat in system_plan["beats"]])
        self.assertIn("trajectory:signal-convergence", ai_plan["dependencies"][0]["property_channels"])
        self.assertEqual(ai_plan["runtime"]["trajectory_id"], "signal-convergence")

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
            runtime_html = (Path(temp_dir) / "project" / "package" / "motion.html").read_text(encoding="utf-8")
            runtime_css = (Path(temp_dir) / "project" / "package" / "motion.css").read_text(encoding="utf-8")
            self.assertIn('data-trajectory="signal-convergence"', runtime_html)
            self.assertIn('[data-trajectory="signal-convergence"]', runtime_css)
            report = validate("project", Path(temp_dir) / "project" / "project.json")
            self.assertTrue(report["valid"], report["errors"])
            index = json.loads((Path(temp_dir) / "project" / "artifact-index.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(index["count"], 1)
            source_record = next(item for item in index["artifacts"] if item["path"] == "source-analysis.json")
            payload = (Path(temp_dir) / "project" / source_record["path"]).read_bytes()
            self.assertEqual(source_record["bytes"], len(payload))
            self.assertEqual(source_record["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(result["architecture_version"], "1.1")
            self.assertEqual(result["execution"]["runner"], "PipelineRunner")
            self.assertIn("runtime_probe", result["artifacts"])

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
            self.assertIn("missing-prerequisite:canonical-mark", result["not_run"])

    def test_artifact_index_rejects_changed_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "project"
            run_project(EXAMPLE / "mark.svg", "AI logo animation", output)
            index_path = output / "artifact-index.json"
            first = validate("artifact-index", index_path)
            self.assertTrue(first["valid"], first["errors"])
            source_path = output / "source-analysis.json"
            source_path.write_text(source_path.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
            second = validate("artifact-index", index_path)
            self.assertFalse(second["valid"])
            self.assertTrue(any("hash mismatch" in error or "size mismatch" in error for error in second["errors"]))

    def test_pipeline_runner_blocks_missing_prerequisites_and_does_not_call_handler(self) -> None:
        calls: list[str] = []

        def handler(context: PipelineContext) -> StageResult:
            calls.append("called")
            return StageResult("downstream", "complete")

        runner = PipelineRunner((StageDefinition("downstream", ("missing",), (), handler),))
        with tempfile.TemporaryDirectory() as temp_dir:
            context = PipelineContext.create(EXAMPLE / "mark.svg", "test", Path(temp_dir), ArtifactStore(Path(temp_dir)), load_catalog())
            result = runner.run(context)[0]
        self.assertEqual(result.status, "blocked")
        self.assertEqual(calls, [])
        self.assertIn("missing-prerequisite:missing", result.not_run)

    def test_runtime_probe_reports_node_and_browser_evidence_separately(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "package"
            build(EXAMPLE / "mark.svg", EXAMPLE / "motion-plan.yaml", output)
            report = probe_runtime(output, node_executable=None)
        self.assertEqual(report["status"], "candidate")
        self.assertTrue(report["checks"]["static-contract"]["passed"])
        self.assertIn("browser-runtime-check", report["not_run"])
        self.assertIn("node-runtime-harness", report["not_run"])

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

    def test_showcase_gifs_are_blank_to_canonical_growth_sequences(self) -> None:
        snapshot = json.loads((ROOT / "showcase" / "themes.json").read_text(encoding="utf-8"))
        expected = ["blank", "spark", "arc", "bar", "monogram", "wordmark", "canonical"]
        self.assertEqual(snapshot["themes"][3]["growth_sequence"], expected)
        html = (ROOT / "showcase" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count('class="growth-gif"'), 13)
        self.assertIn("blank / spark / arc / bar / monogram / wordmark / canonical", html)
        with Image.open(ROOT / "showcase" / "assets" / "animations" / "prysai-ai-field.gif") as gif:
            frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(gif)]
        self.assertGreater(len(frames), 1)
        white_pixels = [sum(1 for pixel in frame.getdata() if min(pixel) > 190) for frame in frames]
        self.assertEqual(white_pixels[0], 0)
        self.assertLess(white_pixels[7], white_pixels[-1] * 0.45)
        self.assertGreater(white_pixels[-1], white_pixels[0] + 1000)

    def test_showcase_foregrounds_have_distinct_midframes_and_canonical_endpoints(self) -> None:
        catalog = load_catalog()
        animation_dir = ROOT / "showcase" / "assets" / "animations"
        midframe_masks: list[bytes] = []
        canonical = Image.open(ROOT / "showcase" / "assets" / "prysai-mark-transparent.png").convert("RGBA")
        canonical.thumbnail((int(900 * .68), int(302 * .76)), Image.Resampling.LANCZOS)
        expected = Image.new("L", (900, 302), 0)
        expected.paste(canonical.getchannel("A"), ((900 - canonical.width) // 2, (302 - canonical.height) // 2))
        expected_pixels = bytes(1 if value > 128 else 0 for value in expected.getdata())
        for profile in catalog.profiles:
            with Image.open(animation_dir / f"prysai-{profile.id}.gif") as gif:
                frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(gif)]
            middle = frames[len(frames) // 2]
            midframe_masks.append(bytes(1 if min(pixel) > 180 else 0 for pixel in middle.getdata()))
            actual = bytes(1 if min(pixel) > 180 else 0 for pixel in frames[-1].getdata())
            intersection = sum(left and right for left, right in zip(actual, expected_pixels))
            union = sum(left or right for left, right in zip(actual, expected_pixels))
            self.assertGreater(intersection / max(1, union), .97, profile.id)
        self.assertEqual(len(set(midframe_masks)), 13)

    def test_github_gallery_uses_static_to_gif_cards(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start = readme.index("<!-- GITHUB_GALLERY:START -->")
        end = readme.index("<!-- GITHUB_GALLERY:END -->")
        gallery = readme[start:end]
        self.assertIn('<table class="motiflux-gallery">', gallery)
        self.assertEqual(gallery.count("<h3>"), 13)
        self.assertEqual(gallery.count("STATIC SOURCE"), 13)
        self.assertEqual(gallery.count("PLAYING GIF"), 13)

    def test_motion_graph_plan_preserves_scene_actor_bindings(self) -> None:
        actor = SceneActor(
            id="mark",
            tag="path",
            role="identity-bearing actor",
            layer=0,
            bounds=(0, 0, 100, 40),
            geometry_ref="mark.svg#mark",
        )
        graph = MotionGraph(
            schema_version="1.0",
            status="complete",
            project={"name": "test"},
            theme_selection={"primary_id": "ai-field"},
            motion_language={"traits": []},
            constraints=(),
            actor_ids=("mark",),
            actors=(actor,),
            beats=(MotionBeat("form", "apply motion", 1.0),),
            edges=(MotionEdge("mark", "form", property_channels=("transform",)),),
            runtime={"duration_ms": 1000},
        )
        plan_actor = graph.to_plan()["actors"][0]
        self.assertEqual(plan_actor["id"], "mark")
        self.assertEqual(plan_actor["tag"], "path")
        self.assertEqual(plan_actor["geometry_ref"], "mark.svg#mark")


if __name__ == "__main__":
    unittest.main()
