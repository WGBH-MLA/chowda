from json import loads

from fastapi import APIRouter, HTTPException
from metaflow import Run, namespace
from sqlmodel import Session

from chowda.db import engine
from chowda.models import MetaflowRun

events = APIRouter()


@events.post('/')
def event(event: dict):
    """Receive an event from Argo Events."""
    print('Chowda event received', event)
    if not event.get('body'):
        raise HTTPException(400, 'No body')
    body = loads(event['body'])
    if body['name'] == 'pipeline':
        print('new pipeline event!')
        # FIXME: Ideally, we would add the run to the database here,
        # but the run_id won't be minted until metaflow gets this event.
        # For now, we can continue creating the db row inside the running flow,
        # then update metaflow status events, as they come in.
        return
    if body['name'].startswith('metaflow.Pipeline'):
        print('Found event!', body['name'])
        payload = body['payload']
        with Session(engine) as db:
            row = db.get(MetaflowRun, payload['run_id'])
            if not row:
                raise HTTPException(404, 'MetaflowRun row not found!')
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
            return
    raise HTTPException(400, 'Unknown event')
