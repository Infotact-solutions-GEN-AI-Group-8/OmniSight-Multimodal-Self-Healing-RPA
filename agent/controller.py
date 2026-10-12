import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_agent():
    """
    Initial OmniSight agent controller.

    This stage verifies that the controller can locate
    the existing automation modules.
    """
    playwright_script = PROJECT_ROOT / "Playwright automation.py"
    screenshot_script = PROJECT_ROOT / "responsive_screenshots.py"

    result = {
        "success": False,
        "playwright_script": str(playwright_script),
        "screenshot_script": str(screenshot_script),
        "errors": [],
    }

    if not playwright_script.is_file():
        result["errors"].append("Playwright automation script not found.")

    if not screenshot_script.is_file():
        result["errors"].append("Responsive screenshot script not found.")

    if result["errors"]:
        logger.error("Agent initialization failed: %s", result["errors"])
        return result

    result["success"] = True
    result["message"] = "Agent initialized; automation modules located."

    logger.info("OmniSight agent initialized successfully.")
    return result
