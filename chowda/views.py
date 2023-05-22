from dataclasses import dataclass
from json import loads
from typing import Any

from requests import Request
from starlette_admin import BaseField, IntegerField
from starlette_admin._types import RequestAction
from starlette_admin.contrib.sqlmodel import ModelView


@dataclass
class MediaFilesGuidLinkField(BaseField):
    """A field that displays a list of MediaFile GUIDs as html links"""

    render_function_key: str = 'media_file_guid_links'

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


class CollectionView(ModelView):
    fields = [
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
    fields = [
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
            exclude_from_list=True,
        ),
    ]


class MediaFileView(ModelView):
    fields = ['guid', 'collections', 'batches']


class UserView(ModelView):
    fields = ['first_name', 'last_name', 'email']


class ClamsAppView(ModelView):
    fields = ['name', 'endpoint', 'description', 'pipelines']


class PipelineView(ModelView):
    fields = ['name', 'description', 'clams_apps']


class ClamsEventView(ModelView):
    fields = [
        'batch',
        'media_file',
        'clams_app',
        'status',
        'response_json',
    ]


class SonyCiAssetView(ModelView):
    fields = [
        'name',
        'size',
        'type',
        'format',
        'thumbnails',
    ]
