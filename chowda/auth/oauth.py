from typing import Optional
from urllib import request

from authlib.integrations.starlette_client import OAuth
from starlette.datastructures import URL
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route
from starlette_admin import BaseAdmin
from starlette_admin.auth import AdminUser, AuthMiddleware, AuthProvider

from chowda.config import (
    AUTH_CLIENT_ID,
    AUTH_CLIENT_SECRET,
    AUTH_OPENID_URL,
)

oauth = OAuth()
oauth.register(
    'authentik',
    client_id=AUTH_CLIENT_ID,
    client_secret=AUTH_CLIENT_SECRET,
    client_kwargs={
        'scope': 'openid profile email',
    },
    server_metadata_url=AUTH_OPENID_URL,
)


class OAuthProvider(AuthProvider):
    async def is_authenticated(self, request: Request) -> bool:
        if request.session.get('user', None) is not None:
            request.state.user = request.session.get('user')
            return True
        return False

    def get_admin_user(self, request: Request) -> Optional[AdminUser]:
        user = request.state.user
        return AdminUser(
            username=user['name'],
            photo_url=user.get('picture'),
        )

    async def render_login(self, request: Request, admin: BaseAdmin):
        """Override the default login behavior to implement custom logic."""
        auth = oauth.authentik
        redirect_uri = request.url_for(
            admin.route_name + ':authorize_auth'
        ).include_query_params(next=request.query_params.get('next'))
        return await auth.authorize_redirect(request, str(redirect_uri))

    async def render_logout(self, request: Request, admin: BaseAdmin) -> Response:
        """Override the default logout to implement custom logic"""
        request.session.clear()
        auth = oauth.authentik
        id_token = request.session.pop('id_token', None)
        # redirect_uri = request.url_for('index')
        return await auth.logout_redirect(
            request,
            post_logout_redirect_uri='/',
            id_token_hint=id_token,
        )

    async def handle_auth_callback(self, request: Request):
        auth = oauth.authentik
        token = await auth.authorize_access_token(request)
        request.session.update({'user': token['userinfo']})
        return RedirectResponse(request.query_params.get('next'))

    def setup_admin(self, admin: BaseAdmin):
        super().setup_admin(admin)
        """add custom authentication callback route"""
        admin.routes.append(
            Route(
                '/auth/authorize',
                self.handle_auth_callback,
                methods=['GET'],
                name='authorize_auth',
            )
        )

    def get_middleware(self, admin: BaseAdmin) -> Middleware:
        return Middleware(
            AuthMiddleware, provider=self, allow_paths=['/auth/authorize']
        )
