"""Test Work Targets and Evaluation System"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta, date
from app.services.evaluation import evaluate_targets_for_date


def test_create_work_target(client: TestClient):
    """Test creating a work target"""
    register_data = {
        "email": "target_test@example.com",
        "username": "targetuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    target_data = {
        "period": "daily",
        "target_seconds": 28800,
        "effective_from": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.post("/api/v1/targets", json=target_data, headers=headers)
    assert response.status_code == 201
    
    target = response.json()
    assert target["period"] == "daily"
    assert target["target_seconds"] == 28800
    assert target["is_active"] is True
    print(f"✓ Created work target: {target['id']}")


def test_list_targets(client: TestClient):
    """Test listing work targets"""
    register_data = {
        "email": "list_targets@example.com",
        "username": "listtargets",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    client.post("/api/v1/targets", json={
        "period": "daily",
        "target_seconds": 14400,
        "effective_from": datetime.now(timezone.utc).isoformat()
    }, headers=headers)
    
    client.post("/api/v1/targets", json={
        "period": "weekly",
        "target_seconds": 100800,
        "effective_from": datetime.now(timezone.utc).isoformat()
    }, headers=headers)
    
    response = client.get("/api/v1/targets", headers=headers)
    assert response.status_code == 200
    
    targets = response.json()
    assert len(targets) == 2
    periods = {t["period"] for t in targets}
    assert "daily" in periods
    assert "weekly" in periods
    print("✓ Listed work targets")


def test_update_target(client: TestClient):
    """Test updating a work target"""
    register_data = {
        "email": "update_target@example.com",
        "username": "updatetarget",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    create_response = client.post("/api/v1/targets", json={
        "period": "daily",
        "target_seconds": 21600,
        "effective_from": datetime.now(timezone.utc).isoformat()
    }, headers=headers)
    target_id = create_response.json()["id"]
    
    update_data = {
        "target_seconds": 28800,
        "is_active": False
    }
    response = client.patch(f"/api/v1/targets/{target_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    
    updated = response.json()
    assert updated["target_seconds"] == 28800
    assert updated["is_active"] is False
    print("✓ Updated work target")


def test_evaluation_service_target_met(client: TestClient, db_session):
    """Test evaluation service when target is met"""
    register_data = {
        "email": "eval_met@example.com",
        "username": "evalmet",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    me_response = client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]
    
    target_date = date(2025, 12, 15)
    target_data = {
        "period": "daily",
        "target_seconds": 14400,
        "effective_from": datetime(2025, 12, 15, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    }
    client.post("/api/v1/targets", json=target_data, headers=headers)
    
    sessions = [
        {
            "start_time": datetime(2025, 12, 15, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
            "end_time": datetime(2025, 12, 15, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
            "note": "Morning work"
        },
        {
            "start_time": datetime(2025, 12, 15, 14, 0, 0, tzinfo=timezone.utc).isoformat(),
            "end_time": datetime(2025, 12, 15, 16, 0, 0, tzinfo=timezone.utc).isoformat(),
            "note": "Afternoon work"
        }
    ]
    
    for session in sessions:
        client.post("/api/v1/sessions/manual", json=session, headers=headers)
    
    evaluations = evaluate_targets_for_date(target_date, db_session, user_id=user_id)
    
    assert len(evaluations) == 1
    assert evaluations[0].status == "met"
    assert evaluations[0].actual_seconds == 18000
    assert evaluations[0].target_seconds == 14400
    assert evaluations[0].deficit_seconds == 0
    
    print(f"✓ Target met: {evaluations[0].actual_seconds}s >= {evaluations[0].target_seconds}s")
    
    notifications = client.get("/api/v1/notifications", headers=headers).json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "target_met"
    print("✓ Success notification created")


def test_evaluation_service_target_missed(client: TestClient, db_session):
    """Test evaluation service when target is missed"""
    register_data = {
        "email": "eval_missed@example.com",
        "username": "evalmissed",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    me_response = client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]
    
    target_date = date(2025, 12, 14)
    target_data = {
        "period": "daily",
        "target_seconds": 28800,
        "effective_from": datetime(2025, 12, 14, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    }
    client.post("/api/v1/targets", json=target_data, headers=headers)
    
    session = {
        "start_time": datetime(2025, 12, 14, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
        "end_time": datetime(2025, 12, 14, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        "note": "Partial work"
    }
    client.post("/api/v1/sessions/manual", json=session, headers=headers)
    
    evaluations = evaluate_targets_for_date(target_date, db_session, user_id=user_id)
    
    assert len(evaluations) == 1
    assert evaluations[0].status == "missed"
    assert evaluations[0].actual_seconds == 10800
    assert evaluations[0].target_seconds == 28800
    assert evaluations[0].deficit_seconds == 18000
    
    print(f"✓ Target missed: {evaluations[0].actual_seconds}s < {evaluations[0].target_seconds}s")
    
    notifications = client.get("/api/v1/notifications", headers=headers).json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "target_missed"
    print("✓ Missed notification created")
    
    evaluations_response = client.get("/api/v1/evaluations", headers=headers).json()
    assert len(evaluations_response) == 1
    assert evaluations_response[0]["status"] == "missed"
    print("✓ Evaluation retrieved via API")


def test_evaluation_with_category_filter(client: TestClient, db_session):
    """Test evaluation with category filtering"""
    register_data = {
        "email": "eval_category@example.com",
        "username": "evalcategory",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    me_response = client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]
    
    work_cat = client.post("/api/v1/categories", json={"name": "Work"}, headers=headers).json()
    play_cat = client.post("/api/v1/categories", json={"name": "Play"}, headers=headers).json()
    
    target_date = date(2025, 12, 13)
    target_data = {
        "period": "daily",
        "target_seconds": 14400,
        "include_category_ids": [work_cat["id"]],
        "effective_from": datetime(2025, 12, 13, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    }
    client.post("/api/v1/targets", json=target_data, headers=headers)
    
    work_session = {
        "category_id": work_cat["id"],
        "start_time": datetime(2025, 12, 13, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
        "end_time": datetime(2025, 12, 13, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        "note": "Work session"
    }
    client.post("/api/v1/sessions/manual", json=work_session, headers=headers)
    
    play_session = {
        "category_id": play_cat["id"],
        "start_time": datetime(2025, 12, 13, 14, 0, 0, tzinfo=timezone.utc).isoformat(),
        "end_time": datetime(2025, 12, 13, 19, 0, 0, tzinfo=timezone.utc).isoformat(),
        "note": "Play session"
    }
    client.post("/api/v1/sessions/manual", json=play_session, headers=headers)
    
    evaluations = evaluate_targets_for_date(target_date, db_session, user_id=user_id)
    
    assert len(evaluations) == 1
    assert evaluations[0].actual_seconds == 10800
    assert evaluations[0].status == "missed"
    assert evaluations[0].deficit_seconds == 3600
    
    print("✓ Category filtering works: only counted Work sessions")


def test_notification_read(client: TestClient, db_session):
    """Test marking notification as read"""
    register_data = {
        "email": "notif_read@example.com",
        "username": "notifread",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    me_response = client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]
    
    target_data = {
        "period": "daily",
        "target_seconds": 28800,
        "effective_from": datetime(2025, 12, 12, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    }
    client.post("/api/v1/targets", json=target_data, headers=headers)
    
    evaluate_targets_for_date(date(2025, 12, 12), db_session, user_id=user_id)
    
    notifications = client.get("/api/v1/notifications", headers=headers).json()
    assert len(notifications) == 1
    assert notifications[0]["read_at"] is None
    
    notification_id = notifications[0]["id"]
    
    response = client.post(f"/api/v1/notifications/{notification_id}/read", headers=headers)
    assert response.status_code == 200
    
    read_notif = response.json()
    assert read_notif["read_at"] is not None
    
    print("✓ Notification marked as read")


def test_no_duplicate_evaluations(client: TestClient, db_session):
    """Test that evaluation doesn't create duplicates for same date"""
    register_data = {
        "email": "no_dup@example.com",
        "username": "nodup",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    me_response = client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]
    
    target_data = {
        "period": "daily",
        "target_seconds": 14400,
        "effective_from": datetime(2025, 12, 11, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    }
    client.post("/api/v1/targets", json=target_data, headers=headers)
    
    target_date = date(2025, 12, 11)
    evaluations1 = evaluate_targets_for_date(target_date, db_session, user_id=user_id)
    evaluations2 = evaluate_targets_for_date(target_date, db_session, user_id=user_id)
    
    assert len(evaluations1) == 1
    assert len(evaluations2) == 0
    
    print("✓ No duplicate evaluations created")
