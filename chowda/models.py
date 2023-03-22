from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import AnyHttpUrl, BaseModel, EmailStr, stricturl
from pydantic import Field as PydField
from pydantic.color import Color
from sqlalchemy import JSON, Column, DateTime, Enum, String, Text

from sqlmodel import Field, Relationship, SQLModel

MediaUrl = stricturl(allowed_schemes=['video', 'audio', 'text'], tld_required=False)
"""Media url type. Must have prefix of video, audio, or text. No TLD required.
Example:
    video://*
"""


class User(SQLModel, table=True):
    __tablename__ = 'users'
    id: Optional[int] = Field(primary_key=True)
    email: EmailStr = Field(index=True)
    first_name: str = Field(min_length=3, index=True)
    last_name: str = Field(min_length=3, index=True)


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


class Collection(SQLModel, table=True):
    __tablename__ = 'collections'
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: str
    media_files: List['MediaFile'] = Relationship(
        back_populates='collections', link_model=MediaFileCollectionLink
    )


class Batch(SQLModel, table=True):
    __tablename__ = 'batches'
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: str
    media_files: List[MediaFile] = Relationship(
        back_populates='batches', link_model=MediaFileBatchLink
    )


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


class Pipeline(SQLModel, table=True):
    __tablename__ = 'pipelines'
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: str
    clams_apps: List[ClamsApp] = Relationship(
        back_populates='pipelines', link_model=ClamsAppPipelineLink
    )
    clams_events: List['ClamsEvent'] = Relationship(back_populates='pipeline')


class ClamsEvent(SQLModel, table=True):
    __tablename__ = 'clams_events'
    id: Optional[int] = Field(primary_key=True)
    status: str
    response_json: Dict[str, Any] = Field(sa_column=Column(JSON))
    pipeline_id: Optional[int] = Field(default=None, foreign_key='pipelines.id')
    pipeline: Optional[Pipeline] = Relationship(back_populates='clams_events')
    clams_app_id: Optional[int] = Field(default=None, foreign_key='clams_apps.id')
    clams_app: Optional[ClamsApp] = Relationship(back_populates='clams_events')
    media_file_id: Optional[int] = Field(default=None, foreign_key='media_files.id')
    media_file: Optional[MediaFile] = Relationship(back_populates='clams_events')
