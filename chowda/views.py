from datetime import datetime, timedelta
from typing import Any, ClassVar, Dict, List, Set

from fastapi import status
from metaflow import Flow
from metaflow.exception import MetaflowNotFound
from metaflow.integrations import ArgoEvent
from multipart.exceptions import MultipartParseError
from sqlmodel import Session, select
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.templating import Jinja2Templates
from starlette_admin import CustomView, action, row_action
from starlette_admin._types import RequestAction
from starlette_admin.contrib.sqlmodel import ModelView
from starlette_admin.exceptions import ActionFailed
from starlette_admin.fields import BaseField, HasMany, HasOne

from chowda.auth.utils import get_oauth_user
from chowda.db import engine
from chowda.fields import (
    BatchMetaflowRunDisplayField,
    BatchPercentCompleted,
    BatchPercentSuccessful,
    BatchUnstartedGuids,
    BatchUnstartedGuidsCount,
    FinishedField,
    MediaFileCount,
    MediaFilesGuidsField,
    MetaflowPathspecLinkField,
    MetaflowStepLinkField,
    MetaflowTaskLinkField,
    SonyCiAssetThumbnail,
    SuccessfulField,
)
from chowda.models import MMIF, Batch, Collection, MediaFile
from chowda.utils import get_duplicates, validate_media_file_guids, yes
from templates import filters  # noqa: F401


class ChowdaModelView(ModelView):
    """Base settings for all views"""

    page_size_options: ClassVar[list[int]] = [10, 25, 100, 1000, -1]
    additional_js_links: ClassVar[list[str]] = [
        '/static/js/datatables-extensions.min.js',
        '/static/js/bootstrap-input.js',
    ]
    additional_css_links: ClassVar[list[str]] = [
        '/static/css/datatables-extensions.min.css',
    ]
    datatables_options: ClassVar[Dict[str, Any]] = {
        # Customize the dom to put the pagination controls above the table.
        # https://datatables.net/reference/option/dom
        # <processing/> <card-header> <info/> <pagination/> </card-header> <table/>
        'dom': "r<'card-header d-flex align-items-center'<'m-0'i><'m-0 ms-auto'p>><'table-responsive't>",  # noqa E501
        # Use the bootstrap input plugin for pagination controls.
        # Includes First/Last, Next/Previous, and page number input.
        'pagingType': 'bootstrap_input',
        # Enable the KeyTable extension to allow keyboard navigation of the table.
        'keys': {
            # Copy cell value, instead of the html element.
            'clipboardOrthogonal': 'export'
        },
        # Enable the FixedHeader extension to keep the table header visible.
        'fixedHeader': True,
    }

    def title(self, request: Request) -> str:
        if request.state.action == RequestAction.LIST:
            return self.label
        if request.state.action == RequestAction.DETAIL:
            return f'{self.label} - {request.path_params["pk"]}'
        if request.state.action == RequestAction.EDIT:
            return f'{self.label} - Edit {request.path_params["pk"]}'
        if request.state.action == RequestAction.CREATE:
            return f'{self.label} - Create'
        return None


class ClammerModelView(ChowdaModelView):
    """Base Clammer permissions for all protected views"""

    def can_create(self, request: Request) -> bool:
        return get_oauth_user(request).is_clammer

    def can_delete(self, request: Request) -> bool:
        return get_oauth_user(request).is_clammer

    def can_edit(self, request: Request) -> bool:
        return get_oauth_user(request).is_clammer


class AdminModelView(ClammerModelView):
    """Base Admin permissions for all protected views"""

    def is_accessible(self, request: Request) -> bool:
        user = get_oauth_user(request)
        return user.is_admin or user.is_clammer

    def can_create(self, request: Request) -> bool:
        return get_oauth_user(request).is_admin

    def can_delete(self, request: Request) -> bool:
        return get_oauth_user(request).is_admin

    def can_edit(self, request: Request) -> bool:
        return get_oauth_user(request).is_admin


