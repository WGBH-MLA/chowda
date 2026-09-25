import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from httpx import AsyncClient
from metaflow.plugins.argo.argo_events import ArgoEventException
from pytest_mock import MockerFixture
from sqlmodel import Session, select

from chowda.db import engine
from chowda.models import (
    AssetType,
    MediaFile,
    SonyCiArchiveStatus,
    SonyCiAsset,
    SonyCiAssetStatus,
    SonyCiEvent,
    SonyCiEventType,
    SonyCiTrashbin,
    SonyCiUploadTransferType,
)
from chowda.routers.sony_ci import SyncResponse


@pytest.mark.asyncio
async def test_sony_ci_sync(
    mocker: MockerFixture, async_client: AsyncClient, fake_access_token: type[callable]
):
    mocker.patch('metaflow.integrations.ArgoEvent.publish')
    mocker.patch('fastapi_cache.FastAPICache.clear')

    async with async_client as ac:
        bearer_token = fake_access_token(permissions=['sync:sonyci'])
        response = await ac.post(
            '/api/sonyci/sync',
            headers={'Authorization': f'Bearer {bearer_token}'},
        )

    assert response.status_code == 200
    sync_response = SyncResponse(**response.json())
    assert sync_response.started_at is not None


@pytest.mark.asyncio
async def test_sony_ci_sync_no_permission(
    async_client: AsyncClient, fake_access_token: type[callable]
):
    async with async_client as ac:
        bearer_token = fake_access_token(permissions=['wrong_permission:sonyci'])
        response = await ac.post(
            '/api/sonyci/sync', headers={'Authorization': f'Bearer {bearer_token}'}
        )

    assert response.status_code == 403
    response_json = response.json()
    error = response_json['detail']
    assert 'Missing required permissions:' in error
    assert "{'sync:sonyci'}" in error


@pytest.mark.asyncio
async def test_sony_ci_sync_fail(
    mocker: MockerFixture, async_client: AsyncClient, fake_access_token: type[callable]
):
    mocker.patch(
        'metaflow.integrations.ArgoEvent.publish',
        side_effect=ArgoEventException('Mocked exception'),
    )
    async with async_client as ac:
        bearer_token = fake_access_token(permissions=['sync:sonyci'])
        response = await ac.post(
            '/api/sonyci/sync',
            headers={
                'Authorization': f'Bearer {bearer_token}',
            },
        )

    assert response.status_code == 500
    response_json = response.json()
    assert response_json['detail']['error'] == 'Mocked exception'


@pytest.fixture
def sony_ci_ids(request) -> dict[str, str]:
    """SonyCi event and asset ids that are unique to each test, and are removed from
    the database before and after the test runs."""
    ids = {'event': f'event-{request.node.name}', 'asset': f'asset-{request.node.name}'}

    def clean():
        with Session(engine) as db:
            rows = [
                db.get(SonyCiEvent, ids['event']),
                db.get(SonyCiAsset, ids['asset']),
                db.get(SonyCiTrashbin, ids['asset']),
            ]
            for row in rows:
                if row:
                    db.delete(row)
            db.commit()

    clean()
    yield ids
    clean()


def sony_ci_event(
    ids: dict[str, str], event_type: str = 'AssetProcessingFinished'
) -> dict:
    """A SonyCi webhook event, as sent by the SonyCi notification API."""
    return {
        'id': ids['event'],
        'type': event_type,
        'createdOn': '2026-01-02T00:00:00.000Z',
        'createdBy': {
            'id': 'c460dfc1447f4240b14b2f32ce8d4a5f',
            'name': 'Julia Child',
            'email': 'juliachild@wgbh.org',
        },
        'assets': [{'id': ids['asset'], 'name': 'cpb-aacip-1234.mp4'}],
    }


def sony_ci_asset(ids: dict[str, str]) -> dict:
    """An asset, as returned by the SonyCi asset API."""
    return {
        'id': ids['asset'],
        'name': 'cpb-aacip-1234.mp4',
        'size': 1234,
        'type': 'Video',
        'status': 'Complete',
    }


def complete_sony_ci_asset(ids: dict[str, str]) -> dict:
    """A complete asset response, captured from the SonyCi asset API."""
    asset = json.loads((Path(__file__).parent / 'asset.json').read_text())
    asset['id'] = ids['asset']
    return asset


async def post_event(
    async_client: AsyncClient,
    credentials: tuple[str, str],
    event: dict,
    url: str = '/events/sonyci',
):
    async with async_client as ac:
        return await ac.post(url, json=event, auth=credentials)


