"""Test time trace endpoints."""
from fastapi.testclient import TestClient


def test_create_and_list_time_traces(client: TestClient):
    register_data = {
        "email": "trace_test@example.com",
        "username": "tracetest",
        "password": "testpass123",
    }
    client.post("/api/v1/auth/register", json=register_data)

    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"],
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/time-traces",
        json={"content": "今天完成了一件重要的小事"},
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text

    created = create_response.json()
    assert created["content"] == "今天完成了一件重要的小事"
    assert created["created_at"]

    list_response = client.get("/api/v1/time-traces", headers=headers)
    assert list_response.status_code == 200
    entries = list_response.json()
    assert len(entries) == 1
    assert entries[0]["id"] == created["id"]


def test_time_traces_are_user_scoped(client: TestClient):
    first = {"email": "trace_owner@example.com", "username": "traceowner", "password": "testpass123"}
    second = {"email": "trace_other@example.com", "username": "traceother", "password": "testpass123"}
    client.post("/api/v1/auth/register", json=first)
    client.post("/api/v1/auth/register", json=second)

    first_login = client.post("/api/v1/auth/login", json={
        "username": first["username"],
        "password": first["password"],
    })
    first_headers = {"Authorization": f"Bearer {first_login.json()['access_token']}"}

    second_login = client.post("/api/v1/auth/login", json={
        "username": second["username"],
        "password": second["password"],
    })
    second_headers = {"Authorization": f"Bearer {second_login.json()['access_token']}"}

    client.post("/api/v1/time-traces", json={"content": "Only mine"}, headers=first_headers)

    response = client.get("/api/v1/time-traces", headers=second_headers)
    assert response.status_code == 200
    assert response.json() == []
