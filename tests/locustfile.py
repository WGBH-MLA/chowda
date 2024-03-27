from random import choice, randint

from factories import (
    BatchFactory,
    ClamsAppFactory,
    CollectionFactory,
    MediaFileFactory,
    PipelineFactory,
    UserFactory,
)
from locust import HttpUser, task

models = {
    'user': UserFactory,
    'media-file': MediaFileFactory,
    'collection': CollectionFactory,
    'clams-app': ClamsAppFactory,
    'pipeline': PipelineFactory,
    'batch': BatchFactory,
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

    def get_total(self, model: str) -> int:
        """Use the API to get the total number of records in this model"""
        response = self.client.get(f'/admin/api/{model}')
        results = response.json()
        return results['total']

    @task
    def get_model_detail(self):
        model = random_model()
        total = self.get_total(model)
        with self.client.rename_request(f'/admin/{model}/detail/[id]'):
            self.client.get(f'/admin/{random_model()}/detail/{randint(1, total)}')

    @task
    def edit_model(self):
        """Update the model through the admin route"""
        model = random_model()
        factory = models[model]()
        widget = factory.build(id=None)
        total = self.get_total(model)
        with self.client.rename_request(f'/admin/{model}/edit/[id]'):
            self.client.post(
                f'/admin/{model}/edit/{randint(1, total)}',
                widget.dict(exclude_none=True),
            )

    def create_from_factory(self, name, factory):
        """Create a new record using a factory"""
        factory = factory()
        widget = factory.build(id=None)
        self.client.post(f'/admin/{name}/create', widget.dict(exclude_none=True))

    @task
    def run_factories(self):
        model = random_model()
        self.create_from_factory(model, models[model])
