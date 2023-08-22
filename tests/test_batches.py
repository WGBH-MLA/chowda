from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture
from sqlmodel import Session, select

from chowda.db import engine
from chowda.models import Batch


@fixture
def app():
    from chowda.app import app

    return app


@fixture
def client(app: FastAPI):
    return TestClient(app)


@async_fixture
async def async_client(app: FastAPI):
    async with AsyncClient(app=app, base_url='http://testserver') as c:
        yield c


@fixture
def session():
    return Session(engine)


@fixture
def unsaved_batch():
    from tests.factories import BatchFactory

    return BatchFactory.build()


@mark.anyio
@mark.skip("Redirecting due to user being unauthenticated in tests")
async def test_create_batch(
    async_client: AsyncClient,
    session: Session,
    unsaved_batch: Batch,
):
    response = await async_client.post(
        '/admin/batch/create',
        data=unsaved_batch.dict(),
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Batch).where(Batch.name == unsaved_batch.name)
    batch = session.execute(stmt).scalar_one()
    assert batch is not None
