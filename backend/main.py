import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("omnisight")

app = FastAPI(
    title="OmniSight Webhook API",
    description="Receives simulated CI/CD build events",
    version="1.1.0"
)


class BuildEvent(BaseModel):
    event_type: str = Field(min_length=1)
    repository: str = Field(min_length=1)
    branch: str = Field(min_length=1)
    build_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    commit_sha: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_type", "repository", "branch", "build_id")
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
            "cancelled"
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
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/webhook")
async def receive_webhook(event: BuildEvent):
    try:
        logger.info(
            "Received build event: build_id=%s, repository=%s, "
            "branch=%s, status=%s",
            event.build_id,
            event.repository,
            event.branch,
            event.status
        )

        received_at = datetime.now(timezone.utc).isoformat()

        # Future integration point:
        # Send the validated event to the OmniSight agent controller.

        return {
            "success": True,
            "message": "CI/CD build event received successfully",
            "event": event.model_dump(),
            "received_at": received_at,
            "next_step": "Ready for OmniSight agent processing"
        }

    except Exception:
        logger.exception(
            "Failed to process build event: build_id=%s",
            event.build_id
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process build event"
        )
