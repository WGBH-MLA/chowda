from json import JSONDecodeError, loads

from fastapi import APIRouter, Depends, HTTPException, status
from metaflow import Run, namespace
from sqlmodel import Session

from chowda.auth.utils import permissions
from chowda.db import engine
from chowda.models import MetaflowRun

events = APIRouter()


@events.post('/', dependencies=[Depends(permissions('create:event'))])
async def event(event: dict):
    """Receive an event from Argo Events."""
    print('Chowda event received', event)
    body = event.get('body')
    if not body:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            'Argo Event must include a `body` key as a string',
        )
    try:
        body = loads(event['body'])
    except JSONDecodeError as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 'Argo Event body must be valid JSON'
        ) from e
    name = body.get('name')
    if not name:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Argo Event body string must include a `name` key",
        )
    if name == 'pipeline':
        print('new pipeline event!')
        # FIXME: Ideally, we would add the run to the database here,
        # but the run_id won't be minted until metaflow gets this event.
        # For now, we can continue creating the db row inside the running flow,
        # then update metaflow status events, as they come in.
        return None
    if body['name'].startswith('metaflow.Pipeline'):
        print('Found event!', body['name'])
        payload = body['payload']
        with Session(engine) as db:
            row = db.get(MetaflowRun, payload['run_id'])
            if not row:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, 'MetaflowRun row not found!'
                )
            namespace(None)
            run = Run(f"{payload['flow_name']}/{payload['run_id']}")
            row.finished = run.finished
            row.finished_at = run.finished_at
            row.successful = run.successful
            row.current_step = payload['step_name']
            row.current_task = payload['task_id']
            db.add(row)
            db.commit()
            print('Successfully updated MetaflowRun row!', row)
            return None
    return 'Event successfully processed, but did not match known event'
