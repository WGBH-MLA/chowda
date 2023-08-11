from fastapi import APIRouter, Depends, Request, status
from metaflow.integrations import ArgoEvent
from starlette.responses import RedirectResponse, Response

from chowda.auth.utils import admin_user

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
