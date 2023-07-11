from fastapi import APIRouter, HTTPException
from metaflow.integrations import ArgoEvent
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix='/sony_ci')


class SyncResponse(BaseModel):
    started_at: datetime


@router.post('/sync', tags=['sync'])
async def sony_ci_sync() -> SyncResponse:
    try:
        ArgoEvent('sync').publish(ignore_errors=False)
        return SyncResponse(started_at=datetime.utcnow())
    except Exception as error:
        raise HTTPException(status_code=500, detail={'error': str(error)}) from error
