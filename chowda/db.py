from sqlalchemy import create_engine
from .config import DB_URL, ENVIRONMENT, ECHO

connect_args = {'check_same_thread': False}


if ENVIRONMENT == 'production':
    ECHO = False

if ENVIRONMENT == 'test':
    DB_URL = 'sqlite:///:memory:'


engine = create_engine(DB_URL, connect_args=connect_args, echo=ECHO)


def create_async_engine():
    from sqlmodel.ext.asyncio.session import AsyncEngine

    return AsyncEngine(create_engine(DB_URL, connect_args=connect_args, echo=ECHO))
