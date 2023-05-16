"""Models

SQLModels for DB and validation
"""

from typing import Any, Dict, List, Optional
from pydantic import AnyHttpUrl, EmailStr, stricturl
from sqlalchemy import JSON, Column
from starlette.requests import Request
from sqlmodel import Field, Relationship, SQLModel

from enum import Enum

from sonyci import SonyCi

# TODO: find a better place for this?
ci = SonyCi.load(toml_filename='ci.toml')

MediaUrl = stricturl(allowed_schemes=['video', 'audio', 'text'], tld_required=False)
"""Media url validator. Must have prefix of video, audio, or text. No TLD required.
Example:
    video://*
"""


class AppStatus(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETE = 'complete'
    FAILED = 'failed'


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
    media_file_id: Optional[int] = Field(
        default=None, foreign_key='media_files.id', primary_key=True
    )
    collection_id: Optional[int] = Field(
        default=None, foreign_key='collections.id', primary_key=True
    )


class MediaFileBatchLink(SQLModel, table=True):
    media_file_id: Optional[int] = Field(
        default=None, foreign_key='media_files.id', primary_key=True
    )
    batch_id: Optional[int] = Field(
        default=None, foreign_key='batches.id', primary_key=True
    )


class MediaFile(SQLModel, table=True):
    __tablename__ = 'media_files'
    id: Optional[int] = Field(primary_key=True)
    guid: str = Field(index=True)
    mmif_json: Dict[str, Any] = Field(sa_column=Column(JSON), default=None)
    collections: List['Collection'] = Relationship(
        back_populates='media_files', link_model=MediaFileCollectionLink
    )
    batches: List['Batch'] = Relationship(
        back_populates='media_files', link_model=MediaFileBatchLink
    )
    clams_events: List['ClamsEvent'] = Relationship(back_populates='media_file')

    @property
    def sonyci_asset(self):
        if len(self.sonyci_assets_found) > 1:
            raise f'Found {len(self.sonyci_assets_found)} Sony Ci files for GUID="{self.guid}".'  # noqa: E501

        if len(self.sonyci_assets_found) == 0:
            raise f'No Sony Ci Asset found for GUID="{self.guid}"'

        return self.sonyci_assets_found[0]

    @property
    def sonyci_assets_found(self):
        return ci.workspace_search(query=self.guid[10:], kind='asset')

    async def __admin_repr__(self, request: Request):
        return self.guid

    async def __admin_select2_repr__(self, request: Request) -> str:
        return f'<span><strong>{self.guid}</strong></span>'


class Collection(SQLModel, table=True):
    __tablename__ = 'collections'
    id: Optional[int] = Field(primary_key=True)
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
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: str
    pipeline_id: Optional[int] = Field(default=None, foreign_key='pipelines.id')
    pipeline: Optional['Pipeline'] = Relationship(back_populates='batches')
    media_files: List[MediaFile] = Relationship(
        back_populates='batches', link_model=MediaFileBatchLink
    )
    clams_events: List['ClamsEvent'] = Relationship(back_populates='batch')

    async def __admin_repr__(self, request: Request):
        return f'{self.name or self.id}'

    async def __admin_select2_repr__(self, request: Request):
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
    id: Optional[int] = Field(primary_key=True)
    name: str
    endpoint: AnyHttpUrl
    description: str
    pipelines: List['Pipeline'] = Relationship(
        back_populates='clams_apps', link_model=ClamsAppPipelineLink
    )
    clams_events: List['ClamsEvent'] = Relationship(back_populates='clams_app')

    async def __admin_repr__(self, request: Request):
        return f'{self.name or self.id}'


class Pipeline(SQLModel, table=True):
    __tablename__ = 'pipelines'
    id: Optional[int] = Field(primary_key=True)
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


class ClamsEvent(SQLModel, table=True):
    __tablename__ = 'clams_events'
    id: Optional[int] = Field(primary_key=True)
    status: str
    response_json: Dict[str, Any] = Field(sa_column=Column(JSON))
    batch_id: Optional[int] = Field(default=None, foreign_key='batches.id')
    batch: Optional[Batch] = Relationship(back_populates='clams_events')
    clams_app_id: Optional[int] = Field(default=None, foreign_key='clams_apps.id')
    clams_app: Optional[ClamsApp] = Relationship(back_populates='clams_events')
    media_file_id: Optional[int] = Field(default=None, foreign_key='media_files.id')
    media_file: Optional[MediaFile] = Relationship(back_populates='clams_events')

    async def __admin_repr__(self, request: Request):
        return f'{self.clams_app.name}: {self.status}'

    async def __admin_select2_repr__(self, request: Request) -> str:
        return f'<span><strong>{self.clams_app.name}:</strong> {self.status}</span>'
