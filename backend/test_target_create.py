"""Quick test for target creation"""
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Register
resp = client.post('/api/v1/auth/register', json={
    'email': 'test@example.com',
    'username': 'testuser',
    'password': 'pass123'
})
print(f'Register: {resp.status_code}')

# Login
login = client.post('/api/v1/auth/login', json={
    'username': 'testuser',
    'password': 'pass123'
})
print(f'Login: {login.status_code}')
token = login.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Create target
target_resp = client.post('/api/v1/targets', json={
    'period': 'daily',
    'target_seconds': 14400,
    'effective_from': datetime(2025, 12, 15, 0, 0, 0, tzinfo=timezone.utc).isoformat()
}, headers=headers)

print(f'Target create: {target_resp.status_code}')
if target_resp.status_code == 201:
    print(f'Target: {target_resp.json()}')
else:
    print(f'Error: {target_resp.json()}')
