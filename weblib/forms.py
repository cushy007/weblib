#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import hashlib
import json
import logging
import mimetypes
from datetime import datetime
from os import environ
from os.path import expanduser, join

from bcrypt import checkpw
from flask import request
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from markupsafe import Markup, escape
from werkzeug.datastructures import MultiDict

from weblib.requests import get_roles_choices, get_user_by_username

_LOGGER = logging.getLogger(__name__)


class UnknownFieldException(Exception):
	pass


def format_attribute(name, value):
	try:
		if value is None or value is False:
			return ""
		elif value is True:
			return name
		else:
			return f'{name.replace("_", "-")}="{value}"'
	except KeyError:
		# ~ _LOGGER.error(f"Trying to get a non existing attribute '{name}' on field '{self.name}'")
		return ""


class BaseField:
	"""
	Fields can have arbitrary HTML attributes passed by kwargs. The underscores (_) of the kwargs' keys are replaced by dashes (-) for building the HTML attribute's name.

	"""
	#ATTRIBUTES = ("required", "min", "max", "step", "multiple", "autocomplete")

	def __init__(self, label=None, default=None, validators=(), **attributes):
		"""
		param: validators is a list of functions taking (form, field_data) as parameters and returning None if OK or the
		error message to display in case of error

		"""
		self.name = "populated by the form"
		self.attributes = attributes
		self.label = label
		self.default = default
		self.readonly = False
		self._data = default
		self.validators = list(validators)
		self.error_messages = []

	def build_id(self):
		return self.name
		# ~ return '-'.join((self.db_id, self.name))

	@property
	def data(self):
		return self._data

	@data.setter
	def data(self, value):
		self._data = value

	def to_repr(self):
		return self.data

	def from_repr(self, value):
		return value

	def validate(self):
		self.error_messages = []
		if self.validators and self.data is None:
			_LOGGER.debug("By-pass validators for field '%s' because its value is None", self.name)
			return False
		for validator in self.validators:
			error_message = validator(self.form, self.data)
			if error_message:
				self.error_messages.append(error_message)
				_LOGGER.debug("Form validator returned error '%s'", self.error_messages)
		return bool(self.error_messages)

	def __getattr__(self, name):
		return self.attributes.get(name)

	def _build_attributes(self, attributes_dict=None):
		attributes_dict = self.attributes if attributes_dict is None else attributes_dict
		attributes = [format_attribute(name, attributes_dict[name]) for name in attributes_dict]
		attributes = [a for a in attributes if a]
		attributes = " ".join(attributes)
		if attributes:
			attributes = " " + attributes
		if self.is_first_field:
			attributes += " autofocus"
		if self.readonly:
			attributes += " readonly"
		return attributes

	def _get_errors(self):
		return f'<div class="invalid-field">{"<br>".join(self.error_messages)}</div>' if self.error_messages else ""

	def __str__(self):
		value = f' value="{self.to_repr()}"' if self.data is not None else ""
		attributes = self._build_attributes()
		units = getattr(self, 'units', None)
		if units is not None:
			pre_units = '<div class="input-group mb-3">'
			units = f'<span class="input-group-text">{units}</span></div>'
		else:
			pre_units = units = ""
		errors = self._get_errors()
		self.readonly = False
		return f"""<div class="form-group mb-3">
	<label for="{self.name}">{self.label}</label>
	{pre_units}<{self.html_tag} type="{self.html_type}" name="{self.name}" class="form-control{" is-invalid" if errors else ""}"{value}{attributes}></{self.html_tag}>{units}{errors}
</div>"""


class HiddenField(BaseField):

	def __str__(self):
		return f"""<input type="hidden" name="{self.name}" class="form-control" value="{self.data}"></input>"""


class TextField(BaseField):
	html_tag = "input"
	html_type = "text"