class CollectionView(ClammerModelView):
    exclude_fields_from_list: ClassVar[list[Any]] = [Collection.media_files]
    exclude_fields_from_detail: ClassVar[list[Any]] = [Collection.id]
    exclude_actions_from_detail: ClassVar[list[Any]] = ['create_multiple_batches']

    actions: ClassVar[list[Any]] = ['create_batch', 'create_multiple_batches']
    row_actions: ClassVar[list[Any]] = ['view', 'edit', 'create_batch']
    fields: ClassVar[list[Any]] = [
        'name',
        'description',
        MediaFileCount(),
        # 'media_files',  # default view
        MediaFilesGuidsField('media_files', label='GUIDs'),
    ]

    async def validate(self, request: Request, data: Dict[str, Any]):
        validate_media_file_guids(request, data)

    @row_action(
        name='create_batch',
        text='Create Batch',
        confirmation='Create a Batch from this Collection?',
        action_btn_class='btn-ghost-primary',
        submit_btn_text=yes(),
        icon_class='fa-regular fa-square-plus',
    )
    @action(
        name='create_batch',
        text='Create Batch',
        confirmation='Create a single Batch from these Collections?',
        submit_btn_text=yes(),
        icon_class='fa-regular fa-square-plus',
    )
    async def create_batch(
        self, request: Request, pks: list[int | str] | int | str
    ) -> str:
        """Create a new batch from the combined collections"""
        if not isinstance(pks, list):
            pks = [pks]
        try:
            with Session(engine) as db:
                collections = db.exec(
                    select(Collection).where(Collection.id.in_(pks))
                ).all()
                names = [collection.name for collection in collections]
                ids = [str(collection.id) for collection in collections]
                new_batch = Batch(
                    name=f'Batch from {", ".join(names)}',
                    description=f'Batch from {", ".join(ids)}',
                )
                for collection in collections:
                    new_batch.media_files += collection.media_files
                db.add(new_batch)
                db.commit()

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Created Batch from {", ".join(names)}'

    @action(
        name='create_multiple_batches',
        text='Create multiple Batches',
        confirmation='Create multiple Batches from these Collections?',
        action_btn_class='btn-ghost-primary',
        icon_class='fa-solid fa-square-plus',
        submit_btn_text=yes(),
    )
    async def create_multiple_batches(self, request: Request, pks: List[Any]) -> str:
        """Create multiple batches from the collections"""
        try:
            with Session(engine) as db:
                collections = db.exec(
                    select(Collection).where(Collection.id.in_(pks))
                ).all()
                names = [collection.name for collection in collections]
                for collection in collections:
                    new_batch = Batch(
                        name=f'Batch from {collection.name}',
                        description=f'Batch from Collection {collection.id!s}',
                    )
                    new_batch.media_files = collection.media_files
                    db.add(new_batch)
                db.commit()

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Created Batches from {", ".join(names)}'


