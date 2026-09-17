import json
from json import dumps

import pytest
from fastapi import status
from httpx import AsyncClient
from pytest_mock import MockerFixture


@pytest.fixture
def event():
    body = {'name': 'pipeline'}
    return {'body': dumps(body)}


@pytest.mark.asyncio
async def test_events(
    event: dict, async_client: AsyncClient, events_api_credentials: tuple[str, str]
):
    async with async_client as ac:
        response = await ac.post('/events/', json=event, auth=events_api_credentials)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_events_missing_credentials(
    event: dict, async_client: AsyncClient, events_api_credentials: tuple[str, str]
):
    async with async_client as ac:
        response = await ac.post('/events/', json=event)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers['WWW-Authenticate'] == 'Basic'


@pytest.mark.asyncio
async def test_events_wrong_username(
    event: dict, async_client: AsyncClient, events_api_credentials: tuple[str, str]
):
    async with async_client as ac:
        response = await ac.post(
            '/events/', json=event, auth=('wrong', events_api_credentials[1])
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers['WWW-Authenticate'] == 'Basic'
    error = json.loads(response.text)
    assert error['detail'] == 'Invalid credentials'


@pytest.mark.asyncio
async def test_events_wrong_password(
    event: dict, async_client: AsyncClient, events_api_credentials: tuple[str, str]
):
    async with async_client as ac:
        response = await ac.post(
            '/events/', json=event, auth=(events_api_credentials[0], 'wrong')
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = json.loads(response.text)
    assert error['detail'] == 'Invalid credentials'


@pytest.mark.asyncio
async def test_events_unconfigured_credentials(
    event: dict, async_client: AsyncClient, mocker: MockerFixture
):
    """Without credentials in the environment, the events API rejects everything,
    rather than letting anyone in."""
    mocker.patch('chowda.auth.utils.EVENTS_API_USERNAME', None)
    mocker.patch('chowda.auth.utils.EVENTS_API_PASSWORD', None)

    async with async_client as ac:
        response = await ac.post('/events/', json=event, auth=('', ''))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = json.loads(response.text)
    assert error['detail'] == 'Invalid credentials'
