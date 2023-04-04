from factories import (
    factory_session,
    MediaFileFactory,
    BatchFactory,
    ClamsAppFactory,
    PipelineFactory,
    ClamsEventFactory,
    CollectionFactory,
)
from random import sample, randint, choice


def seed(
    num_media_files: int = 1000,
    num_collections: int = 100,
    num_batches: int = 100,
    num_clams_apps: int = 10,
    num_pipelines: int = 10,
    num_clams_events: int = 800,
):

    # Create some sample CLAMS Apps and Pipelines
    clams_apps = ClamsAppFactory.create_batch(num_clams_apps)
    pipelines = PipelineFactory.create_batch(num_pipelines)
    for pipeline in pipelines:
        pipeline.clams_apps = sample(clams_apps, randint(1, 4))

    media_files = MediaFileFactory.create_batch(num_media_files)
    collections = CollectionFactory.create_batch(num_collections)
    batches = BatchFactory.create_batch(num_batches)

    for batch in batches:
        batch.pipeline = choice(pipelines)

    # Randomly assign all media files to 0-3 batches and to 1 collection
    for media_file in media_files:
        media_file.batches = sample(batches, randint(0, 3))
        media_file.collections = [choice(collections)]

    for _ in range(num_clams_events):
        ClamsEventFactory.create(
            batch=choice(batches),
            media_file=choice(batch.media_files),
            clams_app=choice(batch.pipeline.clams_apps),
        )

    factory_session.commit()


seed()
