from fastapi import APIRouter

events = APIRouter()


@events.post('/')
def pipeline_event(event: dict):
    """Receive a pipeline event from Argo Events."""
    print('Chowda event received', event)
