"""Action Engine for generating safe CSS fix proposals."""

from typing import Any

from vision.schemas import VisionAnalysis


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


def generate_fix_proposals(
    analysis: VisionAnalysis,
) -> dict[str, Any]:
    """Generate reviewable CSS proposals from validated analysis."""

    proposals = []

    for issue in analysis.issues:
        suggested_fix = issue.suggested_fix

        if suggested_fix is None:
            proposals.append({
                "issue": issue.type,
                "status": "needs_manual_review",
                "reason": "No CSS suggestion was provided.",
            })
            continue

        if not suggested_fix.css:
            proposals.append({
                "issue": issue.type,
                "status": "needs_manual_review",
                "reason": "The suggested CSS is empty.",
            })
            continue

        safe_css = {}

        for property_name, value in suggested_fix.css.items():
            if property_name not in ALLOWED_CSS_PROPERTIES:
                continue

            # Keep the first implementation deliberately restrictive.
            if any(token in value for token in (";", "{", "}", "<", ">")):
                continue

            safe_css[property_name] = value

        if not safe_css:
            proposals.append({
                "issue": issue.type,
                "status": "needs_manual_review",
                "reason": "No permitted CSS properties remained.",
            })
            continue

        proposals.append({
            "issue": issue.type,
            "severity": issue.severity,
            "target": suggested_fix.selector,
            "css": safe_css,
            "rationale": suggested_fix.rationale,
            "status": "pending_validation",
        })

    return {
        "defect_detected": analysis.defect_detected,
        "proposal_count": len(proposals),
        "proposals": proposals,
        "automatic_application": False,
    }
