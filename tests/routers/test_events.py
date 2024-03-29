import json
from json import dumps

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.fixture
def event():
    body = {'name': 'pipeline'}
    return {'body': dumps(body)}


@pytest.mark.asyncio
async def test_events(event: dict, async_client: AsyncClient, fake_access_token: str):
    async with async_client as ac:
        bearer_token = fake_access_token(permissions=["create:event"])
        response = await ac.post(
            '/api/event/',
            json=event,
            follow_redirects=True,
            headers={'Authorization': f'Bearer {bearer_token}'},
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_events_missing_auth_header(event: dict, async_client: AsyncClient):
    async with async_client as ac:
        response = await ac.post('/api/event/', json=event, follow_redirects=True)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = json.loads(response.text)
    assert error['detail'] == 'Missing Authorization header'


@pytest.mark.asyncio
async def test_events_malformed_auth_header(event: dict, async_client: AsyncClient):
    async with async_client as ac:
        response = await ac.post(
            '/api/event/',
            json=event,
            follow_redirects=True,
            headers={'Authorization': 'not a bearer token'},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = json.loads(response.text)
    assert (
        error['detail'] == 'Bearer token malformed or missing in Authorization header'
    )


@pytest.mark.asyncio
async def test_events_invalid_bearer_token(event: dict, async_client: AsyncClient):
    async with async_client as ac:
        response = await ac.post(
            '/api/event/',
            json=event,
            follow_redirects=True,
            headers={'Authorization': 'Bearer N0t.AR3al.TOKeN'},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = json.loads(response.text)
    assert 'Invalid header string' in error['detail']


@pytest.mark.asyncio
async def test_events_valid_unauthorized_bearer_token(
    event: dict, async_client: AsyncClient
):
    async with async_client as ac:
        response = await ac.post(
            '/api/event/',
            json=event,
            follow_redirects=True,
            headers={
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'  # noqa E501
            },
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = json.loads(response.text)
    assert error['detail'] == 'Signature verification failed'


@pytest.mark.asyncio
async def test_events_without_permission(
    event: dict, async_client: AsyncClient, fake_access_token: str
):
    async with async_client as ac:
        response = await ac.post(
            '/api/event/',
            json=event,
            follow_redirects=True,
            headers={
                'Authorization': f'Bearer {fake_access_token(permissions=["wrong"])}'
            },
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
