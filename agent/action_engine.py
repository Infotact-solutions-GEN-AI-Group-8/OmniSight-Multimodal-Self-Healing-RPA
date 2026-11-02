"""Action Engine for generating safe CSS fix proposals."""

import re
from typing import Any

from vision.schemas import VisionAnalysis


# Only these CSS properties are permitted.
ALLOWED_CSS_PROPERTIES = {
    "width",
    "max-width",
    "min-width",
    "height",
    "max-height",
    "margin",
    "margin-left",
    "margin-right",
    "padding",
    "display",
    "position",
    "overflow",
    "overflow-x",
    "box-sizing",
    "flex-wrap",
    "gap",
    "text-align",
}


# Restrict selectors to simple CSS selectors and descendants.
SELECTOR_PATTERN = re.compile(
    r"^[a-zA-Z0-9_*#.-]+(?:\s+[a-zA-Z0-9_*#.-]+)*$"
)


# Restrict CSS values to a conservative character set.
CSS_VALUE_PATTERN = re.compile(
    r"^[a-zA-Z0-9#.,()%\s-]+$"
)


DANGEROUS_CSS_PATTERNS = (
    "javascript:",
    "expression(",
    "url(",
    "@import",
    "behavior:",
    "-moz-binding",
    "!important",
)


def validate_selector(selector: str | None) -> bool:
    """Validate a proposed CSS selector."""

    if not selector:
        return False

    if len(selector) > 300:
        return False

    if not SELECTOR_PATTERN.fullmatch(selector.strip()):
        return False

    return True


def validate_css_value(value: str) -> bool:
    """Validate an individual CSS property value."""

    if not isinstance(value, str):
        return False

    value = value.strip()

    if not value or len(value) > 200:
        return False

    if not CSS_VALUE_PATTERN.fullmatch(value):
        return False

    normalized_value = value.lower()

    if any(
        pattern in normalized_value
        for pattern in DANGEROUS_CSS_PATTERNS
    ):
        return False

    return True


def generate_fix_proposals(
    analysis: VisionAnalysis,
) -> dict[str, Any]:
    """Generate safe, reviewable CSS proposals."""

    proposals = []

    for issue in analysis.issues:

        suggested_fix = issue.suggested_fix

        # Handle missing suggestions.
        if suggested_fix is None:
            proposals.append({
                "issue": issue.type,
                "severity": issue.severity,
                "status": "needs_manual_review",
                "reason": "No CSS suggestion was provided.",
            })
            continue

        # Handle empty CSS suggestions.
        if not suggested_fix.css:
            proposals.append({
                "issue": issue.type,
                "severity": issue.severity,
                "status": "needs_manual_review",
                "reason": "The suggested CSS is empty.",
            })
            continue

        # Validate the target selector.
        if not validate_selector(suggested_fix.selector):
            proposals.append({
                "issue": issue.type,
                "severity": issue.severity,
                "status": "needs_manual_review",
                "reason": "Missing or invalid CSS selector.",
            })
            continue

        safe_css = {}
        rejected_properties = []

        # Validate each CSS property and value.
        for property_name, value in suggested_fix.css.items():

            if property_name not in ALLOWED_CSS_PROPERTIES:
                rejected_properties.append(property_name)
                continue

            if not validate_css_value(value):
                rejected_properties.append(property_name)
                continue

            safe_css[property_name] = value.strip()

        # No safe CSS properties remain.
        if not safe_css:
            proposals.append({
                "issue": issue.type,
                "severity": issue.severity,
                "status": "needs_manual_review",
                "reason": "No permitted CSS properties remained.",
                "rejected_properties": rejected_properties,
            })
            continue

        # Generate a reviewable proposal.
        proposals.append({
            "issue": issue.type,
            "severity": issue.severity,
            "target": suggested_fix.selector,
            "css": safe_css,
            "rationale": suggested_fix.rationale,
            "status": "pending_validation",
            "rejected_properties": rejected_properties,
        })

    return {
        "defect_detected": analysis.defect_detected,
        "proposal_count": len(proposals),
        "proposals": proposals,
        "automatic_application": False,
    }
