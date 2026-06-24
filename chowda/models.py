"""Models

SQLModels for DB and validation
"""

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from metaflow import Run, namespace
from pydantic.networks import AnyHttpUrl, EmailStr
from sqlalchemy import JSON, Column, DateTime, Enum
from sqlalchemy.dialects import postgresql
from sqlmodel import AutoString, Field, Relationship, SQLModel
from starlette.requests import Request


class AppStatus(enum.Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETE = 'complete'
    FAILED = 'failed'


class MediaType(enum.Enum):
    """Media type enum
    Type of Media: video or audio.
    This is not the same as the format of the media file.

    # FIXME:
    Enum class attributes are the values that are stored in the database.
    The value of the class attribute is the value returned by SonyCi (for validation)
    But starlette-admin + SQLAlchemy send the value to the db, not the name.
    Therefore, we need to Capatalize the name to make it match the db value.
    """

    Audio = 'Audio'
    Video = 'Video'


class AssetType(enum.Enum):
    """Asset type enum
    Type of SonyCi asset: audio, video, or document / other.

    This is not the same as the `MediaType` of the asset (Audio or Video).

    Note: Assets with "status: Uploading" have no type
    """

    Audio = 'Audio'
    Video = 'Video'
    Image = 'Image'
    Document = 'Document'
    TimedText = 'TimedText'
    Other = 'Other'


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
    email: EmailStr = Field(unique=True, index=True, sa_type=AutoString)
    first_name: str = Field(min_length=3, index=True)
    last_name: str = Field(min_length=3, index=True)

    async def __admin_repr__(self, request: Request):
        return f'{self.first_name} {self.last_name}'


class MediaFileCollectionLink(SQLModel, table=True):
    media_file_id: Optional[str] = Field(
        default=None, foreign_key='media_files.guid', primary_key=True, index=True
    )
    collection_id: Optional[int] = Field(
        default=None, foreign_key='collections.id', primary_key=True, index=True
    )


class MediaFileBatchLink(SQLModel, table=True):
    media_file_id: Optional[str] = Field(
        default=None, foreign_key='media_files.guid', primary_key=True, index=True
    )
    batch_id: Optional[int] = Field(
        default=None, foreign_key='batches.id', primary_key=True, index=True
    )
    source_mmif_id: Optional[int] = Field(
        default=None, foreign_key='mmifs.id', index=True
    )


class MMIFBatchInputLink(SQLModel, table=True):
    mmif_id: Optional[int] = Field(
        default=None, foreign_key='mmifs.id', primary_key=True, index=True
    )
    batch_id: Optional[int] = Field(
        default=None, foreign_key='batches.id', primary_key=True, index=True
    )


class MediaFile(SQLModel, table=True):
    """Media file model

    Attributes:
        guid: MediaFile GUID
        assets: List of SonyCiAssets
        collections: List of Collections
        batches: List of Batches
        metaflow_runs: List of MetaflowRuns
        mmifs: List of MMIFs
    """

    __tablename__ = 'media_files'
    guid: Optional[str] = Field(primary_key=True, default=None, index=True)
    mmifs: List['MMIF'] = Relationship(back_populates='media_file')
    assets: List['SonyCiAsset'] = Relationship(back_populates='media_files')
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

class SonyCiAssetStatus(enum.Enum):
    """SonyCi Asset status
    Status of SonyCi asset
    
    ## Typical statuses
    Created - The asset record has been created in our database.
    Waiting - Once uploaded the asset's status will transition to Waiting to indicate it is waiting for backend processing jobs to begin (thumbnails, preview proxies, calculating MD5 checksum, extract technical metadata, check for viruses, etc.).
    Processing - Once those jobs begin its status moves to Processing.
    Complete - The status will go to Complete when all applicable thumbnails and preview proxies are finished (note: other jobs like calculating MD5 checksum, gathering technical metadata, and performing other verifications may not be completed even though the status is Complete).
    Failed - If a failure happens during upload the status will go to Failed.
    
    ## Other statuses
    Limited - There were problems generating thumbnails and/or preview proxies, The source file is still available for download.
    Virus Detected - A virus was found and the file is not downloadable and generally cannot be used in our system.
    Executable Detected - An executable file was found and the file is not downloadable and generally cannot be used in our system.
    Deleted - The file has been deleted.
    """
    
    Created = 'Created'
    Waiting = 'Waiting'
    Processing = 'Processing'
    Complete = 'Complete'
    Failed = 'Failed'
    Limited = 'Limited'
    VirusDetected = 'Virus Detected'
    ExecutableDetected = 'Executable Detected'
    Deleted = 'Deleted'

class SonyCiArchiveStatus(enum.Enum):
    """SonyCi archive status

    Accepted values:
    - Not archived
    - Archive in progress
    - Archived
    - Restore in progress
    - Restored
    """
    
    NotArchived = 'Not archived'
    ArchiveInProgress = 'Archive in progress'
    Archived = 'Archived'
    RestoreInProgress = 'Restore in progress'
    Restored = 'Restored'

class SonyCiRestoreStatus(enum.Enum):
    """SonyCi restore status

    Accepted values:
     - Not restored
     - Restore in progress
     - Restore failed
     - Restored
    """
    
    NotRestored = 'Not restored'
    RestoreInProgress = 'Restore in progress'
    RestoreFailed = 'Restore failed'
    Restored = 'Restored'
    
class SonyCiUploadTransferType(enum.Enum):
    """SonyCi upload transfer type
    Indicates how the asset was uploaded. 
    
    Valid values are:
    
    - SinglepartHttp
    - MultipartHttp
    - Aspera
    - Copy
    - FTP
    - WorkspaceSend
    """

    SinglepartHttp = 'SinglepartHttp'
    MultipartHttp = 'MultipartHttp'
    Aspera = 'Aspera'
    Copy = 'Copy'
    FTP = 'FTP'
    WorkspaceSend = 'WorkspaceSend'
    
class SonyCiAsset(SQLModel, table=True):
    """SonyCiAsset model"""
    __tablename__ = 'sonyci_assets'
    id: Optional[str] = Field(primary_key=True, index=True, default=None)
    name: str = Field(index=True)
    size: int = Field(sa_column=Column(postgresql.BIGINT))
    createdOn: Optional[datetime] = Field(default=None, index=True)
    modifiedOn: Optional[datetime] = Field(default=None, index=True)
    type: Optional[AssetType] = Field(sa_column=Column(Enum(AssetType), default=None))
    format: Optional[str] = Field(default=None, index=True)
    folder: Optional[str] = Field(default=None, index=True)
    md5Checksum: Optional[str] = Field(default=None, index=True)
    status: Optional[SonyCiAssetStatus] = Field(sa_column=Column(Enum(SonyCiAssetStatus), default=None))
    archive_status: Optional[SonyCiArchiveStatus] = Field(sa_column=Column(Enum(SonyCiArchiveStatus), default=None))
    restore_status: Optional[SonyCiRestoreStatus] = Field(sa_column=Column(Enum(SonyCiRestoreStatus), default=None))
    isDeleted: Optional[bool] = Field(default=None, index=True)
    isTrashed: Optional[bool] = Field(default=None, index=True)
    runtime: Optional[float] = Field(default=None, index=True)
    lastActivityOn: Optional[datetime] = Field(default=None, index=True)
    uploadCompleteDate: Optional[datetime] = Field(default=None, index=True)
    uploadTransferType: Optional[SonyCiUploadTransferType] = Field(sa_column=Column(Enum(SonyCiUploadTransferType), default=None))
    hasPlayableProxies: Optional[bool] = Field(default=None, index=True)
    generatingPlayableProxies: Optional[bool] = Field(default=None, index=True)
    thumbnails: Optional[List[Dict[str, Any]]] = Field(
        sa_column=Column(postgresql.ARRAY(JSON)), default=None
    )
    media_file_id: Optional[str] = Field(
        default=None, foreign_key='media_files.guid', index=True
    )
    media_files: Optional[MediaFile] = Relationship(back_populates='assets')

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
    output_mmifs: List['MMIF'] = Relationship(
        back_populates='batch_output',
        sa_relationship_kwargs={
            "primaryjoin": "Batch.id==MMIF.batch_output_id",
        },
    )

    input_mmifs: List['MMIF'] = Relationship(
        back_populates='batch_inputs',
        link_model=MMIFBatchInputLink,
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
        default=None, foreign_key='clams_apps.id', primary_key=True, index=True
    )
    pipeline_id: Optional[int] = Field(
        default=None, foreign_key='pipelines.id', primary_key=True, index=True
    )


class ClamsApp(SQLModel, table=True):
    __tablename__ = 'clams_apps'
    id: Optional[int] = Field(primary_key=True, default=None)
    name: str
    endpoint: AnyHttpUrl = Field(index=True, sa_type=AutoString)
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
    id: Optional[int] = Field(primary_key=True, default=None, index=True)
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
    id: Optional[str] = Field(primary_key=True, default=None, index=True)
    pathspec: str
    batch_id: Optional[int] = Field(default=None, foreign_key='batches.id', index=True)
    batch: Optional[Batch] = Relationship(back_populates='metaflow_runs')
    media_file_id: Optional[str] = Field(
        default=None, foreign_key='media_files.guid', index=True
    )
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

    mmif: Optional['MMIF'] = Relationship(back_populates='metaflow_run')

    @property
    def source(self):
        # TODO: is setting namespace to None the right way to go here?
        namespace(None)
        return Run(self.pathspec)


class MMIF(SQLModel, table=True):
    """MMIF model

    Attributes:
        id: Primary key
        created_at: Creation timestamp
        media_file_id: GUID
        media_file: MediaFile
        metaflow_run_id: MetaflowRun ID
        metaflow_run: MetaflowRun
        batch_output: Batch that generated this MMIF
        batch_inputs: Batch that uses this as an input
        mmif_location: S3 URL of the mmif
    """

    __tablename__ = 'mmifs'
    id: Optional[int] = Field(primary_key=True, default=None, index=True)
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), default=datetime.utcnow)
    )
    media_file_id: Optional[str] = Field(
        default=None, foreign_key='media_files.guid', index=True
    )
    media_file: Optional[MediaFile] = Relationship(back_populates='mmifs')
    metaflow_run_id: Optional[str] = Field(default=None, foreign_key='metaflow_runs.id')
    metaflow_run: Optional[MetaflowRun] = Relationship(back_populates='mmif')
    batch_output_id: Optional[int] = Field(default=None, foreign_key='batches.id')
    batch_output: Optional[Batch] = Relationship(
        back_populates='output_mmifs',
        sa_relationship_kwargs={
            "primaryjoin": "MMIF.batch_output_id==Batch.id",
        },
    )
    batch_inputs: List[Batch] = Relationship(
        back_populates='input_mmifs',
        link_model=MMIFBatchInputLink,
    )

    mmif_location: Optional[str] = Field(default=None)

    async def __admin_repr__(self, request: Request):
        return (
            f'{self.metaflow_run.batch.name}'
            if self.metaflow_run and self.metaflow_run.batch
            else self.id
        )

    async def __admin_select2_repr__(self, request: Request) -> str:
        text = (
            self.metaflow_run.batch.name
            if self.metaflow_run and self.metaflow_run.batch
            else self.id
        )
        return f'<span>{text}</span>'
