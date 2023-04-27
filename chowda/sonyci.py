from pydantic import BaseModel
from requests import get, post
from requests_oauth2client import ApiClient, OAuth2Client
from requests_oauth2client.auth import OAuth2AccessTokenAuth
from requests_oauth2client.tokens import BearerToken


class SonyCi(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    base_url: str = 'https://api.cimediacloud.com/'
    token_url: str = 'https://api.cimediacloud.com/oauth2/token'
    username: str
    password: str
    client_id: str
    client_secret: str
    workspace_id: str | None = None
    token: dict | None = None
    oauth: OAuth2Client | None = None
    auth: OAuth2AccessTokenAuth | None = None
    client: ApiClient | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.oauth = OAuth2Client(
            token_endpoint=self.token_url,
            auth=(self.username, self.password),
            data={
                'grant_type': 'password',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            },
        )
        self.token: BearerToken = self.get_token()
        self.auth = OAuth2AccessTokenAuth(client=self.oauth, token=self.token)
        self.client = ApiClient(self.base_url, auth=self.auth)

    def get_token(self) -> BearerToken:
        response = post(
            self.token_url,
            auth=(self.username, self.password),
            data={
                'grant_type': 'password',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            },
        )
        assert response.status_code == 200, 'Token did not return 200'
        return BearerToken(**response.json())

    @property
    def workspace(self):
        return f'workspaces/{self.workspace_id}'
