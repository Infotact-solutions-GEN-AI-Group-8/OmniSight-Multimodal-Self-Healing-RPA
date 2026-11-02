"""Controlled CSS Repair Engine for OmniSight."""

import logging
import re
from pathlib import Path
from typing import Any

from agent.action_engine import ALLOWED_CSS_PROPERTIES
from playwright.sync_api import Page


logger = logging.getLogger("omnisight.repair")


SELECTOR_PATTERN = re.compile(
    r"^[a-zA-Z0-9_*#.-]+(?:\s+[a-zA-Z0-9_*#.-]+)*$"
)

CSS_VALUE_PATTERN = re.compile(
    r"^[a-zA-Z0-9#.,()%\s-]+$"
)


def validate_repair_proposal(
    proposal: dict[str, Any],
) -> tuple[bool, str]:
    """Validate a CSS proposal before applying it."""

    if proposal.get("status") != "pending_validation":
        return False, "Proposal is not pending validation."

    selector = proposal.get("target")

    if not isinstance(selector, str) or not selector.strip():
        return False, "A valid CSS selector is required."

    if len(selector) > 300:
        return False, "CSS selector is too long."

    if not SELECTOR_PATTERN.fullmatch(selector.strip()):
        return False, "CSS selector contains unsupported characters."

    css = proposal.get("css")

    if not isinstance(css, dict) or not css:
        return False, "CSS proposal is empty or invalid."

    for property_name, value in css.items():

        if property_name not in ALLOWED_CSS_PROPERTIES:
            return False, f"CSS property not permitted: {property_name}"

        if not isinstance(value, str):
            return False, f"Invalid CSS value for {property_name}."

        value = value.strip()

        if not value or len(value) > 200:
            return False, f"Invalid CSS value for {property_name}."

        if not CSS_VALUE_PATTERN.fullmatch(value):
            return False, f"Unsafe CSS value for {property_name}."

    return True, "Proposal validation successful."


def apply_approved_css(
    page: Page,
    proposal: dict[str, Any],
    approved: bool = False,
) -> dict[str, Any]:
    """
    Apply an approved CSS proposal to a Playwright page.

    Automatic application is disabled by default.
    A human must explicitly approve the proposal.
    """

    if not approved:
        return {
            "success": False,
            "status": "approval_required",
            "message": "Human approval is required before applying CSS.",
        }

    is_valid, validation_message = validate_repair_proposal(
        proposal
    )

    if not is_valid:
        return {
            "success": False,
            "status": "rejected",
            "message": validation_message,
        }

    selector = proposal["target"].strip()
    css = proposal["css"]

    try:
        locator = page.locator(selector)

        matching_elements = locator.count()

        if matching_elements != 1:
            return {
                "success": False,
                "status": "needs_manual_review",
                "message": (
                    "Expected exactly one matching element, "
                    f"but found {matching_elements}."
                ),
            }

        # Apply only the validated CSS properties.
        locator.evaluate(
            """
            (element, styles) => {
                for (const [property, value] of Object.entries(styles)) {
                    element.style.setProperty(property, value);
                }
            }
            """,
            css,
        )

        logger.info(
            "Approved CSS repair applied: selector=%s properties=%s",
            selector,
            list(css.keys()),
        )

        return {
            "success": True,
            "status": "applied",
            "target": selector,
            "applied_css": css,
            "message": "Approved CSS changes applied successfully.",
        }

    except Exception:
        logger.exception(
            "CSS repair failed for selector: %s",
            selector,
        )

        return {
            "success": False,
            "status": "failed",
            "message": "CSS repair could not be applied.",
        }


def capture_repaired_screenshot(
    page: Page,
    screenshot_path: str,
) -> dict[str, Any]:
    """Capture a screenshot after applying an approved repair."""

    path = Path(screenshot_path)

    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        return {
            "success": False,
            "message": "Unsupported screenshot format.",
        }

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        page.screenshot(
            path=str(path),
            full_page=True,
        )

        logger.info(
            "Repaired screenshot captured: %s",
            path,
        )

        return {
            "success": True,
            "screenshot": str(path),
            "message": "Repaired screenshot captured successfully.",
        }

    except Exception:
        logger.exception(
            "Failed to capture repaired screenshot."
        )

        return {
            "success": False,
            "message": "Screenshot capture failed.",
        }
