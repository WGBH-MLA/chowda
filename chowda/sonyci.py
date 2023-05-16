from sonyci import SonyCi
from os import getenv

ci_config_file = getenv('CI_CONFIG', 'ci.toml')


ci = SonyCi.load(toml_filename=ci_config_file)
