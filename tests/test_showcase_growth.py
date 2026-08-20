"""Contract tests for source-derived, stage-based logo growth."""

from __future__ import annotations

import sys
import unittest
from collections.abc import Mapping
import json
import re
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills" / "motiflux" / "tools"))

import showcase.generate_showcase as showcase  # noqa: E402
from validate_artifact import validate  # noqa: E402


PRE_WORDMARK_STAGES = ("blank", "spark", "arc", "bar", "monogram")
VISIBLE_THRESHOLD = 32


def _visible(mask: Image.Image) -> int:
    return sum(mask.histogram()[VISIBLE_THRESHOLD:])


def _mask(value: object, label: str) -> Image.Image:
    if not isinstance(value, Image.Image):
        raise TypeError(f"{label} must be a PIL image, got {type(value).__name__}")
    if value.mode == "L":
        return value
    if "A" in value.getbands():
        return value.getchannel("A")
    return value.convert("L")


def _union(values: list[object], label: str) -> Image.Image:
    masks = [_mask(value, f"{label}[{index}]") for index, value in enumerate(values)]
    if not masks:
        raise AssertionError(f"{label} must contain at least one mask")
    result = Image.new("L", masks[0].size, 0)
    for current in masks:
        result = ImageChops.lighter(result, current)
    return result


def _coverage(actual: Image.Image, expected: Image.Image) -> float:
    overlap = _visible(ImageChops.multiply(actual, expected))
    return overlap / max(1, _visible(expected))


class _GrowthFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source_path = Path(showcase.MARK_PNG)
        if not source_path.is_file():
            raise unittest.SkipTest(f"missing source-derived mark: {source_path}")
        with Image.open(source_path) as source:
            cls.mark = source.convert("RGBA")

        builder = getattr(showcase, "build_growth_components", None)
        if builder is None:
            builder = getattr(showcase, "_build_growth_components", None)
        if builder is None:
            raise unittest.SkipTest("pending seam: expose build_growth_components(mark, size)")
        cls.components = builder(cls.mark, showcase.ANIMATION_SIZE)
        if not isinstance(cls.components, Mapping):
            raise TypeError("growth component builder must return a mapping")

        cls.themes = tuple(showcase.load_data()["themes"])

    def _component(self, *names: str) -> Image.Image:
        for name in names:
            if name in self.components:
                return _mask(self.components[name], name)
        self.fail(f"growth components must expose one of: {', '.join(names)}")

    def _wordmark(self) -> Image.Image:
        value = self.components.get("wordmark")
        if not isinstance(value, (list, tuple)):
            self.fail("growth components['wordmark'] must be a sequence of masks")
        return _union(list(value), "wordmark")

    def _render_stage(self, theme: Mapping[str, object], stage: str, progress: float = 1.0) -> Image.Image:
        renderer = getattr(showcase, "render_growth_stage", None)
        if renderer is None:
            self.skipTest("pending seam: expose render_growth_stage(components, theme, stage, progress)")
        result = renderer(components=self.components, theme=theme, stage=stage, progress=progress)
        return _mask(result, f"rendered {theme['id']}:{stage}")


class GrowthComponentContractTests(_GrowthFixture):
    def test_component_builder_exposes_source_derived_stage_masks(self) -> None:
        for name in ("origin_dot", "arc", "bar", "bar_stroke", "monogram"):
            with self.subTest(component=name):
                component = self._component(name)
                self.assertEqual(component.size, showcase.ANIMATION_SIZE)
                self.assertGreater(_visible(component), 0)

        wordmark = self._wordmark()
        canonical = self._component("canonical", "final")
        self.assertEqual(wordmark.size, showcase.ANIMATION_SIZE)
        self.assertGreater(_visible(wordmark), 0)
        self.assertEqual(canonical.size, showcase.ANIMATION_SIZE)
        self.assertGreater(_visible(canonical), 0)


