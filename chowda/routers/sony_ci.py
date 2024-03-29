from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from metaflow import Flow
from metaflow.exception import MetaflowNotFound
from metaflow.integrations import ArgoEvent
from pydantic import BaseModel

from chowda.auth.utils import permissions
from chowda.config import MARIO_URL

sony_ci = APIRouter()


# The startup / shutdown lifecycle events are deprecated, but the lifespan event handler
# does not currently work with APIRouter, even though it accepts the lifespan argument.
# https://github.com/tiangolo/fastapi/discussions/9664
@sony_ci.on_event('startup')
async def lifespan():
    FastAPICache.init(InMemoryBackend())
    await sync_history()


@cache(namespace='sonyci', expire=15 * 60)
async def sync_history(n: int = 3) -> Dict[str, Any]:
    try:
        return [
            {
                'created_at': sync_run.created_at,
                'finished': sync_run.finished,
                'finished_at': sync_run.finished_at,
                'successful': sync_run.successful,
                'link': MARIO_URL + sync_run.pathspec,
            }
            for sync_run in list(Flow('IngestFlow'))[:n]
        ]
    except MetaflowNotFound:
        return []


class SyncResponse(BaseModel):
    started_at: datetime


@sony_ci.post(
    '/sync', tags=['sync'], dependencies=[Depends(permissions('sync:sonyci'))]
)
async def sony_ci_sync() -> SyncResponse:
    try:
        ArgoEvent('sync').publish(ignore_errors=False)
        FastAPICache.clear(namespace='sonyci')
        return SyncResponse(started_at=datetime.utcnow())
    except Exception as error:
        raise HTTPException(status_code=500, detail={'error': str(error)}) from error
