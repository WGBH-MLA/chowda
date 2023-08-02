from starlette.responses import Response, RedirectResponse
from metaflow.integrations import ArgoEvent
from starlette.routing import Route, Router


def sync_now(request) -> Response:
    flash = error = ''
    try:
        ArgoEvent('sync').publish(ignore_errors=False)
        flash = 'Sync Started'
    except Exception as e:
        error = str(e)

    return RedirectResponse(f'/dashboard?error={error}&flash={flash}', status_code=303)


dashboard_router = Router(
    routes=[
        Route('/sync_now', sync_now, methods=['POST']),
    ],
)
