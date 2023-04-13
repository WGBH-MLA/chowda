from sqlalchemy import create_engine
from sqlmodel import SQLModel
from sqlmodel.pool import StaticPool
from chowda import models
from chowda.config import ENVIRONMENT, DB_URL

# All engines for different environments
engines = {
    "test": create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        echo=True,
        poolclass=StaticPool,
    ),
    "development": create_engine(
        DB_URL,
        connect_args={'check_same_thread': False},
        echo=True,
    ),
    "production": create_engine(
        DB_URL, connect_args={'check_same_thread': True}, echo=False
    ),
}


# Set the db engine based on which environment we're in
# default is 'develpment' unless we're running tests (see above)
engine = engines.get(ENVIRONMENT)


# Create database from SQLModel schema
SQLModel.metadata.create_all(engine)


# TODO: implement async engine
def create_async_engine():
    from sqlmodel.ext.asyncio.session import AsyncEngine

    return AsyncEngine(engine)
