
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from responsive_screenshots import (
    _validate_screenshot,
    capture_responsive_screenshots,
)


def make_test_png(path, width=100, height=80):
    """Create a minimal PNG header for validation tests."""
    header = (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
    )
    path.write_bytes(header)


class ResponsiveScreenshotTests(unittest.TestCase):

    def test_invalid_or_missing_png(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.png"

            self.assertIsNotNone(_validate_screenshot(path))

            path.write_bytes(b"")
            self.assertIsNotNone(_validate_screenshot(path))

            path.write_bytes(b"not a png file")
            self.assertIsNotNone(_validate_screenshot(path))

    def test_valid_png(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "valid.png"
            make_test_png(path, 100, 80)

            self.assertIsNone(_validate_screenshot(path))
            self.assertIsNone(
                _validate_screenshot(path, expected_size=(100, 80))
            )

    def test_dimensions_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "dimensions.png"
            make_test_png(path, 100, 80)

            error = _validate_screenshot(path, expected_size=(1440, 900))

            self.assertIsNotNone(error)
            self.assertIn("Dimensions mismatch", error)

    def test_capture_failure_returns_structured_results(self):
        with patch(
            "responsive_screenshots.sync_playwright"
        ) as mock_playwright:
            mock_playwright.return_value.__enter__.side_effect = RuntimeError(
                "Simulated browser startup failure"
            )

            results = capture_responsive_screenshots()

        self.assertIsInstance(results, dict)
        self.assertIn("screenshots", results)
        self.assertIn("errors", results)
        self.assertEqual(results["screenshots"], [])
        self.assertTrue(results["errors"])
        self.assertIn("Browser startup", results["errors"][0])

    def test_empty_devices_returns_structured_results(self):
        results = capture_responsive_screenshots(devices={})

        self.assertEqual(
            results,
            {"screenshots": [], "errors": []},
        )

    def test_importable_function(self):
        self.assertTrue(callable(capture_responsive_screenshots))


if __name__ == "__main__":
    unittest.main()
