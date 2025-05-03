#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from os import environ

from bcrypt import checkpw
from flask import request
from flask_babel import gettext as _, lazy_gettext as _l
from markupsafe import Markup
from weblib.requests import get_roles_choices, get_user_by_username
from werkzeug.datastructures import MultiDict

from weblib.forms.fields import BooleanField, FileField, HiddenField, PasswordField, SelectField, TextField


_LOGGER = logging.getLogger(__name__)


class UnknownFieldException(Exception):
	pass


class BaseForm:
	_is_initialized = False

	def __new__(cls, *_args, **_kwargs):
		if not cls._is_initialized:
			cls.form_name = cls.__name__.lower()
			_LOGGER.info(f"Initializing from '{cls.form_name}'")
			upload_dir = environ.get('UPLOAD_DIR', environ['HOME'])
			is_first_field = True
			for name, field in cls.fields.items():
				field.name = name
				field.form_name = cls.form_name
				field.upload_dir = upload_dir
				if not isinstance(field, HiddenField):
					field.is_first_field = is_first_field
					is_first_field = False
				try:
					model_field = field.label
					field.label = getattr(model_field, name).i18n
					field.units = getattr(model_field, name).units
				except AttributeError:
					pass
			cls.fields['id'] = HiddenField()
			cls.fields['id'].name = "id"
			cls._is_initialized = True
		return super(BaseForm, cls).__new__(cls)

	def __init__(self, db_dict=None, request_object=request):
		"""
		The data of the form's fields are populated from the dict of the Flask request's form. If the db_dict parameter is set,
		the form's fields are populated from this dict and it is assumed that the dict is comming from a DB query.

		"""
		self.request_object = request_object
		if db_dict is None:
			form_dict = request_object.form
			is_from_db = False
			_LOGGER.debug("Form instanciated from request '%s'", form_dict)
		else:
			form_dict = db_dict
			is_from_db = True
			_LOGGER.debug("Form instanciated from DB '%s'", form_dict)
		for key in self.fields:
			self.fields[key].form = self
			self.fields[key].data = self.fields[key].default
			if form_dict and isinstance(self.fields[key], BooleanField):
				self.fields[key].data = False
			self.fields[key].selected_parent_value = None
			self.fields[key].error_messages = []
		for key, value in (form_dict.items(multi=True) if isinstance(form_dict, MultiDict) else form_dict.items()):
			if key not in self.fields:
				_LOGGER.warning(f"Field '{key}' is not declared in this form")
				continue
			try:
				formatted_value = value if is_from_db else self.fields[key].from_repr(value)
			except:
				_LOGGER.exception("Could not format value '%s' for field '%s'", value, key)
				raise
			value = formatted_value if value != "" else None
			if self.fields[key].multiple:
				self.fields[key].add_data(value)
			else:
				self.fields[key].data = value

	@property
	def html(self):
		return str(self)

	def __str__(self):
		return Markup("\n".join([str(f) for f in self.fields.values()]))

	def __repr__(self):
		return self.__str__()

	def __getattr__(self, name):
		try:
			return self.fields[name]
		except KeyError:
			for key in self.fields:
				if name in key:
					return self.fields[key]
			raise UnknownFieldException(f"No field '{name}' found in '{self.fields}'")

	def validate(self):
		is_valid = True
		for field in self.fields.values():
			if field.validate():
				is_valid = False
		if is_valid:
			_LOGGER.info("Form is valid -> executing actions...")
			for field in self.fields.values():
				try:
					field.do_action()
				except TypeError:
					pass
		return is_valid

	@property
	def dict(self):
		"""
		Used for populating the DB

		"""
		return dict([(key, value.data) for key, value in self.fields.items() if key != 'id' and (not isinstance(value, FileField) or value.data is not None)])


def equal_to_field(field_name):

	def wrapped(form, field_data):
		if field_data != form.fields[field_name].data:
			return f'Must be identical to field "{_l(field_name)}"'

	return wrapped


def validate_username_unique(form, field_data):
	if get_user_by_username(field_data) is not None:
		return _('Username already exists')


class RegistrationForm(BaseForm):
	fields = {
		'username': TextField(_l("User name"),  required=True, validators=(validate_username_unique, )),
		'password': PasswordField(_l("Password"), required=True),
		'password_confirmation': PasswordField(_l("Password confirmation"), required=True, validators=(equal_to_field('password'), )),
		'first_name': TextField(_l("First name"), required=True),
		'last_name': TextField(_l("Last name"), required=True),
		'roles': SelectField(_l("Roles"), choices=get_roles_choices, multiple=True, required=True),
	}


class UserForm(BaseForm):
	fields = {
		'username': TextField(_l("User name"),  required=True),
		'first_name': TextField(_l("First name")),
		'last_name': TextField(_l("Last name"), required=True),
	}


class ModifyPasswordForm(BaseForm):
	fields = {
		'password': PasswordField(_l("Password"), required=True),
		'password_confirmation': PasswordField(_l("Password confirmation"), required=True, validators=(equal_to_field('password'), )),
	}


class ModifyRolesForm(BaseForm):
	fields = {
		'user_id': HiddenField(),
		'roles': SelectField(_l("Roles"), choices=get_roles_choices, multiple=True, required=True),
	}


def validate_username(form, field_data):
	form.user = get_user_by_username(field_data)  # Use the form as the user's holder for validating the password hereunder
	if form.user is None:
		return _("Invalid user")

def validate_password(form, field_data):
	if form.user is not None and not checkpw(form.password.data.encode(), form.user.password.encode()):
		return _("Invalid password")


class LoginForm(BaseForm):
	fields = {
		'username': TextField(_l("User name"), required=True, validators=(validate_username, )),
		'password': PasswordField(_l("Password"), required=True, validators=(validate_password, )),
	}

