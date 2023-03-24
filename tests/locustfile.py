from locust import HttpUser, task
from random import shuffle
from factories import UserFactory

models = [
    'user',
    'media-file',
    'collection',
    'clams-app',
    'pipeline',
    'batch',
    'clams-event',
]


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
        model_list = models.copy()
        shuffle(model_list)
        with self.client.rename_request('admin/[app]/list'):
            for app in model_list:
                self.client.get(f'/admin/{app}/list')

    @task
    def create_user(self):
        uf = UserFactory()
        user = uf.build(id=None)
        self.client.post('/admin/user/create', data=user.dict(exclude_none=True))
