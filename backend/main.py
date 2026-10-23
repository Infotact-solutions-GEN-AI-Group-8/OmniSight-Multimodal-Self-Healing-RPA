import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import (
    FastAPI,
    HTTPException,
    File,
    Form,
    UploadFile,
)
from pydantic import BaseModel, Field, field_validator

from vision.vlm_analyzer import analyze_screenshot
from vision.schemas import VisionAnalysis
from agent.action_engine import generate_fix_proposals

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("omnisight")

app = FastAPI(
    title="OmniSight Webhook API",
    description=(
        "Receives simulated CI/CD build events and provides "
        "AI-powered visual UI defect analysis."
    ),
    version="1.2.0",
)

class BuildEvent(BaseModel):
    event_type: str = Field(min_length=1)
    repository: str = Field(min_length=1)
    branch: str = Field(min_length=1)
    build_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    commit_sha: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "event_type",
        "repository",
        "branch",
        "build_id",
    )
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty")

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        value = value.strip().lower()

        allowed_statuses = {
            "success",
            "failure",
            "pending",
            "cancelled",
        }

        if value not in allowed_statuses:
            raise ValueError(
                f"Invalid status. Allowed values: {sorted(allowed_statuses)}"
            )

        return value

@app.get("/")
async def home():
    return {
        "message": "OmniSight Webhook API is running",
        "status": "healthy",
        "version": app.version,
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "omnisight-backend",
    }

@app.post("/webhook")
async def receive_webhook(event: BuildEvent):
    try:
        logger.info(
            "Received build event: build_id=%s, repository=%s, "
            "branch=%s, status=%s",
            event.build_id,
            event.repository,
            event.branch,
            event.status,
        )

        received_at = datetime.now(timezone.utc).isoformat()

        return {
            "success": True,
            "message": "CI/CD build event received successfully",
            "event": event.model_dump(),
            "received_at": received_at,
            "next_step": (
                "Build event validated. "
                "Screenshot analysis can be requested separately."
            ),
        }

    except Exception:
        logger.exception(
            "Failed to process build event: build_id=%s",
            event.build_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process build event",
        )

@app.post("/analyze-screenshot")
async def analyze_ui_screenshot(
    screenshot: UploadFile = File(...),
    viewport: str = Form("unknown"),
):
    allowed_types = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
    }

    content_type = (screenshot.content_type or "").lower()

    if content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail="Upload a PNG, JPEG, or WebP screenshot.",
        )

    viewport = viewport.strip().lower()

    allowed_viewports = {
        "desktop",
        "tablet",
        "mobile",
        "unknown",
    }

    if viewport not in allowed_viewports:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid viewport. Allowed values: "
                "desktop, tablet, mobile, unknown."
            ),
        )

    content = await screenshot.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Screenshot file is empty.",
        )

    max_size = 10 * 1024 * 1024

    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail="Screenshot exceeds the 10 MB limit.",
        )

    temp_path: Path | None = None

    try:
        with NamedTemporaryFile(
            suffix=allowed_types[content_type],
            delete=False,
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        logger.info(
            "Starting screenshot analysis: viewport=%s, filename=%s",
            viewport,
            screenshot.filename,
        )
        analysis = analyze_screenshot(
            str(temp_path),
            viewport=viewport,
        )
        if isinstance(analysis, dict):
            analysis = VisionAnalysis.model_validate(analysis)

        if not isinstance(analysis, VisionAnalysis):
            raise ValueError(
                "VLM analyzer returned an unsupported result type."
            )
        proposals = generate_fix_proposals(analysis)

        logger.info(
            "Screenshot analysis completed: defects=%s, proposals=%s",
            analysis.defect_detected,
            proposals.get("proposal_count", 0),
        )

        return {
            "success": True,
            "message": "Screenshot analysis completed",
            "analysis": analysis.model_dump(),
            "action_engine": proposals,
            "automatic_application": False,
        }

    except HTTPException:
        raise

    except FileNotFoundError as error:
        logger.warning("Screenshot file error: %s", error)

        raise HTTPException(
            status_code=400,
            detail="Screenshot could not be accessed.",
        ) from error

    except ValueError as error:
        logger.warning("Invalid screenshot analysis result: %s", error)

        raise HTTPException(
            status_code=422,
            detail="The screenshot analysis result was invalid.",
        ) from error

    except Exception:
        logger.exception("Screenshot analysis failed")

        raise HTTPException(
            status_code=502,
            detail=(
                "Screenshot analysis failed. Check the VLM configuration "
                "and backend logs."
            ),
        )

    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                logger.warning(
                    "Could not remove temporary screenshot: %s",
                    temp_path,
                )

        await screenshot.close()
