from os import environ

ENVIRONMENT = environ.get('ENVIRONMENT', 'development')
DB_URL = environ.get('DB_URL', 'sqlite:///chowda.development.sqlite')
