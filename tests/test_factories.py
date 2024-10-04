from sqlmodel import SQLModel

from chowda.models import Batch, ClamsApp, MediaFile

from .factories import (
    BatchFactory,
    ClamsAppFactory,
    CollectionFactory,
    MediaFileFactory,
    PipelineFactory,
)


def test_media_file_factory():
    media_file = MediaFileFactory.create()
    assert type(media_file) is MediaFile


def test_media_file_with_batches():
    batches = BatchFactory.create_batch(2)
    media_file = MediaFileFactory.create(batches=batches)
    assert_related(media_file, batches=batches)


def test_media_file_with_collections():
    collections = CollectionFactory.create_batch(2)
    media_file = MediaFileFactory.create(collections=collections)
    assert_related(media_file, collections=collections)


def test_batch_factory():
    batch = BatchFactory.create(media_files=MediaFileFactory.create_batch(2))
    assert type(batch) is Batch


def test_batch_factory_with_media_files():
    media_files = MediaFileFactory.create_batch(2)
    batch = BatchFactory.create(media_files=media_files)
    assert_related(batch, media_files=media_files)


def test_clams_app_factory():
    clams_app = ClamsAppFactory.create()
    assert type(clams_app) is ClamsApp


def test_pipeline_factory_with_clams_apps():
    clams_apps = ClamsAppFactory.create_batch(2)
    pipeline = PipelineFactory.create(clams_apps=clams_apps)
    assert_related(pipeline, clams_apps=clams_apps)


def assert_related(model_instance: SQLModel, **kwargs):
    for relation_field, related in kwargs.items():
        if type(related) is SQLModel:
            assert related == getattr(model_instance, relation_field)
        else:
            for related_instance in list(related):
                assert related_instance in getattr(model_instance, relation_field)
