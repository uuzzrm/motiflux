"""Regression contracts for the checked-in Motiflux showcase surface."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
SHOWCASE = ROOT / "showcase"
ANIMATIONS = SHOWCASE / "assets" / "animations"
STAGES = ("blank", "spark", "arc", "bar", "monogram", "wordmark", "canonical")
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ShowcaseGeneratedSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (SHOWCASE / "index.html").read_text(encoding="utf-8")
        cls.runtime = (SHOWCASE / "app.js").read_text(encoding="utf-8")
        cls.snapshot = json.loads((SHOWCASE / "themes.json").read_text(encoding="utf-8"))

    def test_showcase_bakes_seekable_stage_checkpoint_contract(self) -> None:
        self.assertEqual(self.html.count("data-motion-seek"), 13)
        self.assertEqual(self.html.count("data-stage-files="), 13)
        self.assertEqual(self.runtime.count("showCheckpoint"), 2)
        self.assertGreaterEqual(self.runtime.count("seekPlayer"), 2)

        theme_ids = [str(theme["id"]) for theme in self.snapshot["themes"]]
        self.assertEqual(len(theme_ids), 13)
        for theme_id in theme_ids:
            with self.subTest(theme=theme_id):
                for stage in STAGES:
                    self.assertIn(f"prysai-{theme_id}-{stage}.png", self.html)

    def test_prompt_lab_exposes_main_route_poster_and_copyable_export_command(self) -> None:
        self.assertEqual(self.html.count("data-route-animation-poster"), 1)
        self.assertEqual(self.html.count("data-route-export-command"), 1)
        self.assertIn("routeAnimationPoster", self.runtime)
        self.assertIn("routeExportCommand", self.runtime)
        self.assertIn("routeCommand", self.runtime)
        self.assertIn("Copy export command", self.html)
        self.assertIn("browser controls never execute shell commands", self.html)

    def test_readme_feature_overview_is_a_playable_4x3_capability_map(self) -> None:
        manifest_path = SHOWCASE / "output" / "previews" / "motiflux-feature-overview.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["layout"], {"columns": 4, "rows": 3, "cards": 12})
        self.assertEqual(len(manifest["cards"]), 12)
        self.assertEqual(len({card["id"] for card in manifest["cards"]}), 12)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start = readme.index("<!-- FEATURE_OVERVIEW:START -->")
        end = readme.index("<!-- FEATURE_OVERVIEW:END -->")
        overview = readme[start:end]
        self.assertIn("## Capability overview", overview)
        self.assertIn("showcase/output/previews/motiflux-feature-overview.gif", overview)
        with Image.open(SHOWCASE / "output" / "previews" / "motiflux-feature-overview.gif") as gif:
            self.assertEqual(gif.size, (1280, 688))
            self.assertEqual(gif.n_frames, 24)
            first = gif.convert("RGB").tobytes()
            gif.seek(gif.n_frames - 1)
            self.assertNotEqual(first, gif.convert("RGB").tobytes())

    def test_showcase_exposes_ai_readable_workflow_and_status_ladder(self) -> None:
        for marker in ("workflow-guide", "data-guide-live", "data-guide-detail", "state-ladder", "PREVIEW", "BAKED", "VERIFIED"):
            self.assertIn(marker, self.html)
        for marker in ("guideCopy", "setGuide", 'setGuide("theme")', 'setGuide("tune")', 'setGuide("bake")'):
            self.assertIn(marker, self.runtime)


class ShowcaseCanonicalFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = Image.open(SHOWCASE / "assets" / "prysai-mark-transparent.png").convert("RGBA")
        cls.themes = json.loads((SHOWCASE / "themes.json").read_text(encoding="utf-8"))["themes"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.source.close()

    def _expected_canonical_frame(self, background: str) -> Image.Image:
        mark = self.source.copy()
        mark.thumbnail((round(900 * 0.68), round(302 * 0.76)), Image.Resampling.LANCZOS)
        color = tuple(int(background[index : index + 2], 16) for index in (1, 3, 5))
        frame = Image.new("RGBA", (900, 302), (*color, 255))
        position = ((900 - mark.width) // 2, (302 - mark.height) // 2)
        frame.alpha_composite(mark, position)
        return frame.convert("RGB")

    def test_every_theme_gif_ends_at_the_exact_source_canonical_frame(self) -> None:
        for theme in self.themes:
            theme_id = str(theme["id"])
            with self.subTest(theme=theme_id):
                gif_path = ANIMATIONS / f"prysai-{theme_id}.gif"
                with Image.open(gif_path) as gif:
                    gif.seek(gif.n_frames - 1)
                    actual = gif.convert("RGB").copy()
                expected = self._expected_canonical_frame(str(theme["background"]))
                self.assertEqual(actual.size, expected.size)
                self.assertIsNone(
                    ImageChops.difference(actual, expected).getbbox(),
                    "the final GIF frame must be byte-identical to the source-derived canonical composite",
                )
                self.assertEqual(
                    hashlib.sha256(actual.tobytes()).hexdigest(),
                    hashlib.sha256(expected.tobytes()).hexdigest(),
                )


class ShowcaseEncodedGrowthTests(unittest.TestCase):
    """Check the encoded GIFs, not only the pre-quantization renderer."""

    @classmethod
    def setUpClass(cls) -> None:
        import sys

        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        import showcase.generate_showcase as showcase

        cls.showcase = showcase
        with Image.open(SHOWCASE / "assets" / "prysai-mark-transparent.png") as source:
            cls.components = showcase.build_growth_components(source.convert("RGBA"), showcase.ANIMATION_SIZE)
        cls.themes = json.loads((SHOWCASE / "themes.json").read_text(encoding="utf-8"))["themes"]

    def test_first_frame_is_blank_and_only_final_frame_is_canonical(self) -> None:
        for theme in self.themes:
            path = ANIMATIONS / f"prysai-{theme['id']}.gif"
            with Image.open(path) as gif:
                frames = []
                for index in range(gif.n_frames):
                    gif.seek(index)
                    frames.append(gif.convert("RGB").copy())
            poster_path = ANIMATIONS / f"prysai-{theme['id']}-poster.png"
            with Image.open(poster_path) as poster:
                poster_frame = poster.convert("RGB").copy()
            identity = [self.showcase._encoded_identity_mask(frame, self.components["final"]) for frame in frames]
            with self.subTest(theme=theme["id"]):
                self.assertGreater(len(frames), 1)
                self.assertEqual(sum(identity[0].histogram()[1:]), 0)
                self.assertGreater(sum(identity[-1].histogram()[1:]), 0)
                self.assertEqual(frames[-1].tobytes(), poster_frame.tobytes())
                self.assertTrue(any(frame.tobytes() != frames[-1].tobytes() for frame in frames[:-1]))

    def test_encoded_stage_order_and_letter_order_are_preserved(self) -> None:
        stages = ("blank", "spark", "arc", "bar", "monogram", "wordmark", "canonical")
        letters = self.components["wordmark"]
        for theme in self.themes:
            path = ANIMATIONS / f"prysai-{theme['id']}.gif"
            frames, _ = self.showcase._read_encoded_gif(path)
            identity = [self.showcase._encoded_identity_mask(frame, self.components["final"]) for frame in frames]
            stage_progress = self.showcase._storyboard_progress(theme)
            stage_indices = [round(stage_progress[stage] * (len(frames) - 1)) for stage in stages]
            with self.subTest(theme=theme["id"]):
                self.assertEqual(stage_indices, sorted(stage_indices))
                self.assertEqual(stage_indices[-1], len(frames) - 1)
                self.assertEqual(sum(identity[stage_indices[0]].histogram()[1:]), 0)
                self.assertGreater(sum(identity[stage_indices[1]].histogram()[1:]), 0)
                self.assertGreater(sum(identity[stage_indices[2]].histogram()[1:]), sum(identity[stage_indices[1]].histogram()[1:]))
                first_seen = []
                for letter in letters:
                    first_seen.append(next((index for index, mask in enumerate(identity) if ImageChops.multiply(mask, letter).getbbox()), None))
                self.assertEqual(first_seen, sorted(first_seen))
                self.assertTrue(all(index is not None for index in first_seen))

    def test_theme_difference_survives_identity_only_measurement(self) -> None:
        midframes = []
        for theme in self.themes:
            path = ANIMATIONS / f"prysai-{theme['id']}.gif"
            frames, _ = self.showcase._read_encoded_gif(path)
            index = round(.75 * (len(frames) - 1))
            midframes.append(self.showcase._encoded_identity_mask(frames[index], self.components["final"]).tobytes())
        self.assertEqual(len(set(midframes)), len(self.themes))


if __name__ == "__main__":
    unittest.main()
