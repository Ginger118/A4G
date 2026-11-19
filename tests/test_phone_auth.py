from fastapi.testclient import TestClient

from app.main import app


def test_register_and_switch_phone_accounts():
    credentials = {'phone': '17000000001', 'password': 'Course-test-2026'}
    other = {'phone': '17000000002', 'password': 'Course-test-2026'}
    with TestClient(app) as client:
        weak = client.post('/api/auth/register', json={**credentials, 'password': 'weak'})
        assert weak.status_code == 422 and 'weak' not in weak.text
        assert client.post('/api/auth/register', json={**credentials, 'phone': '123'}).status_code == 422
        assert client.post('/api/auth/register', json=credentials).status_code == 201
        assert client.post('/api/auth/register', json={**credentials, 'phone': '+86 17000000001'}).status_code == 409
        assert client.post('/api/auth/register', json=other).status_code == 201
        assert client.get('/api/auth/me').status_code == 401

        assert client.post('/api/auth/login', json={**credentials, 'password': 'wrong'}).status_code == 401
        first = client.post('/api/auth/login', json={**credentials, 'phone': '+86 17000000001'})
        assert first.status_code == 200
        assert first.json()['username'] == '170****0001'
        assert first.json()['role'] == 'user'
        assert client.get('/api/auth/me').json() == first.json()
        assert client.get('/api/admin/summary').status_code == 403
        first_cookie = client.cookies.get('agent_session')
        asset = client.post('/api/assets', json={
            'name': 'first-account.md', 'kind': 'knowledge', 'content': '# First account\nOnly one account owns this.',
        })
        assert asset.status_code == 201
        asset_path = '/api/assets/' + asset.json()['id']

        second = client.post('/api/auth/login', json=other)
        assert second.status_code == 200
        assert first.json()['id'] != second.json()['id']
        assert client.get(asset_path).status_code == 404
        assert client.get('/api/assets').json() == []
        with TestClient(app, cookies={'agent_session': first_cookie}) as old_session:
            assert old_session.get('/api/auth/me').status_code == 401
        assert client.post('/api/auth/logout').status_code == 200
        assert client.get('/api/auth/me').status_code == 401

        assert client.post('/api/auth/login', json=credentials).status_code == 200
        assert client.get(asset_path).status_code == 200
