from sqlalchemy import create_engine
from sqlmodel import SQLModel
from sqlmodel.pool import StaticPool
from chowda import models  # noqa F401
from chowda.config import ENVIRONMENT, DB_URL


def get_engine(env=ENVIRONMENT):
    """Return a SQLAlchemy engine for the given environment"""
    if env == 'test':
        return create_engine(
            'sqlite:///:memory:',
            connect_args={'check_same_thread': False},
            echo=True,
            poolclass=StaticPool,
        )
    if env == 'development':
        return create_engine(
            DB_URL,
            connect_args={'check_same_thread': False},
            echo=True,
        )
    if env == 'production':
        return create_engine(
            DB_URL, connect_args={'check_same_thread': True}, echo=False
        )
    raise Exception(f'Unknown environment: {env}')


engine = get_engine()


# Create database from SQLModel schema
SQLModel.metadata.create_all(engine)


# TODO: implement async engine
def create_async_engine():
    from sqlmodel.ext.asyncio.session import AsyncEngine

    return AsyncEngine(engine)
