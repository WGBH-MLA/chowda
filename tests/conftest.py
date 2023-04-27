from os import environ, path

from pytest import fixture

environ['ENVIRONMENT'] = 'test'


@fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return path.join(
        path.dirname(path.abspath(__file__)), 'vhs', request.module.__name__
    )


@fixture(scope='module')
def vcr_config(request):
    return {
        # Replace the Authorization request header with "DUMMY" in cassettes
        'filter_headers': [('authorization', 'DUMMY')],
    }
