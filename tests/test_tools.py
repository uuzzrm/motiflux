from __future__ import annotations

import json
import hashlib
import sys
import shutil
import subprocess
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
from engine.runtime import compile_runtime, mark_with_runtime_actor_attributes  # noqa: E402
from engine.raster import analyze_pixels, analyze_raster  # noqa: E402
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
            self.assertIn('data-growth-mode="staged-source-actors"', html)
            self.assertIn('data-motiflux-role="arc"', html)
            self.assertIn('data-motiflux-role="origin-dot"', html)
            self.assertIn('data-foreground-actor-stages="{&quot;orbit&quot;:1,&quot;spark&quot;:0}"', html)
            self.assertIn("actorProgress", runtime)
            self.assertIn("strokeDashoffset", runtime)
            self.assertIn("directionTransform", runtime)
            self.assertIn('data-motiflux-runtime', runtime)
            evidence = json.loads((output / "evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(evidence["status"], "candidate")

    def test_build_binds_source_actors_and_emits_valid_javascript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "package"
            build(EXAMPLE / "mark.svg", EXAMPLE / "motion-plan.yaml", output)
            html = (output / "motion.html").read_text(encoding="utf-8")
            runtime = (output / "motion.js").read_text(encoding="utf-8")
            self.assertIn('data-motiflux-actor="orbit"', html)
            self.assertIn('data-motiflux-actor="spark"', html)
            self.assertIn("data-foreground-stage-order", html)
            self.assertIn("sourceNodes.find", runtime)
            if shutil.which("node"):
                checked = subprocess.run(["node", "--check", str(output / "motion.js")], capture_output=True, text=True)
                self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_runtime_prefers_source_element_ids_over_plan_order(self) -> None:
        mark = '<svg><path id="spark"/><circle id="orbit"/></svg>'
        result = mark_with_runtime_actor_attributes(
            mark,
            ["orbit", "spark"],
            {"orbit": "arc", "spark": "origin-dot"},
        )
        self.assertIn('id="spark" data-motiflux-actor="spark" data-motiflux-role="origin-dot"', result)
        self.assertIn('id="orbit" data-motiflux-actor="orbit" data-motiflux-role="arc"', result)

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
        required_fields = {
            "mode",
            "variant",
            "timing",
            "easing",
            "path_strategy",
            "speed_profile",
            "fallback",
        }
        for profile in catalog.profiles:
            with self.subTest(theme=profile.id):
                self.assertTrue(required_fields.issubset(profile.foreground_plan))
                self.assertTrue(all(str(profile.foreground_plan[field]).strip() for field in required_fields))
                self.assertEqual(profile.foreground_plan["fallback"], "static-canonical")
        route_shapes = [
            (
                profile.foreground_plan["mode"],
                profile.foreground_plan["variant"],
                profile.foreground_plan["path_strategy"],
            )
            for profile in catalog.profiles
        ]
        self.assertEqual(len(set(route_shapes)), 13)

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

    def test_prompt_controls_reach_the_motion_plan(self) -> None:
        catalog = load_catalog()
        analysis = measure(EXAMPLE / "mark.svg")
        request = "AI logo animation, 2 seconds, 1.25x, left to right, solid background #101820, no particles, export GIF HTML SVG"
        selection = catalog.route(request)
        plan = build_plan(analysis, selection, catalog.get("ai-field"), project_name="AI", source_name="mark.svg", request=request)
        self.assertEqual(plan["runtime"]["duration_ms"], 2000)
        self.assertEqual(plan["runtime"]["tempo"], 1.25)
        self.assertEqual(plan["runtime"]["direction"], "left-to-right")
        self.assertEqual(plan["runtime"]["background"]["color"], "#101820")
        self.assertFalse(plan["runtime"]["particles"])
        self.assertEqual(plan["runtime"]["requested_formats"], ["gif", "html", "svg"])

    def test_extended_prompt_controls_are_normalized_or_recorded(self) -> None:
        catalog = load_catalog()
        analysis = measure(EXAMPLE / "mark.svg")
        request = "AI logo, 1600ms, speed 1.25x, center outward, sparse secondary particles, seed 7, low-amplitude, no overshoot, opacity-first"
        selection = catalog.route(request)
        plan = build_plan(analysis, selection, catalog.get("ai-field"), project_name="AI", source_name="mark.svg", request=request)
        self.assertEqual(plan["runtime"]["direction"], "radial")
        self.assertEqual(plan["runtime"]["direction_vector"], [0, 0])
        self.assertEqual(plan["runtime"]["particle_density"], "sparse")
        self.assertEqual(plan["runtime"]["seed"], 7)
        constraint_ids = {item["id"] for item in plan["constraints"]}
        self.assertIn("low-motion-policy", constraint_ids)
        self.assertIn("particle-policy", constraint_ids)

    def test_nested_role_review_is_consumed_without_promoting_proposals(self) -> None:
        catalog = load_catalog()
        selection = catalog.route("AI logo animation")
        analysis = {
            "source": {"format": "jpeg"},
            "observations": {"elements": [{
                "id": "actor",
                "tag": "raster-component",
                "bounds": [0, 0, 30, 30],
                "area": 100,
                "role": "unknown",
                "selected_role": "unknown",
                "role_candidates": [],
                "role_review": {
                    "proposed_role": "arc",
                    "accepted_role": None,
                    "confidence": "low",
                    "review_status": "needs-review",
                    "evidence": "reviewable proposal",
                },
            }]},
        }
        plan = build_plan(analysis, selection, catalog.get("ai-field"), project_name="Raster", source_name="mark.jpg")
        annotation = plan["foreground_plan"]["role_annotations"]["actor"]
        self.assertEqual(annotation["role"], "unknown")
        self.assertEqual(annotation["selected_role"], "unknown")
        self.assertEqual(annotation["review_status"], "needs-review")
        self.assertIsNone(annotation["accepted_role"])
        self.assertEqual(plan["actors"][0]["role"], "unknown")
        self.assertEqual(plan["actors"][0]["selected_role"], "unknown")

    def test_bare_accepted_role_without_review_evidence_does_not_promote(self) -> None:
        catalog = load_catalog()
        selection = catalog.route("AI logo animation")
        analysis = {
            "source": {"format": "jpeg"},
            "observations": {"elements": [{
                "id": "actor",
                "tag": "raster-component",
                "bounds": [0, 0, 30, 30],
                "area": 100,
                "accepted_role": "arc",
                "role_candidates": [],
            }]},
        }
        plan = build_plan(analysis, selection, catalog.get("ai-field"), project_name="Raster", source_name="mark.jpg")
        annotation = plan["foreground_plan"]["role_annotations"]["actor"]
        self.assertEqual(annotation["review_status"], "needs-review")
        self.assertIsNone(annotation["accepted_role"])

    def test_raster_accepted_role_requires_accepted_review_and_evidence(self) -> None:
        catalog = load_catalog()
        selection = catalog.route("AI logo animation")
        cases = (
            {
                "accepted_role": "arc",
                "review_status": "needs-review",
                "evidence": "candidate geometry only",
            },
            {
                "accepted_role": "arc",
                "review_status": "accepted",
                "evidence": "",
            },
        )
        for review in cases:
            with self.subTest(review=review):
                analysis = {
                    "source": {"format": "jpeg"},
                    "observations": {"elements": [{
                        "id": "actor",
                        "tag": "raster-component",
                        "bounds": [0, 0, 30, 30],
                        "area": 100,
                        "role_review": review,
                    }]},
                }
                plan = build_plan(analysis, selection, catalog.get("ai-field"), project_name="Raster", source_name="mark.jpg")
                annotation = plan["foreground_plan"]["role_annotations"]["actor"]
                self.assertNotEqual(annotation["review_status"], "accepted")
                self.assertIsNone(annotation["accepted_role"])

    def test_raster_accepted_role_is_promoted_only_by_explicit_review_evidence(self) -> None:
        catalog = load_catalog()
        selection = catalog.route("AI logo animation")
        analysis = {
            "source": {"format": "jpeg"},
            "observations": {"elements": [{
                "id": "actor",
                "tag": "raster-component",
                "bounds": [0, 0, 30, 30],
                "area": 100,
                "role_review": {
                    "proposed_role": "arc",
                    "accepted_role": "arc",
                    "confidence": "medium",
                    "review_status": "accepted",
                    "evidence": "reviewer matched the source component to the arc stage",
                },
            }]},
        }
        plan = build_plan(analysis, selection, catalog.get("ai-field"), project_name="Raster", source_name="mark.jpg")
        annotation = plan["foreground_plan"]["role_annotations"]["actor"]
        self.assertEqual(annotation["review_status"], "accepted")
        self.assertEqual(annotation["accepted_role"], "arc")

    def test_unconfirmed_raster_actors_use_static_canonical_runtime(self) -> None:
        """Unaccepted geometry keeps candidate evidence out of generic growth."""

        catalog = load_catalog()
        selection = catalog.route("AI logo animation")
        analysis = measure(EXAMPLE / "mark.svg")
        analysis["source"]["format"] = "jpeg"
        plan = build_plan(
            analysis,
            selection,
            catalog.get("ai-field"),
            project_name="Raster runtime",
            source_name="mark.jpg",
        )
        files = compile_runtime((EXAMPLE / "mark.svg").read_text(encoding="utf-8"), plan)
        html = files["motion.html"]
        self.assertIn('data-foreground-resolution="static-canonical"', html)
        self.assertIn('data-role-review-status="needs-review"', html)
        self.assertIn('data-foreground-review-open="true"', html)
        self.assertIn('data-motiflux-actor="spark"', html)
        self.assertIn('data-motiflux-actor="orbit"', html)
        self.assertIn('data-foreground-actor-stages="{}"', html)
        self.assertIn('data-motiflux-runtime', files["motion.js"])
        self.assertIn('"static-canonical"', files["motion.js"])

    def test_accepted_raster_roles_keep_dynamic_runtime(self) -> None:
        catalog = load_catalog()
        selection = catalog.route("AI logo animation")
        analysis = {
            "source": {"format": "jpeg"},
            "observations": {"elements": [{
                "id": "actor",
                "tag": "raster-component",
                "bounds": [0, 0, 30, 30],
                "area": 100,
                "role": "arc",
                "selected_role": "arc",
                "role_candidates": [{"role": "arc", "score": 0.9, "confidence": "medium"}],
                "role_review": {
                    "proposed_role": "arc",
                    "accepted_role": "arc",
                    "confidence": "high",
                    "review_status": "accepted",
                    "evidence": "reviewer matched the source component to the arc stage",
                },
            }]},
        }
        plan = build_plan(analysis, selection, catalog.get("ai-field"), project_name="Raster runtime", source_name="mark.jpg")
        files = compile_runtime('<svg><path id="actor"/></svg>', plan)
        html = files["motion.html"]
        self.assertIn('data-foreground-resolution="accepted-source-actors"', html)
        self.assertIn('data-role-review-status="accepted"', html)
        self.assertIn('data-foreground-actor-stages="{&quot;actor&quot;:1}"', html)
        self.assertIn('data-motiflux-runtime', files["motion.js"])
        self.assertIn('"actor-growth"', files["motion.js"])

    def test_raster_observer_writes_complete_role_review_records(self) -> None:
        result = analyze_raster(ROOT / "showcase" / "assets" / "prysai-logo-white.jpg")
        components = result["observations"]["raster"]["components"]
        self.assertTrue(components)
        for component in components:
            review = component["role_review"]
            self.assertEqual(review["accepted_role"], None)
            self.assertEqual(review["review_status"], "needs-review")
            self.assertIn("proposed_role", review)
            self.assertTrue(review["evidence"])

    def test_single_symbol_does_not_invent_origin_dot_hint(self) -> None:
        catalog = load_catalog()
        selection = catalog.route("AI logo animation")
        analysis = {
            "source": {"format": "jpeg"},
            "observations": {"elements": [{
                "id": "symbol",
                "tag": "raster-component",
                "layout_group": "symbol",
                "bounds": [0, 0, 100, 100],
                "area": 10000,
                "role_candidates": [{"role": "monogram", "score": 0.4, "confidence": "low"}],
            }]},
        }
        plan = build_plan(analysis, selection, catalog.get("ai-field"), project_name="Raster", source_name="mark.jpg")
        self.assertNotEqual(plan["foreground_plan"]["role_annotations"]["symbol"]["role"], "origin-dot")

    def test_surface_and_unresolved_preferences_are_preserved(self) -> None:
        catalog = load_catalog()
        analysis = measure(EXAMPLE / "mark.svg")
        request = "AI showcase logo animation, full motion, high contrast, glow, keyboard focus, export MP4"
        selection = catalog.route(request)
        plan = build_plan(analysis, selection, catalog.get("ai-field"), project_name="Showcase", source_name="mark.svg", request=request)
        self.assertEqual(plan["project"]["surface"], "showcase")
        self.assertEqual(plan["runtime"]["reduced_motion"], "user-choice")
        constraint_ids = {item["id"] for item in plan["constraints"]}
        self.assertTrue({"glow-policy", "contrast-policy", "keyboard-proof", "video-export"}.issubset(constraint_ids))
        self.assertTrue(all(item["status"] == "recorded-unresolved" for item in plan["constraints"] if item["id"] in constraint_ids - {"identity-source", "canonical-end-state"}))

    def test_raster_group_hints_stage_pixels_without_claiming_vector_geometry(self) -> None:
        catalog = load_catalog()
        selection = catalog.route("AI logo animation")
        analysis = {
            "source": {"format": "jpeg"},
            "observations": {
                "elements": [
                    {
                        "id": "dot",
                        "tag": "raster-component",
                        "layout_group": "symbol",
                        "bounds": [0, 0, 4, 4],
                        "area": 16,
                        "role_candidates": [{"role": "origin-dot", "score": 0.9, "confidence": "medium"}],
                    },
                    {
                        "id": "arc",
                        "tag": "raster-component",
                        "layout_group": "symbol",
                        "bounds": [10, 0, 30, 30],
                        "area": 220,
                        "role_candidates": [
                            {"role": "arc", "score": 0.8, "confidence": "medium"},
                            {"role": "monogram", "score": 0.3, "confidence": "low"},
                        ],
                    },
                    {
                        "id": "monogram",
                        "tag": "raster-component",
                        "layout_group": "symbol",
                        "bounds": [45, 0, 20, 30],
                        "area": 180,
                        "role_candidates": [
                            {"role": "monogram", "score": 0.8, "confidence": "medium"},
                            {"role": "arc", "score": 0.2, "confidence": "low"},
                        ],
                    },
                    {
                        "id": "wordmark-a",
                        "tag": "raster-component",
                        "layout_group": "wordmark",
                        "bounds": [80, 0, 12, 30],
                        "area": 100,
                        "role_candidates": [{"role": "origin-dot", "score": 0.95, "confidence": "medium"}],
                    },
                ]
            },
        }
        plan = build_plan(
            analysis,
            selection,
            catalog.get("ai-field"),
            project_name="Raster test",
            source_name="mark.jpg",
        )
        annotations = plan["foreground_plan"]["role_annotations"]
        self.assertTrue(all(item["role"] == "unknown" for item in annotations.values()))
        self.assertTrue(all(item["selected_role"] == "unknown" for item in annotations.values()))
        self.assertTrue(all(item["accepted_role"] is None for item in annotations.values()))
        self.assertEqual(plan["actors"][0]["geometry_strategy"], "pixel-observation-only")
        self.assertTrue(all(item["review_status"] == "needs-review" for item in annotations.values()))

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

    def test_raster_pixel_observation_is_deterministic_and_not_vector_claim(self) -> None:
        pixels = []
        for y in range(12):
            for x in range(20):
                visible = (x - 4) ** 2 + (y - 6) ** 2 <= 4 or (8 <= x < 17 and 5 <= y <= 6)
                pixels.append((255, 255, 255, 255) if visible else (0, 0, 0, 255))
        first = analyze_pixels(pixels, 20, 12)
        second = analyze_pixels(pixels, 20, 12)
        self.assertEqual(first["foreground_mask"], second["foreground_mask"])
        self.assertGreaterEqual(first["topology"]["component_count"], 1)
        self.assertTrue(all("bounds" in item and "centroid" in item for item in first["components"]))

    def test_raster_measurement_uses_pixel_adapter_when_available(self) -> None:
        result = measure(ROOT / "showcase" / "assets" / "prysai-logo-white.jpg")
        self.assertEqual(result["status"], "candidate")
        if "raster-pixels" in result["capabilities"]:
            self.assertIn("raster", result["observations"])
            self.assertEqual(result["review"]["vector_reconstruction"], "not-claimed")
            self.assertGreater(len(result["observations"]["elements"]), 0)

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
        self.assertEqual(html.count('class="motion-canonical"'), 13)
        self.assertEqual(html.count('class="motion-freeze"'), 13)
        self.assertNotIn('class="motion-freeze" hidden src="" alt="Paused frame of the logo growth animation" aria-hidden="true"', html)
        self.assertIn("requestAnimationFrame", runtime)
        self.assertIn("showCanonical", runtime)
        self.assertIn("showReadyGif", runtime)
        self.assertIn("loadToken", runtime)
        self.assertIn('addEventListener("load"', runtime)
        self.assertIn("finalHoldMs", runtime)
        self.assertIn("showLoading", runtime)
        self.assertIn("motionOverride", runtime)
        self.assertIn("systemPrefersReduced", runtime)
        self.assertIn("data-motion-beat", html)
        self.assertIn("data-route-animation", html)
        self.assertIn("data-gif-src", html)
        self.assertIn('data-param="reduced-motion"', html)
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

    def test_showcase_player_clock_matches_encoded_gif_duration(self) -> None:
        snapshot = json.loads((ROOT / "showcase" / "themes.json").read_text(encoding="utf-8"))
        animation_dir = ROOT / "showcase" / "assets" / "animations"
        for theme in snapshot["themes"]:
            with Image.open(animation_dir / f"prysai-{theme['id']}.gif") as gif:
                encoded_duration = sum(
                    int(frame.info.get("duration", 0))
                    for frame in ImageSequence.Iterator(gif)
                )
            self.assertEqual(encoded_duration, theme["playback_duration_ms"], theme["id"])

    def test_showcase_growth_evidence_has_all_stage_frames_and_hashes(self) -> None:
        evidence_path = ROOT / "showcase" / "output" / "growth-evidence.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertIn(evidence["frame_count"], {None, 35, 36, 37, 38, 39})
        self.assertEqual(evidence["canonical_handoff_progress"], 1.0)
        self.assertEqual(evidence["export_options"]["speed"], 1.0)
        self.assertTrue(evidence["export_options"]["particles"])
        self.assertEqual(evidence["stage_order"], ["blank", "spark", "arc", "bar", "monogram", "wordmark", "canonical"])
        self.assertEqual(len(evidence["themes"]), 13)
        animation_dir = ROOT / "showcase" / "assets" / "animations"
        for theme in evidence["themes"]:
            with self.subTest(theme=theme["id"]):
                self.assertEqual(len(theme["sha256"]), 64)
                with Image.open(animation_dir / Path(theme["gif"]).name) as gif:
                    frames = []
                    durations = []
                    for frame_index in range(gif.n_frames):
                        gif.seek(frame_index)
                        durations.append(int(gif.info.get("duration", 0)))
                        frames.append(gif.convert("RGB").copy())
                self.assertEqual(theme["encoded_frame_count"], len(frames))
                self.assertEqual(theme["canonical_frame"], len(frames) - 1)
                self.assertEqual(theme["encoded_duration_ms"], sum(durations))
                self.assertEqual(theme["sha256"], hashlib.sha256((animation_dir / Path(theme["gif"]).name).read_bytes()).hexdigest())
                self.assertEqual(theme["canonical_frame_sha256"], hashlib.sha256(frames[-1].tobytes()).hexdigest())
                self.assertEqual(list(theme["stages"]), evidence["stage_order"])
                self.assertEqual(theme["stages"]["blank"]["frame_index"], 0)
                self.assertEqual(theme["stages"]["canonical"]["frame_index"], len(frames) - 1)

    def test_canonical_final_frame_fingerprint_matches_the_supplied_mark(self) -> None:
        snapshot = json.loads((ROOT / "showcase" / "themes.json").read_text(encoding="utf-8"))
        canonical_source = Image.open(ROOT / "showcase" / "assets" / "prysai-mark-transparent.png").convert("RGBA")
        animation_dir = ROOT / "showcase" / "assets" / "animations"
        expected_size = (900, 302)
        for theme in snapshot["themes"]:
            with self.subTest(theme=theme["id"]):
                background = tuple(int(theme["background"][index:index + 2], 16) for index in (1, 3, 5))
                expected = Image.new("RGBA", expected_size, (*background, 255))
                mark = canonical_source.copy()
                mark.thumbnail((int(expected_size[0] * .68), int(expected_size[1] * .76)), Image.Resampling.LANCZOS)
                expected.alpha_composite(mark, ((expected_size[0] - mark.width) // 2, (expected_size[1] - mark.height) // 2))
                expected_fingerprint = hashlib.sha256(expected.convert("RGB").tobytes()).hexdigest()

                with Image.open(animation_dir / f"prysai-{theme['id']}.gif") as gif:
                    gif.seek(gif.n_frames - 1)
                    actual_fingerprint = hashlib.sha256(gif.convert("RGB").tobytes()).hexdigest()
                self.assertEqual(actual_fingerprint, expected_fingerprint)

    def test_showcase_source_review_fields_remain_candidate(self) -> None:
        analysis = json.loads((ROOT / "showcase" / "output" / "source-analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(analysis["observation_review"]["status"], "needs-review")
        components = analysis["observations"]["raster"]["components"]
        self.assertTrue(components)
        for component in components:
            review = component["role_review"]
            self.assertIn(review["proposed_role"], {"origin-dot", "arc", "bar", "monogram", "wordmark", "unknown"})
            self.assertIsNone(review["accepted_role"])
            self.assertEqual(review["review_status"], "needs-review")

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
