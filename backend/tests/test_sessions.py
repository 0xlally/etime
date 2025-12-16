"""Test Session API Endpoints"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
import time


def test_session_timer_flow(client: TestClient):
    """
    Test timer session flow: start -> stop
    """
    # Setup: Register, login, create category
    register_data = {
        "email": "session_test@example.com",
        "username": "sessionuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a category
    category_response = client.post("/api/v1/categories", 
                                   json={"name": "Focus Work", "color": "#FF5733"}, 
                                   headers=headers)
    category_id = category_response.json()["id"]
    
    # Step 1: Start a session
    start_data = {
        "category_id": category_id,
        "note": "Working on project"
    }
    response = client.post("/api/v1/sessions/start", json=start_data, headers=headers)
    assert response.status_code == 201, f"Failed to start session: {response.text}"
    
    session = response.json()
    assert session["category_id"] == category_id
    assert session["note"] == "Working on project"
    assert session["source"] == "timer"
    assert session["end_time"] is None
    assert session["duration_seconds"] is None
    session_id = session["id"]
    print(f"✓ Started timer session: {session_id}")
    
    # Verify active session exists
    active_response = client.get("/api/v1/sessions/active", headers=headers)
    assert active_response.status_code == 200
    active = active_response.json()
    assert active is not None
    assert active["id"] == session_id
    assert "elapsed_seconds" in active
    print(f"✓ Active session retrieved: {active['elapsed_seconds']} seconds elapsed")
    
    # Wait a bit to accumulate time
    time.sleep(2)
    
    # Step 2: Stop the session
    stop_data = {"note": "Completed the task"}
    response = client.post("/api/v1/sessions/stop", json=stop_data, headers=headers)
    assert response.status_code == 200
    
    stopped_session = response.json()
    assert stopped_session["id"] == session_id
    assert stopped_session["end_time"] is not None
    assert stopped_session["duration_seconds"] is not None
    assert stopped_session["duration_seconds"] >= 2  # At least 2 seconds
    assert stopped_session["note"] == "Completed the task"
    print(f"✓ Stopped session: duration = {stopped_session['duration_seconds']} seconds")
    
    # Verify no active session now
    active_response = client.get("/api/v1/sessions/active", headers=headers)
    assert active_response.json() is None
    print("✓ No active session after stop")


def test_session_manual_creation(client: TestClient):
    """
    Test manually creating a completed session
    """
    # Setup
    register_data = {
        "email": "manual_test@example.com",
        "username": "manualuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create category
    category_response = client.post("/api/v1/categories", 
                                   json={"name": "Reading"}, 
                                   headers=headers)
    category_id = category_response.json()["id"]
    
    # Create manual session
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=2)
    end_time = now - timedelta(hours=1)
    
    manual_data = {
        "category_id": category_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "note": "Read for an hour yesterday"
    }
    
    response = client.post("/api/v1/sessions/manual", json=manual_data, headers=headers)
    assert response.status_code == 201
    
    session = response.json()
    assert session["category_id"] == category_id
    assert session["source"] == "manual"
    assert session["duration_seconds"] == 3600  # 1 hour
    assert session["note"] == "Read for an hour yesterday"
    print(f"✓ Manual session created: {session['duration_seconds']} seconds")
    
    # Test validation: end_time must be after start_time
    invalid_data = {
        "category_id": category_id,
        "start_time": end_time.isoformat(),
        "end_time": start_time.isoformat(),  # Invalid: end before start
        "note": "Invalid session"
    }
    
    response = client.post("/api/v1/sessions/manual", json=invalid_data, headers=headers)
    assert response.status_code == 422  # Validation error
    print("✓ Validation rejected invalid time range")


def test_concurrent_session_prevention(client: TestClient):
    """
    Test that only one session can be active at a time
    """
    # Setup
    register_data = {
        "email": "concurrent_test@example.com",
        "username": "concurrentuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Start first session
    response = client.post("/api/v1/sessions/start", json={"note": "First session"}, headers=headers)
    assert response.status_code == 201
    print("✓ Started first session")
    
    # Try to start second session while first is active
    response = client.post("/api/v1/sessions/start", json={"note": "Second session"}, headers=headers)
    assert response.status_code == 409  # Conflict
    assert "already have an active session" in response.json()["detail"].lower()
    print("✓ Second concurrent start rejected with 409 Conflict")
    
    # Stop first session
    client.post("/api/v1/sessions/stop", json={}, headers=headers)
    print("✓ Stopped first session")
    
    # Now we can start a new session
    response = client.post("/api/v1/sessions/start", json={"note": "New session"}, headers=headers)
    assert response.status_code == 201
    print("✓ Started new session after stopping previous one")


def test_session_list_and_filter(client: TestClient):
    """
    Test listing sessions with filters
    """
    # Setup
    register_data = {
        "email": "list_test@example.com",
        "username": "listuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create categories
    cat1 = client.post("/api/v1/categories", json={"name": "Work"}, headers=headers).json()
    cat2 = client.post("/api/v1/categories", json={"name": "Study"}, headers=headers).json()
    
    # Create manual sessions
    now = datetime.now(timezone.utc)
    
    # Session 1: Work, 2 hours ago
    session1_data = {
        "category_id": cat1["id"],
        "start_time": (now - timedelta(hours=2)).isoformat(),
        "end_time": (now - timedelta(hours=1)).isoformat(),
        "note": "Work session"
    }
    client.post("/api/v1/sessions/manual", json=session1_data, headers=headers)
    
    # Session 2: Study, 4 hours ago
    session2_data = {
        "category_id": cat2["id"],
        "start_time": (now - timedelta(hours=4)).isoformat(),
        "end_time": (now - timedelta(hours=3)).isoformat(),
        "note": "Study session"
    }
    client.post("/api/v1/sessions/manual", json=session2_data, headers=headers)
    
    # List all sessions
    response = client.get("/api/v1/sessions", headers=headers)
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 2
    print(f"✓ Listed {len(sessions)} sessions")
    
    # Filter by category
    response = client.get(f"/api/v1/sessions?category_id={cat1['id']}", headers=headers)
    filtered = response.json()
    assert len(filtered) == 1
    assert filtered[0]["category_id"] == cat1["id"]
    print(f"✓ Filtered by category: {len(filtered)} session(s)")
    
    # Filter by time range
    start_filter = (now - timedelta(hours=3)).isoformat()
    response = client.get(f"/api/v1/sessions?start={start_filter}", headers=headers)
    recent = response.json()
    assert len(recent) == 1  # Only the recent work session
    print(f"✓ Filtered by time: {len(recent)} session(s)")


def test_session_category_ownership(client: TestClient):
    """
    Test that users can only use their own categories
    """
    # Create two users
    user1_data = {
        "email": "owner1_session@example.com",
        "username": "owner1session",
        "password": "pass123"
    }
    user2_data = {
        "email": "owner2_session@example.com",
        "username": "owner2session",
        "password": "pass123"
    }
    
    client.post("/api/v1/auth/register", json=user1_data)
    client.post("/api/v1/auth/register", json=user2_data)
    
    # Login as user1 and create category
    login1 = client.post("/api/v1/auth/login", json={
        "username": user1_data["username"],
        "password": user1_data["password"]
    })
    token1 = login1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    category_response = client.post("/api/v1/categories", 
                                    json={"name": "User1 Category"}, 
                                    headers=headers1)
    category_id = category_response.json()["id"]
    
    # Login as user2
    login2 = client.post("/api/v1/auth/login", json={
        "username": user2_data["username"],
        "password": user2_data["password"]
    })
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # User2 tries to start session with user1's category
    response = client.post("/api/v1/sessions/start", 
                          json={"category_id": category_id, "note": "Hacked"}, 
                          headers=headers2)
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]
    print("✓ User2 cannot use User1's category in session")


def test_session_deletion(client: TestClient):
    """
    Test session deletion
    """
    # Setup
    register_data = {
        "email": "delete_test@example.com",
        "username": "deleteuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create and stop a session
    client.post("/api/v1/sessions/start", json={"note": "Test"}, headers=headers)
    stop_response = client.post("/api/v1/sessions/stop", json={}, headers=headers)
    session_id = stop_response.json()["id"]
    
    # Delete the session
    response = client.delete(f"/api/v1/sessions/{session_id}", headers=headers)
    assert response.status_code == 204
    print(f"✓ Deleted session {session_id}")
    
    # Verify it's gone
    response = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert response.status_code == 404
    print("✓ Deleted session not found")
