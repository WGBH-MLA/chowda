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


unauthorized = HTTPException(
    status_code=status.HTTP_303_SEE_OTHER,
    detail='Not Authorized',
    headers={'Location': '/admin'},
)


def user(request: Request):
    """Get the user token from the session."""
    user = request.session.get('user', None)
    if not user:
        request.session['error'] = 'Not Logged In'
        raise unauthorized
    return UserToken(**user)


def admin_user(request: Request, user: Annotated[UserToken, Depends(user)]):
    """Check if the user has the admin role."""
    if 'admin' not in user.roles:
        request.session['error'] = 'Not Authorized'
        raise unauthorized

    return user


dashboard = APIRouter(dependencies=[Depends(admin_user)])


@dashboard.post('/sync')
def sync_now(request: Request) -> Response:
    """Initiate a SonyCi IngestFlow with Argo Events."""
    admin_url = request.url_for('admin:index')
    try:
        ArgoEvent('sync').publish(ignore_errors=False)
        request.session['flash'] = 'Sync Started'
        return RedirectResponse(
            f'{admin_url}',
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as error:
        request.session['error'] = str(error)
        return RedirectResponse(f'{admin_url}', status_code=status.HTTP_303_SEE_OTHER)
