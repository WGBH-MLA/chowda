from fastapi.testclient import TestClient


def test_get_admin_home(client: TestClient):
    """GET / returns a Redirect response"""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 200, 'Home page did not display sucessfully'


def test_get_admin_redirect(client: TestClient):
    """GET /admin returns a Redirect response"""
    response = client.get('/admin/', follow_redirects=False)
    assert response.status_code == 303, 'Home page did not redirect sucessfully'
    assert (
        '/admin/login?next=' in response.headers['location']
    ), 'Home page did not redirect to /admin/'
