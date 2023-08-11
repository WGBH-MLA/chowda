from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, ClassVar, Dict, List

from metaflow import Flow
from metaflow.exception import MetaflowNotFound
from metaflow.integrations import ArgoEvent
from sqlmodel import Session
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin import CustomView, IntegerField, TextAreaField, action
from starlette_admin._types import RequestAction
from starlette_admin.contrib.sqlmodel import ModelView
from starlette_admin.exceptions import ActionFailed

from chowda.auth.utils import get_user
from chowda.db import engine
from chowda.models import Batch
from chowda.utils import validate_media_files


@dataclass
class MediaFilesGuidsField(TextAreaField):
    """A field that displays a list of MediaFile GUIDs as html links"""

    render_function_key: str = 'media_file_guid_links'
    form_template: str = 'forms/media_files.html'
    display_template: str = 'displays/media_files.html'

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return [media_file.guid for media_file in value]


@dataclass
class MediaFileCount(IntegerField):
    """A field that displays the number of MediaFiles in a collection or batch"""

    render_function_key: str = 'media_file_count'
    display_template: str = 'displays/media_file_count.html'

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return len(value)


class BaseModelView(ModelView):
    """Base permissions for all views"""

    def can_create(self, request: Request) -> bool:
        return get_user(request).is_clammer

    def can_delete(self, request: Request) -> bool:
        return get_user(request).is_clammer

    def can_edit(self, request: Request) -> bool:
        return get_user(request).is_clammer


class AdminModelView(ModelView):
    """Base Admin permissions for all protected views"""

    def is_accessible(self, request: Request) -> bool:
        user = get_user(request)
        return user.is_admin or user.is_clammer

    def can_create(self, request: Request) -> bool:
        return get_user(request).is_admin

    def can_delete(self, request: Request) -> bool:
        return get_user(request).is_admin

    def can_edit(self, request: Request) -> bool:
        return get_user(request).is_admin


class CollectionView(BaseModelView):
    fields: ClassVar[list[Any]] = [
        'name',
        'description',
        MediaFileCount(
            'media_files',
            id='media_file_count',
            label='Size',
            read_only=True,
            exclude_from_edit=True,
            exclude_from_create=True,
        ),
        'media_files',  # default view
    ]


class BatchView(BaseModelView):
    exclude_fields_from_create: ClassVar[list[Any]] = [Batch.id]
    exclude_fields_from_edit: ClassVar[list[Any]] = [Batch.id]

    actions: ClassVar[list[Any]] = ['start_batch']

    fields: ClassVar[list[Any]] = [
        'id',
        'name',
        'pipeline',
        'description',
        MediaFileCount(
            'media_files',
            id='media_file_count',
            label='Size',
            read_only=True,
            exclude_from_edit=True,
            exclude_from_create=True,
        ),
        # 'media_files',  # default view
        MediaFilesGuidsField(
            'media_files',
            id='media_file_guids',
            label='GUIDs',
        ),
    ]

    async def validate(self, request: Request, data: Dict[str, Any]):
        validate_media_files(data)

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == 'start_batch':
            return get_user(request).is_clammer
        return await super().is_action_allowed(request, name)

    @action(
        name='start_batch',
        text='Start',
        confirmation='This might cost money. Are you sure?',
        submit_btn_text='Yep',
        submit_btn_class='btn-success',
    )
    async def start_batch(self, request: Request, pks: List[Any]) -> str:
        """Starts a Batch by sending a message to the Argo Event Bus"""
        try:
            for batch_id in pks:
                with Session(engine) as db:
                    batch = db.get(Batch, batch_id)
                    for media_file in batch.media_files:
                        ArgoEvent(
                            batch.pipeline.name, payload={'guid': media_file.guid}
                        ).publish(ignore_errors=False)

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Started {len(pks)} Batche(s)'


class MediaFileView(BaseModelView):
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
        return get_user(request).is_admin


class UserView(AdminModelView):
    fields: ClassVar[list[Any]] = ['first_name', 'last_name', 'email']


class ClamsAppView(BaseModelView):
    fields: ClassVar[list[Any]] = ['name', 'endpoint', 'description', 'pipelines']


class PipelineView(AdminModelView):
    fields: ClassVar[list[Any]] = ['name', 'description', 'clams_apps']

    def is_accessible(self, request: Request) -> bool:
        return True


class ClamsEventView(BaseModelView):
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
        user = get_user(request)
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
