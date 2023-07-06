from sqlalchemy import create_engine

from chowda.config import DB_URL, DEBUG

engine = create_engine(DB_URL, echo=DEBUG)


# TODO: implement async engine
def create_async_engine():
    from sqlmodel.ext.asyncio.session import AsyncEngine

    return AsyncEngine(engine)


def init_db():
    from sqlmodel import SQLModel

    from chowda import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
