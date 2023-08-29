import factory
from faker.providers import BaseProvider
from sqlalchemy import orm

from chowda.db import engine
from chowda.models import (
    Batch,
    ClamsApp,
    Collection,
    MediaFile,
    Pipeline,
    User,
)


class CLAMSProvider(BaseProvider):
    """A custom Faker provider for generating CLAMS data"""

    app_names = (
        'Whisper',
        'OCR',
        'Slates',
        'NER',
        'Chyrons',
        'Credits',
        'Bars',
    )

    def app_name(self):
        return self.generator.random.choice(self.app_names)

    def guid(self):
        return (
            'cpb-aacip-'
            + str(self.generator.random_int())
            + '-'
            + self.generator.hexify(8 * '^')
        )

    def collection_name(self):
        if self.generator.random.choice([True, False]):
            return self.title() + ' Collection'
        return self.generator.name() + ' Collection'

    def batch_name(self):
        return f'Batch {self.random_int()}: {self.title()}'

    def title(self):
        num_words = self.generator.random.randint(1, 10)
        return self.generator.sentence(nb_words=num_words).title()[:-1]


factory.Faker.add_provider(CLAMSProvider)

# Create a factory-specific engine for factory data. This can be used to modify
# factory-generated data (see seeds.py)
factory_session = orm.scoped_session(orm.sessionmaker(engine))


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

    id = factory.Faker('sha256')

    guid = factory.Faker('guid')

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

    name = factory.Faker('collection_name')
    description = factory.Faker('text')


class BatchFactory(ChowdaFactory):
    class Meta:
        model = Batch

    name = factory.Faker('batch_name')
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

    @factory.sequence
    def name(n):  # noqa N805
        index = n % len(CLAMSProvider.app_names)
        return CLAMSProvider.app_names[index]

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
