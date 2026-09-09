from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from metaflow import Flow
from metaflow.exception import MetaflowException
from metaflow.integrations import ArgoEvent
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session

from chowda.auth.utils import permissions
from chowda.config import METAFLOW_URL
from chowda.db import engine
from chowda.log import log
from chowda.models import (
    SonyCiAsset,
    SonyCiEvent,
    SonyCiEventType,
    SonyCiTrashbin,
)
from chowda.utils import upsert

sony_ci = APIRouter(tags=['sony-ci'])


@cache(namespace='sonyci', expire=30)
async def sync_history(n: int = 3) -> list[dict[str, Any]]:
    try:
        flow = Flow('IngestFlow')

    except MetaflowException as error:

        log.error(f'Error fetching sync history: {error!s}')
        return []
    return [
        {
            'created_at': sync_run.created_at,
            'finished': sync_run.finished,
            'finished_at': sync_run.finished_at,
            'successful': sync_run.successful,
            'link': f'{METAFLOW_URL}/{sync_run.pathspec}',
        }
        for sync_run in list(flow)[:n]
    ]


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


class EventAsset(BaseModel):
    """An asset referenced by a SonyCi event."""

    id: str
    name: str | None = None


class EventRequest(BaseModel):
    """A webhook event sent by SonyCi.

    Unknown keys are kept, so that the complete event can be stored.
    """

    model_config = ConfigDict(extra='allow')

    id: str
    type: SonyCiEventType
    createdOn: datetime | None = None
    createdBy: dict[str, Any] | None = None
    assets: list[EventAsset] = []


class EventResponse(BaseModel):
    """The result of processing a SonyCi event."""

    id: str
    type: SonyCiEventType
    updated: list[str] = []
    trashed: list[str] = []
    deleted: list[str] = []
    errors: dict[str, str] = {}


def sony_ci_client():
    """Create a SonyCi client from the environment."""
    from sonyci import SonyCi

    client = SonyCi(**SonyCi.from_env())
    client.login()
    return client


def save_event(db: Session, event: EventRequest) -> SonyCiEvent:
    """Store a SonyCi event in the database.

    SonyCi retries deliveries, so an event that was already received is updated
    rather than duplicated."""
    ci_event = db.get(SonyCiEvent, event.id) or SonyCiEvent(id=event.id)
    ci_event.type = event.type
    ci_event.createdOn = event.createdOn
    ci_event.createdBy = event.createdBy
    ci_event.payload = event.model_dump(mode='json')
    db.add(ci_event)
    db.commit()
    db.refresh(ci_event)
    return ci_event


def sync_asset(db: Session, client, ci_event: SonyCiEvent, asset_id: str) -> None:
    """Fetch an asset from SonyCi, update it in the database, and link it to the
    event."""
    asset = SonyCiAsset(**client.asset(asset_id))
    existing = db.get(SonyCiAsset, asset_id)
    if existing:
        # The MediaFile link is not part of the SonyCi response, so keep the one
        # we already have.
        asset.media_file_id = existing.media_file_id
    db.exec(upsert(SonyCiAsset, asset, ['id']))
    db.commit()
    updated_asset = db.get(SonyCiAsset, asset_id)
    if updated_asset not in ci_event.assets:
        ci_event.assets.append(updated_asset)
        db.add(ci_event)
        db.commit()


def trash_asset(db: Session, asset_id: str, trashed_on: datetime | None) -> bool:
    """Move a SonyCiAsset into the trashbin. Returns False if it was not found."""
    asset = db.get(SonyCiAsset, asset_id)
    if not asset:
        return False
    values = asset.model_dump()
    values['isTrashed'] = True
    db.exec(
        upsert(SonyCiTrashbin, SonyCiTrashbin(**values, trashedOn=trashed_on), ['id'])
    )
    db.delete(asset)
    db.commit()
    return True


def delete_asset(db: Session, asset_id: str) -> bool:
    """Delete an asset, and any trashbin entry for it. Returns False if neither was
    found."""
    rows = [db.get(model, asset_id) for model in (SonyCiAsset, SonyCiTrashbin)]
    rows = [row for row in rows if row]
    for row in rows:
        db.delete(row)
    db.commit()
    return bool(rows)


@sony_ci.post(
    '/event', tags=['event'], dependencies=[Depends(permissions('create:event'))]
)
def sony_ci_event(event: EventRequest) -> EventResponse:
    """Receive a webhook event from SonyCi.

    The event is stored in the database, then every SonyCi asset it references is
    updated. Errors are reported in the response, but always with a 2xx status, so
    that SonyCi does not retry the event."""
    log.info(f'SonyCi event received: {event.type.value} {event.id}')
    response = EventResponse(id=event.id, type=event.type)
    client = None
    with Session(engine) as db:
        ci_event = save_event(db, event)
        for asset in event.assets:
            try:
                if event.type == SonyCiEventType.DeleteAsset:
                    if delete_asset(db, asset.id):
                        response.deleted.append(asset.id)
                    continue
                if event.type == SonyCiEventType.TrashAsset:
                    if trash_asset(db, asset.id, event.createdOn):
                        response.trashed.append(asset.id)
                    continue
                if client is None:
                    client = sony_ci_client()
                sync_asset(db, client, ci_event, asset.id)
                response.updated.append(asset.id)
            except Exception as error:  # NOQA BLE001
                log.error(f'Error updating SonyCi asset {asset.id}: {error!s}')
                response.errors[asset.id] = str(error)
                db.rollback()
    return response
