from typing import Any, Dict

from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert

from starlette.requests import Request


def upsert(
    model: BaseModel,
    value: BaseModel,
    index_elements: list[str],
):
    """Returns the SQLAlchemy statement to upsert a values into a table"""
    return (
        insert(model)
        .values(value.dict())
        .on_conflict_do_update(
            index_elements=index_elements,
            set_=value.dict(),
        )
    )


def chunks_of_size(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def chunks_striped(lst, n):
    """Yield n number of striped chunks from l."""
    for i in range(0, n):
        yield lst[i::n]


def chunks_sequential(lst, n):
    """Yield n number of sequential chunks from lst."""
    d, r = divmod(len(lst), n)
    for i in range(n):
        si = (d + 1) * (i if i < r else r) + d * (0 if i < r else i - r)
        yield lst[si : si + (d + 1 if i < r else d)]


# def validate_media_files(view: ModelView, request: Request, data: Dict[str, Any]):
def validate_media_file_guids(request: Request, data: Dict[str, Any]):
    """
    1) Validates MediaFile GUIDs by fetching the MediaFile objects from the database,
    2) Replaces the GUID strings with the found objects in the `data` dict
    3) Adds the found objects to request.state.session which is the db session used by
       Starlette-admin when saving.

    NOTE: Starlette-admin does not provide a clean way to trigger validation errors when
    related objects cannot be found because it does not provide an out-of-box feature
    for end users to enter foreign keys as strings in order to related them to other
    objects. But that's exactly what we need to do here: enter GUIDs as strings to
    relate to Batch and  Collection objects.
    """
    from sqlmodel import Session, select
    from chowda.db import engine
    from chowda.models import MediaFile
    from starlette_admin.exceptions import FormValidationError

    errors = []

    with Session(engine) as db:
        for guid in data['media_files']:
            media_files = db.exec(select(MediaFile).where(MediaFile.guid == guid)).all()
            if not media_files:
                errors.append(guid)
    if errors:
        raise FormValidationError({'media_files': errors})

    # Replace GUID strings with MediaFile objects in `data` dict. Very important.
    data['media_files'] = media_files

    # Add MediaFile objects to the DB session Starlette admin uses for persistence.
    for media_file in data['media_files']:
        request.state.session.add(media_file)
