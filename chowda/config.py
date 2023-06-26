from os import environ

ENVIRONMENT = environ.get('ENVIRONMENT', 'development')
DB_USER = environ.get('DB_USER', 'postgres')
DB_PASSWORD = environ.get('DB_PASSWORD', 'postgres')
DB_HOST = environ.get('DB_HOST', 'localhost')
DB_NAME = 'chowda'
DB_PORT = environ.get('DB_PORT', '5432')
DB_URL = environ.get(
    'DB_URL', f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
DEBUG = bool(environ.get('DEBUG', ENVIRONMENT == 'development'))

TEMPLATES_DIR = environ.get('TEMPLATES_DIR', 'templates')
STATIC_DIR = environ.get('STATIC_DIR', 'static')
