#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from os import environ
from os.path import basename, dirname

if environ.get('APP_MODULE') == "testapp":
	import testapp
	print(testapp.__path__)
	from testapp import CONFIG_SECRETS
	from testapp.models import MODELS
	from testapp.models import VERSION as WEBAPP_VERSION
	from testapp.models import Migrator
	from testapp.roles import AVAILABLE_ROLES
	from testapp.views import all_views
	APP_REPO_NAME = basename(dirname(testapp.__path__[0]))
else:
	import webapp
	from webapp import CONFIG_SECRETS
	from webapp.models import MODELS
	from webapp.models import VERSION as WEBAPP_VERSION
	from webapp.models import Migrator
	from webapp.roles import AVAILABLE_ROLES
	from webapp.views import all_views
	APP_REPO_NAME = basename(dirname(webapp.__path__[0]))
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

from weblib.flask_app import FlaskApp
from weblib.views import user_views

_LOGGER = logging.getLogger(__name__)


try:
	if environ.get('APP_MODULE') == "testapp":
		from testapp import populate_db
	else:
		from webapp.data import populate_db
	_LOGGER.info("Found a DB populator")
except ImportError:
	_LOGGER.info("No DB populator found")
	populate_db = None


def create_app(cleanup=False, cleanup_app_part=False, database_name="", is_disable_client_cache=False):
	config_dict = {
		# Generate the key with: secrets.token_urlsafe()
		'SECRET_KEY': bytes(CONFIG_SECRETS['session_key'], encoding='utf8'),
		'OVERRIDEN_DATABASE_NAME': database_name or environ.get('DATABASE_NAME', ""),
	}
	return FlaskApp(
			config_dict,
			MODELS,
			(user_views, ) + all_views,
			WEBAPP_VERSION,
			Migrator,
			roles=AVAILABLE_ROLES,
			app_repo_name=APP_REPO_NAME,
			is_disable_client_cache=is_disable_client_cache,
			populate_function=populate_db,
		).create_app(cleanup=cleanup, cleanup_app_part=cleanup_app_part)


if __name__ == "__main__":
	for logger in ("werkzeug", ):
		logging.getLogger(logger).setLevel(logging.INFO)
	server_port = environ['FLASK_PORT']
	_LOGGER.info("Will run Flask app on port '%s'", server_port)
	create_app(
		cleanup_app_part=environ.get('CLEANUP_DB', False),
		is_disable_client_cache=True,
	)[0].run(host="0.0.0.0", port=server_port)
