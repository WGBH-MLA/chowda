from typing import Annotated, List

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from chowda.config import AUTH0_API_AUDIENCE, AUTH0_JWKS_URL

unauthorized_redirect = HTTPException(
    status_code=status.HTTP_303_SEE_OTHER,
    detail='Not Authorized',
    headers={'Location': '/admin'},
)

unauthorized = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Not Authorized',
)


class OAuthAccessToken(BaseModel):
    """OAuth Authorization token"""

    sub: str
    permissions: List[str] = []


class OAuthUser(BaseModel):
    """ID Token model for authorization."""

    name: str
    email: str | None = None
    roles: set[str] = Field(set(), alias=f'{AUTH0_API_AUDIENCE}/roles')

    @property
    def is_admin(self) -> bool:
        """Check if the user has the admin role."""
        return 'admin' in self.roles

    @property
    def is_clammer(self) -> bool:
        """Check if the user has the clammer role."""
        return 'clammer' in self.roles


def get_oauth_user(request: Request) -> OAuthUser:
    """Get the user token from the session."""
    user = request.session.get('user', None)
    if not user:
        request.session['error'] = 'Not Logged In'
        raise unauthorized_redirect
    return OAuthUser(**user)


def get_admin_user(
    request: Request, user: Annotated[OAuthUser, Depends(get_oauth_user)]
) -> OAuthUser:
    """Check if the user has the admin role using FastAPI Depends.
    If not, sets a session error and raises an HTTPException."""
    if not user.is_admin:
        request.session['error'] = 'Not Authorized'
        raise unauthorized_redirect

    return user


def unverified_access_token(request: Request) -> str:
    """Extract and return the unverified access token from the Authorization header.
    Raises an HTTPUnauthorizedException if the header is missing or malformed."""
    auth_header = request.headers.get('Authorization', None)

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=401,
            detail="Bearer token malformed or missing in Authorization header",
        )

    # Return the access token from the Authorization header,
    # i.e. the string without the "Bearer " prefix
    return auth_header.replace('Bearer ', '')


def jwt_signing_key(
    unverified_access_token: Annotated[str, Depends(unverified_access_token)]
) -> str:
    """Get the JWT signing key from the JWKS URL."""
    from jwt import PyJWKClient

    jwks_client = PyJWKClient(AUTH0_JWKS_URL)
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(unverified_access_token)
        return signing_key.key

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


def verified_access_token(
    request: Request,
    unverified_access_token: Annotated[str, Depends(unverified_access_token)],
    jwt_signing_key: Annotated[str, Depends(jwt_signing_key)],
) -> OAuthAccessToken:
    """Decodes and verifies an access token. If any exceptions occur, an
    HTTPUnauthorizedException is raised from the original exception."""
    from jwt import decode

    try:
        decoded_token = decode(
            unverified_access_token,
            jwt_signing_key,
            algorithms=['RS256', 'HS256'],
            audience='https://chowda.wgbh-mla.org/api',
        )
        return OAuthAccessToken(**decoded_token)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


def permissions(permissions: List[str]) -> None:
    """Dependency function to check if token has required permissions.

    Args:
        permissions (List[str]): List of required permissions
    Examples:
        @app.get('/users/', dependencies=[Depends(permissions(['read:user']))])


    """

    def _permissions(
        token: Annotated[OAuthAccessToken, Depends(verified_access_token)],
    ) -> None:
        """Check if user has required permissions."""
        missing_permissions = set(permissions) - set(token.permissions)
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Missing required permissions: {missing_permissions}',
            )

    return _permissions
