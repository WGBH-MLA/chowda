from datetime import datetime, timezone
from typing import Any, Dict


from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from metaflow import Flow
from metaflow.exception import MetaflowNotFound
from metaflow.integrations import ArgoEvent
from pydantic import BaseModel

from chowda.auth.utils import permissions
from chowda.config import METAFLOW_URL

sony_ci = APIRouter(tags=['sony-ci'])


@cache(namespace='sonyci', expire=30)
async def sync_history(n: int = 3) -> list[Dict[str, Any]]:
    try:
        return [
            {
                'created_at': sync_run.created_at,
                'finished': sync_run.finished,
                'finished_at': sync_run.finished_at,
                'successful': sync_run.successful,
                'link': f'{METAFLOW_URL}/{sync_run.pathspec}',
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
        await FastAPICache.clear(namespace='sonyci')
        return SyncResponse(started_at=datetime.now(timezone.utc))
    except Exception as error:
        raise HTTPException(status_code=500, detail={'error': str(error)}) from error
