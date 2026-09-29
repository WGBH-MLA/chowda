from os import environ as env

ADMIN_SECRET_KEY = env.get('ADMIN_SECRET_KEY')

DB_USER = env.get('DB_USER', 'postgres')
DB_PASSWORD = env.get('DB_PASSWORD', 'postgres')
DB_HOST = env.get('DB_HOST', 'localhost')
DB_NAME = env.get('DB_NAME', 'chowda')
DB_PORT = env.get('DB_PORT', '5432')
DB_URL = env.get(
    'DB_URL', f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
DEBUG = bool(env.get('DEBUG'))

TEMPLATES_DIR = env.get('TEMPLATES_DIR', 'templates')
STATIC_DIR = env.get('STATIC_DIR', 'static')

AUTH_CLIENT_ID = env.get('AUTH_CLIENT_ID')
AUTH_CLIENT_SECRET = env.get('AUTH_CLIENT_SECRET')
AUTH_API_AUDIENCE = env.get('AUTH_API_AUDIENCE', 'https://chowda.wgbh-mla.org/api')
AUTH_JWKS_URL = env.get('AUTH_JWKS_URL')
AUTH_OPENID_URL = env.get('AUTH_OPENID_URL', '.well-known/openid-configuration')
AUTH_SCOPE = env.get('AUTH_SCOPE', 'openid profile email entitlements')

EVENTS_API_USERNAME = env.get('EVENTS_API_USERNAME')
EVENTS_API_PASSWORD = env.get('EVENTS_API_PASSWORD')

SECRET = env.get('CHOWDA_SECRET')

MMIF_S3_BUCKET_NAME = env.get('MMIF_S3_BUCKET_NAME', 'clams-mmif')

METAFLOW_URL = env.get('METAFLOW_URL')
