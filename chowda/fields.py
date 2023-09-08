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
        # Check if any runs are still running
        running = [run for run in obj.metaflow_runs if not run.finished]
        new_runs = None
        if running:
            from metaflow import Run, namespace

            # Check status of running runs
            namespace(None)
            runs = [Run(run.pathspec) for run in running]
            finished = [run for run in runs if run.finished]
            if finished:
                from sqlmodel import Session, select

                from chowda.db import engine
                from chowda.models import Batch, MetaflowRun

                with Session(engine) as db:
                    for run in finished:
                        r = db.exec(
                            select(MetaflowRun).where(MetaflowRun.id == run.id)
                        ).one()
                        r.finished = True
                        r.successful = run.successful
                        r.finished_at = run.finished_at
                        db.add(r)
                    db.commit()
                    # Refresh the data for the page
                    new_runs = db.get(Batch, obj.id).metaflow_runs

        return [run.dict() for run in new_runs or obj.metaflow_runs]

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return [
            {
                **run,
                'finished_at': run['finished_at'].isoformat()
                if run.get('finished_at')
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
