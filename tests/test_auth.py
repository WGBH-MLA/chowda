"""Tests for the access token authorization of the /api routes."""

import json

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_missing_auth_header(async_client: AsyncClient):
    async with async_client as ac:
        response = await ac.post('/api/sonyci/sync')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = json.loads(response.text)
    assert error['detail'] == 'Missing Authorization header'


@pytest.mark.asyncio
async def test_api_malformed_auth_header(async_client: AsyncClient):
    async with async_client as ac:
        response = await ac.post(
            '/api/sonyci/sync',
            headers={'Authorization': 'not a bearer token'},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = json.loads(response.text)
    assert (
        error['detail'] == 'Bearer token malformed or missing in Authorization header'
    )


@pytest.mark.asyncio
async def test_api_invalid_bearer_token(async_client: AsyncClient):
    async with async_client as ac:
        response = await ac.post(
            '/api/sonyci/sync',
            headers={'Authorization': 'Bearer N0t.AR3al.TOKeN'},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = json.loads(response.text)
    assert 'Invalid header' in error['detail']


@pytest.mark.asyncio
async def test_api_valid_unauthorized_bearer_token(async_client: AsyncClient):
    async with async_client as ac:
        response = await ac.post(
            '/api/sonyci/sync',
            headers={
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
            },
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = json.loads(response.text)
    assert error['detail'] == 'Signature verification failed'
