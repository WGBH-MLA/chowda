from sqlalchemy import create_engine
from .config import ENGINE_URI

engine = create_engine(ENGINE_URI, connect_args={'check_same_thread': False}, echo=True)


def create_async_engine():
    from sqlmodel.ext.asyncio.session import AsyncEngine

    return AsyncEngine(
        create_engine(ENGINE_URI, connect_args={'check_same_thread': False}, echo=True)
    )