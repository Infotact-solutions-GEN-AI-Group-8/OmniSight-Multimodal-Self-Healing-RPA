"""VLM-based visual defect analysis for OmniSight."""

import base64
import json
import logging
import os
from pathlib import Path

from openai import OpenAI

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
Do not invent CSS selectors.
If an exact selector is unknown, return null.

Return a JSON object with these fields:
{
  "status": "completed",
  "defect_detected": true,
  "summary": "Short explanation",
  "viewport": "mobile",
  "screenshot": null,
  "issues": [
    {
      "type": "horizontal_overflow",
      "severity": "high",
      "element": null,
      "description": "Description of the visible issue",
      "confidence": 0.9,
      "suggested_fix": {
        "selector": null,
        "css": {
          "max-width": "100%"
        },
        "rationale": "Why the change might help"
      }
    }
  ],
  "limitations": []
}

Each issue must include all required fields.
If no clear defect is visible, return defect_detected=false
and an empty issues array.
Do not return executable code.
"""


def analyze_screenshot(
    screenshot_path: str,
    viewport: str | None = None,
) -> VisionAnalysis:
    """Analyze a screenshot and return a validated defect report."""

    path = Path(screenshot_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Screenshot not found: {path}"
        )

    if path.suffix.lower() not in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }:
        raise ValueError("Unsupported screenshot format.")

    if path.stat().st_size == 0:
        raise ValueError("Screenshot file is empty.")

    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Screenshot exceeds the 10 MB limit.")

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is missing."
        )

    client = OpenAI(api_key=api_key)

    image_bytes = path.read_bytes()
    encoded_image = base64.b64encode(
        image_bytes
    ).decode("ascii")

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    mime_type = mime_types[path.suffix.lower()]

    model = os.getenv(
        "OMNISIGHT_VLM_MODEL",
        "gpt-4o-mini",
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this screenshot for UI defects. "
                                f"Viewport: {viewport or 'unknown'}."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:{mime_type};base64,"
                                    f"{encoded_image}"
                                )
                            },
                        },
                    ],
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("VLM returned an empty response.")

        result = json.loads(content)

        # Store trusted application metadata rather than relying
        # on the model to supply the screenshot path.
        result["screenshot"] = str(path)
        result["viewport"] = viewport

        return VisionAnalysis.model_validate(result)

    except Exception:
        logger.exception(
            "VLM screenshot analysis failed: %s",
            path,
        )
        raise
