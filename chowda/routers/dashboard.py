from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from metaflow.integrations import ArgoEvent
from pydantic import BaseModel, Field
from starlette.responses import RedirectResponse, Response

from chowda.config import API_AUDIENCE


class User(BaseModel):
    name: str
    email: str | None = None
    roles: set[str] = Field(set(), alias=f'{API_AUDIENCE}/roles')


dashboard = APIRouter()


def user(request: Request):
    user = request.session.get('user', None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not Authorized',
        )
    return User(**user)


def admin_user(user: Annotated[User, Depends(user)]):
    if 'admin' not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not Authorized',
        )

    return user


@dashboard.post('/sync')
def sync_now(user: Annotated[User, Depends(admin_user)]) -> Response:
    flash = error = ''
    try:
        ArgoEvent('sync').publish(ignore_errors=False)
        flash = 'Sync Started'
    except Exception as e:
        error = str(e)

    return RedirectResponse(f'/dashboard?error={error}&flash={flash}', status_code=303)
