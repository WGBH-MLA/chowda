from datetime import datetime

import pytest
from httpx import AsyncClient
from metaflow.plugins.argo.argo_events import ArgoEventException
from pytest_mock import MockerFixture
from sqlmodel import Session, select

from chowda.db import engine
from chowda.models import (
    MediaFile,
    SonyCiAsset,
    SonyCiEvent,
    SonyCiEventType,
    SonyCiTrashbin,
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
            '/api/sony_ci/sync',
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
            '/api/sony_ci/sync', headers={'Authorization': f'Bearer {bearer_token}'}
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
            '/api/sony_ci/sync',
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
            'name': 'John Smith',
            'email': 'johnsmith@example.com',
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


async def post_event(
    async_client: AsyncClient,
    bearer_token: str,
    event: dict,
    url: str = '/api/sonyci/event',
):
    async with async_client as ac:
        return await ac.post(
            url, json=event, headers={'Authorization': f'Bearer {bearer_token}'}
        )


@pytest.mark.asyncio
async def test_sony_ci_event(
    mocker: MockerFixture,
    async_client: AsyncClient,
    fake_access_token: type[callable],
    sony_ci_ids: dict[str, str],
):
    """The event is stored, and the assets it references are updated."""
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client').return_value
    client.asset.return_value = sony_ci_asset(sony_ci_ids)

    response = await post_event(
        async_client,
        fake_access_token(permissions=['create:event']),
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
        assert event.createdOn == datetime(2026, 1, 2)
        assert event.createdBy['email'] == 'johnsmith@example.com'
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
    fake_access_token: type[callable],
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
        fake_access_token(permissions=['create:event']),
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
async def test_sony_ci_event_is_not_duplicated(
    mocker: MockerFixture,
    async_client: AsyncClient,
    fake_access_token: type[callable],
    sony_ci_ids: dict[str, str],
):
    """SonyCi retries events, so receiving the same event twice updates it."""
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client').return_value
    client.asset.return_value = sony_ci_asset(sony_ci_ids)
    event = sony_ci_event(sony_ci_ids)
    bearer_token = fake_access_token(permissions=['create:event'])

    async with async_client as ac:
        headers = {'Authorization': f'Bearer {bearer_token}'}
        first = await ac.post('/api/sonyci/event', json=event, headers=headers)
        second = await ac.post('/api/sonyci/event', json=event, headers=headers)

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
    fake_access_token: type[callable],
    sony_ci_ids: dict[str, str],
):
    """A TrashAsset event moves the asset into the trashbin."""
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client')
    with Session(engine) as db:
        db.add(SonyCiAsset(**sony_ci_asset(sony_ci_ids)))
        db.commit()

    response = await post_event(
        async_client,
        fake_access_token(permissions=['create:event']),
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
        assert trashed.trashedOn == datetime(2026, 1, 2)


@pytest.mark.asyncio
async def test_sony_ci_event_delete_asset(
    mocker: MockerFixture,
    async_client: AsyncClient,
    fake_access_token: type[callable],
    sony_ci_ids: dict[str, str],
):
    """A DeleteAsset event removes the asset from the database."""
    mocker.patch('chowda.routers.sony_ci.sony_ci_client')
    with Session(engine) as db:
        db.add(SonyCiAsset(**sony_ci_asset(sony_ci_ids)))
        db.commit()

    response = await post_event(
        async_client,
        fake_access_token(permissions=['create:event']),
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
    fake_access_token: type[callable],
    sony_ci_ids: dict[str, str],
):
    """Asset errors are reported, but the event is still stored, and SonyCi is not
    asked to send the event again."""
    client = mocker.patch('chowda.routers.sony_ci.sony_ci_client').return_value
    client.asset.side_effect = Exception('SonyCi is down')

    response = await post_event(
        async_client,
        fake_access_token(permissions=['create:event']),
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
    fake_access_token: type[callable],
    sony_ci_ids: dict[str, str],
):
    """Events that SonyCi does not document are rejected."""
    response = await post_event(
        async_client,
        fake_access_token(permissions=['create:event']),
        sony_ci_event(sony_ci_ids, event_type='NotAnEvent'),
    )

    assert response.status_code == 422
    with Session(engine) as db:
        assert db.get(SonyCiEvent, sony_ci_ids['event']) is None


@pytest.mark.asyncio
async def test_sony_ci_event_no_permission(
    async_client: AsyncClient,
    fake_access_token: type[callable],
    sony_ci_ids: dict[str, str],
):
    response = await post_event(
        async_client,
        fake_access_token(permissions=['wrong_permission:event']),
        sony_ci_event(sony_ci_ids),
    )

    assert response.status_code == 403
    assert "{'create:event'}" in response.json()['detail']
    with Session(engine) as db:
        assert db.get(SonyCiEvent, sony_ci_ids['event']) is None
