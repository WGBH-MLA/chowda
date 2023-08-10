from dataclasses import dataclass
from datetime import datetime, timedelta
from json import loads
from typing import Any, ClassVar, Dict, List

from metaflow import Flow
from metaflow.integrations import ArgoEvent
from metaflow.exception import MetaflowNotFound
from requests import Request
from sqlmodel import Session, select
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin import CustomView, IntegerField, TextAreaField, action
from starlette_admin._types import RequestAction
from starlette_admin.contrib.sqlmodel import ModelView
from starlette_admin.exceptions import FormValidationError
from starlette_admin.exceptions import ActionFailed


from chowda.config import API_AUDIENCE
from chowda.db import engine
from chowda.models import MediaFile, Batch
from chowda.routers.dashboard import UserToken


@dataclass
class MediaFilesGuidsField(TextAreaField):
    """A field that displays a list of MediaFile GUIDs as html links"""

    render_function_key: str = 'media_file_guid_links'
    form_template: str = 'forms/media_files.html'

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        if action == RequestAction.LIST:
            return [loads(m.json()) for m in value]
        return [media_file.guid for media_file in value]


@dataclass
class MediaFileCount(IntegerField):
    """A field that displays the number of MediaFiles in a collection or batch"""

    render_function_key: str = 'media_file_count'

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return str(len(value))


class AdminModelView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        return set(request.state.user.get(f'{API_AUDIENCE}/roles', set())).intersection(
            {'admin', 'clammer'}
        )


class CollectionView(ModelView):
    fields: ClassVar[list[Any]] = [
        'name',
        'description',
        MediaFileCount(
            'media_files',
            label='Size',
            read_only=True,
            exclude_from_edit=True,
            exclude_from_create=True,
        ),
        # 'media_files',  # default view
        MediaFilesGuidsField(
            'media_files',
            label='GUID Links',
            display_template='displays/media_files.html',
        ),
    ]


class BatchView(ModelView):
    exclude_fields_from_list: ClassVar[list[Any]] = [Batch.media_files]
    exclude_fields_from_create: ClassVar[list[Any]] = [Batch.id]
    exclude_fields_from_edit: ClassVar[list[Any]] = [Batch.id]

    actions: ClassVar[list[Any]] = ['start_batch']

    fields: ClassVar[list[Any]] = [
        'id',
        'name',
        'pipeline',
        'description',
        MediaFilesGuidsField(
            'media_files',
            required=True,
            placeholder='Enter GUIDs here',
            form_template='forms/media_files.html',
            display_template='displays/media_files.html',
        ),
        # MediaFileCount(
        #     'media_files',
        #     label='Size',
        #     exclude_from_edit=True,
        #     exclude_from_create=True,
        # ),
        'media_files',  # default view
        # MediaFilesGuidsField(
        #     'media_files',
        #     label='GUIDs',
        #     display_template='displays/media_files.html',
        #     exclude_from_list=True,
        # ),
    ]

    async def validate(self, request: Request, data: Dict[str, Any]):
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
            raise FormValidationError({'media_files': errors})
        data['media_files'] = media_files

    @action(
        name='start_batch',
        text='Start',
        confirmation='This might cost money. Are you sure?',
        submit_btn_text='Yep',
        submit_btn_class='btn-success',
    )
    async def start_batch(self, request: Request, pks: List[Any]) -> str:
        try:
            for batch_id in pks:
                with Session(engine) as db:
                    batch = db.get(Batch, batch_id)
                    for media_file in batch.media_files:
                        ArgoEvent(
                            'app-barsdetection', payload={'guid': media_file.guid}
                        ).publish(ignore_errors=False)

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Started {len(pks)} Batche(s)'


class MediaFileView(ModelView):
    fields: ClassVar[list[Any]] = [
        'guid',
        'collections',
        'batches',
        'assets',
        'mmif_json',
        'clams_events',
    ]
    exclude_fields_from_list: ClassVar[list[str]] = ['mmif_json', 'clams_events']

    def can_create(self, request: Request) -> bool:
        """Permission for creating new Items. Return True by default"""
        return False


class UserView(AdminModelView):
    fields: ClassVar[list[Any]] = ['first_name', 'last_name', 'email']


class ClamsAppView(ModelView):
    fields: ClassVar[list[Any]] = ['name', 'endpoint', 'description', 'pipelines']


class PipelineView(ModelView):
    fields: ClassVar[list[Any]] = ['name', 'description', 'clams_apps']


class ClamsEventView(ModelView):
    fields: ClassVar[list[Any]] = [
        'batch',
        'media_file',
        'clams_app',
        'status',
        'response_json',
    ]


class DashboardView(CustomView):
    def sync_history(self) -> Dict[str, Any]:
        try:
            return [
                {'created_at': sync_run.created_at, 'successful': sync_run.successful}
                for sync_run in list(Flow('IngestFlow'))[:10]
            ]
        except MetaflowNotFound:
            return []

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        history = self.sync_history()
        user = UserToken(**request.state.user)
        sync_disabled = datetime.now() - history[0]['created_at'] < timedelta(
            minutes=15
        )
        return templates.TemplateResponse(
            'dashboard.html',
            {
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
        'name',
        'size',
        'type',
        'format',
        'thumbnails',
        'media_files',
    ]

    def can_create(self, request: Request) -> bool:
        """Sony Ci Assets are ingested from Sony Ci API, not created from the UI."""
        return False