class BatchView(ClammerModelView):
    label: ClassVar[str] = 'Batches'
    exclude_fields_from_create: ClassVar[list[Any]] = [Batch.id]
    exclude_fields_from_edit: ClassVar[list[Any]] = [Batch.id]
    exclude_fields_from_list: ClassVar[list[Any]] = [Batch.media_files]
    exclude_fields_from_detail: ClassVar[list[Any]] = [Batch.id]
    exclude_actions_from_detail: ClassVar[list[Any]] = ['combine_batches']

    fields_default_sort: ClassVar[BaseField] = [(Batch.id, True)]

    actions: ClassVar[list[Any]] = [
        'start_batches',
        'duplicate_batches',
        'combine_batches',
        'download_mmif',
    ]

    fields: ClassVar[list[Any]] = [
        'id',
        'name',
        'pipeline',
        'description',
        MediaFileCount(),
        BatchPercentCompleted(),
        BatchPercentSuccessful(),
        BatchUnstartedGuidsCount(),
        'input_mmifs',
        BatchUnstartedGuids('media_files'),
        MediaFilesGuidsField('media_files', exclude_from_detail=True),
        BatchMetaflowRunDisplayField(),
        'output_mmifs',
    ]

    async def validate(self, request: Request, data: Dict[str, Any]):
        validate_media_file_guids(request, data)

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        user = get_oauth_user(request)
        if name == 'start_batches':
            return user.is_clammer
        if name == 'duplicate_batches':
            return user.is_clammer or user.is_admin
        if name == 'combine_batches':
            return user.is_clammer or user.is_admin
        if name == 'download_mmif':
            return user.is_clammer or user.is_admin
        return await super().is_action_allowed(request, name)

    @action(
        name='start_batches',
        text='Start',
        confirmation='This might cost money. Are you sure?',
        icon_class='fa fa-play',
        action_btn_class='btn-outline-success',
        submit_btn_text=yes(),
        submit_btn_class='btn-success',
        form="""
        <form>
                <input type="checkbox" id="new_mmif" name="new_mmif">
                <label for="new_mmif">Start from blank MMIF?</label>
                <input type="hidden" name="_" value="">
        </form>
        """,
    )
    async def start_batches(self, request: Request, pks: List[Any]) -> str:
        """Starts a Batch by sending a message to the Argo Event Bus"""
        try:
            data: FormData = await request.form()
        except MultipartParseError as parse_error:
            raise ActionFailed('Error parsing form') from parse_error

        new_mmif = data.get('new_mmif') == 'on'
        try:
            with Session(engine) as db:
                for batch_id in pks:
                    batch = db.get(Batch, batch_id)
                    pipeline = ','.join(
                        [app.endpoint for app in batch.pipeline.clams_apps]
                    )
                    mmifs = {
                        mmif.media_file_id: mmif.mmif_location
                        for mmif in batch.input_mmifs
                    }
                    mmif_guids = set(mmifs.keys())
                    for media_file in batch.media_files:
                        payload = {
                            'batch_id': batch_id,
                            'guid': media_file.guid,
                            'pipeline': pipeline,
                        }
                        if new_mmif:
                            payload['mmif_location'] = ''
                        elif media_file.guid in mmif_guids:
                            # Prefer the Batch's MMIF if specified
                            payload['mmif_location'] = mmifs[media_file.guid]
                        elif media_file.mmifs:
                            # If there is an MMIF in the MediaFile's MMIFs
                            payload['mmif_location'] = media_file.mmifs[
                                -1
                            ].mmif_location
                        ArgoEvent('pipeline', payload=payload).publish(
                            ignore_errors=False
                        )

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Started {len(pks)} Batch(es)'

    @action(
        name='duplicate_batches',
        text='Duplicate',
        confirmation='Duplicate all selected Batches?',
        icon_class='fa fa-copy',
        submit_btn_text=yes(),
        submit_btn_class='btn-outline-primary',
    )
    async def duplicate_batches(self, request: Request, pks: List[Any]) -> str:
        """Create a new batch from the selected batch"""
        try:
            with Session(engine) as db:
                for batch_id in pks:
                    existing_batch = db.get(Batch, batch_id)
                    new_batch_params = existing_batch.dict()
                    new_batch_params.pop('id')
                    new_batch_params['name'] += ' [COPY]'
                    new_batch = Batch(**new_batch_params)
                    new_batch.media_files = existing_batch.media_files
                    db.add(new_batch)
                db.commit()

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Duplicated {len(pks)} Batch(es)'

    @action(
        name='combine_batches',
        text='Combine',
        confirmation='Combine all selected Batches into a new Batch?',
        icon_class='fa fa-compress',
        action_btn_class='btn-ghost',
        submit_btn_text=yes(),
        submit_btn_class='btn-outline-primary',
    )
    async def combine_batches(self, request: Request, pks: List[Any]) -> str:
        """Merge multiple batches into a new batch"""
        try:
            with Session(engine) as db:
                batches = db.exec(select(Batch).where(Batch.id.in_(pks))).all()
                # TODO: What are the best defaults for a newly combined Batch?
                new_batch = Batch(
                    name=f'Combination of {len(batches)} Batches',
                    description=f'Combination of {len(batches)} Batches',
                )

                for batch in batches:
                    new_batch.media_files += batch.media_files

                db.add(new_batch)
                db.commit()

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Combined {len(pks)} Batch(es)'

    @action(
        name='download_mmif',
        text='Download MMIF',
        confirmation='Download all MMIF JSON for these Batches?',
        icon_class='fa fa-download',
        submit_btn_text=yes() + ' Gimme the MMIF!',
        submit_btn_class='btn-outline-primary',
        custom_response=True,
    )
    async def download_mmif(self, request: Request, pks: List[Any]) -> str:
        """Create a new batch from the selected batch"""
        import zipfile
        from tempfile import TemporaryDirectory

        import boto3

        from chowda.config import MMIF_S3_BUCKET_NAME

        try:
            with Session(engine) as db:
                # Get all of the MMIF S3 locations from the database.
                batches = db.exec(select(Batch).where(Batch.id.in_(pks))).all()
                all_mmif_locations = [
                    mmif.mmif_location
                    for batch in batches
                    for mmif in batch.output_mmifs
                ]

            # Download files from S3
            s3 = boto3.client('s3')
            downloaded_mmif_files = []
            tmp_dir = TemporaryDirectory()
            download_errors = {}
            for mmif_location in all_mmif_locations:
                mmif_tmp_location = f'{tmp_dir.name}/{mmif_location.split("/")[-1]}'
                try:
                    s3.download_file(
                        MMIF_S3_BUCKET_NAME, mmif_location, mmif_tmp_location
                    )
                    downloaded_mmif_files.append(mmif_tmp_location)
                except Exception as ex:
                    # TODO: log errors and notify user of them
                    download_errors[mmif_location] = ex

            # Create zip archive
            import io
            from datetime import datetime

            from starlette.responses import StreamingResponse

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
                headers={
                    'Content-Disposition': f'attachment; filename="{zip_filename}"'
                },
                media_type='application/zip',
            )
        except Exception as error:
            # TODO: pop 'error' out of session and display with javascript
            # dangrerAlert() when admin/batch/list renders.
            # See statics/js/alerts.js from starlette-admin.
            request.session['error'] = f'{error!s}'
            return RedirectResponse(
                request.url_for('admin:list', identity='batch'),
                status_code=status.HTTP_303_SEE_OTHER,
            )


