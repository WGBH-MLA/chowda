from fastapi import APIRouter

from chowda.routers import events, sony_ci

api = APIRouter()

api.include_router(events, prefix='/event')
api.include_router(sony_ci, prefix='/sonyci')
# Legacy prefix, kept so existing SonyCi API clients keep working.
api.include_router(sony_ci, prefix='/sony_ci', include_in_schema=False)
