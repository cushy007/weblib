#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from os import environ

from flask import Flask, request
from flask_babel import Babel
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

from weblib.login import login_manager
from weblib.models import VERSION as WEBLIB_VERSION
from weblib.models import WEBLIB_MODELS
from weblib.models import Migrator as WeblibMigrator
from weblib.models import flask_db
from weblib.requests import get_app_db_version, get_lib_db_version, init_db_version, populate_roles, set_db_version
from weblib.roles import AVAILABLE_ROLES
from weblib.views import page_forbidden, page_server_error

_LOGGER = logging.getLogger(__name__)

def disable_client_cache(response):
	# response.cache_control.no_store = True
	# ~ if 'Cache-Control' not in response.headers:
	response.headers['Cache-Control'] = 'no-store, max-age=0'
	return response


def init_db(
		db,
		app_models,
		init_db_version_factory,
		cur_lib_db_version,
		cur_app_db_version,
		app_db_target_version,
		app_migrator,
		cleanup=False,
		cleanup_app_part=False,
		populate_function=None,
	):
	models_to_cleanup = WEBLIB_MODELS + app_models if not cleanup_app_part else app_models
	if cleanup or cleanup_app_part:
		_LOGGER.info("Cleaning up DB...")
		_LOGGER.info("Removing tables '%s'", models_to_cleanup)
		db.drop_tables(models_to_cleanup, safe=True, cascade=True)
	if cleanup or cleanup_app_part or cur_lib_db_version is None:
		_LOGGER.info("Create tables...")
		db.create_tables(models_to_cleanup, safe=True)
		if not cleanup and not cleanup_app_part:
			init_db_version_factory(app_db_target_version)
		if populate_function and cleanup_app_part:
			_LOGGER.info("Populating DB...")
			populate_function()
	else:
		for db_part, migrator_factory, cur_version, target_version in (
			("lib", WeblibMigrator, cur_lib_db_version, WEBLIB_VERSION),
			("app", app_migrator, cur_app_db_version, app_db_target_version),
		):
			migrator_factory(db, db_part, cur_version, target_version, set_db_version_factory=set_db_version).migrate()
	populate_roles()
	db.close()


class FlaskApp:

	def __init__(self,
			config_dict,
			models,
			blueprints,
			app_db_version,
			app_db_migrator,
			roles=(),
			is_disable_client_cache=False,
			app_repo_name="",
			populate_function=None,
		):
		self._config_dict = config_dict
		self._models = models
		self._blueprints = blueprints
		self._app_db_version = app_db_version
		self._app_db_migrator = app_db_migrator
		self._roles = roles
		self._app_repo_name = app_repo_name
		self._populate_function = populate_function
		self.app_module = environ.get('APP_MODULE', "webapp")
		self._app = Flask(__name__, static_folder=f"../../%s/{self.app_module}/static" % self._app_repo_name)
		global AVAILABLE_ROLES
		AVAILABLE_ROLES += roles or []
		_LOGGER.debug("AVAILABLE_ROLES are %s", AVAILABLE_ROLES)
		self._is_disable_client_cache = is_disable_client_cache

	def create_app(self, cleanup=False, cleanup_app_part=False):

		@self._app.route('/shutdown')
		def shutdown():
			shutdown_func = request.environ.get('werkzeug.server.shutdown')
			if shutdown_func is None:
				raise RuntimeError('Not running werkzeug')
			shutdown_func()
			return "Shutting down..."

		self._app.config.from_object(f"{self.app_module}.config")

		self._app.config['BABEL_TRANSLATION_DIRECTORIES'] = ";".join((
			"../../weblib/weblib/translations",
			"../weblib/translations",
			f"../../%s/{self.app_module}/translations" % self._app_repo_name,
		))
		_LOGGER.info("Translation directories are '%s'", self._app.config['BABEL_TRANSLATION_DIRECTORIES'])
		babel = Babel(self._app)

		@babel.localeselector
		def get_locale():
			return 'fr'

		DEV_MODE = (environ.get('FLASK_ENV') == "development")
		if DEV_MODE:
			self._app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
			#self._app.config['EXPLAIN_TEMPLATE_LOADING'] = True

		self._app.config['DATABASE'] = {
			'host': "localhost",
			'name': (
				self._config_dict.pop('OVERRIDEN_DATABASE_NAME')
				or self._app.config.get('OVERRIDEN_DATABASE_NAME')
				or self._app.config['PROJECT_REPO_NAME']
			),
			'engine': 'playhouse.pool.PooledPostgresqlDatabase',
			'user': environ.get('USER', ""),
		}
		self._app.config.update(self._config_dict)

		flask_db.init_app(self._app)
		lib_db_version = get_lib_db_version()
		app_db_version = get_app_db_version()
		_LOGGER.info("Initializing DB '%s'...", self._app.config['DATABASE']['name'])
		init_db(
			flask_db.database,
			self._models,
			init_db_version,
			lib_db_version,
			app_db_version,
			self._app_db_version,
			self._app_db_migrator,
			cleanup=cleanup,
			cleanup_app_part=cleanup_app_part,
			populate_function=self._populate_function,
		)

		login_manager.init_app(self._app)

		self._app.register_error_handler(403, page_forbidden)
		self._app.register_error_handler(500, page_server_error)
		for bp in self._blueprints:
			self._app.register_blueprint(bp)


		if self._is_disable_client_cache:
			self._app.after_request(disable_client_cache)

		return self._app, flask_db.database
