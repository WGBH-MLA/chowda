from dataclasses import dataclass
from typing import Any

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.fields import IntegerField, TextAreaField, BaseField
from metaflow import Run, namespace


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
class BatchMediaFilesDisplayField(BaseField):
    name: str = 'batch_media_files'
    display_template: str = 'displays/batch_media_files.html'
    label: str = 'Media Files'
    exclude_from_edit: bool = True
    exclude_from_create: bool = True
    exclude_from_list: bool = True
    read_only: bool = True

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        media_file_rows = []
        namespace(None)

        for media_file in obj.media_files:
            # Lookup the real Metaflow Run using the last Run ID
            run = Run(media_file.metaflow_runs[-1].pathspec)
            media_file_row = {
                'guid': media_file.guid,
                'run_id': run.id,
                'run_link': f'http://mario.wgbh-mla.org/{run.pathspec}',
                'finished_at': run.finished_at or '',
                'successful': run.successful,
            }
            media_file_rows.append(media_file_row)
        return media_file_rows
