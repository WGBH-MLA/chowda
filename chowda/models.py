"""Models

SQLModels for DB and validation
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import AnyHttpUrl, BaseModel, EmailStr, stricturl
from sqlalchemy import JSON, Column
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, Relationship, SQLModel, String
from starlette.requests import Request

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


class MediaType(Enum):
    VIDEO = 'Video'
    AUDIO = 'Audio'


class ThumbnailType(Enum):
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
    """Media file model

    Attributes:
        id: SonyCi asset id
        guid: asset guid
    """

    __tablename__ = 'media_files'
    id: Optional[str] = Field(primary_key=True)
    guid: str = Field(index=True)
    mmif_json: Dict[str, Any] = Field(sa_column=Column(JSON), default=None)
    collections: List['Collection'] = Relationship(
        back_populates='media_files', link_model=MediaFileCollectionLink
    )
    batches: List['Batch'] = Relationship(
        back_populates='media_files', link_model=MediaFileBatchLink
    )
    clams_events: List['ClamsEvent'] = Relationship(back_populates='media_file')

    async def __admin_repr__(self, request: Request):
        return self.guid

    async def __admin_select2_repr__(self, request: Request) -> str:
        return f'<span><strong>{self.guid}</strong></span>'


class SonyCiAssetThumbnail(SQLModel):
    type: ThumbnailType
    location: str
    size: int
    width: int
    height: int


class SonyCiAsset(SQLModel, table=True):
    __tablename__ = 'sonyci_assets'
    id: Optional[str] = Field(primary_key=True)
    name: str
    size: int
    type: Optional[MediaType] = Field(default=None)
    # thumbnails: Optional[List[SonyCiAssetThumbnail]] = Field(
    #     sa_column=Column(JSON), default=None
    # )
    # thumbnails: List[SonyCiAssetThumbnail]
    # thumbnails: Optional[Set[str]] = Field(
    #     default=None, sa_column=Column(postgresql.ARRAY(String()))
    # )
    thumbnails: Optional[List[str]] = Field(sa_column=Column(JSON), default=None)
    description: Optional[str] = Field(default=None)


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
        return f'<span><strong>{self.clams_app.name}:</strong> {self.status}</span>'
