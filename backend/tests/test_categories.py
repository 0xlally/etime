"""Test Category API Endpoints"""
import pytest
from fastapi.testclient import TestClient


def test_category_crud_flow(client: TestClient):
    """
    Test complete category CRUD flow:
    - Create categories
    - List categories
    - Update category
    - Delete (archive) category
    """
    # Setup: Register and login a user
    register_data = {
        "email": "category_test@example.com",
        "username": "categoryuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Create categories
    category1_data = {
        "name": "Work",
        "color": "#FF5733"
    }
    response = client.post("/api/v1/categories", json=category1_data, headers=headers)
    assert response.status_code == 201, f"Failed to create category: {response.text}"
    
    category1 = response.json()
    assert category1["name"] == "Work"
    assert category1["color"] == "#FF5733"
    assert category1["is_archived"] is False
    assert "id" in category1
    print(f"✓ Created category 1: {category1['name']}")
    
    category2_data = {
        "name": "Personal",
        "color": "#3498DB"
    }
    response = client.post("/api/v1/categories", json=category2_data, headers=headers)
    assert response.status_code == 201
    category2 = response.json()
    assert category2["name"] == "Personal"
    print(f"✓ Created category 2: {category2['name']}")
    
    # Step 2: List categories
    response = client.get("/api/v1/categories", headers=headers)
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) == 2
    assert any(c["name"] == "Work" for c in categories)
    assert any(c["name"] == "Personal" for c in categories)
    print(f"✓ Listed {len(categories)} categories")
    
    # Step 3: Update category
    update_data = {
        "name": "Work Projects",
        "color": "#E74C3C"
    }
    response = client.patch(f"/api/v1/categories/{category1['id']}", json=update_data, headers=headers)
    assert response.status_code == 200
    updated_category = response.json()
    assert updated_category["name"] == "Work Projects"
    assert updated_category["color"] == "#E74C3C"
    print(f"✓ Updated category: {category1['name']} -> {updated_category['name']}")
    
    # Step 4: Delete (archive) category
    response = client.delete(f"/api/v1/categories/{category2['id']}", headers=headers)
    assert response.status_code == 204
    print(f"✓ Archived category: {category2['name']}")
    
    # Verify soft delete - should not appear in default list
    response = client.get("/api/v1/categories", headers=headers)
    categories = response.json()
    assert len(categories) == 1
    assert categories[0]["name"] == "Work Projects"
    print(f"✓ Verified soft delete - only {len(categories)} active category")
    
    # Verify archived category appears when including archived
    response = client.get("/api/v1/categories?include_archived=true", headers=headers)
    all_categories = response.json()
    assert len(all_categories) == 2
    archived = [c for c in all_categories if c["is_archived"]]
    assert len(archived) == 1
    assert archived[0]["name"] == "Personal"
    print(f"✓ Verified archived category exists with include_archived=true")


def test_category_name_uniqueness(client: TestClient):
    """
    Test that category names must be unique per user.
    """
    # Setup: Register and login
    register_data = {
        "email": "unique_test@example.com",
        "username": "uniqueuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=register_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": register_data["username"],
        "password": register_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create first category
    category_data = {"name": "Fitness"}
    response = client.post("/api/v1/categories", json=category_data, headers=headers)
    assert response.status_code == 201
    print("✓ Created first category: Fitness")
    
    # Try to create duplicate
    response = client.post("/api/v1/categories", json=category_data, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()
    print("✓ Duplicate category name rejected")


def test_category_ownership(client: TestClient):
    """
    Test that users can only access their own categories.
    """
    # Create two users
    user1_data = {
        "email": "owner1@example.com",
        "username": "owner1",
        "password": "pass123"
    }
    user2_data = {
        "email": "owner2@example.com",
        "username": "owner2",
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
    print(f"✓ User1 created category with ID: {category_id}")
    
    # Login as user2
    login2 = client.post("/api/v1/auth/login", json={
        "username": user2_data["username"],
        "password": user2_data["password"]
    })
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # User2 tries to access user1's category
    response = client.get(f"/api/v1/categories/{category_id}", headers=headers2)
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]
    print("✓ User2 cannot access User1's category")
    
    # User2 tries to update user1's category
    response = client.patch(f"/api/v1/categories/{category_id}", 
                           json={"name": "Hacked"}, 
                           headers=headers2)
    assert response.status_code == 403
    print("✓ User2 cannot update User1's category")
    
    # User2 tries to delete user1's category
    response = client.delete(f"/api/v1/categories/{category_id}", headers=headers2)
    assert response.status_code == 403
    print("✓ User2 cannot delete User1's category")
    
    # User2's categories list should be empty
    response = client.get("/api/v1/categories", headers=headers2)
    assert len(response.json()) == 0
    print("✓ User2's category list is empty")
