from typing import Optional

from authlib.integrations.starlette_client import OAuth
from starlette.datastructures import URL
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route
from starlette_admin import BaseAdmin
from starlette_admin.auth import AdminUser, AuthMiddleware, AuthProvider

from chowda.config import (
    AUTH_API_AUDIENCE,
    AUTH_CLIENT_ID,
    AUTH_CLIENT_SECRET,
    AUTH_DOMAIN,
    AUTH_METADATA_CONFIG,
    AUTH_ACCESS_TOKEN_PATH,
    AUTH_AUTHORIZATION_PATH,
    AUTH_LOGOUT_PATH,
)

oauth = OAuth()
oauth.register(
    'authentik',
    client_id=AUTH_CLIENT_ID,
    client_secret=AUTH_CLIENT_SECRET,
    access_token_url=f'{AUTH_DOMAIN}/{AUTH_ACCESS_TOKEN_PATH}',
    client_kwargs={
        'scope': 'openid profile email',
    },
    server_metadata_url=f'{AUTH_DOMAIN}/{AUTH_METADATA_CONFIG}',
    authorize_params={'audience': AUTH_API_AUDIENCE},
    authorize_url=f'{AUTH_DOMAIN}/{AUTH_AUTHORIZATION_PATH}',
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
        return RedirectResponse(
            url=URL(f'{AUTH_DOMAIN}/{AUTH_LOGOUT_PATH}').include_query_params(
                returnTo=request.url_for(admin.route_name + ':index'),
                client_id=AUTH_CLIENT_ID,
            )
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
