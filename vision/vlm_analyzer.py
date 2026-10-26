"""Gemini-based visual defect analysis for OmniSight."""

import json
import logging
import os
from pathlib import Path

from google import genai
from google.genai import types

from vision.schemas import VisionAnalysis

logger = logging.getLogger("omnisight.vision")

SYSTEM_PROMPT = """
You are OmniSight, an AI visual quality assurance engineer.

Analyze the supplied web UI screenshot and identify visible defects.

Look for:
- Elements extending beyond the viewport.
- Overlapping text or buttons.
- Clipped content.
- Broken alignment.
- Unreadable or low-contrast text.
- Unexpected spacing or layout problems.

Only report defects supported by visible screenshot evidence.
Do not claim to have inspected the DOM or source code.
Do not invent CSS selectors. If an exact selector is unknown, return null.

Return a JSON object with these fields:
{
  "status": "completed",
  "defect_detected": false,
  "summary": "Short explanation",
  "viewport": "desktop",
  "screenshot": null,
  "issues": [],
  "limitations": []
}

Each issue must contain:
- type
- severity
- element
- description
- confidence
- suggested_fix, containing selector, css, and rationale

If no clear defect is visible, return defect_detected=false
and an empty issues array.

Do not return executable code.
"""


def analyze_screenshot(
    screenshot_path: str,
    viewport: str | None = None,
) -> VisionAnalysis:
    """Analyze a screenshot with Gemini and validate the result."""

    path = Path(screenshot_path)

    if not path.is_file():
        raise FileNotFoundError(f"Screenshot not found: {path}")

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    extension = path.suffix.lower()

    if extension not in mime_types:
        raise ValueError("Unsupported screenshot format.")

    if path.stat().st_size == 0:
        raise ValueError("Screenshot file is empty.")

    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Screenshot exceeds the 10 MB limit.")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY or GOOGLE_API_KEY environment variable is missing."
        )

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)

    prompt = (
        SYSTEM_PROMPT
        + "\n\nAnalyze this screenshot for UI defects."
        + f"\nViewport: {viewport or 'unknown'}."
        + "\nReturn only a valid JSON object."
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=path.read_bytes(),
                    mime_type=mime_types[extension],
                ),
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        result = json.loads(response.text)

        # Use trusted application metadata for these fields.
        result["screenshot"] = str(path)
        result["viewport"] = viewport

        return VisionAnalysis.model_validate(result)

    except Exception:
        logger.exception("Gemini screenshot analysis failed: %s", path)
        raise

    finally:
        client.close()
