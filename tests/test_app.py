from fastapi.testclient import TestClient

from chowda.app import app

client = TestClient(app)


def test_get_admin_home():
    """GET / returns a Redirect response"""
    response = client.get('/', allow_redirects=False)
    assert response.status_code == 200, 'Home page did not display sucessfully'


def test_get_admin_redirect():
    """GET /admin returns a Redirect response"""
    response = client.get('/admin', allow_redirects=False)
    assert response.status_code == 307, 'Home page did not redirect sucessfully'
    assert (
        '/admin/' in response.headers['location']
    ), 'Home page did not redirect to /admin/'
