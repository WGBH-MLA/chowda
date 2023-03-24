from chowda.db import engine
from chowda.models import (
    MediaFile,
    Collection,
    ClamsApp,
    User,
    Pipeline,
    ClamsEvent,
    Batch
)
from pydantic_factories import (
    ModelFactory,
    SyncPersistenceProtocol,
    AsyncPersistenceProtocol,
)
from typing import TypeVar, List
from pydantic import BaseModel
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

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
    __allow_none_optionals__ = False
    __sync_persistence__ = SyncPersistenceHandler
    __async_persistence__ = AsyncPersistenceHandler


class MediaFileFactory(ChowdaFactory):
    __model__ = MediaFile


class CollectionFactory(ChowdaFactory):
    __model__ = Collection


class ClamsAppFactory(ChowdaFactory):
    __model__ = ClamsApp


class UserFactory(ChowdaFactory):
    __model__ = User


class PipelineFactory(ChowdaFactory):
    __model__ = Pipeline


class ClamsEventFactory(ChowdaFactory):
    __model__ = ClamsEvent


class BatchFactory(ChowdaFactory):
    __model__ = Batch
