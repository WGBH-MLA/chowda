from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends
from metaflow.integrations import ArgoEvent
from pydantic import BaseModel
from chowda.auth.utils import verified_access_token, OAuthAccessToken

sony_ci = APIRouter()


class SyncResponse(BaseModel):
    started_at: datetime


@sony_ci.post('/sync', tags=['sync'])
async def sony_ci_sync(
    token: Annotated[OAuthAccessToken, Depends(verified_access_token)]
) -> SyncResponse:
    try:
        ArgoEvent('sync').publish(ignore_errors=False)
        return SyncResponse(started_at=datetime.utcnow())
    except Exception as error:
        raise HTTPException(status_code=500, detail={'error': str(error)}) from error
