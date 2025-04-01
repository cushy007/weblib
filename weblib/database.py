#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging

from playhouse.migrate import PostgresqlMigrator, migrate

_LOGGER = logging.getLogger(__name__)


class AbstractMigrator:
	"""
	https://docs.peewee-orm.com/en/latest/peewee/playhouse.html#migrate

	"""

	def __init__(self, db, db_part, cur_version, target_version, set_db_version_factory):
		self._db = db
		self._migrator = PostgresqlMigrator(self._db)
		self._migrate = migrate
		self._db_part = db_part
		self._cur_version = cur_version
		self._target_version = target_version
		self._set_db_version_factory = set_db_version_factory

	def migrate(self):
		_LOGGER.info("Will migrate DB for '%s' if needed", self._db_part)
		with self._db.atomic():
			for version in range(self._cur_version + 1, self._target_version + 1):
				_LOGGER.warning("Migrating DB '%s' models to version '%d'", self._db_part, version)
				try:
					method = getattr(self, 'migrate_to_version_%d' % version)
				except AttributeError:
					_LOGGER.warning("Nothing to migrate in DB for version '%d'. This should not happen !", version)
					continue
				try:
					method()
				except:
					_LOGGER.exception("Something went wrong while upgrading '%s' models to version '%s'", self._db_part, version)
					raise
				else:
					self._set_db_version_factory(self._db_part, version)

