from dataclasses import dataclass
from json import loads
from typing import Any, ClassVar, Dict

from metaflow import Flow
from metaflow.exception import MetaflowNotFound
from requests import Request
from sqlmodel import Session, select
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin import BaseField, CustomView, IntegerField
from starlette_admin._types import RequestAction
from starlette_admin.contrib.sqlmodel import ModelView
from starlette_admin.exceptions import FormValidationError

from chowda.config import API_AUDIENCE
from chowda.db import engine
from chowda.models import MediaFile


@dataclass
class MediaFilesGuidLinkField(BaseField):
    """A field that displays a list of MediaFile GUIDs as html links"""

    render_function_key: str = 'media_file_guid_links'
    form_template: str = 'forms/media_files.html'

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        if action == RequestAction.LIST:
            return [loads(m.json()) for m in value]
        return await super().serialize_value(request, value, action)


@dataclass
class MediaFileCount(IntegerField):
    """A field that displays the number of MediaFiles in a collection or batch"""

    render_function_key: str = 'media_file_count'

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return len(value)


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
        MediaFilesGuidLinkField(
            'media_files',
            label='GUID Links',
            display_template='displays/media_file_guid_links.html',
        ),
    ]


class BatchView(ModelView):
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
        MediaFilesGuidLinkField(
            'media_files',
            label='GUIDs',
            display_template='displays/media_file_guid_links.html',
            exclude_from_list=True,
        ),
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


class MediaFileView(ModelView):
    fields: ClassVar[list[Any]] = ['guid', 'collections', 'batches']


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
                for sync_run in list(Flow('IngestFlow'))
            ][:10]
        except MetaflowNotFound:
            return []

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        return templates.TemplateResponse(
            'dashboard.html',
            {
                'request': request,
                'sync_history': self.sync_history(),
            },
        )


class SonyCiAssetView(AdminModelView):
    fields: ClassVar[list[Any]] = [
        'name',
        'size',
        'type',
        'format',
        'thumbnails',
    ]
