from os import environ

ENVIRONMENT = environ.get('ENVIRONMENT', 'dev')

DB_FILE = environ.get('DB_FILE', 'chowda.sqlite')
DB_URL = environ.get('DB_URL', 'sqlite:///' + DB_FILE)

ECHO = True
