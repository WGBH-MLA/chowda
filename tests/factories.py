from chowda.models import (
    MediaFile,
    Batch,
    Collection,
    ClamsApp,
    Pipeline,
    ClamsEvent,
    User,
)
import factory
from sqlalchemy import orm
from faker import Faker
from chowda.db import engine


# Create a factory-specific engine for factory data. This can be used to modify
# factory-generated data (see seeds.py)
factory_session = orm.scoped_session(orm.sessionmaker(engine))

fake = Faker()


class ChowdaFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = factory_session
        sqlalchemy_session_persistence = 'commit'


class UserFactory(ChowdaFactory):
    class Meta:
        model = User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')


class MediaFileFactory(ChowdaFactory):
    class Meta:
        model = MediaFile

    guid = factory.Faker('hexify', text='cpb-aacip-^^^-^^^^^^^^')

    @factory.post_generation
    def batches(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for batch in extracted:
                self.batches.append(batch)

    @factory.post_generation
    def collections(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for collection in extracted:
                self.collections.append(collection)


class CollectionFactory(ChowdaFactory):
    class Meta:
        model = Collection

    name = factory.Sequence(lambda n: 'Collection %d' % n)
    description = factory.Faker('text')


class BatchFactory(ChowdaFactory):
    class Meta:
        model = Batch

    name = factory.Sequence(lambda n: 'Batch %d' % n)
    description = factory.Faker('text')

    @factory.post_generation
    def media_files(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for media_file in extracted:
                self.media_files.append(media_file)


class ClamsAppFactory(ChowdaFactory):
    class Meta:
        model = ClamsApp

    name = factory.Faker("last_name_nonbinary")
    description = factory.Faker('text')
    endpoint = factory.Faker('url')

    @factory.post_generation
    def pipelines(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for pipeline in extracted:
                self.pipelines.append(pipeline)


class PipelineFactory(ChowdaFactory):
    class Meta:
        model = Pipeline

    name = factory.Faker('bs')
    description = factory.Faker('catch_phrase')

    @factory.post_generation
    def clams_apps(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for clams_app in extracted:
                self.clams_apps.append(clams_app)


class ClamsEventFactory(ChowdaFactory):
    class Meta:
        model = ClamsEvent

    status: str = "TODO: REPLACE WITH ENUM VAL"
    response_json: dict = {"TODO": "REPLACE WITH EXPECTED RESPONSE"}
