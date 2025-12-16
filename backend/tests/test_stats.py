"""Test Stats API Endpoints"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta


def test_stats_today(client: TestClient):
    """
    Test today's statistics
    """
    # Setup: Register, login, create categories
    register_data = {
        "email": "stats_today@example.com",
        "username": "statstoday",
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
    work_cat = client.post("/api/v1/categories", json={"name": "Work"}, headers=headers).json()
    study_cat = client.post("/api/v1/categories", json={"name": "Study"}, headers=headers).json()
    
    # Create manual sessions for today
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Work session: 2 hours
    session1 = {
        "category_id": work_cat["id"],
        "start_time": today_start.isoformat(),
        "end_time": (today_start + timedelta(hours=2)).isoformat(),
        "note": "Morning work"
    }
    client.post("/api/v1/sessions/manual", json=session1, headers=headers)
    
    # Study session: 1 hour
    session2 = {
        "category_id": study_cat["id"],
        "start_time": (today_start + timedelta(hours=3)).isoformat(),
        "end_time": (today_start + timedelta(hours=4)).isoformat(),
        "note": "Study session"
    }
    client.post("/api/v1/sessions/manual", json=session2, headers=headers)
    
    # Work session again: 1.5 hours
    session3 = {
        "category_id": work_cat["id"],
        "start_time": (today_start + timedelta(hours=5)).isoformat(),
        "end_time": (today_start + timedelta(hours=6, minutes=30)).isoformat(),
        "note": "Afternoon work"
    }
    client.post("/api/v1/sessions/manual", json=session3, headers=headers)
    
    # Get today's stats
    response = client.get("/api/v1/stats/summary?range=today", headers=headers)
    assert response.status_code == 200
    
    stats = response.json()
    print(f"\nToday's Stats: {stats}")
    
    # Verify total: 2 + 1 + 1.5 = 4.5 hours = 16200 seconds
    assert stats["total_seconds"] == 16200
    
    # Verify by_category
    assert len(stats["by_category"]) == 2
    
    # Find Work and Study stats
    work_stats = next(c for c in stats["by_category"] if c["category_id"] == work_cat["id"])
    study_stats = next(c for c in stats["by_category"] if c["category_id"] == study_cat["id"])
    
    assert work_stats["category_name"] == "Work"
    assert work_stats["seconds"] == 12600  # 2 + 1.5 hours = 3.5 hours
    
    assert study_stats["category_name"] == "Study"
    assert study_stats["seconds"] == 3600  # 1 hour
    
    print("✓ Today stats verified correctly")


def test_stats_week(client: TestClient):
    """
    Test week statistics (Monday to Sunday)
    """
    # Setup
    register_data = {
        "email": "stats_week@example.com",
        "username": "statsweek",
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
    cat = client.post("/api/v1/categories", json={"name": "Exercise"}, headers=headers).json()
    
    # Create sessions across this week
    now = datetime.now(timezone.utc)
    
    # Calculate this Monday
    days_since_monday = now.weekday()  # 0 = Monday, 6 = Sunday
    this_monday = now - timedelta(days=days_since_monday)
    monday_morning = this_monday.replace(hour=8, minute=0, second=0, microsecond=0)
    
    # Monday session: 1 hour
    session1 = {
        "category_id": cat["id"],
        "start_time": monday_morning.isoformat(),
        "end_time": (monday_morning + timedelta(hours=1)).isoformat(),
        "note": "Monday workout"
    }
    client.post("/api/v1/sessions/manual", json=session1, headers=headers)
    
    # Wednesday session: 1.5 hours
    wednesday = monday_morning + timedelta(days=2)
    session2 = {
        "category_id": cat["id"],
        "start_time": wednesday.isoformat(),
        "end_time": (wednesday + timedelta(hours=1, minutes=30)).isoformat(),
        "note": "Wednesday workout"
    }
    client.post("/api/v1/sessions/manual", json=session2, headers=headers)
    
    # Friday session: 45 minutes
    friday = monday_morning + timedelta(days=4)
    session3 = {
        "category_id": cat["id"],
        "start_time": friday.isoformat(),
        "end_time": (friday + timedelta(minutes=45)).isoformat(),
        "note": "Friday workout"
    }
    client.post("/api/v1/sessions/manual", json=session3, headers=headers)
    
    # Get week stats
    response = client.get("/api/v1/stats/summary?range=week", headers=headers)
    assert response.status_code == 200
    
    stats = response.json()
    print(f"\nWeek Stats: {stats}")
    
    # Verify total: 1 + 1.5 + 0.75 = 3.25 hours = 11700 seconds
    assert stats["total_seconds"] == 11700
    
    # Verify by_category
    assert len(stats["by_category"]) == 1
    assert stats["by_category"][0]["category_name"] == "Exercise"
    assert stats["by_category"][0]["seconds"] == 11700
    
    print("✓ Week stats verified correctly (Monday to Sunday)")


def test_stats_month(client: TestClient):
    """
    Test month statistics
    """
    # Setup
    register_data = {
        "email": "stats_month@example.com",
        "username": "statsmonth",
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
    cat = client.post("/api/v1/categories", json={"name": "Reading"}, headers=headers).json()
    
    # Create sessions in current month
    now = datetime.now(timezone.utc)
    
    # First day of month: 2 hours
    first_day = now.replace(day=1, hour=10, minute=0, second=0, microsecond=0)
    session1 = {
        "category_id": cat["id"],
        "start_time": first_day.isoformat(),
        "end_time": (first_day + timedelta(hours=2)).isoformat(),
        "note": "First day reading"
    }
    client.post("/api/v1/sessions/manual", json=session1, headers=headers)
    
    # Mid-month: 3 hours
    mid_month = now.replace(day=15, hour=14, minute=0, second=0, microsecond=0)
    session2 = {
        "category_id": cat["id"],
        "start_time": mid_month.isoformat(),
        "end_time": (mid_month + timedelta(hours=3)).isoformat(),
        "note": "Mid-month reading"
    }
    client.post("/api/v1/sessions/manual", json=session2, headers=headers)
    
    # Get month stats
    response = client.get("/api/v1/stats/summary?range=month", headers=headers)
    assert response.status_code == 200
    
    stats = response.json()
    print(f"\nMonth Stats: {stats}")
    
    # Verify total: 2 + 3 = 5 hours = 18000 seconds
    assert stats["total_seconds"] == 18000
    
    # Verify by_category
    assert len(stats["by_category"]) == 1
    assert stats["by_category"][0]["category_name"] == "Reading"
    assert stats["by_category"][0]["seconds"] == 18000
    
    print("✓ Month stats verified correctly")


def test_stats_custom_range(client: TestClient):
    """
    Test custom date range statistics
    """
    # Setup
    register_data = {
        "email": "stats_custom@example.com",
        "username": "statscustom",
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
    cat1 = client.post("/api/v1/categories", json={"name": "Project A"}, headers=headers).json()
    cat2 = client.post("/api/v1/categories", json={"name": "Project B"}, headers=headers).json()
    
    # Define custom range: Dec 1-7, 2025
    range_start = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
    range_end = datetime(2025, 12, 7, 23, 59, 59, tzinfo=timezone.utc)
    
    # Session inside range: Project A, 4 hours (Dec 3)
    session1 = {
        "category_id": cat1["id"],
        "start_time": datetime(2025, 12, 3, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        "end_time": datetime(2025, 12, 3, 14, 0, 0, tzinfo=timezone.utc).isoformat(),
        "note": "In range"
    }
    client.post("/api/v1/sessions/manual", json=session1, headers=headers)
    
    # Session inside range: Project B, 2 hours (Dec 5)
    session2 = {
        "category_id": cat2["id"],
        "start_time": datetime(2025, 12, 5, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
        "end_time": datetime(2025, 12, 5, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
        "note": "Also in range"
    }
    client.post("/api/v1/sessions/manual", json=session2, headers=headers)
    
    # Session OUTSIDE range: Project A, 3 hours (Dec 10 - after range_end)
    session3 = {
        "category_id": cat1["id"],
        "start_time": datetime(2025, 12, 10, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        "end_time": datetime(2025, 12, 10, 13, 0, 0, tzinfo=timezone.utc).isoformat(),
        "note": "Out of range"
    }
    client.post("/api/v1/sessions/manual", json=session3, headers=headers)
    
    # Get stats for custom range
    from urllib.parse import quote
    start_param = quote(range_start.isoformat())
    end_param = quote(range_end.isoformat())
    url = f"/api/v1/stats/summary?start={start_param}&end={end_param}"
    response = client.get(url, headers=headers)
    assert response.status_code == 200, f"Failed with: {response.text}"
    
    stats = response.json()
    print(f"\nCustom Range Stats (Dec 1-7): {stats}")
    
    # Verify total: Only sessions 1 and 2 = 4 + 2 = 6 hours = 21600 seconds
    assert stats["total_seconds"] == 21600
    
    # Verify by_category
    assert len(stats["by_category"]) == 2
    
    project_a = next(c for c in stats["by_category"] if c["category_id"] == cat1["id"])
    project_b = next(c for c in stats["by_category"] if c["category_id"] == cat2["id"])
    
    assert project_a["seconds"] == 14400  # 4 hours
    assert project_b["seconds"] == 7200   # 2 hours
    
    print("✓ Custom range stats verified correctly (excluded out-of-range session)")


def test_stats_no_category(client: TestClient):
    """
    Test statistics with sessions without category
    """
    # Setup
    register_data = {
        "email": "stats_nocat@example.com",
        "username": "statsnocat",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create session without category
    now = datetime.now(timezone.utc)
    session = {
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
        "note": "No category session"
    }
    client.post("/api/v1/sessions/manual", json=session, headers=headers)
    
    # Get today's stats
    response = client.get("/api/v1/stats/summary?range=today", headers=headers)
    assert response.status_code == 200
    
    stats = response.json()
    print(f"\nStats with uncategorized session: {stats}")
    
    # Verify total
    assert stats["total_seconds"] == 3600  # 1 hour
    
    # Verify uncategorized entry
    assert len(stats["by_category"]) == 1
    assert stats["by_category"][0]["category_id"] is None
    assert stats["by_category"][0]["category_name"] is None
    assert stats["by_category"][0]["seconds"] == 3600
    
    print("✓ Uncategorized session stats verified correctly")


def test_stats_active_session_excluded(client: TestClient):
    """
    Test that active (ongoing) sessions are excluded from statistics
    """
    # Setup
    register_data = {
        "email": "stats_active@example.com",
        "username": "statsactive",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a completed session: 2 hours
    now = datetime.now(timezone.utc)
    completed = {
        "start_time": (now - timedelta(hours=3)).isoformat(),
        "end_time": (now - timedelta(hours=1)).isoformat(),
        "note": "Completed session"
    }
    client.post("/api/v1/sessions/manual", json=completed, headers=headers)
    
    # Start an active session (not completed yet)
    client.post("/api/v1/sessions/start", json={"note": "Active session"}, headers=headers)
    
    # Get today's stats
    response = client.get("/api/v1/stats/summary?range=today", headers=headers)
    assert response.status_code == 200
    
    stats = response.json()
    print(f"\nStats (should exclude active session): {stats}")
    
    # Should only count the completed session
    assert stats["total_seconds"] == 7200  # Only 2 hours from completed session
    
    print("✓ Active session correctly excluded from stats")


def test_stats_parameter_validation(client: TestClient):
    """
    Test parameter validation for stats endpoint
    """
    # Setup
    register_data = {
        "email": "stats_validation@example.com",
        "username": "statsvalidation",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Missing all parameters
    response = client.get("/api/v1/stats/summary", headers=headers)
    assert response.status_code == 400
    assert "Either 'range' or both 'start' and 'end'" in response.json()["detail"]
    print("✓ Missing parameters rejected")
    
    # Test 2: Invalid range type
    response = client.get("/api/v1/stats/summary?range=invalid", headers=headers)
    assert response.status_code == 400
    assert "Invalid range type" in response.json()["detail"]
    print("✓ Invalid range type rejected")
    
    # Test 3: start >= end
    now = datetime.now(timezone.utc)
    start = now
    end = now - timedelta(hours=1)  # end before start
    from urllib.parse import quote
    start_param = quote(start.isoformat())
    end_param = quote(end.isoformat())
    response = client.get(
        f"/api/v1/stats/summary?start={start_param}&end={end_param}",
        headers=headers
    )
    assert response.status_code == 400
    assert "start must be before end" in response.json()["detail"]
    print("✓ Invalid time range (start >= end) rejected")
