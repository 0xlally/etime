"""
Test Authentication Flow: Register -> Login -> Access /me

This test demonstrates the complete authentication workflow:
1. Register a new user
2. Login to get access token
3. Use token to access protected /me endpoint
"""
import pytest
from fastapi.testclient import TestClient


def test_user_authentication_flow(client: TestClient):
    """
    Test complete user authentication flow:
    - Register a new user
    - Login to get access token
    - Access protected endpoint with token
    """
    
    # Step 1: Register a new user
    register_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 201, f"Registration failed: {response.text}"
    
    user_data = response.json()
    assert user_data["email"] == register_data["email"]
    assert user_data["username"] == register_data["username"]
    assert user_data["role"] == "user"
    assert user_data["is_active"] is True
    assert "id" in user_data
    print(f"✓ User registered successfully: {user_data['username']}")
    
    # Step 2: Login with credentials
    login_data = {
        "username": register_data["username"],
        "password": register_data["password"]
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"
    
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    access_token = token_data["access_token"]
    print(f"✓ Login successful, got access token")
    
    # Step 3: Access protected endpoint /me
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200, f"Access /me failed: {response.text}"
    
    current_user = response.json()
    assert current_user["email"] == register_data["email"]
    assert current_user["username"] == register_data["username"]
    assert current_user["is_active"] is True
    print(f"✓ Successfully accessed /me endpoint")
    print(f"✓ Current user: {current_user['username']} ({current_user['email']})")


def test_login_with_email(client: TestClient):
    """Test that users can login with email instead of username"""
    
    # Register user
    register_data = {
        "email": "email@example.com",
        "username": "emailuser",
        "password": "password123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    # Login with email
    login_data = {
        "username": register_data["email"],  # Using email as username
        "password": register_data["password"]
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    print("✓ Login with email successful")


def test_token_refresh(client: TestClient):
    """Test token refresh functionality"""
    
    # Register and login
    register_data = {
        "email": "refresh@example.com",
        "username": "refreshuser",
        "password": "password123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh token
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    print("✓ Token refresh successful")


def test_unauthorized_access(client: TestClient):
    """Test that protected endpoints require authentication"""
    
    # Try to access /me without token
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    print("✓ Unauthorized access correctly blocked")


def test_duplicate_registration(client: TestClient):
    """Test that duplicate email/username are rejected"""
    
    register_data = {
        "email": "duplicate@example.com",
        "username": "duplicateuser",
        "password": "password123"
    }
    
    # First registration
    response1 = client.post("/api/v1/auth/register", json=register_data)
    assert response1.status_code == 201
    
    # Try to register with same email
    response2 = client.post("/api/v1/auth/register", json=register_data)
    assert response2.status_code == 400
    assert "Email already registered" in response2.json()["detail"]
    print("✓ Duplicate email correctly rejected")


def test_invalid_credentials(client: TestClient):
    """Test login with invalid credentials"""
    
    # Try to login with non-existent user
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
    print("✓ Invalid credentials correctly rejected")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
