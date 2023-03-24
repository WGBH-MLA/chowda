from locust import HttpUser, task
from random import shuffle
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
        with self.client.rename_request('/admin/[app]/list'):
            for app in list(models):
                self.client.get(f'/admin/{app}/list')

    def create_from_factory(self, name, factory):
        factory = factory()
        widget = factory.build(id=None)
        self.client.post(f'/admin/{name}/create', widget.dict(exclude_none=True))

    @task
    def run_factories(self):
        for name in models:
            self.create_from_factory(name, models[name])
