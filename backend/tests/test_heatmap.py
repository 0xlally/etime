"""Test Heatmap API Endpoints"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta, date


def test_heatmap_basic(client: TestClient):
    """
    Test basic heatmap data retrieval
    """
    # Setup: Register, login, create category
    register_data = {
        "email": "heatmap_basic@example.com",
        "username": "heatmapbasic",
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
    cat = client.post("/api/v1/categories", json={"name": "Work"}, headers=headers).json()
    
    # Create sessions on different dates
    # Day 1: 2025-12-10, 3 hours total
    day1 = datetime(2025, 12, 10, 9, 0, 0, tzinfo=timezone.utc)
    session1 = {
        "category_id": cat["id"],
        "start_time": day1.isoformat(),
        "end_time": (day1 + timedelta(hours=2)).isoformat(),
        "note": "Morning work"
    }
    client.post("/api/v1/sessions/manual", json=session1, headers=headers)
    
    session2 = {
        "category_id": cat["id"],
        "start_time": (day1 + timedelta(hours=3)).isoformat(),
        "end_time": (day1 + timedelta(hours=4)).isoformat(),
        "note": "Afternoon work"
    }
    client.post("/api/v1/sessions/manual", json=session2, headers=headers)
    
    # Day 2: 2025-12-11, 1.5 hours
    day2 = datetime(2025, 12, 11, 14, 0, 0, tzinfo=timezone.utc)
    session3 = {
        "category_id": cat["id"],
        "start_time": day2.isoformat(),
        "end_time": (day2 + timedelta(hours=1, minutes=30)).isoformat(),
        "note": "Day 2 work"
    }
    client.post("/api/v1/sessions/manual", json=session3, headers=headers)
    
    # Get heatmap for this range
    response = client.get(
        "/api/v1/heatmap?start=2025-12-10&end=2025-12-11",
        headers=headers
    )
    assert response.status_code == 200
    
    heatmap = response.json()
    print(f"\nHeatmap data: {heatmap}")
    
    # Should have 2 days
    assert len(heatmap) == 2
    
    # Verify Day 1
    day1_data = next(d for d in heatmap if d["date"] == "2025-12-10")
    assert day1_data["total_seconds"] == 10800  # 3 hours
    
    # Verify Day 2
    day2_data = next(d for d in heatmap if d["date"] == "2025-12-11")
    assert day2_data["total_seconds"] == 5400  # 1.5 hours
    
    print("✓ Heatmap basic aggregation verified")


def test_heatmap_cross_day_sessions(client: TestClient):
    """
    Test that sessions are grouped by start_time date
    """
    # Setup
    register_data = {
        "email": "heatmap_cross@example.com",
        "username": "heatmapcross",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a session that crosses midnight
    # Starts on 2025-12-15 at 23:00, ends on 2025-12-16 at 01:00 (2 hours)
    start = datetime(2025, 12, 15, 23, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 12, 16, 1, 0, 0, tzinfo=timezone.utc)
    
    session = {
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "note": "Cross-midnight session"
    }
    client.post("/api/v1/sessions/manual", json=session, headers=headers)
    
    # Get heatmap
    response = client.get(
        "/api/v1/heatmap?start=2025-12-15&end=2025-12-16",
        headers=headers
    )
    assert response.status_code == 200
    
    heatmap = response.json()
    print(f"\nCross-day heatmap: {heatmap}")
    
    # Should be grouped by start date (2025-12-15)
    assert len(heatmap) == 1
    assert heatmap[0]["date"] == "2025-12-15"
    assert heatmap[0]["total_seconds"] == 7200  # 2 hours
    
    print("✓ Cross-midnight session grouped by start_time date")


def test_heatmap_default_365_days(client: TestClient):
    """
    Test default date range is last 365 days
    """
    # Setup
    register_data = {
        "email": "heatmap_default@example.com",
        "username": "heatmapdefault",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create sessions at different times
    now = datetime.now(timezone.utc)
    
    # Recent session (within 365 days)
    recent = now - timedelta(days=30)
    session1 = {
        "start_time": recent.isoformat(),
        "end_time": (recent + timedelta(hours=1)).isoformat(),
        "note": "Recent session"
    }
    client.post("/api/v1/sessions/manual", json=session1, headers=headers)
    
    # Old session (beyond 365 days)
    old = now - timedelta(days=400)
    session2 = {
        "start_time": old.isoformat(),
        "end_time": (old + timedelta(hours=2)).isoformat(),
        "note": "Old session"
    }
    client.post("/api/v1/sessions/manual", json=session2, headers=headers)
    
    # Get heatmap without parameters (should default to last 365 days)
    response = client.get("/api/v1/heatmap", headers=headers)
    assert response.status_code == 200
    
    heatmap = response.json()
    print(f"\nDefault range heatmap (365 days): {len(heatmap)} days with data")
    
    # Should only include recent session (within 365 days)
    # Old session (400 days ago) should be excluded
    recent_date = recent.date().isoformat()
    old_date = old.date().isoformat()
    
    dates_in_heatmap = [d["date"] for d in heatmap]
    assert recent_date in dates_in_heatmap
    assert old_date not in dates_in_heatmap
    
    print("✓ Default 365-day range excludes old sessions")


def test_heatmap_day_details(client: TestClient):
    """
    Test getting session details for a specific day
    """
    # Setup
    register_data = {
        "email": "heatmap_day@example.com",
        "username": "heatmapday",
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
    cat1 = client.post("/api/v1/categories", json={"name": "Coding"}, headers=headers).json()
    cat2 = client.post("/api/v1/categories", json={"name": "Reading"}, headers=headers).json()
    
    # Create multiple sessions on 2025-12-12
    target_date = datetime(2025, 12, 12, 0, 0, 0, tzinfo=timezone.utc)
    
    # Session 1: 9:00-11:00, Coding
    session1 = {
        "category_id": cat1["id"],
        "start_time": target_date.replace(hour=9).isoformat(),
        "end_time": target_date.replace(hour=11).isoformat(),
        "note": "Morning coding"
    }
    client.post("/api/v1/sessions/manual", json=session1, headers=headers)
    
    # Session 2: 14:00-15:30, Reading
    session2 = {
        "category_id": cat2["id"],
        "start_time": target_date.replace(hour=14).isoformat(),
        "end_time": target_date.replace(hour=15, minute=30).isoformat(),
        "note": "Afternoon reading"
    }
    client.post("/api/v1/sessions/manual", json=session2, headers=headers)
    
    # Session 3: 16:00-17:00, No category
    session3 = {
        "start_time": target_date.replace(hour=16).isoformat(),
        "end_time": target_date.replace(hour=17).isoformat(),
        "note": "Uncategorized work"
    }
    client.post("/api/v1/sessions/manual", json=session3, headers=headers)
    
    # Session on different day (should be excluded)
    other_day = datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc)
    session4 = {
        "category_id": cat1["id"],
        "start_time": other_day.isoformat(),
        "end_time": (other_day + timedelta(hours=1)).isoformat(),
        "note": "Different day"
    }
    client.post("/api/v1/sessions/manual", json=session4, headers=headers)
    
    # Get day details for 2025-12-12
    response = client.get("/api/v1/heatmap/day?date=2025-12-12", headers=headers)
    assert response.status_code == 200
    
    sessions = response.json()
    print(f"\nDay details for 2025-12-12: {len(sessions)} sessions")
    
    # Should have 3 sessions (excluding the one on 2025-12-13)
    assert len(sessions) == 3
    
    # Verify session details
    coding_session = next(s for s in sessions if s["note"] == "Morning coding")
    assert coding_session["category_name"] == "Coding"
    assert coding_session["duration_seconds"] == 7200  # 2 hours
    
    reading_session = next(s for s in sessions if s["note"] == "Afternoon reading")
    assert reading_session["category_name"] == "Reading"
    assert reading_session["duration_seconds"] == 5400  # 1.5 hours
    
    uncat_session = next(s for s in sessions if s["note"] == "Uncategorized work")
    assert uncat_session["category_id"] is None
    assert uncat_session["category_name"] is None
    assert uncat_session["duration_seconds"] == 3600  # 1 hour
    
    # Verify sessions are ordered by start_time
    assert sessions[0]["note"] == "Morning coding"
    assert sessions[1]["note"] == "Afternoon reading"
    assert sessions[2]["note"] == "Uncategorized work"
    
    print("✓ Day details returned correctly with category names")


def test_heatmap_empty_days(client: TestClient):
    """
    Test that days with no sessions are not included in heatmap
    """
    # Setup
    register_data = {
        "email": "heatmap_empty@example.com",
        "username": "heatmapempty",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create session only on 2025-12-10
    session = {
        "start_time": datetime(2025, 12, 10, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        "end_time": datetime(2025, 12, 10, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
        "note": "Single session"
    }
    client.post("/api/v1/sessions/manual", json=session, headers=headers)
    
    # Query a range with gaps: 2025-12-09 to 2025-12-11
    response = client.get(
        "/api/v1/heatmap?start=2025-12-09&end=2025-12-11",
        headers=headers
    )
    assert response.status_code == 200
    
    heatmap = response.json()
    print(f"\nHeatmap with gaps: {heatmap}")
    
    # Should only have data for 2025-12-10 (not 12-09 or 12-11)
    assert len(heatmap) == 1
    assert heatmap[0]["date"] == "2025-12-10"
    assert heatmap[0]["total_seconds"] == 3600
    
    print("✓ Empty days excluded from heatmap")


def test_heatmap_active_session_excluded(client: TestClient):
    """
    Test that active (ongoing) sessions are excluded from heatmap
    """
    # Setup
    register_data = {
        "email": "heatmap_active@example.com",
        "username": "heatmapactive",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a completed session today
    now = datetime.now(timezone.utc)
    completed = {
        "start_time": (now - timedelta(hours=2)).isoformat(),
        "end_time": (now - timedelta(hours=1)).isoformat(),
        "note": "Completed"
    }
    client.post("/api/v1/sessions/manual", json=completed, headers=headers)
    
    # Start an active session (ongoing)
    client.post("/api/v1/sessions/start", json={"note": "Active"}, headers=headers)
    
    # Get today's heatmap
    today = now.date().isoformat()
    response = client.get(
        f"/api/v1/heatmap?start={today}&end={today}",
        headers=headers
    )
    assert response.status_code == 200
    
    heatmap = response.json()
    print(f"\nHeatmap (should exclude active): {heatmap}")
    
    # Should only count completed session
    assert len(heatmap) == 1
    assert heatmap[0]["date"] == today
    assert heatmap[0]["total_seconds"] == 3600  # Only 1 hour from completed
    
    print("✓ Active session excluded from heatmap")


def test_heatmap_parameter_validation(client: TestClient):
    """
    Test parameter validation for heatmap endpoints
    """
    # Setup
    register_data = {
        "email": "heatmap_validation@example.com",
        "username": "heatmapvalidation",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: start > end
    response = client.get(
        "/api/v1/heatmap?start=2025-12-20&end=2025-12-10",
        headers=headers
    )
    assert response.status_code == 400
    assert "start date must be before or equal to end date" in response.json()["detail"]
    print("✓ Invalid date range rejected")
    
    # Test 2: /day endpoint requires date parameter
    response = client.get("/api/v1/heatmap/day", headers=headers)
    assert response.status_code == 422  # Missing required parameter
    print("✓ Missing date parameter rejected")
