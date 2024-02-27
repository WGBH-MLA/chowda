from typing import Any, Dict, List, Set

from psycopg2.extensions import QuotedString
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from starlette.requests import Request


def adapt_url(url):
    """Adapt a Pydantic2 Url to a psycopg2 QuotedString"""
    return QuotedString(str(url))


def upsert(
    model: BaseModel,
    value: BaseModel,
    index_elements: list[str],
):
    """Returns the SQLAlchemy statement to upsert a values into a table"""
    return (
        insert(model)
        .values(value.model_dump())
        .on_conflict_do_update(
            index_elements=index_elements,
            set_=value.model_dump(),
        )
    )


def chunks_of_size(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def chunks_striped(lst, n):
    """Yield n number of striped chunks from l."""
    for i in range(n):
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
    from starlette_admin.exceptions import FormValidationError

    from chowda.db import engine
    from chowda.models import MediaFile

    media_files = []

    # Clear the session to avoid conflicts with session instances used by the API
    request.state.session.expire_all()

    with Session(engine) as db:
        # Get all MediaFiles objects for the GUIDs in data['media_files']
        media_files = db.exec(
            select(MediaFile).where(MediaFile.guid.in_(data['media_files']))
        ).all()

        # Any value in data['media_files'] that does not have a corresponding MediaFile
        # object is invalid, so add it to the errors
        valid_guids = [media_file.guid for media_file in media_files]
        invalid_guids = [
            guid for guid in data['media_files'] if guid not in valid_guids
        ]

        if len(invalid_guids):
            raise FormValidationError({'media_files': invalid_guids})

    # Replace GUID strings with MediaFile objects in `data` dict so they will get added
    # the parent object.
    data['media_files'] = media_files

    # Add MediaFile objects to the DB session Starlette admin uses for persistence.
    # This is a bit of a hack to play nice with starlette-admin, but without it, an
    # error is thrown if starlette-admin tries to add a validated MediaFile object
    # to a parent object when that MediaFile is already there.
    for media_file in data['media_files']:
        request.state.session.add(media_file)


def get_duplicates(values: List[Any]) -> Set[Any]:
    """Return a set of duplicate values in a list, or an empty set if there are none.

    NOTE: This is a fast approach that does not preserve order, but runs in O(n)"""
    unique: Set = set()
    duplicates: Set = set()
    for v in values:
        if v not in unique:
            unique.add(v)
        else:
            duplicates.add(v)
    return duplicates


YES = [
    'Yes!',
    'Aye!',
    'Aye aye!',
    'Aye aye, Captain!',
    "Aye aye, Capt'n!",
    'YAAASS!!!',
    'Yup!',
    'Yuppers!',
    'Yup yup!',
    'Yup yup yup!',
    'Do it!',
    'Make it so!',
    'Absolutley!',
    'Sure!',
    'Sure thing!',
    'You bet!',
    'You betcha!',
    'Certainly',
    'Of course!',
    'Definitely!',
    'Affirmative!',
    'Indubitably!',
    'Without a doubt!',
    'By all means!',
    'Without question!',
]


def yes() -> str:
    """Return a random 'yes' string"""
    from random import choice

    return choice(YES)
