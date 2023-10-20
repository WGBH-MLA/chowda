from httpx import AsyncClient
import pytest

from chowda.app import app


@pytest.fixture
def userinfo_in_session(async_client: AsyncClient):
    async_client.session


@pytest.mark.asyncio
async def test_batch_action_download_mmif(async_client: AsyncClient):
    async with async_client as ac:
        response = await ac.get(
            "/admin/api/batch/action", params={"name": "downlaod_mmif", "pks": [2, 3]}
        )
    assert response.status_code == 200
    assert response.json()["msg"] == "Downlaoded MMIF for Test Batch 1, Test Batch 2"
