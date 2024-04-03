from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Set

from psycopg2.extensions import QuotedString
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from starlette.requests import Request
from starlette.responses import FileResponse, StreamingResponse

# This should belong inside `download_mmif` function, but the download fails
# unless the temporary directory is created outside of the function.
tmp_dir = TemporaryDirectory()


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


def download_mmif(pks: list[str]) -> StreamingResponse | FileResponse:
    """Download MMIF files from S3 and return a zip archive of them."""
    import zipfile

    import boto3
    from sqlmodel import Session, select

    from chowda.config import MMIF_S3_BUCKET_NAME
    from chowda.db import engine
    from chowda.models import MMIF

    s3 = boto3.client('s3')
    downloaded_mmif_files = []
    download_errors = {}
    with Session(engine) as db:
        mmifs = db.exec(select(MMIF).where(MMIF.id.in_(pks)))

        for mmif in mmifs:
            mmif_tmp_location = f'{tmp_dir.name}/{mmif.mmif_location.split("/")[-1]}'
            try:
                s3.download_file(
                    MMIF_S3_BUCKET_NAME, mmif.mmif_location, mmif_tmp_location
                )
                downloaded_mmif_files.append(mmif_tmp_location)
            except Exception as ex:
                # TODO: log errors and notify user of them
                download_errors[mmif.mmif_location] = ex
    if download_errors:
        from chowda.exceptions import DownloadException

        raise DownloadException(download_errors)
    if len(pks) == 1:
        # If only one batch was downloaded, return the file directly
        return FileResponse(
            downloaded_mmif_files[0],
            media_type='application/octet-stream',
            filename=downloaded_mmif_files[0].split('/')[-1],
        )

    # Create zip archive
    import io
    from datetime import datetime

    current_datetime = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    # TODO: include batch count, or names in the download file name?
    zip_filename = f'chowda_mmif_download.{current_datetime}.zip'
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip:
        for downloaded_mmif_file in downloaded_mmif_files:
            filename = downloaded_mmif_file.split('/')[-1]
            zip.write(downloaded_mmif_file, arcname=filename)

    # Reset buffer to beginning of stream
    zip_buffer.seek(0)

    # Send download response
    return StreamingResponse(
        zip_buffer,
        headers={'Content-Disposition': f'attachment; filename="{zip_filename}"'},
        media_type='application/zip',
    )
