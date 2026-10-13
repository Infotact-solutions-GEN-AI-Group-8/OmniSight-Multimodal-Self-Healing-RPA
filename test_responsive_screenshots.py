
import tempfile
import unittest
from pathlib import Path

from responsive_screenshots import (
    _validate_screenshot,
    capture_responsive_screenshots,
)


class ResponsiveScreenshotTests(unittest.TestCase):

    def test_invalid_or_missing_png(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.png"
            self.assertIsNotNone(_validate_screenshot(path))

            path.write_bytes(b"")
            self.assertIsNotNone(_validate_screenshot(path))

            path.write_bytes(b"not a png file")
            self.assertIsNotNone(_validate_screenshot(path))

    def test_importable_function(self):
        self.assertTrue(callable(capture_responsive_screenshots))


if __name__ == "__main__":
    unittest.main()