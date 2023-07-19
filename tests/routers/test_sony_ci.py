import pytest
from httpx import AsyncClient

from chowda.app import app

from chowda.routers.sony_ci import SyncResponse

from metaflow.plugins.argo.argo_events import ArgoEventException


@pytest.fixture
def async_client(request):
    return AsyncClient(app=app, base_url='http://test')


@pytest.mark.anyio
async def test_sony_ci_sync(mocker, async_client):
    mocker.patch(
        'metaflow.integrations.ArgoEvent.publish',
        autospec=True,
        return_value=True,
    )

    async with async_client as ac:
        response = await ac.post('/api/sony_ci/sync')

    assert response.status_code == 200
    assert SyncResponse(**response.json())


@pytest.mark.anyio
async def test_sony_ci_sync_fail(mocker, async_client):
    mocker.patch(
        'metaflow.integrations.ArgoEvent.publish',
        autospec=True,
        side_effect=ArgoEventException('Mocked exception'),
    )

    async with async_client as ac:
        response = await ac.post('/api/sony_ci/sync')

    assert response.status_code == 500
    response_json = response.json()
    assert response_json['detail']['error'] == 'Mocked exception'
