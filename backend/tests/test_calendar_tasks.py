"""Test calendar task API endpoints."""
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

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


def _create_category(client: TestClient, headers: dict[str, str], name: str = "Planner") -> dict:
    response = client.post("/api/v1/categories", json={"name": name, "color": "#2f855a"}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_calendar_task_create_update_and_list(client: TestClient):
    headers = _auth_headers(client, "planner_create")
    category = _create_category(client, headers)

    create_response = client.post("/api/v1/calendar-tasks", json={
        "title": "Read paper",
        "description": "Keep it calm",
        "category_id": category["id"],
        "priority": "high",
        "estimated_seconds": 1800,
    }, headers=headers)
    assert create_response.status_code == 201, create_response.text
    task = create_response.json()
    assert task["status"] == "unscheduled"
    assert task["category_name"] == "Planner"

    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=2)
    end = start + timedelta(minutes=45)
    patch_response = client.patch(f"/api/v1/calendar-tasks/{task['id']}", json={
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
        "reminder_enabled": True,
        "reminder_minutes_before": 15,
    }, headers=headers)
    assert patch_response.status_code == 200, patch_response.text
    scheduled = patch_response.json()
    assert scheduled["status"] == "scheduled"
    assert scheduled["reminder_enabled"] is True

    list_response = client.get(
        f"/api/v1/calendar-tasks?start={quote((start - timedelta(days=1)).isoformat())}"
        f"&end={quote((end + timedelta(days=1)).isoformat())}&include_unscheduled=false",
        headers=headers,
    )
    assert list_response.status_code == 200
    tasks = list_response.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == task["id"]


def test_calendar_task_reminders_due_and_fired(client: TestClient):
    headers = _auth_headers(client, "planner_reminder")
    category = _create_category(client, headers)
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=10)
    end = start + timedelta(minutes=30)

    response = client.post("/api/v1/calendar-tasks", json={
        "title": "Soon",
        "category_id": category["id"],
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
        "reminder_enabled": True,
        "reminder_minutes_before": 15,
    }, headers=headers)
    assert response.status_code == 201, response.text
    task = response.json()

    due_response = client.get(
        f"/api/v1/calendar-tasks/reminders/due?now={quote(datetime.now(timezone.utc).isoformat())}",
        headers=headers,
    )
    assert due_response.status_code == 200
    due = due_response.json()
    assert [item["id"] for item in due] == [task["id"]]

    fired_response = client.post(f"/api/v1/calendar-tasks/{task['id']}/reminder-fired", headers=headers)
    assert fired_response.status_code == 200
    assert fired_response.json()["reminder_fired_at"] is not None

    due_again = client.get("/api/v1/calendar-tasks/reminders/due", headers=headers)
    assert due_again.status_code == 200
    assert due_again.json() == []


def test_calendar_task_complete_and_convert_session(client: TestClient):
    headers = _auth_headers(client, "planner_complete")
    category = _create_category(client, headers)
    start = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=1)

    create_response = client.post("/api/v1/calendar-tasks", json={
        "title": "Focused block",
        "description": "Converted from planner",
        "category_id": category["id"],
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
    }, headers=headers)
    assert create_response.status_code == 201, create_response.text
    task = create_response.json()

    complete_response = client.post(
        f"/api/v1/calendar-tasks/{task['id']}/complete?create_session=true",
        headers=headers,
    )
    assert complete_response.status_code == 200, complete_response.text
    completed = complete_response.json()
    assert completed["status"] == "done"
    assert completed["converted_session_id"] is not None

    sessions_response = client.get("/api/v1/sessions", headers=headers)
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()
    converted = next(item for item in sessions if item["id"] == completed["converted_session_id"])
    assert converted["category_id"] == category["id"]
    assert converted["duration_seconds"] == 3600
    assert "Focused block" in converted["note"]


def test_calendar_task_complete_unscheduled_without_session(client: TestClient):
    headers = _auth_headers(client, "planner_unscheduled_done")

    create_response = client.post("/api/v1/calendar-tasks", json={"title": "Inbox item"}, headers=headers)
    assert create_response.status_code == 201, create_response.text
    task = create_response.json()

    complete_response = client.post(f"/api/v1/calendar-tasks/{task['id']}/complete", headers=headers)
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "done"

    bad_convert = client.post(
        f"/api/v1/calendar-tasks/{task['id']}/complete?create_session=true",
        headers=headers,
    )
    assert bad_convert.status_code == 400


def test_calendar_task_permission_isolation(client: TestClient):
    owner_headers = _auth_headers(client, "planner_owner")
    other_headers = _auth_headers(client, "planner_other")
    owner_category = _create_category(client, owner_headers, "Owner Category")
    other_category = _create_category(client, other_headers, "Other Category")

    create_response = client.post("/api/v1/calendar-tasks", json={
        "title": "Owner only",
        "category_id": owner_category["id"],
    }, headers=owner_headers)
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    other_list = client.get("/api/v1/calendar-tasks", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json() == []

    patch_response = client.patch(
        f"/api/v1/calendar-tasks/{task_id}",
        json={"title": "Nope"},
        headers=other_headers,
    )
    assert patch_response.status_code == 404

    cross_category = client.post("/api/v1/calendar-tasks", json={
        "title": "Cross category",
        "category_id": owner_category["id"],
    }, headers=other_headers)
    assert cross_category.status_code == 403

    other_task = client.post("/api/v1/calendar-tasks", json={
        "title": "Allowed",
        "category_id": other_category["id"],
    }, headers=other_headers)
    assert other_task.status_code == 201
