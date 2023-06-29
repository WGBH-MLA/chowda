from os import environ
from dotenv import load_dotenv, find_dotenv

ENVIRONMENT = environ.get('ENVIRONMENT', 'development')


dotenv_path = find_dotenv(
    filename=f'chowda/.env.{ENVIRONMENT}', raise_error_if_not_found=True
)


load_dotenv(dotenv_path, override=True)

DEBUG = bool(environ.get('DEBUG'))


DB_URL = environ.get('DB_URL')

TEMPLATES_DIR = environ.get('TEMPLATES_DIR', 'templates')
STATIC_DIR = environ.get('STATIC_DIR', 'static')
