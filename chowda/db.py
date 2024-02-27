from psycopg2.extensions import register_adapter
from pydantic_core import Url
from sqlalchemy import create_engine

from chowda.config import DB_URL, DEBUG
from chowda.utils import adapt_url

register_adapter(Url, adapt_url)

engine = create_engine(DB_URL, echo=DEBUG)


# TODO: implement async engine
def create_async_engine():
    from sqlmodel.ext.asyncio.session import AsyncEngine

    return AsyncEngine(engine)


def init_db():
    from sqlmodel import SQLModel

    from chowda import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
