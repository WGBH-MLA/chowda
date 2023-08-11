from typing import Any, Dict

from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert


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


def validate_media_files(data: Dict[str, Any]):
    """Validate that the media_files are valid GUIDs and exist in the database"""
    from sqlmodel import Session, select

    from chowda.db import engine
    from chowda.models import MediaFile

    data['media_files'] = data['media_files'].split('\r\n')
    data['media_files'] = [guid.strip() for guid in data['media_files'] if guid]
    media_files = []
    errors = []
    with Session(engine) as db:
        for guid in data['media_files']:
            results = db.exec(select(MediaFile).where(MediaFile.guid == guid)).all()
            if not results:
                errors.append(guid)
            else:
                assert len(results) == 1, 'Multiple MediaFiles with same GUID'
                media_files.append(results[0])
    if errors:
        from starlette_admin.exceptions import FormValidationError

        raise FormValidationError({'media_files': errors})
    data['media_files'] = media_files