@pytest.mark.asyncio
async def test_sony_ci_event(
    mocker: MockerFixture,
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """The event is stored, and the assets it references are updated."""
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client').return_value
    client.asset.return_value = sony_ci_asset(sony_ci_ids)

    response = await post_event(
        async_client,
        events_api_credentials,
        sony_ci_event(sony_ci_ids),
    )

    assert response.status_code == 200
    assert response.json() == {
        'id': sony_ci_ids['event'],
        'type': 'AssetProcessingFinished',
        'updated': [sony_ci_ids['asset']],
        'trashed': [],
        'deleted': [],
        'errors': {},
    }
    client.asset.assert_called_once_with(sony_ci_ids['asset'])

    with Session(engine) as db:
        event = db.get(SonyCiEvent, sony_ci_ids['event'])
        assert event.type == SonyCiEventType.AssetProcessingFinished
        assert event.createdOn == datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc)
        assert event.createdBy['email'] == 'juliachild@wgbh.org'
        assert event.payload['assets'] == [
            {'id': sony_ci_ids['asset'], 'name': 'cpb-aacip-1234.mp4'}
        ]
        assert event.created_at is not None
        assert [asset.id for asset in event.assets] == [sony_ci_ids['asset']]
        assert db.get(SonyCiAsset, sony_ci_ids['asset']).name == 'cpb-aacip-1234.mp4'


