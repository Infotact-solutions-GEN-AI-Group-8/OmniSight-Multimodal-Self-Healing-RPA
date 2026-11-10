"""Validated response schemas for OmniSight."""

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

# Supported visual defect severity levels.
Severity = Literal[
    "critical",
    "high",
    "medium",
    "low",
    "info",
]


class SuggestedCSSFix(BaseModel):
    """A proposed CSS correction."""

    model_config = ConfigDict(extra="forbid")

    selector: str | None = Field(
        default=None,
        max_length=300,
    )

    css: dict[str, str] = Field(
        default_factory=dict,
    )

    rationale: str = Field(
        default="",
        max_length=1000,
    )

    @field_validator("css", mode="before")
    @classmethod
    def normalize_css(cls, value):
        """Normalize CSS strings and null values."""

        if value is None:
            return {}

        if isinstance(value, str):
            css_dict = {}

            for declaration in value.split(";"):
                if ":" in declaration:
                    key, val = declaration.split(":", 1)

                    css_dict[key.strip()] = val.strip()

            return css_dict

        return value


class VisualIssue(BaseModel):
    """A visual defect detected by an analyzer."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(
        min_length=1,
        max_length=100,
    )

    severity: Severity = "medium"

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value):
        """Normalize severity values from Gemini."""

        if isinstance(value, str):
            value = value.lower().strip()

            if value == "minor":
                return "low"

            if value == "moderate":
                return "medium"

        return value

    element: str | None = Field(
        default=None,
        max_length=200,
    )

    description: str = Field(
        min_length=1,
        max_length=2000,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    suggested_fix: SuggestedCSSFix | None = None


class VisionAnalysis(BaseModel):
    """Standardized visual analysis result."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["completed", "failed"] = "completed"

    defect_detected: bool

    summary: str = Field(
        min_length=1,
        max_length=2000,
    )

    viewport: str | None = None

    screenshot: str | None = None

    issues: list[VisualIssue] = Field(
        default_factory=list,
    )

    limitations: list[str] = Field(
        default_factory=list,
    )