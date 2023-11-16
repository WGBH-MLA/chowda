import pytest
from httpx import AsyncClient
from typing import Type, Callable
from chowda.config import AUTH0_API_AUDIENCE


@pytest.mark.asyncio
@pytest.mark.skip(reason="TODO: Setting session data for test is buggy")
async def test_download_mmif_as_clammer(
    async_client: AsyncClient, set_session_data: Type[Callable]
):
    set_session_data(
        {'user': {"name": "test user", f"{AUTH0_API_AUDIENCE}/roles": ["clammer"]}}
    )

    async with async_client as ac:
        response = await ac.get(
            "/admin/api/batch/action",
            params={"pks": [2, 3], "name": "download_mmif"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.skip(reason="TODO: Setting session data for test is buggy")
async def test_download_mmif_as_admin(
    async_client: AsyncClient, set_session_data: Type[Callable]
):
    set_session_data(
        {'user': {"name": "test user", f"{AUTH0_API_AUDIENCE}/roles": ["admin"]}}
    )

    async with async_client as ac:
        response = await ac.get(
            "/admin/api/batch/action",
            params={"pks": [2, 3], "name": "download_mmif"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.skip(reason="TODO: Setting session data for test is buggy")
async def test_download_mmif_unauthenticated(
    async_client: AsyncClient, set_session_data: Type[Callable]
):
    set_session_data(None)
    """Assumes no user is in the session; responds with 401 Unauthorized."""
    async with async_client as ac:
        response = await ac.get(
            "/admin/api/batch/action",
            params={"pks": [2, 3], "name": "download_mmif"},
        )
    assert response.status_code == 303


@pytest.mark.asyncio
@pytest.mark.skip(reason="TODO: Setting session data for test is buggy")
async def test_download_mmif_insufficient_role(
    async_client: AsyncClient, set_session_data: Type[Callable]
):
    set_session_data(
        {'user': {"name": "test user", f"{AUTH0_API_AUDIENCE}/roles": ["peon"]}}
    )

    async with async_client as ac:
        response = await ac.get(
            "/admin/api/batch/action",
            params={"pks": [2, 3], "name": "download_mmif"},
        )
    # NOTE: should probably be a 403 Forbidden, but BaseAdmin.handle_action
    # returns a 400
    assert response.status_code == 400
    assert response.json()['msg'] == 'Forbidden'
