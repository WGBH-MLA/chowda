from os import environ, path
from typing import List, Optional, Type

import jwt
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pytest import fixture

from chowda.app import app
from chowda.auth.utils import jwt_signing_key
from chowda.config import AUTH0_API_AUDIENCE

# Set CHOWDA_ENV env var to 'test' always. This serves as a flag for anywhere else in
# the application where we need to detect whether we are running tests or not.
environ['CHOWDA_ENV'] = 'test'

from json import dumps, loads
from json.decoder import JSONDecodeError
from pytest import fixture
from chowda.app import app
from fastapi.testclient import TestClient
from httpx import AsyncClient

# This import must come *after* setting CHOWDA_ENV to 'test' above.
from chowda.db import init_db  # noqa: E402

# Set CI_CONFIG to use ./test/ci.test.toml *only* if it's not already set. We need to be
# able to set the CI_CONFIG to point to a real SonyCi account and workspace when we are
# recording our VCR cassette fixtures for testing.
if not environ.get('CI_CONFIG'):
    environ['CI_CONFIG'] = './tests/ci.test.toml'


# Call init_db to create test database.
init_db()


def clean_response(response: dict):
    """Replace secrets in response body with dummy values."""
    try:
        body = loads(response['body']['string'].decode())
    except JSONDecodeError:
        return response
    if 'access_token' in body:
        body['access_token'] = 'DUMMY_ACCESS_TOKEN'
    if 'refresh_token' in body:
        body['refresh_token'] = 'DUMMY_REFRESH_TOKEN'
    response['body']['string'] = dumps(body).encode()
    return response


@fixture(scope='module')
def vcr_config(request):
    return {
        # Save cassettes in tests/cassettes/<module_name>/<test_name>.yaml
        'cassette_library_dir': path.join(
            path.dirname(path.abspath(__file__)), 'cassettes', request.module.__name__
        ),
        # Replace the Authorization request header with "DUMMY" in cassettes
        'filter_headers': [('authorization', 'Bearer DUMMY')],
        # Replace secrets in request body
        'filter_post_data_parameters': [
            ('client_id', 'FAKE_CLIENT_ID'),
            ('client_secret', 'FAKE_CLIENT_SECRET'),
        ],
        # Replace secrets in response body
        'before_record_response': clean_response,
    }


@fixture
def async_client(request):
    return AsyncClient(app=app, base_url='http://test')


@fixture
def client(request):
    return TestClient(app)


def fake_signing_key() -> str:
    """
    Returns a fake secret key with which to encode/decode JWTS. This is a
    regular function, not a fixture, because it is used as a FastAPI dependency
    override, which will throw an error if it tries to call a fixture directly.
    """

    return 'FAKE SECRET KEY'


@fixture
def fake_access_token() -> Type[callable]:
    """
    Returns a factory for generating fake access tokens for testing.
    """

    def _fake_access_token(
        permissions: Optional[List[str]] = None, algorithm: str = 'HS256'
    ) -> str:
        if permissions is None:
            permissions = []
        jwt_decoded = {
            'permissions': permissions,
            'aud': AUTH0_API_AUDIENCE,
            'sub': 'fake-api-subject',
        }
        return jwt.encode(jwt_decoded, fake_signing_key(), algorithm=algorithm)

    return _fake_access_token


# Override FastAPI dependency for jwt_signing_key to use the same fake signing key we
# use for encoding the JWT.
# NOTE: for testing we us a the synchronous HS256 algorithm which uses the same key for
# encoding and decoding, but in production we may use the asynchronous RS256 algorithm
# which uses a public/private key. We can do this only because the logic that does the
# decoding attempts algorithms, first RS256 then HS256.
# See also chowda.auth.utils.validated_access_token.
app.dependency_overrides[jwt_signing_key] = fake_signing_key


def set_session_data():
    # Define a factory function that can be used to set session data for testing.
    def _set_session_data(data: dict = {}) -> None:
        """Set session data for testing."""

        from starlette.requests import Request
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.middleware import Middleware
        from chowda.app import app

        class SetSessionData(BaseHTTPMiddleware):
            """
            A simple middleware that sets the session data to the value of the data.
            """

            async def dispatch(self, request: Request, call_next):
                request.session.update(data)
                response = await call_next(request)
                return response

        # Append the session-setting middleware to the end of the middleware stack rather
        # than using the add_middleware function that prepends it to the beginning of the
        # middleware stack. This ensures that the SessionMiddleware has already been been
        # run, and the session is available on the request object.
        app.user_middleware.append(Middleware(SetSessionData))

    # Return the factory function so that it can be used as a fixture.
    return _set_session_data
