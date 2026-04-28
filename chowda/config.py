from os import environ

DB_USER = environ.get('DB_USER', 'postgres')
DB_PASSWORD = environ.get('DB_PASSWORD', 'postgres')
DB_HOST = environ.get('DB_HOST', 'localhost')
DB_NAME = environ.get('DB_NAME', 'chowda')
DB_PORT = environ.get('DB_PORT', '5432')
DB_URL = environ.get(
    'DB_URL', f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
DEBUG = bool(environ.get('DEBUG'))

TEMPLATES_DIR = environ.get('TEMPLATES_DIR', 'templates')
STATIC_DIR = environ.get('STATIC_DIR', 'static')

AUTH_CLIENT_ID = environ.get('AUTH_CLIENT_ID')
AUTH_CLIENT_SECRET = environ.get('AUTH_CLIENT_SECRET')
AUTH_DOMAIN = environ.get('AUTH_DOMAIN')
AUTH_JWKS_URL = f'https://{AUTH_DOMAIN}/.well-known/jwks.json'
AUTH_API_AUDIENCE = environ.get('AUTH_API_AUDIENCE', 'https://chowda.wgbh-mla.org/api')
AUTH_METADATA_CONFIG = environ.get(
    'AUTH_METADATA_CONFIG', '.well-known/openid-configuration'
)
AUTH_LOGOUT_PATH = environ.get('AUTH_LOGOUT_PATH', 'v2/logout')
AUTH_ACCESS_TOKEN_PATH = environ.get('AUTH_ACCESS_TOKEN_PATH', 'oauth/token')
AUTH_AUTHORIZATION_PATH = environ.get(
    'AUTH_AUTHORIZATION_PATH', '/login/oauth/authorize'
)

SECRET = environ.get('CHOWDA_SECRET')

MMIF_S3_BUCKET_NAME = environ.get('MMIF_S3_BUCKET_NAME', 'clams-mmif')

MARIO_URL = environ.get('MARIO_URL', 'https://mario.wgbh-mla.org/')
