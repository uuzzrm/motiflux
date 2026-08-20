"""Regression contracts for isolated single-route showcase exports."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import showcase.generate_showcase as showcase  # noqa: E402


class SingleThemeExportTests(unittest.TestCase):
    def test_public_single_theme_export_writes_manifest_and_stage_checkpoints(self) -> None:
        theme_id = "ai-field"
        data = showcase.load_data()
        source_structure = showcase.detect_source_structure(showcase.CROP_JPG)

        with tempfile.TemporaryDirectory(dir=ROOT, prefix=".single-export-test-") as temp_dir:
            temp_root = Path(temp_dir)
            export_root = temp_root / "output"
            with patch.object(showcase, "OUTPUT", export_root), patch.dict(
                showcase.EXPORT_OPTIONS,
                {"background": None, "duration_ms": None, "speed": 1.0, "particles": True, "guides": True},
                clear=True,
            ):
                manifest_path = showcase.build_single_theme_export(data, source_structure, theme_id)

            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "baked")
            self.assertEqual(manifest["evidence_status"], "candidate")
            self.assertEqual(manifest["theme"], theme_id)
            self.assertEqual(manifest["source_sha256"], hashlib.sha256(showcase.CROP_JPG.read_bytes()).hexdigest())
            # Pillow/GIF optimization may coalesce identical rendered samples;
            # the manifest must report the encoded count rather than the raw
            # renderer sample count.
            self.assertGreater(manifest["encoded_frame_count"], 1)
            self.assertLessEqual(manifest["encoded_frame_count"], showcase.ANIMATION_FRAME_COUNT)
            self.assertGreater(manifest["encoded_duration_ms"], 0)
            self.assertIn("human-raster-role-review", manifest["not_run"])

            theme = next(item for item in data["themes"] if item["id"] == theme_id)
            self.assertEqual(manifest["trajectory_id"], theme["trajectory_id"])
            self.assertEqual(manifest["foreground_variant"], theme["foreground_variant"])

            output_paths = manifest["outputs"]
            self.assertEqual(set(output_paths["stage_checkpoints"]), set(showcase.GROWTH_SEQUENCE))
            referenced_paths = [output_paths["gif"], output_paths["poster"], *output_paths["stage_checkpoints"].values()]
            for relative_path in referenced_paths:
                with self.subTest(path=relative_path):
                    # The manifest stores project-root-relative paths, using
                    # the same root as ``Path.relative_to(showcase.ROOT.parent)``.
                    resolved = ROOT / Path(relative_path)
                    self.assertTrue(resolved.is_file(), resolved)
                    self.assertTrue(resolved.is_relative_to(temp_root))

            gif_path = ROOT / Path(output_paths["gif"])
            poster_path = ROOT / Path(output_paths["poster"])
            with Image.open(gif_path) as gif:
                frames = []
                durations = []
                for index in range(gif.n_frames):
                    gif.seek(index)
                    frames.append(gif.convert("RGB").copy())
                    durations.append(int(gif.info.get("duration", 0)))
            self.assertEqual(len(frames), manifest["encoded_frame_count"])
            self.assertEqual(sum(durations), manifest["encoded_duration_ms"])
            self.assertEqual(
                hashlib.sha256(frames[-1].tobytes()).hexdigest(),
                manifest["canonical_frame_sha256"],
            )
            with Image.open(poster_path) as poster:
                self.assertEqual(poster.convert("RGB").tobytes(), frames[-1].tobytes())

    def test_showcase_cli_bakes_only_the_requested_theme_and_propagates_options(self) -> None:
        """The CLI must expose the same isolated route contract as the helper."""

        with tempfile.TemporaryDirectory(dir=ROOT, prefix=".single-cli-test-") as temp_dir:
            project = Path(temp_dir)
            shutil.copytree(
                ROOT / "showcase",
                project / "showcase",
                ignore=shutil.ignore_patterns("output", "__pycache__"),
            )
            shutil.copytree(ROOT / "skills" / "motiflux" / "catalog", project / "skills" / "motiflux" / "catalog")
            shutil.copy2(ROOT / "README.md", project / "README.md")

            result = subprocess.run(
                [
                    sys.executable,
                    str(project / "showcase" / "generate_showcase.py"),
                    "--theme",
                    "ai-field",
                    "--background",
                    "#0B0D12",
                    "--duration-ms",
                    "1600",
                    "--speed",
                    "1.25",
                    "--no-particles",
                    "--skip-pdf",
                ],
                cwd=project,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

            manifest_path = project / "showcase" / "output" / "exports" / "ai-field" / "export-manifest.json"
            self.assertTrue(manifest_path.is_file(), result.stdout)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "baked")
            self.assertEqual(manifest["theme"], "ai-field")
            self.assertRegex(manifest["canonical_frame_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(manifest["export_options"]["background"], "#0B0D12")
            self.assertEqual(manifest["export_options"]["duration_ms"], 1600)
            self.assertEqual(manifest["export_options"]["speed"], 1.25)
            self.assertFalse(manifest["export_options"]["particles"])

            outputs = manifest["outputs"]
            self.assertEqual(set(outputs["stage_checkpoints"]), set(showcase.GROWTH_SEQUENCE))
            relative_outputs = [
                outputs["gif"],
                outputs["poster"],
                *outputs["stage_checkpoints"].values(),
            ]
            for relative_path in relative_outputs:
                with self.subTest(path=relative_path):
                    resolved = project / Path(relative_path)
                    self.assertTrue(resolved.is_file(), resolved)
                    self.assertTrue(resolved.is_relative_to(project))

            gif_path = project / Path(outputs["gif"])
            poster_path = project / Path(outputs["poster"])
            with Image.open(gif_path) as gif:
                frames = []
                durations = []
                for index in range(gif.n_frames):
                    gif.seek(index)
                    frames.append(gif.convert("RGB").copy())
                    durations.append(int(gif.info.get("duration", 0)))
            self.assertGreater(len(frames), 1)
            self.assertEqual(len(frames), manifest["encoded_frame_count"])
            self.assertEqual(sum(durations), manifest["encoded_duration_ms"])
            self.assertEqual(
                hashlib.sha256(frames[-1].tobytes()).hexdigest(),
                manifest["canonical_frame_sha256"],
            )
            with Image.open(poster_path) as poster:
                self.assertEqual(poster.convert("RGB").tobytes(), frames[-1].tobytes())
            self.assertFalse((project / "showcase" / "output" / "exports" / "system-spatial").exists())


if __name__ == "__main__":
    unittest.main()
