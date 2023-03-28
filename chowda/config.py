from os import environ

PRODUCTION = bool(environ.get('PRODUCTION', False))

DATABASE_FILE = environ.get('DB_FILE', 'chowda.sqlite')
ENGINE_URI = environ.get('DB_URL', 'sqlite:///' + DATABASE_FILE)
