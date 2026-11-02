"""Before-and-after UI repair verification for OmniSight."""

import logging
from typing import Any

from vision.schemas import VisionAnalysis

logger = logging.getLogger("omnisight.verification")


def normalize_issue(issue) -> tuple[str, str]:
    """Create a comparable identity for a visual issue."""

    issue_type = issue.type.strip().lower()
    element = (issue.element or "").strip().lower()

    return issue_type, element


def verify_repair(
    before: VisionAnalysis,
    after: VisionAnalysis,
) -> dict[str, Any]:
    """
    Compare visual analysis results before and after repair.

    This provides heuristic verification based on Gemini's
    reported issues. It does not guarantee pixel-perfect repair.
    """

    before_issues = before.issues
    after_issues = after.issues

    before_keys = {
        normalize_issue(issue)
        for issue in before_issues
    }

    after_keys = {
        normalize_issue(issue)
        for issue in after_issues
    }

    resolved = before_keys - after_keys
    remaining = before_keys & after_keys
    new_issues = after_keys - before_keys

    if not before_issues:
        status = "no_initial_defects"

    elif not after_issues:
        status = "likely_resolved"

    elif remaining:
        status = "still_detected"

    elif new_issues:
        status = "inconclusive"

    else:
        status = "inconclusive"

    result = {
        "verification_status": status,
        "before_defect_count": len(before_issues),
        "after_defect_count": len(after_issues),
        "resolved_issue_count": len(resolved),
        "remaining_issue_count": len(remaining),
        "new_issue_count": len(new_issues),
        "resolved_issues": [
            {
                "type": issue_type,
                "element": element,
            }
            for issue_type, element in sorted(resolved)
        ],
        "remaining_issues": [
            {
                "type": issue_type,
                "element": element,
            }
            for issue_type, element in sorted(remaining)
        ],
        "new_issues": [
            {
                "type": issue_type,
                "element": element,
            }
            for issue_type, element in sorted(new_issues)
        ],
        "automatic_repair_verified": False,
    }

    logger.info(
        "Repair verification completed: status=%s, "
        "before=%s, after=%s",
        status,
        len(before_issues),
        len(after_issues),
    )

    return result
