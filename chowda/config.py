from os import environ

from dotenv import find_dotenv, load_dotenv

CHOWDA_ENV = environ.get('CHOWDA_ENV', 'development')


dotenv_path = find_dotenv(filename=f'.env.{CHOWDA_ENV}')


load_dotenv(dotenv_path)

DEBUG = bool(environ.get('DEBUG'))


DB_URL = environ.get('DB_URL')

TEMPLATES_DIR = environ.get('TEMPLATES_DIR', 'templates')
STATIC_DIR = environ.get('STATIC_DIR', 'static')