class MediaFileView(ClammerModelView):
    pk_attr: str = 'guid'

    actions: ClassVar[List[str]] = ['create_new_batch']

    fields: ClassVar[list[str]] = [
        'guid',
        'collections',
        'batches',
        'assets',
        'mmifs',
        'metaflow_runs',
    ]
    exclude_fields_from_list: ClassVar[list[str]] = ['mmif_json', 'mmifs']
    page_size_options: ClassVar[list[int]] = [10, 25, 100, 500, 2000, 10000]

    def can_create(self, request: Request) -> bool:
        return get_oauth_user(request).is_admin

    @action(
        name='create_new_batch',
        text='Create Batch',
        confirmation='Create a Batch from these Media Files?',
        action_btn_class='btn-ghost-primary',
        submit_btn_text=yes(),
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="batch_name"
                    placeholder="Batch Name">
                <textarea class="form-control" name="batch_description"
                    placeholder="Batch Description"></textarea>
            </div>
        </form>
        """,
    )
    async def create_new_batch(self, request: Request, pks: List[Any]) -> str:
        with Session(engine) as db:
            media_files = db.exec(
                select(MediaFile).where(MediaFile.guid.in_(pks))
            ).all()
            data: FormData = await request.form()
            batch = Batch(
                name=data.get('batch_name'),
                description=data.get('batch_description'),
                media_files=media_files,
            )
            db.add(batch)
            db.commit()

        return f'Batch of {len(pks)} Media Files created'


class UserView(AdminModelView):
    fields: ClassVar[list[Any]] = ['first_name', 'last_name', 'email']


class ClamsAppView(ClammerModelView):
    fields: ClassVar[list[Any]] = ['name', 'endpoint', 'description', 'pipelines']


class PipelineView(ClammerModelView):
    fields: ClassVar[list[Any]] = ['name', 'description', 'clams_apps']

    def is_accessible(self, request: Request) -> bool:
        return True


class DashboardView(CustomView):
    def sync_history(self) -> Dict[str, Any]:
        try:
            return [
                {'created_at': sync_run.created_at, 'successful': sync_run.successful}
                for sync_run in list(Flow('IngestFlow'))[:5]
            ]
        except MetaflowNotFound:
            return []

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        history = self.sync_history()
        user = get_oauth_user(request)
        sync_disabled = datetime.now() - history[0]['created_at'] < timedelta(
            minutes=15
        )
        title = self.title(request)
        return templates.TemplateResponse(
            'dashboard.html',
            {
                'title' if title else None: title,
                'request': request,
                'user': user,
                'sync_history': history,
                'sync_disabled': sync_disabled,
                'flash': request.session.pop('flash', ''),
                'error': request.session.pop('error', ''),
            },
        )


class SonyCiAssetView(AdminModelView):
    fields: ClassVar[list[Any]] = [
        SonyCiAssetThumbnail(),
        'name',
        'size',
        'type',
        'format',
        'media_files',
    ]

    page_size_options: ClassVar[list[int]] = [10, 25, 100, 500, 2000, 10000]

    def can_create(self, request: Request) -> bool:
        """Sony Ci Assets are ingested from Sony Ci API, not created from the UI."""
        return False


class MetaflowRunView(AdminModelView):
    form_include_pk: ClassVar[bool] = True

    fields: ClassVar[list[Any]] = [
        'id',
        MetaflowPathspecLinkField('pathspec'),
        'batch',
        'mmif',
        'media_file',
        'created_at',
        FinishedField('finished'),
        SuccessfulField('successful'),
        MetaflowStepLinkField('current_step'),
        MetaflowTaskLinkField('current_task'),
    ]


class MMIFView(ChowdaModelView):
    label: ClassVar[str] = 'MMIFs'
    fields: ClassVar[List[Any]] = [
        'media_file',
        HasMany('batch_inputs', identity='batch', label='Input to Batches'),
        HasOne('batch_output', identity='batch', label='Generated from Batch'),
        'metaflow_run',
        'mmif_location',
        'created_at',
    ]
    actions: ClassVar[List[str]] = ['add_to_new_batch', 'add_to_existing_batch']

    @action(
        name='add_to_new_batch',
        text='Add to New Batch',
        confirmation='Create a Batch from these MMIFs?',
        action_btn_class='btn-ghost-primary',
        submit_btn_text=yes(),
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="batch_name"
                    placeholder="Batch Name">
                <textarea class="form-control" name="batch_description"
                    placeholder="Batch Description"></textarea>
            </div>
        </form>
        """,
    )
    async def add_to_new_batch(self, request: Request, pks: List[Any]) -> str:
        try:
            data: FormData = await request.form()
            with Session(engine) as db:
                mmifs: List[MMIF] = db.exec(select(MMIF).where(MMIF.id.in_(pks))).all()
                media_files: List[MediaFile] = [mmif.media_file for mmif in mmifs]
                guids: List[str] = [media_file.guid for media_file in media_files]
                duplicates: Set = get_duplicates(guids)
                if duplicates:
                    raise ActionFailed(
                        f'{len(duplicates)} duplicate Media File{"s" if len(duplicates) > 1 else ""} found:<br>'  # noqa: E501
                        + '<br>'.join(duplicates)
                    )

                batch = Batch(
                    name=data.get('batch_name'),
                    description=data.get('batch_description'),
                    input_mmifs=mmifs,
                    media_files=media_files,
                )
                db.add(batch)
                db.commit()

            return f'Batch of {len(pks)} MMIFs created'
        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

    @action(
        name='add_to_existing_batch',
        text='Add to Existing Batch',
        confirmation='Which batch should these be added to?',
        action_btn_class='btn-ghost-primary',
        submit_btn_text=yes(),
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="batch_id"
                    placeholder="Batch ID">
            </div>
        </form>
        """,
    )
    async def add_to_existing_batch(self, request: Request, pks: List[Any]) -> str:
        try:
            data: FormData = await request.form()
            with Session(engine) as db:
                mmifs: List[MMIF] = db.exec(select(MMIF).where(MMIF.id.in_(pks))).all()
                batch: Batch = db.get(Batch, data.get('batch_id'))
                batch.input_mmifs += mmifs
                media_files: List[MediaFile] = [mmif.media_file for mmif in mmifs]

                # Check for duplicate Media Files in selection
                guids: List[str] = [media_file.guid for media_file in media_files]
                duplicates: Set = get_duplicates(guids)
                if duplicates:
                    raise ActionFailed(
                        f'{len(duplicates)} duplicate Media File{"s" if len(duplicates) > 1 else ""} found in selection:<br>'  # noqa: E501
                        + '<br>'.join(duplicates)
                    )
                # Check batch input_mmifs for other MMIFs linked to these MediaFiles
                existing_batch_mmif_guids: Set[str] = {
                    mmif.media_file.guid for mmif in batch.input_mmifs
                }
                existing_media_files = existing_batch_mmif_guids.intersection(guids)
                if existing_media_files:
                    s = 's' if len(existing_media_files) > 1 else ''
                    raise ActionFailed(
                        f'{len(existing_media_files)} Media File{s} already exist{"" if s else "s"} in Batch {batch.id}:<br>'  # noqa: E501
                        + '<br>'.join(existing_media_files)
                    )

                batch.media_files += media_files

                db.commit()

                return f'Added {len(pks)} MMIFs to Batch {batch.id}'
        except Exception as error:
            raise ActionFailed(f'{error!s}') from error
