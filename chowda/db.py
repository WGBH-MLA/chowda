from sqlalchemy import create_engine
from sqlmodel.pool import StaticPool
from chowda.config import DB_URL, DEBUG, ENVIRONMENT


engine = create_engine(DB_URL, echo=DEBUG)


# TODO: implement async engine
def create_async_engine():
    from sqlmodel.ext.asyncio.session import AsyncEngine

    return AsyncEngine(engine)