class GrowthStageContractTests(_GrowthFixture):
    def test_theme_foreground_contracts_are_distinct(self) -> None:
        modes = [str(theme["foreground_mode"]) for theme in self.themes]
        self.assertEqual(len(modes), 13)
        self.assertEqual(len(set(modes)), 13, "each theme needs a distinct foreground construction mode")
        for theme in self.themes:
            self.assertEqual(sorted(theme["foreground_order"]), list(range(6)), theme["id"])
            self.assertEqual(theme["foreground_order"], list(range(6)), "wordmark spelling must stay readable")

    def test_temporary_bar_stroke_is_continuous_and_not_canonical(self) -> None:
        stroke = self._component("bar_stroke")
        bar = self._component("bar")
        canonical = self._component("canonical", "final")
        bbox = stroke.getbbox()
        self.assertIsNotNone(bbox)
        assert bbox is not None
        self.assertGreaterEqual(bbox[2] - bbox[0], (bbox[3] - bbox[1]) * 3)
        self.assertGreater(_visible(stroke), _visible(bar) * .75)
        self.assertNotEqual(stroke.tobytes(), canonical.tobytes(), "construction stroke must never replace the canonical source")

    def test_pre_wordmark_stages_have_no_visible_wordmark(self) -> None:
        wordmark = self._wordmark()
        for theme in self.themes:
            for stage in PRE_WORDMARK_STAGES:
                with self.subTest(theme=theme["id"], stage=stage):
                    actual = self._render_stage(theme, stage)
                    self.assertEqual(_visible(ImageChops.multiply(actual, wordmark)), 0, "wordmark pixels leaked into an early construction stage")

    def test_arc_stage_contains_the_source_derived_arc(self) -> None:
        arc = self._component("arc")
        monogram = self._component("monogram")
        for theme in self.themes:
            with self.subTest(theme=theme["id"]):
                actual = self._render_stage(theme, "arc")
                self.assertGreaterEqual(_coverage(actual, arc), 0.80, "arc stage must visibly contain the arc component")
                self.assertLess(_visible(actual), _visible(monogram) * 0.95, "arc stage must not already be the complete monogram")

    def test_bar_stage_contains_a_horizontal_bar(self) -> None:
        bar = self._component("bar")
        monogram = self._component("monogram")
        for theme in self.themes:
            with self.subTest(theme=theme["id"]):
                actual = self._render_stage(theme, "bar")
                self.assertGreaterEqual(_coverage(actual, bar), 0.80, "bar stage must visibly contain the bar component")
                bar_overlap = ImageChops.multiply(actual, bar)
                bbox = bar_overlap.getbbox()
                self.assertIsNotNone(bbox, "bar stage has no visible horizontal stroke")
                assert bbox is not None
                self.assertGreaterEqual(bbox[2] - bbox[0], (bbox[3] - bbox[1]) * 3, "bar stage must preserve a horizontal, not point-like, stroke")
                self.assertLess(_visible(actual), _visible(monogram) * 0.99, "bar stage must not already be the complete monogram")

    def test_canonical_stage_is_pixel_exact(self) -> None:
        canonical = self._component("canonical", "final")
        for theme in self.themes:
            with self.subTest(theme=theme["id"]):
                actual = self._render_stage(theme, "canonical")
                self.assertEqual(actual.size, canonical.size)
                self.assertEqual(actual.tobytes(), canonical.tobytes(), "canonical stage must equal the source-derived canonical mask byte-for-byte")

    def test_theme_midframes_are_not_background_only_variants(self) -> None:
        midframes = [
            self._render_stage(theme, "wordmark", progress=.72).tobytes()
            for theme in self.themes
        ]
        self.assertEqual(len(midframes), 13)
        self.assertEqual(len(set(midframes)), 13, "theme routing must change the source-derived foreground midframe")

    def test_progress_samples_are_partial_source_constructions(self) -> None:
        renderer = getattr(showcase, "render_growth_progress", None)
        if renderer is None:
            self.skipTest("pending seam: expose render_growth_progress(components, theme, progress)")
        canonical = self._component("canonical", "final")
        for theme in self.themes:
            for progress in (.28, .76):
                with self.subTest(theme=theme["id"], progress=progress):
                    actual = _mask(renderer(self.components, theme, progress), f"{theme['id']}@{progress}")
                    self.assertGreater(_visible(actual), 0, "a progress sample must expose source-derived foreground pixels")
                    self.assertNotEqual(actual.tobytes(), canonical.tobytes(), "an intermediate sample must not be the canonical source mask")

    def test_wordmark_midframe_contains_measured_letters_without_complete_lockup(self) -> None:
        renderer = getattr(showcase, "render_growth_progress", None)
        if renderer is None:
            self.skipTest("pending seam: expose render_growth_progress(components, theme, progress)")
        wordmark = self._wordmark()
        for theme in self.themes:
            actual = _mask(renderer(self.components, theme, .76), f"{theme['id']} wordmark midframe")
            coverage = _coverage(actual, wordmark)
            with self.subTest(theme=theme["id"]):
                self.assertGreater(coverage, .05, "wordmark midframe must expose measured letter pixels")
                self.assertLess(coverage, .95, "wordmark midframe must still be a draw-on, not a complete lockup")


