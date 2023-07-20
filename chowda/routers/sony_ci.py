from datetime import datetime

from fastapi import APIRouter, HTTPException
from metaflow.integrations import ArgoEvent
from pydantic import BaseModel

sony_ci = APIRouter()


class SyncResponse(BaseModel):
    started_at: datetime


@sony_ci.post('/sync', tags=['sync'])
async def sony_ci_sync() -> SyncResponse:
    try:
        ArgoEvent('sync').publish(ignore_errors=False)
        return SyncResponse(started_at=datetime.utcnow())
    except Exception as error:
        raise HTTPException(status_code=500, detail={'error': str(error)}) from error
