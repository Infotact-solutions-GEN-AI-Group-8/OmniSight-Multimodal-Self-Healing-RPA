
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from vision.analyzer import compare_screenshots


class AnalyzerTests(unittest.TestCase):

    def test_identical_screenshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "first.png"
            second = Path(temp_dir) / "second.png"

            Image.new("RGB", (100, 100), "white").save(first)
            Image.new("RGB", (100, 100), "white").save(second)

            result = compare_screenshots(first, second)

            self.assertTrue(result["comparable"])
            self.assertEqual(result["changed_pixel_ratio"], 0.0)

    def test_different_screenshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "first.png"
            second = Path(temp_dir) / "second.png"

            Image.new("RGB", (100, 100), "white").save(first)
            Image.new("RGB", (100, 100), "black").save(second)

            result = compare_screenshots(first, second)

            self.assertTrue(result["comparable"])
            self.assertGreater(result["changed_pixel_ratio"], 0.0)

    def test_missing_screenshot(self):
        result = compare_screenshots(
            "missing_first.png",
            "missing_second.png",
        )

        self.assertFalse(result["comparable"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()