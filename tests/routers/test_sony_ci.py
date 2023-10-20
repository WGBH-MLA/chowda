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
        response = await ac.post(
            '/api/sony_ci/sync',
            headers={'Authorization': f'Bearer {fake_access_token()}'},
        )

    assert response.status_code == 200
    assert SyncResponse(**response.json())


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
        response = await ac.post(
            '/api/sony_ci/sync',
            headers={'Authorization': f'Bearer {fake_access_token()}'},
        )

    assert response.status_code == 500
    response_json = response.json()
    assert response_json['detail']['error'] == 'Mocked exception'
