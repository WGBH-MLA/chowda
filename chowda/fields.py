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
    """A field to display SonyCiAsset thumbnails"""

    name: str = 'sony_ci_assest_thumbnail'
    label: str = 'Thumbnail'
    display_template: str = 'displays/sony_ci_asset_thumbnail.html'
    read_only: bool = True
    exclude_from_create: bool = True

    render_function_key: str = 'sony_ci_asset_thumbnail'

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        return obj.thumbnails_by_type.get('standard')


@dataclass
class BatchMetaflowRunDisplayField(BaseField):
    """A field that displays a list of MetaflowRuns in a batch"""

    name: str = 'batch_metaflow_runs'
    display_template: str = 'displays/batch_metaflow_runs.html'
    label: str = 'Metaflow Runs'
    exclude_from_edit: bool = True
    exclude_from_create: bool = True
    exclude_from_list: bool = True
    read_only: bool = True

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        return [
            {
                'guid': run.media_file_id,
                'run_id': run.id,
                'run_link': f'https://mario.wgbh-mla.org/{run.pathspec}',
                'finished_at': run.finished_at or '',
                'finished': run.finished,
                'successful': run.successful,
            }
            for run in obj.metaflow_runs
        ]


@dataclass
class BatchPercentCompleted(BaseField):
    """The percentage of MediaFiles in a batch that have finished"""

    name: str = 'batch_percent_completed'
    exclude_from_edit: bool = True
    exclude_from_create: bool = True
    label: str = 'Completed %'

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        runs = [run.finished for run in obj.metaflow_runs]
        if runs:
            return f'{runs.count(True) / len(obj.media_files):.1%}'
        return None


@dataclass
class BatchPercentSuccessful(BaseField):
    """The percentage of MediaFiles in a batch that have finished successfully"""

    name: str = 'batch_percent_successful'
    label: str = 'Successful %'
    exclude_from_create: bool = True
    exclude_from_edit: bool = True

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        runs = [run.successful for run in obj.metaflow_runs]
        if runs:
            return f'{runs.count(True) / len(obj.media_files):.1%}'
        return None
