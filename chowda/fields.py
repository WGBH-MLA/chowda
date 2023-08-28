from dataclasses import dataclass
from typing import Any

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.fields import BaseField, IntegerField, TextAreaField


@dataclass
class MediaFilesGuidsField(TextAreaField):
    """A field that displays a list of MediaFile GUIDs as html links"""

    render_function_key: str = 'media_file_guid_links'
    form_template: str = 'forms/media_file_guids_textarea.html'

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        """Maps a string of GUID to a list"""
        return form_data.get(self.id).split()

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        """Maps a Collection's MediaFile objects to a list of GUIDs"""
        return [media_file.guid for media_file in value]


@dataclass
class MediaFileCount(IntegerField):
    """A field that displays the number of MediaFiles in a collection or batch"""

    name: str = 'media_file_count'
    label: str = 'Size'
    read_only: bool = True
    exclude_from_edit: bool = True
    exclude_from_create: bool = True

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        return len(obj.media_files)


@dataclass
class SonyCiAssetThumbnail(BaseField):
    """A the thumbnails for a SonyCiAsset mdoel"""

    name: str = 'sony_ci_assest_thumbnail'
    label: str = 'Thumbnail'
    display_template: str = 'displays/sony_ci_asset_thumbnail.html'
    read_only: bool = True
    exclude_from_create: bool = True

    render_function_key: str = 'sony_ci_asset_thumbnail'

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        return obj.thumbnails_by_type['standard']