class RasterObservationGrowthTests(unittest.TestCase):
    def test_generated_source_analysis_is_schema_valid(self) -> None:
        artifact = ROOT / "showcase" / "output" / "source-analysis.json"
        self.assertTrue(artifact.is_file(), artifact)
        report = validate("source-analysis", artifact)
        self.assertTrue(report["valid"], report["errors"])

    def test_source_observation_drives_component_boxes(self) -> None:
        observation = showcase.detect_source_structure(showcase.CROP_JPG)
        self.assertIn(observation["status"], {"candidate", "fallback"})
        self.assertIn("boxes", observation)
        self.assertIn("actor_groups", observation)
        if observation["status"] == "candidate":
            self.assertIn("monogram_raw", observation["boxes"])
            self.assertIn("stage_mapping", observation)
            self.assertEqual(len(observation["stage_mapping"]["wordmark"]), 6)
            self.assertEqual(observation["review_status"], "needs-review")

    def test_monogram_stage_contains_observed_symbol_without_changing_canonical(self) -> None:
        observation = showcase.detect_source_structure(showcase.CROP_JPG)
        with Image.open(showcase.MARK_PNG) as source:
            mark = source.convert("RGBA")
        components = showcase.build_growth_components(mark, showcase.ANIMATION_SIZE, observation)
        theme = showcase.load_data()["themes"][3]
        monogram = showcase.render_growth_stage(components, theme, "monogram")
        symbol = components["monogram"]
        self.assertIsNotNone(symbol.getbbox())
        self.assertIsNone(ImageChops.subtract(symbol, monogram).getbbox())
        if components["p_component"].getbbox() is not None:
            self.assertIsNone(ImageChops.subtract(components["p_component"], monogram).getbbox())
        self.assertEqual(showcase.render_growth_stage(components, theme, "canonical"), components["final"])

    def test_fallback_derives_a_source_pixel_p_actor(self) -> None:
        with Image.open(showcase.MARK_PNG) as source:
            mark = source.convert("RGBA")
        components = showcase.build_growth_components(mark, showcase.ANIMATION_SIZE, {"status": "fallback"})
        self.assertIsNotNone(components["p_component"].getbbox())
        self.assertIsNone(ImageChops.subtract(components["p_component"], components["monogram"]).getbbox())
        self.assertIsNotNone(components["wordmark"][0].getbbox())


class GrowthEvidenceTrajectoryTests(unittest.TestCase):
    PROGRESS_POINTS = (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)
    HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")

    @classmethod
    def setUpClass(cls) -> None:
        artifact = ROOT / "showcase" / "output" / "growth-evidence.json"
        if not artifact.is_file():
            raise unittest.SkipTest(f"missing growth evidence: {artifact}")
        cls.evidence = json.loads(artifact.read_text(encoding="utf-8"))

    def test_progress_points_persist_foreground_trajectory_metrics(self) -> None:
        self.assertEqual(len(self.evidence["themes"]), 13)
        for theme in self.evidence["themes"]:
            with self.subTest(theme=theme["id"]):
                points = theme["progress_points"]
                self.assertEqual([point["progress"] for point in points], list(self.PROGRESS_POINTS))
                self.assertEqual(theme["canonical_frame"], theme["encoded_frame_count"] - 1)
                for point in points:
                    self.assertRegex(point["foreground_mask_sha256"], self.HASH_PATTERN)
                    self.assertRegex(point["trajectory_fingerprint"], self.HASH_PATTERN)
                    self.assertIsInstance(point["alpha_mass"], int)
                    self.assertGreaterEqual(point["alpha_mass"], 0)
                    self.assertIsInstance(point["unique_count"], int)
                    self.assertGreaterEqual(point["unique_count"], 0)
                    if point["unique_count"]:
                        self.assertIsInstance(point["bbox"], dict)
                        self.assertEqual(set(point["bbox"]), {"x", "y", "width", "height"})
                        self.assertIsInstance(point["centroid"], dict)
                        self.assertEqual(set(point["centroid"]), {"x", "y"})
                    else:
                        self.assertIsNone(point["bbox"])
                        self.assertIsNone(point["centroid"])

                final_point = points[-1]
                self.assertEqual(final_point["frame_index"], theme["canonical_frame"])
                self.assertEqual(final_point["progress"], 1.0)

    def test_cross_theme_trajectory_comparison_is_persisted(self) -> None:
        comparison = self.evidence.get("trajectory_comparison")
        self.assertIsInstance(comparison, dict)
        points = comparison.get("progress_points")
        self.assertEqual([point["progress"] for point in points], list(self.PROGRESS_POINTS))
        self.assertEqual([point["theme_count"] for point in points], [13] * len(self.PROGRESS_POINTS))
        self.assertEqual(points[-1]["unique_foreground_mask_count"], 1)
        self.assertGreater(points[1]["unique_foreground_mask_count"], 1)
        self.assertEqual(points[-1]["unique_trajectory_fingerprint_count"], 13)
        self.assertIn("canonical mask is intentionally shared", comparison["canonical_note"])

    def test_mid_progress_keeps_thirteen_distinct_foreground_routes(self) -> None:
        comparison = self.evidence["trajectory_comparison"]["progress_points"]
        mid = next(point for point in comparison if point["progress"] == 0.75)
        self.assertEqual(mid["theme_count"], 13)
        self.assertEqual(mid["unique_foreground_mask_count"], 13)
        self.assertEqual(mid["unique_trajectory_fingerprint_count"], 13)


if __name__ == "__main__":
    unittest.main()
