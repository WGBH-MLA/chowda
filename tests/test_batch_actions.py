import pytest
from httpx import AsyncClient
from typing import Type, Callable



@pytest.mark.asyncio
async def test_batch_action_download_mmif(
    async_client: AsyncClient, set_session_data: Type[Callable]
):
    set_session_data({'user': 'foo'})

    async with async_client as ac:
        response = await ac.get(
            "/admin/api/batch/action", params={"name": "downlaod_mmif", "pks": [2, 3]}
        )
    assert response.status_code == 200
    assert response.json()["msg"] == "Downlaoded MMIF for Test Batch 1, Test Batch 2"
