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


def user(request: Request):
    """Get the user token from the session."""
    user = request.session.get('user', None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not Authorized',
        )
    return UserToken(**user)


def admin_user(user: Annotated[UserToken, Depends(user)]):
    """Check if the user has the admin role."""
    if 'admin' not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not Authorized',
        )

    return user


@dashboard.post('/sync')
def sync_now(user: Annotated[UserToken, Depends(admin_user)]) -> Response:
    """Initiate a SonyCi IngestFlow with Argo Events."""
    try:
        ArgoEvent('sync').publish(ignore_errors=False)
        return RedirectResponse(f'/admin/?flash={"Sync started"}', status_code=303)
    except Exception as error:
        return RedirectResponse(f'/admin/?error={error!s}', status_code=303)
