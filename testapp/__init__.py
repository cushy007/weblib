import logging
from logging import DEBUG
from os.path import dirname, join

from testapp.requests import create_child, create_color, create_parent
from weblib.utils import get_config, log_init

log_init(__name__, level=DEBUG, directory=None)

_LOGGER = logging.getLogger(__name__)


class InconsistentConfig(Exception):
	pass


CONFIG_FILEPATH = join(dirname(__file__), "..", "config.ini")
CONFIG_SECRETS = get_config(filepath=CONFIG_FILEPATH, section="secrets")
CONFIG_CUSTOMIZATION = get_config(filepath=CONFIG_FILEPATH, section="customization")


# app specific
def populate_db():
	colors = (
		{'name': 'Red'},
		{'name': 'Green'},
		{'name': 'Blue'},
	)
	for color in colors:
		create_color(**color)

	parents = (
		{'name': 'Alice'},
		{'name': 'Bob'},
	)
	for parent in parents:
		create_parent(**parent)

	children = (
		{'name': 'David'},
		{'name': 'Jeff'},
		{'name': 'Mark'},
		{'name': 'Jimmy'},
	)
	for child in children:
		create_child(**child)
