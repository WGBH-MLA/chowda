"""App

Main Chowda application"""

from fastapi import FastAPI
from sqlalchemy import create_engine
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqlmodel import Admin, ModelView

from sqlmodel import SQLModel

from .config import ENGINE_URI
from .models import User, MediaFile, Collection, ClamsApp, Pipeline, Batch, ClamsEvent
from ._version import __version__

engine = create_engine(ENGINE_URI, connect_args={'check_same_thread': False}, echo=True)


def init_database() -> None:
    SQLModel.metadata.create_all(engine)


app = FastAPI(
    title='Chowda',
    version=__version__,
    routes=[
        Route(
            '/',
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ],
    on_startup=[init_database],
)

# Create admin
admin = Admin(engine, title='Chowda')

# Add views
admin.add_view(ModelView(User, icon='fa fa-users'))
admin.add_view(ModelView(MediaFile, icon='fa fa-file-video'))
admin.add_view(ModelView(Collection, icon='fa fa-folder'))
admin.add_view(ModelView(ClamsApp, icon='fa fa-box'))
admin.add_view(ModelView(Pipeline, icon='fa fa-boxes-stacked'))
admin.add_view(ModelView(Batch, icon='fa fa-folder'))
admin.add_view(ModelView(ClamsEvent, icon='fa fa-file-lines'))

# Mount to admin to app
admin.mount_to(app)
