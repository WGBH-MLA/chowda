from chowda.app import engine
from chowda.config import ENGINE_URI
from chowda.models import MediaFile, Collection, ClamsApp
from pydantic_factories import (
    ModelFactory,
    SyncPersistenceProtocol,
    AsyncPersistenceProtocol,
)
from typing import TypeVar, List
from pydantic import BaseModel
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession, AsyncEngine

T = TypeVar("T", bound=BaseModel)


class SyncPersistenceHandler(SyncPersistenceProtocol[T]):
    def save(self, data: T) -> T:
        with Session(engine) as session:
            session.add(data)
            session.commit()

    def save_many(self, data: List[T]) -> List[T]:
        with Session(engine) as session:
            for d in data:
                session.add(d)
            session.commit()


class AsyncPersistenceHandler(AsyncPersistenceProtocol[T]):
    async def save(self, data: T) -> T:
        async with AsyncSession(engine) as session:
            session.add(data)
            await session.commit()

    async def save_many(self, data: List[T]) -> List[T]:
        async with AsyncSession(engine) as session:
            for d in data:
                session.add(d)
            await session.commit()


class ChowdaFactory(ModelFactory):
    __sync_persistence__ = SyncPersistenceHandler
    __async_persistence__ = AsyncPersistenceHandler


class MediaFileFactory(ChowdaFactory):
    __model__ = MediaFile


class CollectionFactory(ChowdaFactory):
    __model__ = Collection


class ClamsAppFactory(ChowdaFactory):
    __model__ = ClamsApp
