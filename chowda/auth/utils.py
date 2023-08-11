from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from chowda.config import API_AUDIENCE


class UserToken(BaseModel):
    """ID Token model for authorization."""

    name: str
    email: str | None = None
    roles: set[str] = Field(set(), alias=f'{API_AUDIENCE}/roles')

    @property
    def is_admin(self) -> bool:
        """Check if the user has the admin role."""
        return 'admin' in self.roles

    @property
    def is_clammer(self) -> bool:
        """Check if the user has the clammer role."""
        return 'clammer' in self.roles


unauthorized = HTTPException(
    status_code=status.HTTP_303_SEE_OTHER,
    detail='Not Authorized',
    headers={'Location': '/admin'},
)


def get_user(request: Request) -> UserToken:
    """Get the user token from the session."""
    user = request.session.get('user', None)
    if not user:
        request.session['error'] = 'Not Logged In'
        raise unauthorized
    return UserToken(**user)


def admin_user(
    request: Request, user: Annotated[UserToken, Depends(get_user)]
) -> UserToken:
    """Check if the user has the admin role using FastAPI Depends.
    If not, sets a session error and raises an HTTPException."""
    if not user.is_admin:
        request.session['error'] = 'Not Authorized'
        raise unauthorized

    return user
