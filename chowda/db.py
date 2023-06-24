from sqlalchemy import create_engine
from sqlmodel import SQLModel
from chowda.config import DB_URL, DEBUG
from chowda import models


engine = create_engine(DB_URL, echo=DEBUG)

# Create database from SQLModel schema
SQLModel.metadata.create_all(engine)


# TODO: implement async engine
def create_async_engine():
    from sqlmodel.ext.asyncio.session import AsyncEngine

    return AsyncEngine(engine)