class PasswordField(BaseField):
	html_tag = "input"
	html_type = "password"

	def __str__(self):
		value = f' value="{self.to_repr()}"' if self.data is not None else ""
		attributes = self._build_attributes()
		units = "👁"
		if units is not None:
			pre_units = '<div class="input-group mb-3">'
			units = f'<span class="input-group-text not-a-text password-toggle" id="{self.build_id()}-toggle">{units}</span></div>'
		else:
			pre_units = units = ""
		error = f'<div class="invalid-field">{"".join(self.error_messages)}</div>' if self.error_messages else ""
		return f"""<div class="form-group mb-3">
	<label for="{self.name}">{self.label}</label>
	{pre_units}<{self.html_tag} type="{self.html_type}" id="{self.build_id()}" name="{self.name}" class="form-control{" is-invalid" if self.error_messages else ""}"{value}{attributes}></{self.html_tag}>{units}{error}
</div>"""


class TextAreaField(BaseField):

	def __str__(self):
		attributes = self._build_attributes()
		value = escape(self.data) if self.data is not None else ""
		return f"""<div class="form-group mb-3">
	<label for="{self.name}">{self.label}</label>
	<textarea name="{self.name}" class="form-control"{attributes}>{value}</textarea>
</div>"""


class IntegerField(BaseField):
	html_tag = "input"
	html_type = "number"

	def __init__(self, label, min=None, max=None, step=1, **common_kwargs):
		assert float(step) == int(step)
		BaseField.__init__(self, label, min=min, max=max, step=step, **common_kwargs)


class DecimalField(BaseField):
	html_tag = "input"
	html_type = "number"

	def __init__(self, label, min=None, max=None, step=0.5, **common_kwargs):
		assert float(step) != int(step)
		BaseField.__init__(self, label, min=min, max=max, step=step, **common_kwargs)
		self._coef = int(1 / step)

	# ~ def to_repr(self):
		# ~ return self.data / self._coef

	# ~ def from_repr(self, value):
		# ~ try:
			# ~ return int(float(value) * self._coef)
		# ~ except ValueError:
			# ~ return None


class PriceField(DecimalField):
	html_tag = "input"
	html_type = "number"

	def __init__(self, label, min=0, max=None, step=0.01, **common_kwargs):
		DecimalField.__init__(self, label, min=min, max=max, step=step, **common_kwargs)


class BooleanField(BaseField):
	html_tag = "input"
	html_type = "checkbox"

	def __init__(self, label, default=False, required=False, **common_kwargs):
		"""
		:param required: if set to True then the box must be checked by the user (eg. for terms of services)

		"""
		BaseField.__init__(self, label, default=default, **common_kwargs)

	@property
	def data(self):
		return self._data

	@data.setter
	def data(self, value):
		self._data = bool(value)

	def __str__(self):
		attributes = " checked" if bool(self.data) else ""
		return f"""<div class="form-group mb-3">
	<{self.html_tag} type="{self.html_type}" name="{self.name}"{attributes}></{self.html_tag}> <label for="{self.name}">{self.label}</label>
</div>"""


class DateField(BaseField):
	html_tag = "input"
	html_type = "date"

	def __init__(self, label, min=None, max=None, **common_kwargs):
		"""
		Default value can either be a datetime object, a string like "2025-02-13" or just the string "now"

		"""
		BaseField.__init__(self, label, min=min, max=max, **common_kwargs)
		if self.default not in (None, "now"):
			try:
				self.default = self.default.strftime("%Y-%m-%d")
			except AttributeError:
				_LOGGER.debug("Default date is already in text format: '%s'", self.default)

	def __str__(self):
		if self.default == "now" and self.data == "now":
			self.data = datetime.now().strftime("%Y-%m-%d")
		return BaseField.__str__(self)


class DateTimeField(BaseField):
	html_tag = "input"
	html_type = "datetime-local"

	def __init__(self, label, min=None, max=None, **common_kwargs):
		"""
		Default value can either be a datetime object, a string like "2025-02-13" or just the string "now"

		"""
		BaseField.__init__(self, label, min=min, max=max, **common_kwargs)
		if self.default not in (None, "now"):
			try:
				self.default = self.default.strftime("%Y-%m-%dT%H:%M")
			except AttributeError:
				_LOGGER.debug("Default date is already in text format: '%s'", self.default)

	def to_repr(self):
		return str(self.data).replace(" ", "T")

	def __str__(self):
		if self.default == "now" and self.data == "now":
			self.data = datetime.now().strftime("%Y-%m-%dT%H:%M")
		return BaseField.__str__(self)


