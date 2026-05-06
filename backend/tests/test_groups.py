"""Tests for group MVP APIs."""
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient

from app.models.user import User, UserRole
from app.utils.security import hash_password


def _auth(client: TestClient, email: str, username: str) -> tuple[dict, int]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "testpass123"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "testpass123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = client.get("/api/v1/users/me", headers=headers)
    return headers, me.json()["id"]


def _create_group(client: TestClient, headers: dict, name: str = "晨读小组") -> dict:
    response = client.post(
        "/api/v1/groups",
        json={"name": name, "description": "一起学习"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_group_adds_owner_membership(client: TestClient):
    headers, user_id = _auth(client, "group_owner@example.com", "groupowner")
    group = _create_group(client, headers)

    assert group["name"] == "晨读小组"
    assert group["owner_id"] == user_id
    assert group["my_role"] == "owner"
    assert group["member_count"] == 1
    assert len(group["invite_code"]) >= 8

    listed = client.get("/api/v1/groups", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == group["id"]


def test_join_group_by_invite_code_and_members_list(client: TestClient):
    owner_headers, _ = _auth(client, "group_join_owner@example.com", "joinowner")
    group = _create_group(client, owner_headers)

    member_headers, member_id = _auth(client, "group_join_member@example.com", "joinmember")
    join = client.post(
        "/api/v1/groups/join",
        json={"invite_code": group["invite_code"].lower()},
        headers=member_headers,
    )
    assert join.status_code == 200, join.text
    assert join.json()["my_role"] == "member"
    assert join.json()["member_count"] == 2

    members = client.get(f"/api/v1/groups/{group['id']}/members", headers=member_headers)
    assert members.status_code == 200
    assert any(item["user_id"] == member_id and item["username"] == "joinmember" for item in members.json())


def test_public_exam_group_invite_is_visible_and_joinable(client: TestClient):
    viewer_headers, _ = _auth(client, "group_public_viewer@example.com", "publicviewer")
    public_response = client.get("/api/v1/groups/public", headers=viewer_headers)
    assert public_response.status_code == 200, public_response.text
    public_groups = public_response.json()
    exam_group = next(item for item in public_groups if item["name"] == "考研小组")
    assert exam_group["visibility"] == "public"
    assert exam_group["invite_code"]
    assert exam_group["my_role"] == "owner"

    member_headers, _ = _auth(client, "group_public_member@example.com", "publicmember")
    visible_to_member = client.get("/api/v1/groups/public", headers=member_headers)
    assert visible_to_member.status_code == 200
    member_exam_group = next(item for item in visible_to_member.json() if item["name"] == "考研小组")
    assert member_exam_group["my_role"] is None

    join = client.post(
        "/api/v1/groups/join",
        json={"invite_code": member_exam_group["invite_code"]},
        headers=member_headers,
    )
    assert join.status_code == 200, join.text
    assert join.json()["name"] == "考研小组"
    assert join.json()["my_role"] == "member"


def test_public_group_request_notifies_admin(client: TestClient, db_session):
    admin = User(
        email="group_admin@example.com",
        username="groupadmin",
        password_hash=hash_password("testpass123"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()

    headers, _ = _auth(client, "group_request_user@example.com", "requestuser")
    response = client.post(
        "/api/v1/groups/public-requests",
        json={"name": "政治冲刺小组", "description": "希望公开给考研同学"},
        headers=headers,
    )
    assert response.status_code == 202, response.text

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"username": "groupadmin", "password": "testpass123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    notifications = client.get("/api/v1/notifications", headers=admin_headers)
    assert notifications.status_code == 200
    assert any(
        item["type"] == "group_public_request" and "政治冲刺小组" in (item["content"] or "")
        for item in notifications.json()
    )


def test_non_member_cannot_read_messages(client: TestClient):
    owner_headers, _ = _auth(client, "group_private_owner@example.com", "privateowner")
    group = _create_group(client, owner_headers)

    other_headers, _ = _auth(client, "group_private_other@example.com", "privateother")
    response = client.get(f"/api/v1/groups/{group['id']}/messages", headers=other_headers)
    assert response.status_code == 404


def test_member_can_send_message(client: TestClient):
    owner_headers, _ = _auth(client, "group_msg_owner@example.com", "msgowner")
    group = _create_group(client, owner_headers)

    response = client.post(
        f"/api/v1/groups/{group['id']}/messages",
        json={"content": "今天背单词 30 分钟"},
        headers=owner_headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["message_type"] == "text"
    assert response.json()["content"] == "今天背单词 30 分钟"

    messages = client.get(f"/api/v1/groups/{group['id']}/messages", headers=owner_headers)
    assert messages.status_code == 200
    assert any(item["content"] == "今天背单词 30 分钟" for item in messages.json())


def test_share_status_generates_status_share_message(client: TestClient):
    headers, _ = _auth(client, "group_status@example.com", "statususer")
    group = _create_group(client, headers)

    category = client.post("/api/v1/categories", json={"name": "英语"}, headers=headers).json()
    now = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)
    session = {
        "category_id": category["id"],
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=2, minutes=30)).isoformat(),
        "note": "morning study",
    }
    session_response = client.post("/api/v1/sessions/manual", json=session, headers=headers)
    assert session_response.status_code == 201, session_response.text

    target = client.post(
        "/api/v1/targets",
        json={
            "period": "daily",
            "target_seconds": 7200,
            "effective_from": now.isoformat(),
        },
        headers=headers,
    )
    assert target.status_code == 201, target.text

    response = client.post(f"/api/v1/groups/{group['id']}/share-status", headers=headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["message_type"] == "status_share"
    assert "今天已投入" in data["content"]
    assert data["metadata_json"]["total_seconds"] == 9000
    assert data["metadata_json"]["top_category"]["category_name"] == "英语"
    assert data["metadata_json"]["target_completed_count"] == 1
    assert data["metadata_json"]["target_total_count"] == 1


def test_owner_permission_and_leave_rules(client: TestClient):
    owner_headers, _ = _auth(client, "group_perm_owner@example.com", "permowner")
    group = _create_group(client, owner_headers)

    member_headers, _ = _auth(client, "group_perm_member@example.com", "permmember")
    client.post("/api/v1/groups/join", json={"invite_code": group["invite_code"]}, headers=member_headers)

    denied = client.patch(f"/api/v1/groups/{group['id']}", json={"name": "新名字"}, headers=member_headers)
    assert denied.status_code == 403

    updated = client.patch(f"/api/v1/groups/{group['id']}", json={"name": "新名字"}, headers=owner_headers)
    assert updated.status_code == 200
    assert updated.json()["name"] == "新名字"

    owner_leave = client.post(f"/api/v1/groups/{group['id']}/leave", headers=owner_headers)
    assert owner_leave.status_code == 400

    member_leave = client.post(f"/api/v1/groups/{group['id']}/leave", headers=member_headers)
    assert member_leave.status_code == 204

    hidden_after_leave = client.get(f"/api/v1/groups/{group['id']}/messages", headers=member_headers)
    assert hidden_after_leave.status_code == 404
