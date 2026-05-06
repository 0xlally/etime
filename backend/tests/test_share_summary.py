"""Test share card summary endpoint."""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def _auth_headers(client: TestClient, username: str) -> dict[str, str]:
    payload = {
        "email": f"{username}@example.com",
        "username": username,
        "password": "testpass123",
    }
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/login", json={
        "username": payload["username"],
        "password": payload["password"],
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_category(client: TestClient, headers: dict[str, str], name: str, color: str = "#2f855a") -> dict:
    response = client.post("/api/v1/categories", json={"name": name, "color": color}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def _create_session(
    client: TestClient,
    headers: dict[str, str],
    category_id: int,
    start_time: datetime,
    hours: int,
) -> None:
    response = client.post("/api/v1/sessions/manual", json={
        "category_id": category_id,
        "start_time": start_time.isoformat(),
        "end_time": (start_time + timedelta(hours=hours)).isoformat(),
        "note": "Private note should never be returned by share summary",
    }, headers=headers)
    assert response.status_code == 201, response.text


def test_share_summary_filters_current_user_data(client: TestClient):
    user_headers = _auth_headers(client, "share_user")
    other_headers = _auth_headers(client, "share_other")

    user_category = _create_category(client, user_headers, "Deep Work", "#172033")
    other_category = _create_category(client, other_headers, "Other User Secret", "#b91c1c")

    now = datetime.now(timezone.utc)
    slot = now.replace(hour=9, minute=0, second=0, microsecond=0)
    _create_session(client, user_headers, user_category["id"], slot, 2)
    _create_session(client, other_headers, other_category["id"], slot, 5)

    response = client.get("/api/v1/share/summary?range=today", headers=user_headers)
    assert response.status_code == 200, response.text

    summary = response.json()
    assert summary["range"] == "today"
    assert summary["total_seconds"] == 7200
    assert summary["streak_days"] == 1
    assert summary["target_completion"]["status"] == "no_target"
    assert len(summary["by_category"]) == 1
    assert summary["by_category"][0]["category_name"] == "Deep Work"
    assert summary["by_category"][0]["percent"] == 1.0
    assert "Other User Secret" not in str(summary)
    assert "Private note" not in str(summary)


def test_share_summary_target_completion(client: TestClient):
    headers = _auth_headers(client, "share_target")
    category = _create_category(client, headers, "Study", "#2563eb")

    now = datetime.now(timezone.utc)
    start = now.replace(hour=8, minute=0, second=0, microsecond=0)
    _create_session(client, headers, category["id"], start, 2)

    target_response = client.post("/api/v1/targets", json={
        "period": "daily",
        "target_seconds": 2 * 3600,
        "include_category_ids": [category["id"]],
        "effective_from": now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
    }, headers=headers)
    assert target_response.status_code == 201, target_response.text

    response = client.get("/api/v1/share/summary?range=today", headers=headers)
    assert response.status_code == 200, response.text

    completion = response.json()["target_completion"]
    assert completion["total_count"] == 1
    assert completion["completed_count"] == 1
    assert completion["status"] == "completed"
    assert completion["items"][0]["actual_seconds"] == 7200
    assert completion["items"][0]["progress_ratio"] == 1.0


def test_share_summary_empty_month(client: TestClient):
    headers = _auth_headers(client, "share_empty")

    response = client.get("/api/v1/share/summary?range=month", headers=headers)
    assert response.status_code == 200, response.text

    summary = response.json()
    assert summary["total_seconds"] == 0
    assert summary["by_category"] == []
    assert summary["streak_days"] == 0
    assert len(summary["heatmap_preview"]) >= 28


def test_share_summary_rejects_invalid_range(client: TestClient):
    headers = _auth_headers(client, "share_invalid")

    response = client.get("/api/v1/share/summary?range=year", headers=headers)
    assert response.status_code == 422
