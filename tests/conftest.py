from json import dumps, loads
from json.decoder import JSONDecodeError
from os import environ, path
from pytest import fixture

# Set ENVIRONMENT env var to 'test' always. This serves as a flag for anywhere else in
# the application where we need to detect whether we are running tests or not.
environ['ENVIRONMENT'] = 'test'

# Set CI_CONFIG to use ./test/ci.test.toml *only* if it's not already set. We need to be
# able to set the CI_CONFIG to point to a real SonyCi account and workspace when we are
# recording our VCR cassette fixtures for testing.
if not environ.get('CI_CONFIG'):
    environ['CI_CONFIG'] = './tests/ci.test.toml'


# setup_test_db.
# - scope=session means it's run once per run of pytest.
# - autouse=true means it runs automatically
@fixture(scope='session', autouse=True)
def setup_test_db():
    from chowda.db import engine
    from chowda import models  # noqa: F401
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)


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
