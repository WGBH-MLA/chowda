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

    # NOTE: models must be imported prior to calling SQL.metadata.create_all(engine)
    # Using this method to create the database schems is only temporary until we
    # replace it with a proper migration tool, e.g. Alembic. Disable Ruff linting
    # that flags unused imports: this import *is* used in the sense that once it's
    # imported, it lets SQLModel know about the schema behind the scenes, so that
    # the SQLModel.metadata.create_all(engine) command will actually create the db
    # tables.
    SQLModel.metadata.create_all(engine)
