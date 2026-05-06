"""Test quick start template API endpoints."""
from fastapi.testclient import TestClient


def _auth_headers(client: TestClient, username: str = "quickuser") -> dict[str, str]:
    register_data = {
        "email": f"{username}@example.com",
        "username": username,
        "password": "testpass123",
    }
    client.post("/api/v1/auth/register", json=register_data)
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"],
    })
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_category(client: TestClient, headers: dict[str, str], name: str = "Reading") -> int:
    response = client.post("/api/v1/categories", json={"name": name, "color": "#3498DB"}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_quick_start_template_crud(client: TestClient):
    headers = _auth_headers(client)
    category_id = _create_category(client, headers)

    create_response = client.post(
        "/api/v1/quick-start-templates",
        json={
            "title": "阅读 25 分钟",
            "category_id": category_id,
            "duration_seconds": 1500,
            "note_template": "晚间阅读",
            "sort_order": 2,
            "color": "#22C55E",
            "icon": "book",
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    template = create_response.json()
    assert template["title"] == "阅读 25 分钟"
    assert template["category_id"] == category_id
    assert template["category_name"] == "Reading"
    assert template["duration_seconds"] == 1500
    assert template["is_active"] is True

    list_response = client.get("/api/v1/quick-start-templates", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.patch(
        f"/api/v1/quick-start-templates/{template['id']}",
        json={
            "title": "深度阅读 30 分钟",
            "duration_seconds": 1800,
            "sort_order": 1,
        },
        headers=headers,
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["title"] == "深度阅读 30 分钟"
    assert updated["duration_seconds"] == 1800
    assert updated["sort_order"] == 1

    delete_response = client.delete(f"/api/v1/quick-start-templates/{template['id']}", headers=headers)
    assert delete_response.status_code == 204

    list_response = client.get("/api/v1/quick-start-templates", headers=headers)
    assert list_response.json() == []


def test_start_session_from_quick_start_template(client: TestClient):
    headers = _auth_headers(client, "quickstart")
    category_id = _create_category(client, headers, "English")

    template = client.post(
        "/api/v1/quick-start-templates",
        json={
            "title": "英语 30 分钟",
            "category_id": category_id,
            "duration_seconds": 1800,
            "note_template": "背单词",
        },
        headers=headers,
    ).json()

    response = client.post(f"/api/v1/quick-start-templates/{template['id']}/start", headers=headers)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["template"]["id"] == template["id"]
    assert payload["session"]["category_id"] == category_id
    assert payload["session"]["note"] == "背单词"
    assert payload["session"]["end_time"] is None
    assert payload["session"]["source"] == "timer"

    active_response = client.get("/api/v1/sessions/active", headers=headers)
    assert active_response.status_code == 200
    assert active_response.json()["id"] == payload["session"]["id"]


def test_start_session_from_quick_start_template_is_idempotent(client: TestClient):
    headers = _auth_headers(client, "quickidem")
    category_id = _create_category(client, headers, "Reading")

    template = client.post(
        "/api/v1/quick-start-templates",
        json={
            "title": "阅读 25 分钟",
            "category_id": category_id,
            "duration_seconds": 1500,
        },
        headers=headers,
    ).json()

    start_payload = {
        "client_generated_id": "quick-template-running-001",
        "started_at": "2026-05-06T08:00:00Z",
    }
    first = client.post(
        f"/api/v1/quick-start-templates/{template['id']}/start",
        json=start_payload,
        headers=headers,
    )
    second = client.post(
        f"/api/v1/quick-start-templates/{template['id']}/start",
        json=start_payload,
        headers=headers,
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json()["session"]["id"] == first.json()["session"]["id"]
    assert second.json()["session"]["client_generated_id"] == "quick-template-running-001"


def test_quick_start_template_start_rejects_existing_active_session(client: TestClient):
    headers = _auth_headers(client, "quickconflict")
    category_id = _create_category(client, headers, "Fitness")

    template = client.post(
        "/api/v1/quick-start-templates",
        json={
            "title": "健身 45 分钟",
            "category_id": category_id,
            "duration_seconds": 2700,
        },
        headers=headers,
    ).json()

    first_start = client.post("/api/v1/sessions/start", json={"category_id": category_id}, headers=headers)
    assert first_start.status_code == 201

    response = client.post(f"/api/v1/quick-start-templates/{template['id']}/start", headers=headers)
    assert response.status_code == 409
    assert "already have an active session" in response.json()["detail"].lower()
