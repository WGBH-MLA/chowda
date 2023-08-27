from datetime import datetime, timedelta
from typing import Any, ClassVar, Dict, List

from metaflow import Flow
from metaflow.exception import MetaflowNotFound
from metaflow.integrations import ArgoEvent
from sqlmodel import Session, select
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin import CustomView, action
from starlette_admin.contrib.sqlmodel import ModelView
from starlette_admin.exceptions import ActionFailed
from starlette_admin.fields import BaseField

from chowda.auth.utils import get_user
from chowda.db import engine
from chowda.fields import MediaFileCount, MediaFilesGuidsField
from chowda.models import Batch, Collection
from chowda.utils import validate_media_file_guids


class BaseModelView(ModelView):
    """Base permissions for all views"""

    def can_create(self, request: Request) -> bool:
        return get_user(request).is_clammer

    def can_delete(self, request: Request) -> bool:
        return get_user(request).is_clammer

    def can_edit(self, request: Request) -> bool:
        return get_user(request).is_clammer


class AdminModelView(ModelView):
    """Base Admin permissions for all protected views"""

    def is_accessible(self, request: Request) -> bool:
        user = get_user(request)
        return user.is_admin or user.is_clammer

    def can_create(self, request: Request) -> bool:
        return get_user(request).is_admin

    def can_delete(self, request: Request) -> bool:
        return get_user(request).is_admin

    def can_edit(self, request: Request) -> bool:
        return get_user(request).is_admin


class CollectionView(BaseModelView):
    exclude_fields_from_list: ClassVar[list[Any]] = [Collection.media_files]
    exclude_fields_from_detail: ClassVar[list[Any]] = [Collection.id]

    actions: ClassVar[list[Any]] = ['create_batch', 'create_multiple_batches']

    fields: ClassVar[list[Any]] = [
        'name',
        'description',
        MediaFileCount(),
        # 'media_files',  # default view
        MediaFilesGuidsField(
            'media_files',
            id='media_file_guids',
            label='GUIDs',
            exclude_from_detail=True,
        ),
        BaseField(
            'media_files',
            display_template='displays/collection_media_files.html',
            label='Media Files',
            exclude_from_edit=True,
            exclude_from_create=True,
            exclude_from_list=True,
        ),
    ]

    async def validate(self, request: Request, data: Dict[str, Any]):
        validate_media_file_guids(request, data)

    @action(
        name='create_batch',
        text='Create Batch',
        confirmation='Create a single Batch from these Collections?',
        submit_btn_text='Yep',
        submit_btn_class='btn-success',
    )
    async def create_batch(self, request: Request, pks: List[Any]) -> str:
        """Create a new batch from the combined collections"""
        try:
            with Session(engine) as db:
                collections = db.exec(
                    select(Collection).where(Collection.id.in_(pks))
                ).all()
                names = [collection.name for collection in collections]
                ids = [str(collection.id) for collection in collections]
                new_batch = Batch(
                    name=f'Batch from {", ".join(names)}',
                    description=f'Batch from {", ".join(ids)}',
                )
                for collection in collections:
                    new_batch.media_files += collection.media_files
                db.add(new_batch)
                db.commit()

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Created Batch from {", ".join(names)}'

    @action(
        name='create_multiple_batches',
        text='Create multiple Batches',
        confirmation='Create multiple Batches from these Collections?',
        submit_btn_text='Yep',
        submit_btn_class='btn-success',
    )
    async def create_multiple_batches(self, request: Request, pks: List[Any]) -> str:
        """Create multiple batches from the collections"""
        try:
            with Session(engine) as db:
                collections = db.exec(
                    select(Collection).where(Collection.id.in_(pks))
                ).all()
                names = [collection.name for collection in collections]
                for collection in collections:
                    new_batch = Batch(
                        name=f'Batch from {collection.name}',
                        description=f'Batch from Collection {collection.id!s}',
                    )
                    new_batch.media_files = collection.media_files
                    db.add(new_batch)
                db.commit()

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Created Batches from {", ".join(names)}'


