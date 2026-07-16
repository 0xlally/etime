"""Tests for work target CRUD operations"""
from datetime import datetime, timezone
from fastapi.testclient import TestClient


def register_and_auth(client: TestClient, email: str, username: str) -> dict:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "testpass123"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "testpass123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_target(client: TestClient, headers: dict) -> int:
    effective_from = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    response = client.post(
        "/api/v1/targets",
        json={
            "period": "daily",
            "target_seconds": 7200,
            "effective_from": effective_from,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_target_delete_flow(client: TestClient):
    """User can create and delete their own target."""
    headers = register_and_auth(client, "target_delete@example.com", "targetdelete")
    target_id = create_target(client, headers)

    list_before = client.get("/api/v1/targets", headers=headers)
    assert list_before.status_code == 200
    assert len(list_before.json()) == 1

    delete_resp = client.delete(f"/api/v1/targets/{target_id}", headers=headers)
    assert delete_resp.status_code == 204

    list_after = client.get("/api/v1/targets", headers=headers)
    assert list_after.status_code == 200
    assert list_after.json() == []


def test_target_delete_respects_ownership(client: TestClient):
    """User cannot delete another user's target."""
    owner_headers = register_and_auth(client, "owner@example.com", "owneruser")
    target_id = create_target(client, owner_headers)

    other_headers = register_and_auth(client, "other@example.com", "otheruser")
    delete_resp = client.delete(f"/api/v1/targets/{target_id}", headers=other_headers)
    assert delete_resp.status_code == 404

    owner_list = client.get("/api/v1/targets", headers=owner_headers)
    assert owner_list.status_code == 200
    assert any(t["id"] == target_id for t in owner_list.json())


def test_target_update_allows_category_and_schedule_changes(client: TestClient):
    headers = register_and_auth(client, "target_update@example.com", "targetupdate")
    target_id = create_target(client, headers)

    category = client.post(
        "/api/v1/categories",
        json={"name": "Reading", "color": "#2563eb"},
        headers=headers,
    ).json()
    effective_from = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc).isoformat()

    response = client.patch(
        f"/api/v1/targets/{target_id}",
        json={
            "period": "weekly",
            "target_seconds": 10800,
            "include_category_ids": [category["id"]],
            "effective_from": effective_from,
            "is_active": False,
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["period"] == "weekly"
    assert updated["target_seconds"] == 10800
    assert updated["include_category_ids"] == [category["id"]]
    assert updated["is_active"] is False
    assert datetime.fromisoformat(updated["effective_from"]).replace(tzinfo=timezone.utc) == datetime.fromisoformat(effective_from)

    clear_categories = client.patch(
        f"/api/v1/targets/{target_id}",
        json={"include_category_ids": None},
        headers=headers,
    )
    assert clear_categories.status_code == 200, clear_categories.text
    assert clear_categories.json()["include_category_ids"] is None
