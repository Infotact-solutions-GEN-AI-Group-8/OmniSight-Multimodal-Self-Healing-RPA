"""Validated response schemas for OmniSight."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal["critical", "high", "medium", "low", "info"]


class SuggestedCSSFix(BaseModel):
    """A proposed CSS correction."""

    model_config = ConfigDict(extra="forbid")

    selector: str | None = None

    css: dict[str, str] = Field(default_factory=dict)

    rationale: str = Field(default="", max_length=1000)


class VisualIssue(BaseModel):
    """A visual defect detected by an analyzer."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1, max_length=100)

    severity: Severity = "medium"

    element: str | None = Field(default=None, max_length=200)

    description: str = Field(min_length=1, max_length=2000)

    confidence: float = Field(ge=0.0, le=1.0)

    suggested_fix: SuggestedCSSFix | None = None


class VisionAnalysis(BaseModel):
    """Standardized visual analysis result."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["completed", "failed"] = "completed"

    defect_detected: bool

    summary: str = Field(min_length=1, max_length=2000)

    viewport: str | None = None

    screenshot: str | None = None

    issues: list[VisualIssue] = Field(default_factory=list)

    limitations: list[str] = Field(default_factory=list)
