from dataclasses import dataclass
from typing import Any

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.fields import IntegerField, TextAreaField, BaseField


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

        for media_file in obj.media_files:
            # Lookup the real Metaflow Run using the last Run ID
            run = media_file.last_metaflow_run_for_batch(batch_id=obj.id)
            media_file_row = {
                'guid': media_file.guid,
                'run_id': run.id,
                'run_link': f'https://mario.wgbh-mla.org/{run.pathspec}',
                'finished_at': run.source.finished_at or '',
                'successful': run.source.successful,
            }
            media_file_rows.append(media_file_row)
        return media_file_rows


@dataclass
class BatchPercentCompleted(BaseField):
    name: str = 'batch_percent_completed'
    label: str = 'Completed %'

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        runs = [
            last_run.source
            for last_run in [
                media_file.last_metaflow_run_for_batch(batch_id=obj.id)
                for media_file in obj.media_files
            ]
            if last_run
        ]

        finished_runs = [run for run in runs if run.finished_at]
        failed_runs = [run for run in runs if not run.successful]
        total_complete = len(finished_runs) + len(failed_runs)
        percent_completed = total_complete / len(obj.media_files)

        return f'{percent_completed:.1%}'


@dataclass
class BatchPercentSuccessful(BaseField):
    name: str = 'batch_percent_successful'
    label: str = 'Successful %'

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        runs = [
            last_run.source
            for last_run in [
                media_file.last_metaflow_run_for_batch(batch_id=obj.id)
                for media_file in obj.media_files
            ]
            if last_run
        ]

        successful_runs = [run for run in runs if run.successful]

        percent_successful = len(successful_runs) / len(obj.media_files)

        return f'{percent_successful:.1%}'
