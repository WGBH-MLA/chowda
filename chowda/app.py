"""App

Main Chowda application"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from starlette.routing import Route

from chowda._version import __version__
from chowda.admin import Admin
from chowda.api import api
from chowda.auth import OAuthProvider
from chowda.config import SECRET, STATIC_DIR, TEMPLATES_DIR
from chowda.db import engine
from chowda.models import (
    Batch,
    ClamsApp,
    ClamsEvent,
    Collection,
    MediaFile,
    Pipeline,
    SonyCiAsset,
    User,
)
from chowda.routers.dashboard import dashboard
from chowda.views import (
    BatchView,
    ClamsAppView,
    ClamsEventView,
    CollectionView,
    DashboardView,
    MediaFileView,
    PipelineView,
    SonyCiAssetView,
    UserView,
)

app = FastAPI(
    title='Chowda',
    version=__version__,
    routes=[
        Route(
            '/',
            lambda r: RedirectResponse('/admin'),
        )
    ],
    middleware=[Middleware(SessionMiddleware, secret_key=SECRET)],
)
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')

app.include_router(api, prefix='/api')
app.include_router(dashboard, prefix='/dashboard')


# Create admin
admin = Admin(
    engine,
    title='Chowda',
    templates_dir=TEMPLATES_DIR,
    statics_dir=STATIC_DIR,
    auth_provider=OAuthProvider(),
    base_url='/admin',
    index_view=DashboardView(label='Dashboard', icon='fa fa-gauge', path='/'),
)

# Add views
admin.add_view(MediaFileView(MediaFile, icon='fa fa-file-video'))
admin.add_view(SonyCiAssetView(SonyCiAsset, icon='fa fa-file-video'))
admin.add_view(CollectionView(Collection, icon='fa fa-folder'))
admin.add_view(BatchView(Batch, icon='fa fa-folder', label='Batches'))
admin.add_view(ClamsAppView(ClamsApp, icon='fa fa-box'))
admin.add_view(PipelineView(Pipeline, icon='fa fa-boxes-stacked'))
admin.add_view(ClamsEventView(ClamsEvent, icon='fa fa-file-lines'))
admin.add_view(UserView(User, icon='fa fa-users'))


# Mount admin to app
admin.mount_to(app)
