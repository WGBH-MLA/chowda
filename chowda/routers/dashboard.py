from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from metaflow.integrations import ArgoEvent
from pydantic import BaseModel, Field
from starlette.responses import RedirectResponse, Response

from chowda.config import API_AUDIENCE


class UserToken(BaseModel):
    """ID Token model for authorization."""

    name: str
    email: str | None = None
    roles: set[str] = Field(set(), alias=f'{API_AUDIENCE}/roles')


dashboard = APIRouter()

unauthorized = HTTPException(
    status_code=status.HTTP_303_SEE_OTHER,
    detail='Not Authorized',
    headers={'Location': '/admin/?error=Not Authorized'},
)


def user(request: Request):
    """Get the user token from the session."""
    user = request.session.get('user', None)
    if not user:
        raise unauthorized
    return UserToken(**user)


def admin_user(user: Annotated[UserToken, Depends(user)]):
    """Check if the user has the admin role."""
    if 'admin' not in user.roles:
        raise unauthorized

    return user


@dashboard.post('/sync')
def sync_now(
    user: Annotated[UserToken, Depends(admin_user)], request: Request
) -> Response:
    """Initiate a SonyCi IngestFlow with Argo Events."""
    admin = request.url_for('admin:index')
    try:
        ArgoEvent('sync').publish(ignore_errors=False)
        return RedirectResponse(
            f'{admin}?flash=Sync started',
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as error:
        return RedirectResponse(
            f'{admin}?error={error!s}', status_code=status.HTTP_303_SEE_OTHER
        )
