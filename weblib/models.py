#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
import mimetypes
import re
from os.path import join

from flask import request
from flask_babel import lazy_gettext as _l
from flask_login import UserMixin
from peewee import BooleanField, DecimalField, ForeignKeyField, IntegerField, Metadata, TextField, make_snake_case
from playhouse.flask_utils import FlaskDB

from weblib.database import AbstractMigrator
from weblib.roles import AVAILABLE_ROLES, ROLE_ADMIN, ROLE_USER

for module in ("peewee", ):
	logging.getLogger(module).setLevel(logging.INFO)

_LOGGER = logging.getLogger(__name__)


flask_db = FlaskDB()


class PriceField(DecimalField):
	units = "€"

	def __init__(self, *args, **kwargs):
		kwargs['decimal_places'] = 2
		DecimalField.__init__(self, *args, **kwargs)


class FileField(TextField):
	# TODO manage deletion. For now on, the filename is removed from the DB but the file itself is not removed from the filesystem

	mime2fa = {
		'': "-archive",
		'': "-audio",
		'': "-code",
		'': "-excel",
		'': "-image",
		'': "-movie",
		'application/pdf': "-pdf",
		'': "-photo",
		'': "-picture",
		'': "-powerpoint",
		'': "-text",
		'': "-text",
		'': "-video",
		'': "-word",
		'': "-zip",
	}

	def renderer(self, field_value):
		try:
			fa_suffix = self.mime2fa.get(mimetypes.guess_type(field_value)[0], "")
			return f'<a class="fa-solid fa-file{fa_suffix}" href="{join(request.root_url + request.path.strip("/"), "upload", field_value)}"></a>'
		except TypeError:
			return ""


class DatabaseVersionException(Exception):
	pass


class _BaseMetadata(Metadata):

	def make_table_name(self):
		if self.legacy_table_names:
			name = re.sub(r'model$', '', self.name)
			return re.sub(r'[^\w]+', '_', name)
		return make_snake_case(re.sub(r'model$', '', self.model.__name__.lower()))


class BaseModel(flask_db.Model):

	class Meta:
		model_metadata_class = _BaseMetadata


class DatabaseVersionModel(BaseModel):
	lib = IntegerField(null=True, unique=True)
	app = IntegerField(null=True, unique=True)


class User(UserMixin, BaseModel):
	username = TextField(unique=True)
	username.i18n = _l("User name")
	password = TextField()
	first_name = TextField()
	first_name.i18n = _l("First name")
	last_name = TextField()
	last_name.i18n = _l("Last name")
	active = BooleanField(default=True)
	roles = TextField()  # not used anymore. Keep it for DB migration

	def __init__(self, *args, **kwargs):
		super(User, self).__init__(*args, **kwargs)
		query = (UserRole
			.select(RoleModel.name)
			.where(UserRole.user == self.id)
			.join(RoleModel)
		)
		self.roles = tuple(r.role.name for r in query)
		_LOGGER.debug("Current user roles are '%s'", self.roles)

	@property
	def is_active(self):
		return self.active

	@property
	def is_admin(self):
		return ROLE_ADMIN in self.roles

	def get_id(self):
		return str(self.id)


class RoleModel(BaseModel):
	name = TextField(unique=True)
	name.i18n = _l("Role")


class UserRole(BaseModel):
	user = ForeignKeyField(User)
	role = ForeignKeyField(RoleModel)


WEBLIB_MODELS = [
	DatabaseVersionModel,
	User,
	RoleModel,
	UserRole,
]


VERSION = 4


class MigratorException(Exception):
	pass


class Migrator(AbstractMigrator):

	def migrate_to_version_2(self):
		self._migrate(self._migrator.add_column('user', 'roles', TextField(default="user")))

	def migrate_to_version_3(self):
		ROLES_SEP = ','
		for user in User.select():
			roles = user.roles
			_LOGGER.info("Current '%s' roles : '%s'", user.username, roles)
			roles = ROLES_SEP.join([r for r in roles.split(ROLES_SEP) if r != "user"])
			_LOGGER.info("New '%s' roles : '%s'", user.username, roles)
			query = User.update({'roles': roles}).where(User.id == user.id)
			if query.execute() != 1:
				raise MigratorException("Could not upgrade roles")

	def migrate_to_version_4(self):
		ROLES_SEP = ','
		_LOGGER.info("Creating tables RoleModel and UserRole")
		self._db.create_tables((RoleModel, UserRole))
		for role in AVAILABLE_ROLES:
			if RoleModel.get_or_none(name=role) is None:
				_LOGGER.info("Populating roles table with '%s'", role)
				RoleModel.create(name=role)
		roles_map = {}
		for role in RoleModel.select():
			roles_map[role.name] = role.id
		for user_id, roles in User.select(User.id, User.roles).tuples():
			for role in roles.split(ROLES_SEP):
				if role == "manager":
					role = ROLE_USER
				_LOGGER.info("Populating UserRole table with %s,%s", user_id, role)
				UserRole.create(user=user_id, role=roles_map[role])
