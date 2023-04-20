from starlette_admin.contrib.sqla import ModelView
from starlette_admin import (
    BaseField,
    IntegerField,
    ListField,
    JSONField,
    CollectionField,
)
from dataclasses import dataclass
from json import loads
from requests import Request
from typing import Any


@dataclass
class MediaFilesGuidLinkField(CollectionField):
    # pass
    render_function_key: str = 'media_file_guid_links'
    # display_template = 'displays/media_file_guid_links.html'

    async def serialize_value(self, request: Request, value: Any, action) -> Any:
        # pass
        return [loads(m.json()) for m in value]


@dataclass
class MediaFileCount(IntegerField):
    """A field that displays the number of media files in a collection"""

    render_function_key: str = 'media_file_count'

    async def serialize_value(self, request: Request, value: Any, action) -> Any:
        # This function needs to exist, but it doeesn't do anyting...
        # return len(value)
        pass


class CollectionView(ModelView):
    fields: list = [
        'id',
        'name',
        'description',
        MediaFileCount('media_files', label='MediaFiles Count'),
        # 'media_files', # default view
        MediaFilesGuidLinkField('media_files', label='GUID Links'),
    ]
