"""Contract tests for source-derived, stage-based logo growth.

The intended pure seam is::

    render_growth_stage(
        components, theme, stage, progress
    ) -> PIL.Image.Image  # an ``L`` mask, no file or canvas side effects

The renderer exposes both seams. These tests stay foreground-only and do not
open or create GIF files, so they can catch stage regressions before export.
"""

from __future__ import annotations

import sys
import unittest
from collections.abc import Mapping
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import showcase.generate_showcase as showcase  # noqa: E402


PRE_WORDMARK_STAGES = ("blank", "spark", "arc", "bar", "monogram")
VISIBLE_THRESHOLD = 32


def _visible(mask: Image.Image) -> int:
    """Count pixels that would be visibly present in a stage mask."""

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
            raise unittest.SkipTest(
                "pending seam: expose build_growth_components(mark, size)"
            )
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

    def _render_stage(
        self,
        theme: Mapping[str, object],
        stage: str,
        progress: float = 1.0,
    ) -> Image.Image:
        renderer = getattr(showcase, "render_growth_stage", None)
        if renderer is None:
            self.skipTest(
                "pending seam: expose render_growth_stage(components, theme, stage, progress)"
            )
        result = renderer(
            components=self.components,
            theme=theme,
            stage=stage,
            progress=progress,
        )
        return _mask(result, f"rendered {theme['id']}:{stage}")


class GrowthComponentContractTests(_GrowthFixture):
    def test_component_builder_exposes_source_derived_stage_masks(self) -> None:
        for name in ("origin_dot", "arc", "bar", "monogram"):
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

    def test_pre_wordmark_stages_have_no_visible_wordmark(self) -> None:
        wordmark = self._wordmark()
        for theme in self.themes:
            for stage in PRE_WORDMARK_STAGES:
                with self.subTest(theme=theme["id"], stage=stage):
                    actual = self._render_stage(theme, stage)
                    self.assertEqual(
                        _visible(ImageChops.multiply(actual, wordmark)),
                        0,
                        "wordmark pixels leaked into an early construction stage",
                    )

    def test_arc_stage_contains_the_source_derived_arc(self) -> None:
        arc = self._component("arc")
        monogram = self._component("monogram")
        for theme in self.themes:
            with self.subTest(theme=theme["id"]):
                actual = self._render_stage(theme, "arc")
                self.assertGreaterEqual(
                    _coverage(actual, arc),
                    0.80,
                    "arc stage must visibly contain the arc component",
                )
                self.assertLess(
                    _visible(actual),
                    _visible(monogram) * 0.95,
                    "arc stage must not already be the complete monogram",
                )

    def test_bar_stage_contains_a_horizontal_bar(self) -> None:
        bar = self._component("bar")
        monogram = self._component("monogram")
        for theme in self.themes:
            with self.subTest(theme=theme["id"]):
                actual = self._render_stage(theme, "bar")
                self.assertGreaterEqual(
                    _coverage(actual, bar),
                    0.80,
                    "bar stage must visibly contain the bar component",
                )
                bar_overlap = ImageChops.multiply(actual, bar)
                bbox = bar_overlap.getbbox()
                self.assertIsNotNone(bbox, "bar stage has no visible horizontal stroke")
                assert bbox is not None
                self.assertGreaterEqual(
                    bbox[2] - bbox[0],
                    (bbox[3] - bbox[1]) * 3,
                    "bar stage must preserve a horizontal, not point-like, stroke",
                )
                self.assertLess(
                    _visible(actual),
                    _visible(monogram) * 0.99,
                    "bar stage must not already be the complete monogram",
                )

    def test_canonical_stage_is_pixel_exact(self) -> None:
        canonical = self._component("canonical", "final")
        for theme in self.themes:
            with self.subTest(theme=theme["id"]):
                actual = self._render_stage(theme, "canonical")
                self.assertEqual(actual.size, canonical.size)
                self.assertEqual(
                    actual.tobytes(),
                    canonical.tobytes(),
                    "canonical stage must equal the source-derived canonical mask byte-for-byte",
                )


if __name__ == "__main__":
    unittest.main()