class SelectField(BaseField):

	def __init__(self, label, multiple=False, choices=(), **common_kwargs):
		"""
		param: choices is either a tuple of (id, value) pairs or a function that returns the tuple of pairs
		:param default: set to True for pre-selecting the first entry

		"""
		BaseField.__init__(self, label, multiple=multiple, **common_kwargs)
		self._choices = choices
		self.multiple = multiple

	def add_data(self, value):
		if not self._data:
			if isinstance(value, (list, tuple, set)):
				self._data = set(str(v) for v in value)
			else:
				self._data = {str(value)}
		else:
			self._data.add(str(value))

	def data_as_set(self):
		if self._data is None:
			return {}
		return set(str(v) for v in self._data) if isinstance(self._data, (set, tuple, list)) else {str(self._data)}

	@property
	def choices(self):
		try:
			return self._choices()
		except TypeError:
			return self._choices

	@choices.setter
	def choices(self, value):
		self._choices = value

	def __str__(self):
		attributes = self._build_attributes()
		choices = self.choices
		if not self.default and not self.multiple:
			choices = [("", "")] + list(choices)
		size = ""
		if self.multiple:
			size = ' size="%s"' % min(len(choices), 10)
		options = "\n".join(f'<option value="{value}"' + (" selected" if str(value) in self.data_as_set() else "") + f'>{text}</option>' for value, text in choices)
		return f"""<div class="form-group mb-3">
	<label for="{self.name}">{self.label}</label>
	<select name="{self.name}" class="form-control"{attributes}{size}>
{options}
</select>
</div>"""


class DoubleSelectField(SelectField):
	"""
	Two select elements on the same line. The left one is the parent and the content of the right one depends on the
	parent's selected item.
	**parent_choices** is either a list of pairs (idem select) or a callback that returns the list of pairs.

	"""
	def __init__(self, labels, parent_choices=(), parent_attributes=None, choices=(), choices_url=None, **attributes):
		super(DoubleSelectField, self).__init__(None, **attributes)
		self.labels = labels
		self._parent_choices = parent_choices
		self._parent_attributes = parent_attributes or {}
		self.selected_parent_value = None
		self._choices = choices
		self.choices_url = choices_url

	@property
	def parent_choices(self):
		try:
			return self._parent_choices()
		except TypeError:
			return self._parent_choices

	@parent_choices.setter
	def parent_choices(self, value):
		self._parent_choices = value

	def __str__(self):
		parent_options = "\n".join("<option" + (" selected" if (value == self.selected_parent_value and self.data) else "") + f' value="{value}">{text}</option>' for value, text in self.parent_choices)
		options = "\n".join("<option" + (" selected " if value == self.data else " ") + f'value="{value}">{text}</option>' for value, text in self.choices)
		choices_url = self.choices_url or request.path
		attributes = self._build_attributes()
		parent_attributes = self._build_attributes(self._parent_attributes)
		return f"""<div class="form-group mb-3 double-select">
	<div class="col">
		<label for="{self.name}-parent">{self.labels[0]}</label>
		<select id="{self.build_id()}-parent" name="{self.name}-parent" class="form-control" data-parent-select{parent_attributes}>{parent_options}</select>
	</div>
	<div class="col">
		<label for="{self.name}">{self.labels[1]}</label>
		<select id="{self.build_id()}" name="{self.name}" class="form-control" data-child-select choices-url="{choices_url}"{attributes.replace(" autofocus", "")}>{options}</select>
	</div>
</div>"""


