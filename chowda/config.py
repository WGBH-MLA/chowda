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

AUTH0_CLIENT_ID = environ.get('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = environ.get('AUTH0_CLIENT_SECRET')
AUTH0_DOMAIN = environ.get('AUTH0_DOMAIN')
AUTH0_JWKS_URL = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
AUTH0_API_AUDIENCE = environ.get(
    'AUTH0_API_AUDIENCE', 'https://chowda.wgbh-mla.org/api'
)

SECRET = environ.get('CHOWDA_SECRET')

MMIF_S3_BUCKET_NAME = environ.get('MMIF_S3_BUCKET_NAME', 'clams-mmif')

MARIO_URL = environ.get('MARIO_URL', 'https://mario.wgbh-mla.org/')
