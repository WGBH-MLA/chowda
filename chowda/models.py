"""Models

SQLModels for DB and validation
"""

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from metaflow import Run, namespace
from pydantic import AnyHttpUrl, EmailStr, stricturl
from sqlalchemy import JSON, Column, DateTime, Enum
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, Relationship, SQLModel
from starlette.requests import Request

MediaUrl = stricturl(allowed_schemes=['video', 'audio', 'text'], tld_required=False)
"""Media url validator. Must have prefix of video, audio, or text. No TLD required.
Example:
    video://*
"""


class AppStatus(enum.Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETE = 'complete'
    FAILED = 'failed'


class MediaType(enum.Enum):
    video = 'Video'
    audio = 'Audio'


class ThumbnailType(enum.Enum):
    LARGE = 'large'
    MEDIUM = 'medium'
    SMALL = 'small'
    STANDARD = 'standard'
    VIDEO_SD = 'video-sd'
    VIDEO_3G = 'video-3g'


class User(SQLModel, table=True):
    """User model

    Attributes:
        id: Primary key
        email: User email
        first_name: User first name
        last_name: User last name
    """

    __tablename__ = 'users'
    id: Optional[int] = Field(primary_key=True)
    email: EmailStr = Field(index=True)
    first_name: str = Field(min_length=3, index=True)
    last_name: str = Field(min_length=3, index=True)

    async def __admin_repr__(self, request: Request):
        return f'{self.first_name} {self.last_name}'


class MediaFileCollectionLink(SQLModel, table=True):
    media_file_id: Optional[str] = Field(
        default=None, foreign_key='media_files.guid', primary_key=True
    )
    collection_id: Optional[int] = Field(
        default=None, foreign_key='collections.id', primary_key=True
    )


class MediaFileBatchLink(SQLModel, table=True):
    media_file_id: Optional[str] = Field(
        default=None, foreign_key='media_files.guid', primary_key=True
    )
    batch_id: Optional[int] = Field(
        default=None, foreign_key='batches.id', primary_key=True
    )


class MediaFileSonyCiAssetLink(SQLModel, table=True):
    media_file_id: Optional[str] = Field(
        default=None, foreign_key='media_files.guid', primary_key=True
    )
    sonyci_asset_id: Optional[str] = Field(
        default=None, foreign_key='sonyci_assets.id', primary_key=True
    )


class MediaFile(SQLModel, table=True):
    """Media file model

    Attributes:
        guid: MediaFile GUID
        assets: List of SonyCiAssets
        collections: List of Collections
        batches: List of Batches
        metaflow_runs: List of MetaflowRuns
    """

    __tablename__ = 'media_files'
    guid: Optional[str] = Field(primary_key=True, default=None, index=True)
    mmif_json: Dict[str, Any] = Field(sa_column=Column(JSON), default=None)
    assets: List['SonyCiAsset'] = Relationship(
        back_populates='media_files', link_model=MediaFileSonyCiAssetLink
    )
    collections: List['Collection'] = Relationship(
        back_populates='media_files', link_model=MediaFileCollectionLink
    )
    batches: List['Batch'] = Relationship(
        back_populates='media_files', link_model=MediaFileBatchLink
    )
    metaflow_runs: List['MetaflowRun'] = Relationship(back_populates='media_file')

    def metaflow_runs_for_batch(self, batch_id: int):
        return [
            metaflow_run
            for metaflow_run in self.metaflow_runs
            if metaflow_run.batch_id == batch_id
        ]

    def last_metaflow_run_for_batch(self, batch_id: int):
        # TODO: is getting the last one sufficient, or do we need to add sortable
        # timestamps?
        runs = self.metaflow_runs_for_batch(batch_id=batch_id)
        return runs[-1] if len(runs) > 0 else None

    async def __admin_repr__(self, request: Request):
        return self.guid

    async def __admin_select2_repr__(self, request: Request) -> str:
        return f'<span><strong>{self.guid}</strong></span>'


class AssetThumbnails(SQLModel):
    thumbnails: Dict[str, Any]


class SonyCiAssetThumbnail(SQLModel):
    type: ThumbnailType
    location: str
    size: int
    width: int
    height: int


class SonyCiAsset(SQLModel, table=True):
    __tablename__ = 'sonyci_assets'
    id: Optional[str] = Field(primary_key=True, index=True, default=None)
    name: str = Field(index=True)
    size: int = Field(index=True, sa_column=Column(postgresql.BIGINT))
    type: MediaType = Field(sa_column=Column(Enum(MediaType)))
    format: Optional[str] = Field(default=None, index=True)
    thumbnails: Optional[List[Dict[str, Any]]] = Field(
        sa_column=Column(postgresql.ARRAY(JSON)), default=None
    )
    media_files: List[MediaFile] = Relationship(
        back_populates='assets', link_model=MediaFileSonyCiAssetLink
    )

    @property
    def thumbnails_by_type(self):
        return {thumbnail['type']: thumbnail for thumbnail in self.thumbnails}

    async def __admin_repr__(self, request: Request):
        return self.name


class Collection(SQLModel, table=True):
    __tablename__ = 'collections'
    id: Optional[int] = Field(primary_key=True, default=None)
    name: str
    description: str
    media_files: List['MediaFile'] = Relationship(
        back_populates='collections', link_model=MediaFileCollectionLink
    )

    async def __admin_repr__(self, request: Request):
        return f'{self.name or self.id}'

    async def __admin_select2_repr__(self, request: Request):
        return f'<span><strong>{self.name or self.id}</span>'


class Batch(SQLModel, table=True):
    __tablename__ = 'batches'
    id: Optional[int] = Field(primary_key=True, default=None)
    name: str
    description: str
    pipeline_id: Optional[int] = Field(default=None, foreign_key='pipelines.id')
    pipeline: Optional['Pipeline'] = Relationship(back_populates='batches')
    media_files: List[MediaFile] = Relationship(
        back_populates='batches', link_model=MediaFileBatchLink
    )
    metaflow_runs: List['MetaflowRun'] = Relationship(back_populates='batch')

    def unstarted_guids(self) -> set:
        """Returns the set of GUIDs that are not currently running"""
        ids: set = {media_file.guid for media_file in self.media_files}
        running_guids: set = {run.media_file.guid for run in self.metaflow_runs}
        return ids - running_guids

    async def __admin_repr__(self, request: Request) -> str:
        return f'{self.name or self.id}'

    async def __admin_select2_repr__(self, request: Request) -> str:
        return f'<span><strong>{self.name or self.id}</span>'


class ClamsAppPipelineLink(SQLModel, table=True):
    clams_app_id: Optional[int] = Field(
        default=None, foreign_key='clams_apps.id', primary_key=True
    )
    pipeline_id: Optional[int] = Field(
        default=None, foreign_key='pipelines.id', primary_key=True
    )


class ClamsApp(SQLModel, table=True):
    __tablename__ = 'clams_apps'
    id: Optional[int] = Field(primary_key=True, default=None)
    name: str
    endpoint: AnyHttpUrl
    description: str
    pipelines: List['Pipeline'] = Relationship(
        back_populates='clams_apps', link_model=ClamsAppPipelineLink
    )

    async def __admin_repr__(self, request: Request):
        return f'{self.name or self.id}'

    async def __admin_select2_repr__(self, request: Request):
        return f'<span><strong>{self.name}</span>'


class Pipeline(SQLModel, table=True):
    __tablename__ = 'pipelines'
    id: Optional[int] = Field(primary_key=True, default=None)
    name: str
    description: str
    clams_apps: List[ClamsApp] = Relationship(
        back_populates='pipelines', link_model=ClamsAppPipelineLink
    )
    batches: List[Batch] = Relationship(back_populates='pipeline')

    async def __admin_repr__(self, request: Request):
        return f'{self.name or self.id}'

    async def __admin_select2_repr__(self, request: Request) -> str:
        return f'<span><strong>{self.name or self.id}</span>'


class MetaflowRun(SQLModel, table=True):
    __tablename__ = 'metaflow_runs'
    id: Optional[str] = Field(primary_key=True, default=None)
    pathspec: str
    batch_id: Optional[int] = Field(default=None, foreign_key='batches.id')
    batch: Optional[Batch] = Relationship(back_populates='metaflow_runs')
    media_file_id: Optional[str] = Field(default=None, foreign_key='media_files.guid')
    media_file: Optional[MediaFile] = Relationship(back_populates='metaflow_runs')
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), default=datetime.utcnow)
    )
    finished: bool = Field(default=False)
    finished_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), default=None)
    )
    successful: Optional[bool] = Field(default=None)
    current_step: Optional[str] = Field(default=None)
    current_task: Optional[str] = Field(default=None)

    @property
    def source(self):
        # TODO: is setting namespace to None the right way to go here?
        namespace(None)
        return Run(self.pathspec)