class DatalistField(SelectField):

	def __init__(self, label, creation_request=None, choices_url=None, choices=None, **attributes):
		self._creation_request = creation_request
		super(DatalistField, self).__init__(label, choices=choices, autocomplete="off", **attributes)
		self.choices_url = choices_url
		self.choices = choices
		self._data = None

	@property
	def data(self):
		return self._data

	@data.setter
	def data(self, value):
		try:
			self._data = int(value)
		except:
			if value is None:
				self._data = None
			elif self._creation_request is not None:
				_LOGGER.warning(f"Datalist value '{value}' is not a foreign key -> adding to the DB")
				try:
					db_id = self._creation_request(name=value).id
				except AttributeError:
					db_id = value
				self._data = db_id

	def __str__(self):
		choices_url = self.choices_url or request.path
		id_value = self.data if self.data is not None else ""
		choices = f'<input type="hidden" name="{self.name}-choices" value="{escape(json.dumps(self.choices))}"></input>' if self.choices is not None else ""
		attributes = self._build_attributes()
		try:
			text_value = dict(self.choices)[int(id_value)]
		except:
			text_value = ""
		return f"""<div name="{self.name}-datalist" class="form-group mb-3 datalist">
	<label for="{self.name}">{self.label}</label>
	<input type="text" name="{self.name}-text" class="form-control" choices-url="{self.choices_url}" value="{text_value}"{attributes}></input>
	<input type="hidden" name="{self.name}" value="{id_value}"></input>
	{choices}
	<ul class="dropdown-menu"></ul>
</div>"""


QR_CODE_FORMAT = "qrcode"
BARCODE_FORMAT = "barcode"

class BarcodeField(BaseField):

	def __init__(self, label, code_format=QR_CODE_FORMAT, **attributes):
		BaseField.__init__(self, label, **attributes)
		self._code_format = code_format

	def __str__(self):
		value = f' value="{self.to_repr()}"' if self.data is not None else ""
		errors = self._get_errors()
		return f"""<div class="form-group mb-3" data-{self._code_format}>
	<label for="{self.name}">{self.label}</label>
	<div class="input-group mb-3">
		<button class="btn btn-outline-secondary" type="button" id="scan-btn">Scan</button>
		<input type="text" id="{self.name}-scan-input" name="{self.name}" class="form-control{" is-invalid" if errors else ""}"{value}></input>
	</div>{errors}
	<div id="{self.name}-camera" data-camera></div>
</div>"""


class FileField(BaseField):
	html_tag = "input"
	html_type = "file"

	def __init__(self, label, max_size=(10 * 1024 * 1024), action=None, **attributes):
		"""
		:param max_size: maximum allowed file size in bytes (defaults to 10Mb)
		:param action: a functor that will be given the file content as parameter

		"""
		BaseField.__init__(self, label, **attributes)
		self._max_size = max_size  # TODO handle max size on JS side too
		self.action = action or self.action_upload
		self.validators.insert(0, self.file_size_validator)
		self._file_content = None
		self._file_storage = None

	@property
	def data(self):
		return self._data

	@data.setter
	def data(self, value):
		file_storage = self.form.request_object.files.get(self.name)
		if file_storage:
			self._file_storage = file_storage
			self._file_content = file_storage.read()
			_LOGGER.info("Content lenght is '%s'", len(self._file_content))
			h = hashlib.sha256(self._file_content).hexdigest()
			mimetype = mimetypes.guess_type(self._file_storage.filename)[0]
			try:
				ext = mimetypes.guess_extension(mimetype)
			except AttributeError:
				ext = ""
			self._data =  h + ext
		else:
			self._data = None

	def file_size_validator(self, form, field_data):
		if len(self._file_content) > self._max_size:
			return _("File size is above the max (%s bytes)") % self._max_size

	def do_action(self):
		self.action(self._file_content)

	def action_upload(self):
		if self._data is None:
			return
		_LOGGER.info("Uploading file '%s'", self._file_storage.filename)
		filepath = expanduser(join(self.upload_dir, self._data))
		self._file_storage.seek(0)
		self._file_storage.save(filepath)
		self._file_storage.close()
		_LOGGER.info("File '%s' saved as '%s'", self._file_storage.filename, filepath)


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

