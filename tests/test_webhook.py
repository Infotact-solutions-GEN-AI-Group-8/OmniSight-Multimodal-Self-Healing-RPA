from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_valid_webhook():
    payload = {
        "event_type": "build.completed",
        "repository": "OmniSight",
        "branch": "teamlead-integration",
        "build_id": "test-build-001",
        "status": "success",
        "commit_sha": "abc123",
        "metadata": {
            "environment": "staging"
        }
    }

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["event"]["status"] == "success"


def test_invalid_webhook_status():
    payload = {
        "event_type": "build.completed",
        "repository": "OmniSight",
        "branch": "teamlead-integration",
        "build_id": "test-build-002",
        "status": "unknown"
    }

    response = client.post("/webhook", json=payload)

    assert response.status_code == 422
