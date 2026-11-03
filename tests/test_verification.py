from vision.schemas import VisionAnalysis, VisualIssue
from agent.verification import verify_repair


def make_analysis(issues):
    return VisionAnalysis(
        defect_detected=bool(issues),
        summary="Test analysis",
        issues=issues,
    )


def make_issue(issue_type="overlap", element="button"):
    return VisualIssue(
        type=issue_type,
        severity="medium",
        element=element,
        description="Test visual defect",
        confidence=0.9,
    )


def test_no_initial_defects():
    result = verify_repair(make_analysis([]), make_analysis([]))
    assert result["verification_status"] == "no_initial_defects"


def test_repair_likely_resolved():
    result = verify_repair(make_analysis([make_issue()]), make_analysis([]))
    assert result["verification_status"] == "likely_resolved"
    assert result["resolved_issue_count"] == 1


def test_defect_still_detected():
    result = verify_repair(
        make_analysis([make_issue()]),
        make_analysis([make_issue()]),
    )
    assert result["verification_status"] == "still_detected"
    assert result["remaining_issue_count"] == 1


def test_new_defect_detected():
    result = verify_repair(
        make_analysis([make_issue("overlap", "button")]),
        make_analysis([make_issue("misalignment", "header")]),
    )
    assert result["verification_status"] == "inconclusive"
    assert result["new_issue_count"] == 1