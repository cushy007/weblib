#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import datetime
import logging

from babel.dates import format_date, format_datetime
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from peewee import ProgrammingError

from weblib.models import VERSION as WEBLIB_VERSION
from weblib.models import DatabaseVersionException, DatabaseVersionModel, RoleModel, User, UserRole, flask_db
from weblib.roles import AVAILABLE_ROLES

_LOGGER = logging.getLogger(__name__)

class DatabaseException(Exception):
	pass


class TableRequestResult:

	def __init__(self, model_fields_to_display, query, model_fields_for_compute=None):
		self.model_fields_to_display = model_fields_to_display
		self.query = query
		self.model_fields_for_compute = model_fields_for_compute or []


def alias(field, alias_name, i18n):
	aliased_field = field.alias(alias_name)
	aliased_field.i18n = i18n
	return aliased_field


def translate_field(field_value, model_field=None, is_internationalizable=False):
	try:
		return model_field.renderer(field_value)
	except:
		pass #_LOGGER.debug("Model '%s' doesn't have a renderer -> will duck translate", model_field)
	if field_value is None:
		field_value = ""
	elif field_value is True:
		field_value = _("Yes")
	elif field_value is False:
		field_value = _("No")
	elif isinstance(field_value, datetime.date):
		if isinstance(field_value, datetime.datetime):  # FIXME don not consider < 1970 as a non populated field
			if field_value > datetime.datetime(1970, 1, 1):
				if getattr(model_field, 'display_date_only', False):
					field_value = format_date(field_value, "dd/MM/yyyy")
				else:
					field_value = format_datetime(field_value, "dd/MM/yyyy HH:mm")
			else:
				field_value = ""
		else:
			if field_value > datetime.date(1970, 1, 1):
				field_value = format_date(field_value, "dd/MM/yyyy")
			else:
				field_value = ""
	else:
		try:
			try:
				field_value = model_field.lut(field_value)
			except TypeError:
				field_value = str(model_field.lut.get(field_value))
			_LOGGER.debug("Translated field '%s' value -> '%s'", model_field.__name__, model_field)
		except AttributeError:
			field_value = str(field_value)

	return field_value


def translate_row(row, model_fields=None, internationalizable_fields=()):
	if not model_fields:
		model_fields = [None] * len(row)
	return tuple([
		translate_field(field_value, model_field=model_field, is_internationalizable=not internationalizable_fields or getattr(model_field, 'column_name', False) in internationalizable_fields)
		for field_value, model_field in zip(row, model_fields)
	])


def request_table(model_fields, query):
	header = dict([(field.column_name, {'i18n': field.i18n, 'values': ()}) for field in model_fields])
	return {'header': header, 'rows': tuple([(r[0], translate_row(r[1:], model_fields)) for r in query])}


def create_user(**kwargs):
	roles = kwargs.pop('roles', ())
	user = User.create(**kwargs)
	for role in roles:
		try:
			int(role)
		except ValueError:
			role = RoleModel.get(name=role).id
		UserRole.create(user=user, role=role)
	return user.id


def update_roles(modify_roles_dict):
	user_id = modify_roles_dict['user_id']
	UserRole.delete().where(UserRole.user == user_id).execute()
	for r in modify_roles_dict['roles']:
		UserRole.create(user=user_id, role=r)


def get_db_version(column):
	try:
		row = DatabaseVersionModel.get_or_none()
		try:
			return getattr(row, column)
		except:
			return None
	except ProgrammingError:
		_LOGGER.info("Table databaseversion does not exist")
		flask_db.database.close()


def get_lib_db_version():
	return get_db_version('lib')


def get_app_db_version():
	return get_db_version('app')


def set_db_version(column, number):
	try:
		cur_db_version = get_db_version(column)
		if number < cur_db_version:
			raise DatabaseVersionException("Can not decrease database version.")
		elif number == cur_db_version:
			raise DatabaseVersionException("Can not set database version to the same value.")
		query = DatabaseVersionModel.update({column: number}).where(DatabaseVersionModel.id == 1)
		if query.execute() != 1:
			raise DatabaseException("Could not update DB version")
	except DatabaseVersionException:
		_LOGGER.exception("Error while setting DB version.")
		raise


def init_db_version(app_version, lib_version=WEBLIB_VERSION):
	DatabaseVersionModel.create_table(safe=True)
	DatabaseVersionModel.create(id=1, lib=lib_version, app=app_version)


def set_lib_db_version(number):
	set_db_version('lib', number)


def set_app_db_version(number):
	set_db_version('app', number)


def has_any_registered_user():
	return bool(User.get_or_none())


def get_users():
	columns = [User.last_name, User.first_name, User.username]
	query = (User
		.select(User.id, User.last_name, User.first_name, User.username)
		.order_by(User.last_name)
		.tuples()
	)
	rows = [list(r) for r in query]

	query = (UserRole
		.select(UserRole.user, RoleModel.name)
		.join(RoleModel)
		.tuples()
	)

	roles = {}
	for row in query:
		try:
			roles[row[0]].append(row[1])
		except KeyError:
			roles[row[0]] = [row[1]]

	for row in rows:
		try:
			row.append(", ".join(sorted(roles.get(row[0], []))))
		except KeyError:
			pass

	return TableRequestResult(columns + [RoleModel.name], rows)


def get_user(user_id):
	query = (User
		.select()
		.where(User.id == user_id)
	)
	return query[0]


def get_user_by_username(username):
	user = User.get_or_none(username=username)
	_LOGGER.debug("User is '%s' for username '%s'", user, username)
	return user


def delete_user(user_id):
	query = UserRole.delete().where(UserRole.user == user_id)
	if query.execute() == 0:
		raise DatabaseException("Could not delete user '%s' roles" % user_id)
	query = User.delete().where(User.id == user_id)
	if query.execute() != 1:
		raise DatabaseException("Could not delete user '%s'" % user_id)


def populate_roles():
	for role in AVAILABLE_ROLES:
		if RoleModel.get_or_none(name=role) is None:
			_LOGGER.debug("Populating roles table with '%s'", role)
			RoleModel.create(name=role)


def get_roles_names():
	query = (RoleModel
		.select(RoleModel.name)
	)
	return tuple(r.name for r in query)


def get_roles_choices():
	query = (RoleModel
		.select(RoleModel.id, RoleModel.name)
	)
	return tuple((r.id, r.name) for r in query)


def get_user_roles(user_id):
	query = (UserRole
		.select(UserRole.role)
		.where(UserRole.user == user_id)
	)
	return tuple(r.role.id for r in query)
