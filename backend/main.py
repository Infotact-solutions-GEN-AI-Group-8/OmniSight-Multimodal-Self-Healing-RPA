from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="OmniSight Webhook API",
    description="Receives simulated CI/CD build events",
    version="1.0.0"
)


class BuildEvent(BaseModel):
    event_type: str
    repository: str
    branch: str
    build_id: str
    status: str
    commit_sha: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


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
    allowed_statuses = {
        "success", "failure", "pending", "cancelled"
    }

    if event.status.lower() not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid build status"
        )

    return {
        "success": True,
        "message": "CI/CD build event received successfully",
        "event": event.model_dump(),
        "received_at": datetime.now(timezone.utc).isoformat(),
        "next_step": "Ready for OmniSight agent processing"
    }
