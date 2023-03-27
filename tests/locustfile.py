from locust import HttpUser, task
from random import choice
from factories import (
    UserFactory,
    MediaFileFactory,
    CollectionFactory,
    ClamsAppFactory,
    PipelineFactory,
    BatchFactory,
    ClamsEventFactory,
)

models = {
    'user': UserFactory,
    'media-file': MediaFileFactory,
    'collection': CollectionFactory,
    'clams-app': ClamsAppFactory,
    'pipeline': PipelineFactory,
    'batch': BatchFactory,
    'clams-event': ClamsEventFactory,
}


def random_model():
    return choice(list(models.keys()))


class HomePageUser(HttpUser):
    @task
    def get_home(self):
        self.client.get('/')


class AdminUser(HttpUser):
    @task
    def get_admin(self):
        self.client.get('/admin/')

    @task
    def get_admin_with_redirect(self):
        self.client.get('/admin')

    @task
    def list_models(self):
        self.client.get(f'/admin/{random_model()}/list')

    def create_from_factory(self, name, factory):
        factory = factory()
        widget = factory.build(id=None)
        self.client.post(f'/admin/{name}/create', widget.dict(exclude_none=True))

    @task
    def run_factories(self):
        model = random_model()
        self.create_from_factory(model, models[model])
