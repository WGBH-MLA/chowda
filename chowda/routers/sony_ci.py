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
    SonyCiAssetBase,
    SonyCiEvent,
    SonyCiEventType,
    SonyCiTrashbin,
)
from chowda.utils import find_media_file, upsert

sony_ci = APIRouter(tags=['sony-ci'])
sony_ci_events = APIRouter(tags=['sony-ci', 'event'])


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


def save_event(
    db: Session, event: EventRequest, assets: list[SonyCiAsset]
) -> SonyCiEvent:
    """Store a SonyCi event in the database, linked to the assets it touched.

    SonyCi retries deliveries, so an event that was already received is updated
    rather than duplicated."""
    ci_event = db.get(SonyCiEvent, event.id) or SonyCiEvent(id=event.id)
    ci_event.type = event.type
    ci_event.createdOn = event.createdOn
    ci_event.createdBy = event.createdBy
    ci_event.payload = event.model_dump(mode='json')
    for asset in assets:
        if asset not in ci_event.assets:
            ci_event.assets.append(asset)
    db.add(ci_event)
    db.commit()
    db.refresh(ci_event)
    return ci_event


def sync_asset(db: Session, client, asset_id: str) -> SonyCiAsset:
    """Fetch an asset from SonyCi and update it in the database."""
    # Table models skip validation, so the non-table base model is used to coerce the
    # JSON strings SonyCi sends into the datetimes and enums the columns expect.
    asset = SonyCiAssetBase.model_validate(client.asset(asset_id))
    existing = db.get(SonyCiAsset, asset_id)
    # The MediaFile link is not part of the SonyCi response, so keep the one we
    # already have, and otherwise link the asset by its filename.
    asset.media_file_id = existing.media_file_id if existing else None
    if not asset.media_file_id:
        media_file = find_media_file(db, asset.name)
        if media_file:
            asset.media_file_id = media_file.guid

    db.exec(upsert(SonyCiAsset, asset, ['id']))
    db.commit()
    return db.get(SonyCiAsset, asset_id)


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


@sony_ci_events.post('/sonyci')
def sony_ci_event(event: EventRequest) -> EventResponse:
    """Receive a webhook event from SonyCi.

    Every SonyCi asset the event references is updated, then the event is stored,
    linked to the assets it touched. Errors are reported in the response, but always
    with a 2xx status, so that SonyCi does not retry the event."""
    log.info(f'SonyCi event received: {event.type.value} {event.id}')
    response = EventResponse(id=event.id, type=event.type)
    client = None
    synced: list[SonyCiAsset] = []
    with Session(engine) as db:
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
                synced.append(sync_asset(db, client, asset.id))
                response.updated.append(asset.id)
            except Exception as error:  # NOQA BLE001
                log.exception(f'Error updating SonyCi asset {asset.id}: {error!s}')
                response.errors[asset.id] = str(error)
                db.rollback()
        save_event(db, event, synced)
    return response
