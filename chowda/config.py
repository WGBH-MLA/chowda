from os import environ

ENVIRONMENT = environ.get('ENVIRONMENT', 'development')
DB_URL = environ.get('DB_URL', 'sqlite:///chowda.development.sqlite')

TEMPLATES_DIR = environ.get('TEMPLATES_DIR', 'chowda/templates')
STATIC_DIR = environ.get('STATIC_DIR', 'chowda/static')
