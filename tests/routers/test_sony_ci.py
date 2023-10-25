from typing import Type

import pytest
from httpx import AsyncClient
from metaflow.plugins.argo.argo_events import ArgoEventException
from pytest_mock import MockerFixture

from chowda.routers.sony_ci import SyncResponse


@pytest.mark.asyncio
async def test_sony_ci_sync(
    mocker: MockerFixture, async_client: AsyncClient, fake_access_token: Type[callable]
):
    mocker.patch(
        'metaflow.integrations.ArgoEvent.publish',
        autospec=True,
        return_value=True,
    )

    async with async_client as ac:
        bearer_token = fake_access_token(permissions=['sync:sonyci'])
        response = await ac.post(
            '/api/sony_ci/sync',
            headers={'Authorization': f'Bearer {bearer_token}'},
        )

    assert response.status_code == 200
    assert SyncResponse(**response.json())


@pytest.mark.asyncio
async def test_sony_ci_sync_no_permission(
    mocker: MockerFixture, async_client: AsyncClient, fake_access_token: Type[callable]
):
    mocker.patch(
        'metaflow.integrations.ArgoEvent.publish',
        autospec=True,
        side_effect=ArgoEventException('Mocked exception'),
    )

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
    mocker: MockerFixture, async_client: AsyncClient, fake_access_token: Type[callable]
):
    mocker.patch(
        'metaflow.integrations.ArgoEvent.publish',
        autospec=True,
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
