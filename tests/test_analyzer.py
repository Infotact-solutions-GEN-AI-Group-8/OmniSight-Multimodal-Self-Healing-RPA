
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from vision.analyzer import (
    check_horizontal_overflow,
    find_overflowing_elements,
    compare_screenshots,
)


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
        def test_dimensions_mismatch(self):
         with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "first.png"
            second = Path(temp_dir) / "second.png"

            Image.new("RGB", (100, 100), "white").save(first)
            Image.new("RGB", (80, 100), "white").save(second)

            result = compare_screenshots(first, second)

            self.assertFalse(result["comparable"])
            self.assertIn("error", result)

    def test_invalid_screenshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid = Path(temp_dir) / "invalid.png"
            invalid.write_text("not a valid image")

            result = compare_screenshots(invalid, invalid)

            self.assertFalse(result["comparable"])
            self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()

    class OverflowAnalyzerTests(unittest.TestCase):
        def test_horizontal_overflow_detection(self):
            class FakePage:
               def evaluate(self, script):
                return {
                    "viewport_width": 390,
                    "document_width": 450,
                    "has_horizontal_overflow": True,
                }

        result = check_horizontal_overflow(FakePage())

        self.assertTrue(result["has_horizontal_overflow"])
        self.assertGreater(
            result["document_width"],
            result["viewport_width"],
        )

    def test_no_horizontal_overflow(self):
        class FakePage:
            def evaluate(self, script):
                return {
                    "viewport_width": 390,
                    "document_width": 390,
                    "has_horizontal_overflow": False,
                }

        result = check_horizontal_overflow(FakePage())

        self.assertFalse(result["has_horizontal_overflow"])

    def test_overflowing_elements_detection(self):
        class FakePage:
            def evaluate(self, script):
                return [
                    {
                        "tag": "div",
                        "id": "wide-content",
                        "class_name": "wide",
                        "left": 0,
                        "right": 450,
                    }
                ]

        result = find_overflowing_elements(FakePage())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "wide-content")
        self.assertGreater(result[0]["right"], 390)
