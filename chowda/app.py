"""App

Main Chowda application"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqlmodel import ModelView

from chowda._version import __version__
from chowda.admin import Admin
from chowda.config import STATIC_DIR, TEMPLATES_DIR
from chowda.db import engine
from chowda.models import (
    Batch,
    ClamsApp,
    ClamsEvent,
    Collection,
    MediaFile,
    Pipeline,
    User,
)
from chowda.views import CollectionView


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
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')

# Create admin
admin = Admin(
    engine,
    title='Chowda',
    templates_dir=TEMPLATES_DIR,
    statics_dir=STATIC_DIR,
)

# Add views
admin.add_view(ModelView(User, icon='fa fa-users'))
admin.add_view(ModelView(MediaFile, icon='fa fa-file-video'))
admin.add_view(CollectionView(Collection, icon='fa fa-folder'))
admin.add_view(ModelView(ClamsApp, icon='fa fa-box'))
admin.add_view(ModelView(Pipeline, icon='fa fa-boxes-stacked'))
admin.add_view(ModelView(Batch, icon='fa fa-folder'))
admin.add_view(ModelView(ClamsEvent, icon='fa fa-file-lines'))

# Mount admin to app
admin.mount_to(app)
