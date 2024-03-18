from random import choice, randint, sample

from chowda.models import AppStatus

from .factories import (
    BatchFactory,
    ClamsAppFactory,
    CLAMSProvider,
    CollectionFactory,
    MediaFileFactory,
    PipelineFactory,
    UserFactory,
    factory_session,
)

status = list(AppStatus)


NUM_CLAMS_APPS = len(CLAMSProvider.app_names)


def seed(
    num_media_files: int = 1000,
    num_collections: int = 100,
    num_batches: int = 100,
    num_clams_apps: int = NUM_CLAMS_APPS,
    num_pipelines: int = 10,
    num_users: int = 10,
):
    """Seed the database with sample data."""
    # Create some sample Users
    UserFactory.create_batch(num_users)

    # Create some sample CLAMS Apps and Pipelines
    clams_apps = ClamsAppFactory.create_batch(num_clams_apps)
    pipelines = PipelineFactory.create_batch(num_pipelines)

    # Randomly assign CLAMS Apps to Pipelines
    for pipeline in pipelines:
        pipeline.clams_apps = sample(clams_apps, randint(1, num_clams_apps))

    # Create the sample MediaFiles, Collections, and Batches
    media_files = MediaFileFactory.create_batch(num_media_files)
    collections = CollectionFactory.create_batch(num_collections)
    batches = BatchFactory.create_batch(num_batches)

    # Assign each batch to a random pipeline
    for batch in batches:
        batch.pipeline = choice(pipelines)

    # Randomly assign all MediaFiles to 0-3 batches and to 1 collection
    for media_file in media_files:
        media_file.batches = sample(batches, randint(0, 3))
        media_file.collections = [choice(collections)]

    factory_session.commit()


if __name__ == '__main__':
    seed()