class BatchView(BaseModelView):
    exclude_fields_from_create: ClassVar[list[Any]] = [Batch.id]
    exclude_fields_from_edit: ClassVar[list[Any]] = [Batch.id]
    exclude_fields_from_list: ClassVar[list[Any]] = [Batch.media_files]
    exclude_fields_from_detail: ClassVar[list[Any]] = [Batch.id]

    fields_default_sort: ClassVar[BaseField] = [(Batch.id, True)]

    actions: ClassVar[list[Any]] = [
        'start_batches',
        'duplicate_batches',
        'combine_batches',
    ]

    fields: ClassVar[list[Any]] = [
        'id',
        'name',
        'pipeline',
        'description',
        MediaFileCount(),
        MediaFilesGuidsField(
            'media_files',
            id='media_file_guids',
            label='GUIDs',
            exclude_from_detail=True,
        ),
        BaseField(
            'media_files',
            display_template='displays/batch_media_files.html',
            label='Media Files',
            exclude_from_edit=True,
            exclude_from_create=True,
            exclude_from_list=True,
            read_only=True,
        ),
    ]

    async def validate(self, request: Request, data: Dict[str, Any]):
        validate_media_file_guids(request, data)

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == 'start_batches':
            return get_user(request).is_clammer
        return await super().is_action_allowed(request, name)

    @action(
        name='start_batches',
        text='Start',
        confirmation='This might cost money. Are you sure?',
        submit_btn_text='Yep',
        submit_btn_class='btn-success',
    )
    async def start_batches(self, request: Request, pks: List[Any]) -> str:
        """Starts a Batch by sending a message to the Argo Event Bus"""
        try:
            for batch_id in pks:
                with Session(engine) as db:
                    batch = db.get(Batch, batch_id)
                    for media_file in batch.media_files:
                        publish_return_value = ArgoEvent(
                            batch.pipeline.name,
                            payload={'bach_id': batch_id, 'guid': media_file.guid},
                        ).publish(ignore_errors=False)

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Started {len(pks)} Batch(es)'

    @action(
        name='duplicate_batches',
        text='Duplicate',
        confirmation='Duplicate all selected Batches?',
        submit_btn_text='Indeed!',
        submit_btn_class='btn-success',
    )
    async def duplicate_batches(self, request: Request, pks: List[Any]) -> str:
        """Create a new batch from the selected batch"""
        try:
            with Session(engine) as db:
                for batch_id in pks:
                    existing_batch = db.get(Batch, batch_id)
                    new_batch_params = existing_batch.dict()
                    new_batch_params.pop('id')
                    new_batch_params['name'] += ' [COPY]'
                    new_batch = Batch(**new_batch_params)
                    new_batch.media_files = existing_batch.media_files
                    db.add(new_batch)
                db.commit()

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Duplicated {len(pks)} Batch(es)'

    @action(
        name='combine_batches',
        text='Combine',
        confirmation='Combine all selected Batches into a new Batch?',
        submit_btn_text='Heck yeah!',
        submit_btn_class='btn-success',
    )
    async def combine_batches(self, request: Request, pks: List[Any]) -> str:
        """Merge multiple batches into a new batch"""
        try:
            with Session(engine) as db:
                batches = db.exec(select(Batch).where(Batch.id.in_(pks))).all()
                # TODO: What are the best defaults for a newly combined Batch?
                new_batch = Batch(
                    name=f'Combination of {len(batches)} Batches',
                    description=f'Combination of {len(batches)} Batches',
                )

                for batch in batches:
                    new_batch.media_files += batch.media_files

                db.add(new_batch)
                db.commit()

        except Exception as error:
            raise ActionFailed(f'{error!s}') from error

        # Display Success message
        return f'Combined {len(pks)} Batch(es)'


class MediaFileView(BaseModelView):
    pk_attr = 'guid'
    actions = ['create_new_batch']

    fields: ClassVar[list[Any]] = [
        'guid',
        'collections',
        'batches',
        'assets',
        'mmif_json',
    ]
    exclude_fields_from_list: ClassVar[list[str]] = ['mmif_json']

    def can_create(self, request: Request) -> bool:
        return get_user(request).is_admin

    @action(
        name='create_new_batch',
        text='Create Batch',
        confirmation='Create a Batches from these Media Files?',
        submit_btn_text='Yasss!',
        submit_btn_class='btn-success',
    )
    async def create_new_batch(self, request: Request, pks: List[Any]) -> str:
        return "TODO: code created batch"


class UserView(AdminModelView):
    fields: ClassVar[list[Any]] = ['first_name', 'last_name', 'email']


class ClamsAppView(BaseModelView):
    fields: ClassVar[list[Any]] = ['name', 'endpoint', 'description', 'pipelines']


class PipelineView(AdminModelView):
    fields: ClassVar[list[Any]] = ['name', 'description', 'clams_apps']

    def is_accessible(self, request: Request) -> bool:
        return True


class DashboardView(CustomView):
    def sync_history(self) -> Dict[str, Any]:
        try:
            return [
                {'created_at': sync_run.created_at, 'successful': sync_run.successful}
                for sync_run in list(Flow('IngestFlow'))[:10]
            ]
        except MetaflowNotFound:
            return []

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        history = self.sync_history()
        user = get_user(request)
        sync_disabled = datetime.now() - history[0]['created_at'] < timedelta(
            minutes=15
        )
        return templates.TemplateResponse(
            'dashboard.html',
            {
                'request': request,
                'user': user,
                'sync_history': history,
                'sync_disabled': sync_disabled,
                'flash': request.session.pop('flash', ''),
                'error': request.session.pop('error', ''),
            },
        )


class SonyCiAssetView(AdminModelView):
    fields: ClassVar[list[Any]] = [
        'name',
        'size',
        'type',
        'format',
        'thumbnails',
        'media_files',
    ]

    def can_create(self, request: Request) -> bool:
        """Sony Ci Assets are ingested from Sony Ci API, not created from the UI."""
        return False
