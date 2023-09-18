from dataclasses import dataclass
from typing import Any

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.fields import BaseField, IntegerField, TextAreaField

from chowda.models import MediaFile


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
    exclude_from_edit: bool = True

    render_function_key: str = 'sony_ci_asset_thumbnail'

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        return obj.thumbnails_by_type.get('small')


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
        return [run.dict() for run in obj.metaflow_runs]

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return [
            {
                **run,
                'finished_at': run['finished_at'].isoformat()
                if run.get('finished_at')
                else None,
                'created_at': run['created_at'].isoformat()
                if run.get('created_at')
                else None,
            }
            for run in value
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


@dataclass
class BatchUnstartedGuids(BaseField):
    """GUIDs in a batch that have not yet started"""

    name: str = 'batch_unstarted_guids'
    read_only: bool = True
    label: str = 'Unstarted GUIDs'
    exclude_from_create: bool = True
    exclude_from_edit: bool = True
    exclude_from_list: bool = True

    display_template: str = 'displays/collection_media_files.html'

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        return [MediaFile(guid=guid) for guid in obj.unstarted_guids()]


@dataclass
class BatchUnstartedGuidsCount(IntegerField):
    """The number of MetaflowRuns in a batch that have not yet started"""

    name: str = 'batch_unstarted_guids_count'
    read_only: bool = True
    label: str = 'Unstarted GUIDs'
    exclude_from_create: bool = True
    exclude_from_edit: bool = True

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        return len(obj.unstarted_guids())
