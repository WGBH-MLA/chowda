from json import loads

from fastapi import APIRouter, HTTPException
from metaflow import Flow, Run, namespace
from sqlmodel import select

from chowda.db import get_db
from chowda.models import Batch, MediaFile, MetaflowRun

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
        payload = body['payload']

        # Find which run this event came from.
        namespace(None)
        pipeline_runs = Flow('Pipeline').runs()
        for run in pipeline_runs:
            if (
                run.data.guid == payload['guid']
                and run.data.batch_id == payload['batch_id']
            ):
                print('Found run! Creating new record.')
                db = get_db()
                media_file = db.exec(
                    select(MediaFile).where(MediaFile.guid == payload['guid']).one()
                )
                batch = db.get(Batch, int(payload['batch_id']))
                row = Batch(
                    id=run.id,
                    batch=batch,
                    media_file=media_file,
                    pathspec=run.pathspec,
                    created_at=run.created_at,
                    finished=run.finished,
                    finished_at=run.finished_at,
                    successful=run.successful,
                )
                db.add(row)
                db.commit()
                print('Successfully created new Batch row!', row)
                return
        # If we get here, we didn't find the run.
        # TODO: Should we try again? For now, return 404.
        raise HTTPException(404, 'Run not found')

    if body['name'].startswith('metaflow.Pipeline'):
        print('Found event!', body['name'])
        payload = body['payload']
        db = get_db()
        row = db.get(MetaflowRun, payload['run_id'])
        if not row:
            raise HTTPException(404, 'MetaflowRun row not found!')
        namespace(None)
        run = Run(payload['flow_name'] + payload['run_id'])
        row.finished = run.finished
        row.finished_at = run.finished_at
        row.successful = run.successful
        db.add(row)
        db.commit()
        print('Successfully updated MetaflowRun row!', row)
        return
    raise HTTPException(400, 'Unknown event')
