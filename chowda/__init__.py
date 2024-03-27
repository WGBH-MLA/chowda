from os import environ

from dotenv import find_dotenv, load_dotenv
from metaflow import namespace

from ._version import __version__

namespace(environ.get('METAFLOW_NAMESPACE'))


# Load dotenv file if present
CHOWDA_ENV = environ.get('CHOWDA_ENV', 'development')
dotenv_path = find_dotenv(filename=f'.env.{CHOWDA_ENV}')
load_dotenv(dotenv_path)

__all__ = ['__version__']