@pytest.mark.asyncio
async def test_sony_ci_event_keeps_media_file(
    mocker: MockerFixture,
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """Updating an asset does not drop the MediaFile it is linked to, since SonyCi
    knows nothing about MediaFiles."""
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client').return_value
    client.asset.return_value = sony_ci_asset(sony_ci_ids)
    guid = f'cpb-aacip-{sony_ci_ids["asset"]}'
    with Session(engine) as db:
        db.add(MediaFile(guid=guid))
        db.add(
            SonyCiAsset(
                **{**sony_ci_asset(sony_ci_ids), 'name': 'old name'}, media_file_id=guid
            )
        )
        db.commit()

    response = await post_event(
        async_client,
        events_api_credentials,
        sony_ci_event(sony_ci_ids),
    )

    assert response.status_code == 200
    with Session(engine) as db:
        asset = db.get(SonyCiAsset, sony_ci_ids['asset'])
        assert asset.name == 'cpb-aacip-1234.mp4'
        assert asset.media_file_id == guid
        db.delete(db.get(SonyCiEvent, sony_ci_ids['event']))
        db.delete(asset)
        db.commit()
        db.delete(db.get(MediaFile, guid))
        db.commit()


@pytest.mark.asyncio
# A pydantic serializer warning means raw JSON strings are being sent to the
# database instead of the datetimes and enums the columns expect.
@pytest.mark.filterwarnings('error::UserWarning')
async def test_sony_ci_event_creates_asset(
    mocker: MockerFixture,
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """Every field of a complete SonyCi asset response is stored."""
    asset = complete_sony_ci_asset(sony_ci_ids)
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client').return_value
    client.asset.return_value = asset
    event = sony_ci_event(sony_ci_ids)
    event['assets'][0]['name'] = asset['name']

    response = await post_event(async_client, events_api_credentials, event)

    assert response.status_code == 200
    assert response.json()['errors'] == {}
    assert response.json()['updated'] == [sony_ci_ids['asset']]
    with Session(engine) as db:
        stored = db.get(SonyCiAsset, sony_ci_ids['asset'])
        assert stored is not None
        assert stored.name == 'Amex_604_barcode326978.mp4'
        assert stored.size == 107390168
        assert stored.type == AssetType.Video
        assert stored.status == SonyCiAssetStatus.Complete
        assert stored.archiveStatus == SonyCiArchiveStatus.NotArchived
        assert stored.uploadTransferType == SonyCiUploadTransferType.MultipartHttp
        assert stored.createdOn == datetime(
            2026, 9, 22, 18, 33, 50, 465000, tzinfo=timezone.utc
        )
        assert stored.runtime == 1230.229
        # The filename is not a GUID, so the asset is not linked to a MediaFile.
        assert stored.media_file_id is None


@pytest.mark.asyncio
async def test_sony_ci_event_links_media_file(
    mocker: MockerFixture,
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """An asset that is not yet linked to a MediaFile is linked by its filename,
    even when the asset is already in the database."""
    guid = 'cpb-aacip-chowda-test-link'
    asset = {**sony_ci_asset(sony_ci_ids), 'name': f'{guid}.mp4'}
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client').return_value
    client.asset.return_value = asset
    with Session(engine) as db:
        db.add(MediaFile(guid=guid))
        db.add(SonyCiAsset(**{**asset, 'name': 'old name'}))
        db.commit()

    event = sony_ci_event(sony_ci_ids, event_type='MoveAsset')
    event['assets'][0]['name'] = asset['name']
    response = await post_event(async_client, events_api_credentials, event)

    assert response.status_code == 200
    assert response.json()['errors'] == {}
    with Session(engine) as db:
        stored = db.get(SonyCiAsset, sony_ci_ids['asset'])
        assert stored.media_file_id == guid
        db.delete(db.get(SonyCiEvent, sony_ci_ids['event']))
        db.delete(stored)
        db.commit()
        db.delete(db.get(MediaFile, guid))
        db.commit()


@pytest.mark.asyncio
async def test_sony_ci_event_creates_media_file(
    mocker: MockerFixture,
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """An asset with a GUID filename gets a new MediaFile when there is none yet,
    the same way the ingest flow creates one."""
    guid = 'cpb-aacip-chowda-test-new'
    asset = {**sony_ci_asset(sony_ci_ids), 'name': f'{guid}.mp4'}
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client').return_value
    client.asset.return_value = asset
    with Session(engine) as db:
        leftover = db.get(MediaFile, guid)
        if leftover:
            db.delete(leftover)
            db.commit()

    event = sony_ci_event(sony_ci_ids)
    event['assets'][0]['name'] = asset['name']
    response = await post_event(async_client, events_api_credentials, event)

    assert response.status_code == 200
    assert response.json()['errors'] == {}
    with Session(engine) as db:
        stored = db.get(SonyCiAsset, sony_ci_ids['asset'])
        assert stored.media_file_id == guid
        media_file = db.get(MediaFile, guid)
        assert [linked.id for linked in media_file.assets] == [sony_ci_ids['asset']]
        db.delete(db.get(SonyCiEvent, sony_ci_ids['event']))
        db.delete(stored)
        db.commit()
        db.delete(media_file)
        db.commit()


@pytest.mark.asyncio
async def test_sony_ci_event_is_not_duplicated(
    mocker: MockerFixture,
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """SonyCi retries events, so receiving the same event twice updates it."""
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client').return_value
    client.asset.return_value = sony_ci_asset(sony_ci_ids)
    event = sony_ci_event(sony_ci_ids)

    async with async_client as ac:
        first = await ac.post('/events/sonyci', json=event, auth=events_api_credentials)
        second = await ac.post(
            '/events/sonyci', json=event, auth=events_api_credentials
        )

    assert first.status_code == 200
    assert second.status_code == 200
    with Session(engine) as db:
        events = db.exec(
            select(SonyCiEvent).where(SonyCiEvent.id == sony_ci_ids['event'])
        ).all()
        assert len(events) == 1
        assert [asset.id for asset in events[0].assets] == [sony_ci_ids['asset']]


@pytest.mark.asyncio
async def test_sony_ci_event_trash_asset(
    mocker: MockerFixture,
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """A TrashAsset event moves the asset into the trashbin."""
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client')
    with Session(engine) as db:
        db.add(SonyCiAsset(**sony_ci_asset(sony_ci_ids)))
        db.commit()

    response = await post_event(
        async_client,
        events_api_credentials,
        sony_ci_event(sony_ci_ids, event_type='TrashAsset'),
    )

    assert response.status_code == 200
    assert response.json()['trashed'] == [sony_ci_ids['asset']]
    client.assert_not_called()
    with Session(engine) as db:
        assert db.get(SonyCiAsset, sony_ci_ids['asset']) is None
        trashed = db.get(SonyCiTrashbin, sony_ci_ids['asset'])
        assert trashed.name == 'cpb-aacip-1234.mp4'
        assert trashed.isTrashed
        assert trashed.trashedOn == datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_sony_ci_event_delete_asset(
    mocker: MockerFixture,
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """A DeleteAsset event removes the asset from the database."""
    mocker.patch('chowda.routers.sony_ci.sony_ci_client')
    with Session(engine) as db:
        db.add(SonyCiAsset(**sony_ci_asset(sony_ci_ids)))
        db.commit()

    response = await post_event(
        async_client,
        events_api_credentials,
        sony_ci_event(sony_ci_ids, event_type='DeleteAsset'),
    )

    assert response.status_code == 200
    assert response.json()['deleted'] == [sony_ci_ids['asset']]
    with Session(engine) as db:
        assert db.get(SonyCiAsset, sony_ci_ids['asset']) is None
        assert db.get(SonyCiTrashbin, sony_ci_ids['asset']) is None


@pytest.mark.asyncio
async def test_sony_ci_event_asset_error(
    mocker: MockerFixture,
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """Asset errors are reported, but the event is still stored, and SonyCi is not
    asked to send the event again."""
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client').return_value
    client.asset.side_effect = Exception('SonyCi is down')

    response = await post_event(
        async_client,
        events_api_credentials,
        sony_ci_event(sony_ci_ids),
    )

    assert response.status_code == 200
    assert response.json()['updated'] == []
    assert response.json()['errors'] == {sony_ci_ids['asset']: 'SonyCi is down'}
    with Session(engine) as db:
        assert db.get(SonyCiEvent, sony_ci_ids['event']) is not None


@pytest.mark.asyncio
async def test_sony_ci_event_unknown_type(
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """Events that SonyCi does not document are rejected."""
    response = await post_event(
        async_client,
        events_api_credentials,
        sony_ci_event(sony_ci_ids, event_type='NotAnEvent'),
    )

    assert response.status_code == 422
    with Session(engine) as db:
        assert db.get(SonyCiEvent, sony_ci_ids['event']) is None


@pytest.mark.asyncio
async def test_sony_ci_event_wrong_credentials(
    async_client: AsyncClient,
    events_api_credentials: tuple[str, str],
    sony_ci_ids: dict[str, str],
):
    """The events API is only open to clients with the right credentials."""
    response = await post_event(
        async_client,
        (events_api_credentials[0], 'wrong'),
        sony_ci_event(sony_ci_ids),
    )

    assert response.status_code == 401
    assert response.json()['detail'] == 'Invalid credentials'
    with Session(engine) as db:
        assert db.get(SonyCiEvent, sony_ci_ids['event']) is None
