from sqlalchemy import create_engine
from .config import ENGINE_URI, PRODUCTION

connect_args = {}

if not PRODUCTION:
    connect_args['check_same_thread'] = False

engine = create_engine(ENGINE_URI, connect_args=connect_args, echo=not PRODUCTION)


def create_async_engine():
    from sqlmodel.ext.asyncio.session import AsyncEngine

    return AsyncEngine(
        create_engine(ENGINE_URI, connect_args=connect_args, echo=not PRODUCTION)
    )
