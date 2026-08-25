import pytest
from httpx import AsyncClient
from metaflow.plugins.argo.argo_events import ArgoEventException
from pytest_mock import MockerFixture

from chowda.routers.sony_ci import SyncResponse


@pytest.mark.asyncio
async def test_sony_ci_sync(
    mocker: MockerFixture, async_client: AsyncClient, fake_access_token: type[callable]
):
    mocker.patch('metaflow.integrations.ArgoEvent.publish')
    mocker.patch('fastapi_cache.FastAPICache.clear')

    async with async_client as ac:
        bearer_token = fake_access_token(permissions=['sync:sonyci'])
        response = await ac.post(
            '/api/sony_ci/sync',
            headers={'Authorization': f'Bearer {bearer_token}'},
        )

    assert response.status_code == 200
    sync_response = SyncResponse(**response.json())
    assert sync_response.started_at is not None


@pytest.mark.asyncio
async def test_sony_ci_sync_no_permission(
    async_client: AsyncClient, fake_access_token: type[callable]
):
    async with async_client as ac:
        bearer_token = fake_access_token(permissions=['wrong_permission:sonyci'])
        response = await ac.post(
            '/api/sony_ci/sync', headers={'Authorization': f'Bearer {bearer_token}'}
        )

    assert response.status_code == 403
    response_json = response.json()
    error = response_json['detail']
    assert 'Missing required permissions:' in error
    assert "{'sync:sonyci'}" in error


@pytest.mark.asyncio
async def test_sony_ci_sync_fail(
    mocker: MockerFixture, async_client: AsyncClient, fake_access_token: type[callable]
):
    mocker.patch(
        'metaflow.integrations.ArgoEvent.publish',
        side_effect=ArgoEventException('Mocked exception'),
    )
    async with async_client as ac:
        bearer_token = fake_access_token(permissions=['sync:sonyci'])
        response = await ac.post(
            '/api/sony_ci/sync',
            headers={
                'Authorization': f'Bearer {bearer_token}',
            },
        )

    assert response.status_code == 500
    response_json = response.json()
    assert response_json['detail']['error'] == 'Mocked exception'
