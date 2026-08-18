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


if __name__ == "__main__":
    unittest.main()
