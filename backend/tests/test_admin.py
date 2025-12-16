"""Test Admin Module - User and session management"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from app.models.admin_audit_log import AdminAuditLog


def test_regular_user_cannot_access_admin_endpoints(client: TestClient):
    """Test that regular users get 403 on admin endpoints"""
    # Register and login as regular user
    register_data = {
        "email": "regular@example.com",
        "username": "regularuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to access admin endpoints
    response1 = client.get("/api/v1/admin/users", headers=headers)
    assert response1.status_code == 403
    assert "not enough permissions" in response1.json()["detail"].lower()
    
    response2 = client.get("/api/v1/admin/sessions", headers=headers)
    assert response2.status_code == 403
    
    response3 = client.patch("/api/v1/admin/users/1", json={"is_active": False}, headers=headers)
    assert response3.status_code == 403
    
    print("✓ Regular users blocked from admin endpoints")


def test_admin_can_list_users(client: TestClient, db_session):
    """Test admin can list users with pagination and search"""
    # Create admin user
    admin_data = {
        "email": "admin@example.com",
        "username": "adminuser",
        "password": "adminpass123"
    }
    client.post("/api/v1/auth/register", json=admin_data)
    
    # Get admin user and upgrade to ADMIN role
    me_response = client.post("/api/v1/auth/login", json={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    admin_token = me_response.json()["access_token"]
    
    # Manually upgrade user to admin in database
    from app.models.user import User, UserRole
    admin_user = db_session.query(User).filter(User.username == "adminuser").first()
    admin_user.role = UserRole.ADMIN
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create some test users
    for i in range(5):
        client.post("/api/v1/auth/register", json={
            "email": f"user{i}@example.com",
            "username": f"user{i}",
            "password": "pass123"
        })
    
    # List all users (should include admin + 5 users = 6 total)
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] >= 6
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["users"]) >= 6
    
    # Test pagination
    response2 = client.get("/api/v1/admin/users?page=1&page_size=3", headers=headers)
    assert response2.status_code == 200
    assert len(response2.json()["users"]) == 3
    
    # Test search
    response3 = client.get("/api/v1/admin/users?search=user2", headers=headers)
    assert response3.status_code == 200
    assert response3.json()["total"] == 1
    assert response3.json()["users"][0]["username"] == "user2"
    
    print("✓ Admin can list users with pagination and search")


def test_admin_can_update_user(client: TestClient, db_session):
    """Test admin can update user attributes and audit log is created"""
    # Setup admin
    admin_data = {
        "email": "admin2@example.com",
        "username": "admin2",
        "password": "adminpass123"
    }
    client.post("/api/v1/auth/register", json=admin_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    admin_token = login_response.json()["access_token"]
    
    from app.models.user import User, UserRole
    admin_user = db_session.query(User).filter(User.username == "admin2").first()
    admin_user.role = UserRole.ADMIN
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create target user
    target_response = client.post("/api/v1/auth/register", json={
        "email": "target@example.com",
        "username": "targetuser",
        "password": "pass123"
    })
    target_user_id = db_session.query(User).filter(User.username == "targetuser").first().id
    
    # Update user: deactivate
    update_response = client.patch(
        f"/api/v1/admin/users/{target_user_id}",
        json={"is_active": False},
        headers=headers
    )
    assert update_response.status_code == 200
    
    updated_user = update_response.json()
    assert updated_user["is_active"] is False
    assert updated_user["username"] == "targetuser"
    
    # Check audit log was created
    audit_log = db_session.query(AdminAuditLog).filter(
        AdminAuditLog.action == "update_user",
        AdminAuditLog.target_id == target_user_id
    ).first()
    
    assert audit_log is not None
    assert audit_log.admin_user_id == admin_user.id
    assert audit_log.target_type == "user"
    assert "is_active" in audit_log.detail_json["changes"]
    
    print("✓ Admin can update user and audit log created")


def test_admin_can_update_user_role(client: TestClient, db_session):
    """Test admin can promote user to admin"""
    # Setup admin
    admin_data = {
        "email": "admin3@example.com",
        "username": "admin3",
        "password": "adminpass123"
    }
    client.post("/api/v1/auth/register", json=admin_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    admin_token = login_response.json()["access_token"]
    
    from app.models.user import User, UserRole
    admin_user = db_session.query(User).filter(User.username == "admin3").first()
    admin_user.role = UserRole.ADMIN
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create target user
    client.post("/api/v1/auth/register", json={
        "email": "promote@example.com",
        "username": "promoteuser",
        "password": "pass123"
    })
    target_user_id = db_session.query(User).filter(User.username == "promoteuser").first().id
    
    # Promote to admin
    update_response = client.patch(
        f"/api/v1/admin/users/{target_user_id}",
        json={"role": "ADMIN"},
        headers=headers
    )
    assert update_response.status_code == 200
    # Role is stored as lowercase in database
    assert update_response.json()["role"].upper() == "ADMIN"
    
    # Check audit log
    audit_log = db_session.query(AdminAuditLog).filter(
        AdminAuditLog.action == "update_user",
        AdminAuditLog.target_id == target_user_id
    ).order_by(AdminAuditLog.created_at.desc()).first()
    
    assert audit_log is not None
    assert "role" in audit_log.detail_json["changes"]
    assert audit_log.detail_json["changes"]["role"]["new"] == "ADMIN"
    
    print("✓ Admin can promote user to admin role")


def test_admin_can_list_sessions(client: TestClient, db_session):
    """Test admin can list sessions with filters"""
    # Setup admin
    admin_data = {
        "email": "admin4@example.com",
        "username": "admin4",
        "password": "adminpass123"
    }
    client.post("/api/v1/auth/register", json=admin_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    admin_token = login_response.json()["access_token"]
    
    from app.models.user import User, UserRole
    admin_user = db_session.query(User).filter(User.username == "admin4").first()
    admin_user.role = UserRole.ADMIN
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create user and sessions
    user_data = {
        "email": "sessionuser@example.com",
        "username": "sessionuser",
        "password": "pass123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    user_login = client.post("/api/v1/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    user_token = user_login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    user_id = db_session.query(User).filter(User.username == "sessionuser").first().id
    
    # Create some sessions
    for i in range(3):
        client.post("/api/v1/sessions/manual", json={
            "start_time": datetime(2025, 12, 10 + i, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
            "end_time": datetime(2025, 12, 10 + i, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
            "note": f"Session {i}"
        }, headers=user_headers)
    
    # List all sessions as admin
    response = client.get("/api/v1/admin/sessions", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] >= 3
    assert len(data["sessions"]) >= 3
    
    # Filter by user_id
    response2 = client.get(f"/api/v1/admin/sessions?user_id={user_id}", headers=headers)
    assert response2.status_code == 200
    assert response2.json()["total"] == 3
    
    # Filter by date range
    from urllib.parse import quote
    start_date = datetime(2025, 12, 11, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    response3 = client.get(f"/api/v1/admin/sessions?start={quote(start_date)}", headers=headers)
    assert response3.status_code == 200
    assert response3.json()["total"] == 2  # Sessions on 12/11 and 12/12
    
    # Test pagination
    response4 = client.get("/api/v1/admin/sessions?page_size=2", headers=headers)
    assert response4.status_code == 200
    assert len(response4.json()["sessions"]) == 2
    
    print("✓ Admin can list sessions with filters and pagination")


def test_admin_can_delete_session(client: TestClient, db_session):
    """Test admin can delete session and audit log is created"""
    # Setup admin
    admin_data = {
        "email": "admin5@example.com",
        "username": "admin5",
        "password": "adminpass123"
    }
    client.post("/api/v1/auth/register", json=admin_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    admin_token = login_response.json()["access_token"]
    
    from app.models.user import User, UserRole
    admin_user = db_session.query(User).filter(User.username == "admin5").first()
    admin_user.role = UserRole.ADMIN
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create user and session
    user_data = {
        "email": "deletetest@example.com",
        "username": "deletetest",
        "password": "pass123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    user_login = client.post("/api/v1/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    user_token = user_login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create session
    session_response = client.post("/api/v1/sessions/manual", json={
        "start_time": datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        "end_time": datetime(2025, 12, 15, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        "note": "To be deleted"
    }, headers=user_headers)
    
    session_id = session_response.json()["id"]
    
    # Delete session as admin
    delete_response = client.delete(f"/api/v1/admin/sessions/{session_id}", headers=headers)
    assert delete_response.status_code == 204
    
    # Verify session is deleted
    from app.models.session import Session
    deleted_session = db_session.query(Session).filter(Session.id == session_id).first()
    assert deleted_session is None
    
    # Check audit log was created
    audit_log = db_session.query(AdminAuditLog).filter(
        AdminAuditLog.action == "delete_session",
        AdminAuditLog.target_id == session_id
    ).first()
    
    assert audit_log is not None
    assert audit_log.admin_user_id == admin_user.id
    assert audit_log.target_type == "session"
    assert "deleted_session" in audit_log.detail_json
    # Note field exists and matches
    assert audit_log.detail_json["deleted_session"]["duration_seconds"] == 7200
    
    print("✓ Admin can delete session and audit log created")


def test_admin_update_nonexistent_user_returns_404(client: TestClient, db_session):
    """Test that updating non-existent user returns 404"""
    # Setup admin
    admin_data = {
        "email": "admin6@example.com",
        "username": "admin6",
        "password": "adminpass123"
    }
    client.post("/api/v1/auth/register", json=admin_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    admin_token = login_response.json()["access_token"]
    
    from app.models.user import User, UserRole
    admin_user = db_session.query(User).filter(User.username == "admin6").first()
    admin_user.role = UserRole.ADMIN
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Try to update non-existent user
    response = client.patch(
        "/api/v1/admin/users/99999",
        json={"is_active": False},
        headers=headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    print("✓ Updating non-existent user returns 404")


def test_admin_delete_nonexistent_session_returns_404(client: TestClient, db_session):
    """Test that deleting non-existent session returns 404"""
    # Setup admin
    admin_data = {
        "email": "admin7@example.com",
        "username": "admin7",
        "password": "adminpass123"
    }
    client.post("/api/v1/auth/register", json=admin_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    admin_token = login_response.json()["access_token"]
    
    from app.models.user import User, UserRole
    admin_user = db_session.query(User).filter(User.username == "admin7").first()
    admin_user.role = UserRole.ADMIN
    db_session.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Try to delete non-existent session
    response = client.delete("/api/v1/admin/sessions/99999", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    print("✓ Deleting non-existent session returns 404")
