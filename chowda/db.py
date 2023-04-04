from sqlalchemy import create_engine
from sqlmodel import SQLModel
from chowda.models import MediaFile, Collection, Batch, ClamsApp, Pipeline, ClamsEvent
import os

# All engines for different environments
engines = {
    "test": create_engine(
        'sqlite:///:memory:', connect_args={'check_same_thread': False}, echo=True
    ),
    "development": create_engine(
        'sqlite:///chowda.development.sqlite',
        connect_args={'check_same_thread': False},
        echo=True,
    ),
    # "production": create_engine(ENGINE_URI, connect_args={'check_same_thread': True}, echo=False)
}


# Set the db engine based on which environment we're in, default is 'develpment' unless we're running tests (see above)
engine = engines.get(os.environ.get('ENVIRONMENT', 'development'))

# Create database from SQLModel schema
SQLModel.metadata.create_all(engine)


# TODO: used anywhere yet?
def create_async_engine():
    from sqlmodel.ext.asyncio.session import AsyncEngine

    return AsyncEngine(engine)
