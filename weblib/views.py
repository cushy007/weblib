#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from copy import copy
from os import environ
from os.path import join
from secrets import token_urlsafe
from urllib.parse import urljoin, urlparse

from bcrypt import gensalt, hashpw
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, session, url_for
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_login import current_user, fresh_login_required, login_required, login_user, logout_user

from weblib.requests import (
	DatabaseException, TableRequestResult, create_user, delete_user, get_user, get_user_roles, get_users,
	has_any_registered_user, update_roles
)

if environ.get('APP_MODULE') == "testapp":
	from testapp import CONFIG_CUSTOMIZATION
else:
	from webapp import CONFIG_CUSTOMIZATION

from weblib.forms import LoginForm, ModifyPasswordForm, ModifyRolesForm, RegistrationForm, UserForm
from weblib.models import User
from weblib.roles import ROLE_ADMIN, roles_required, user_has_one_of_these_roles
from weblib.table import Table

_LOGGER = logging.getLogger(__name__)


class Tab:

	def __init__(self, name, i18n, children=None):
		self.name = name
		self.i18n = i18n
		self.children = children or {}

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.__str__()


class Site:

	def __init__(self):
		self._tabs = None

	def set_tabs(self, tabs):
		self._tabs = tabs

	def render_page(self, in_login_process=False, is_display_main_tabs=True, **kwargs):
		_LOGGER.info("Logged-in as user '%s'", current_user)
		computed_html_template = "%s.html" % str(request.url_rule).lstrip('/')
		_LOGGER.debug("computed_html_template=%s", computed_html_template)
		page_path = computed_html_template.split('.')[0].split('/')
		favicon = kwargs.pop('favicon', "favicon")
		if page_path[0] in self._tabs:
			try:
				kwargs['available_tabs'] = self._tabs.values() if is_display_main_tabs else None
				active_path = kwargs.get('active_tab')
				if active_path:
					active_path = active_path.split('/')
				else:
					active_path = page_path
				_LOGGER.info("Will activate tab '%s'", active_path)
				kwargs['active_tab'] = self._tabs[active_path[0]]
				kwargs.setdefault('available_sub_tabs', self._tabs[active_path[0]].children.values())
				_LOGGER.info("Available sub tabs are '%s'", kwargs['available_sub_tabs'])
				kwargs['active_sub_tab'] = self._tabs[active_path[0]].children[active_path[1]]
			except (IndexError, KeyError):
				pass
		else:
			kwargs['available_tabs'] = kwargs['active_tab'] = kwargs['available_sub_tabs'] = kwargs['active_sub_tab'] = None
		return render_template("index.html",
			html_template=kwargs.pop('html_template', None) or computed_html_template,
			project_css=current_app.config['APP_CSS'],
			title=CONFIG_CUSTOMIZATION['title'],
			app_name=current_app.config['APP_NAME'],
			app_version=current_app.config['APP_VERSION'],
			in_login_process=in_login_process,
			is_private_app=current_app.config.get('IS_PRIVATE_APP', False),
			favicon=favicon,
			**kwargs
		)


site = Site()


def form_to_model_dict(form, model, filtered_keys=()):
	filtered_keys = list(filtered_keys) or []
	filtered_keys.append('id')

	def nonify(data):
		return data if data != "" else None

	return dict([(getattr(model, field), nonify(getattr(form, field).data)) for field in form.data if field not in filtered_keys])


def form_to_model_kwargs(form, model, filtered_keys=()):
	filtered_keys = list(filtered_keys) or []
	filtered_keys.append('id')

	def nonify(data):
		return data if data != "" else None

	return dict([(getattr(model, field).name, nonify(getattr(form, field).data)) for field in form.data if field not in filtered_keys])


def build_buttons(buttons):
	""" Filter the buttons according to the roles of the target they are pointing to """
	built_buttons = []
	for button in buttons:
		target = button['target']
		try:
			authorized_roles = current_app.view_functions.get(target).roles
		except AttributeError:
			_LOGGER.warning("No role defined for this view, expect admin.")
			authorized_roles = (ROLE_ADMIN, )
		if not user_has_one_of_these_roles(current_user, authorized_roles):
			continue
		button = copy(button)
		button['href'] = url_for(target)
		built_buttons.append(button)

	return built_buttons


def page_forbidden(e, http_status=403):
  return render_template(f"{http_status}.html", http_status=http_status), http_status


def page_server_error(e, http_status=500):
  return render_template(f"{http_status}.html", http_status=http_status), http_status


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def crud_page(table_name, crud_step,
		tables,
		page_title=None,
		html_template="crud_table.html",
		url=None,
		**kwargs
	):
	url = url or str(request.url_rule).split("/<")[0]  # Ugly but there is no other mean :-/
	try:
		cur_table = tables[table_name]
		model_factory = cur_table.get('model_factory')
		query = cur_table.get('query')
		columns = cur_table.get('columns')
		where_predicate = cur_table.get('where_predicate', True)
		order_by = cur_table.get('order_by')
		form_factory = cur_table.get('form_factory')
		row_title_builder = cur_table.get('row_title_builder')
		fields_builder = cur_table.get('fields_builder')
	except:
		pass

	if table_name and crud_step == "read":
		table = Table(table_name, row_title_builder=row_title_builder, fields_builder=fields_builder)
		query = query if query is not None else (model_factory
			.select(model_factory.id, *columns)
			.order_by(order_by)
			.where(where_predicate)
			.tuples()
		)
		table.build_from_request(TableRequestResult(columns, query))
		table.buttons = (
			{'href': join(url, table_name, "update"), 'i18n': _("Modify")},
			{'href': join(url, table_name, "del"), 'i18n': _("Delete"), 'confirmation_message': _l("Confirm deletion ?")},
		)
		return jsonify(table.dict)

	item_id = request.form.get('id', None) or request.args.get('id')
	form = None
	if crud_step == "create":
		form = form_factory()
		if request.method == 'POST':
			if not form.validate():
				_LOGGER.info(f"Displaying errors for {table_name} form's '%s'", form)
			else:
				_LOGGER.info(f"Adding {form.dict} to table {table_name}")
				model_factory.create(**form.dict)
				return redirect(url)
	elif crud_step == "update":
		if request.method == 'GET':
			item = (model_factory.select().where(model_factory.id == item_id).dicts())[0]
			form = form_factory(item)
		else:
			form = form_factory()
			if form.validate():
				_LOGGER.info(f"Modifying {table_name} '%s'", item_id)
				query = model_factory.update(form.dict).where(model_factory.id == item_id)
				if query.execute() != 1:
					raise DatabaseException(f"Could not update {table_name} '%s'" % item_id)
				return redirect(url)
			else:
				_LOGGER.info(f"Displaying form errors for {table_name} '%s'", ", ".join(["%s=%s" % (field.name, field.data) for field in form.fields.values()]))
	elif crud_step == "del":
		_LOGGER.info(f"Deleting {table_name} with id '%s'", item_id)
		query = model_factory.delete().where(model_factory.id == item_id)
		if query.execute() != 1:
			raise DatabaseException(f"Could not delete {table_name} '%s'" % item_id)
		return redirect(url)

	return site.render_page(
		html_template=html_template,
		page_title=page_title,
		url=url,
		tables=tables,
		crud_step=crud_step,
		form=form,
		table_name=table_name,
		**kwargs
	)


user_views = Blueprint('user_views', __name__)


@user_views.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if request.method == 'POST':
		if form.validate():
			login_user(User.get(username=form.username.data), remember=True)  # default value is , duration=timedelta(days=31)
			session.permanent = True
			next = request.args.get('next')
			if not is_safe_url(next):
				return abort(400)
			return redirect(next or '/')
	return site.render_page(
		form=form,
		in_login_process=True,
	)


@user_views.route('/logout')
def logout():
	logout_user()
	return redirect('/')


@user_views.route('/users')
@login_required
@roles_required(ROLE_ADMIN)
def users():
	return site.render_page()


@user_views.route('/users/users.table')
@login_required
@roles_required(ROLE_ADMIN)
def users_table():
	table = Table("users", row_title_builder=lambda row: f"{row[2]} {row[1]}")
	table.build_from_request(get_users())
	table.buttons = build_buttons((
		{'target': "user_views.user_modify_roles", 'i18n': _("Modify roles")},
		{'target': "user_views.user_reset_password", 'i18n': _("Reset password")},
		{'target': "user_views.user_del", 'i18n': _("Delete"), 'confirmation_message': _("Confirm deleting user ?")},
	))
	return jsonify(table.dict)


@user_views.route('/user/register', methods=['GET', 'POST'])
@user_views.route('/users/users/create', methods=['GET', 'POST'])
def user_register():
	if has_any_registered_user() and not current_user.is_authenticated:
		return current_app.login_manager.unauthorized()
	form = RegistrationForm()
	if request.method == 'POST':
		if form.validate():
			create_user(
				username=form.username.data,
				password=hashpw(form.password.data.encode(), gensalt()),
				last_name=form.last_name.data,
				first_name=form.first_name.data,
				active=True,
				roles=form.roles.data,
			)
			return redirect(url_for('user_views.users'))
		else:
			_LOGGER.info("Displaying form errors...")
	if not has_any_registered_user():
		form.roles.data = 1
	return site.render_page(html_template="/user/register.html",
		form=form
	)


@user_views.route('/user/modify', methods=['GET', 'POST'])
@fresh_login_required
def user_modify():
	form = UserForm()
	if request.method == 'GET':
		for form_field in form.fields:
			try:
				form.fields[form_field].data = getattr(current_user, form_field)
			except AttributeError:
				_LOGGER.exception("Form is expecting a DB column that does not exist")
	else:
		user_id = request.form['id']
		if not form.validate():
			_LOGGER.info("Displaying form errors for user '%s'", ", ".join(["%s=%s" % (field.name, field.data) for field in form]))
		else:
			_LOGGER.info("Modifying user '%s'", user_id)
			query = User.update(**form.dict).where(User.id == user_id)
			if query.execute() != 1:
				raise DatabaseException("Could not update user '%s'" % user_id)
			return redirect('/users' if current_user.is_admin else '/')
	return site.render_page(
		form=form
	)


@user_views.route('/user/modify_password', methods=['GET', 'POST'])
@fresh_login_required
def user_modify_password():
	form = ModifyPasswordForm()
	if request.method == 'POST':
		user_id = current_user.get_id()
		if form.validate():
			_LOGGER.info("Modifying user's '%s' password", user_id)
			query = User.update(password=hashpw(form.password.data.encode(), gensalt())).where(User.id == user_id)
			if query.execute() != 1:
				raise DatabaseException("Could not update user '%s'" % user_id)
			return redirect('/users' if current_user.is_admin else '/')
	return site.render_page(
		form=form
	)


@user_views.route('/user/modify_roles', methods=['GET', 'POST'])
@fresh_login_required
def user_modify_roles():
	if request.method == 'GET':
		user_id = request.args['id']
		roles = get_user_roles(user_id)
		form = ModifyRolesForm({'user_id': user_id, 'roles': roles})
	else:
		form = ModifyRolesForm()
		if form.validate():
			_LOGGER.info(f"Modifying user id '{form.user_id.data}' with '{form.dict}'")
			update_roles(form.dict)
			return redirect('/users')
	return site.render_page(
		form=form
	)


@user_views.route('/user/reset_password')
@fresh_login_required
@roles_required(ROLE_ADMIN)
def user_reset_password():
	user_id = request.args['id']
	user = get_user(user_id)
	_LOGGER.info("Modifying '%s''s password", user_id)
	temp_password = token_urlsafe()
	query = User.update(password=hashpw(temp_password.encode(), gensalt())).where(User.id == user_id)
	if query.execute() != 1:
		raise DatabaseException("Could not update user '%s'" % user_id)
	return site.render_page(temp_password=temp_password, firstname=user.first_name, lastname=user.last_name)


@user_views.route('/user/del')
@login_required
@roles_required(ROLE_ADMIN)
def user_del():
	user_id = request.args['id']
	_LOGGER.info("Deleting user with id '%s'", user_id)
	delete_user(user_id)
	return redirect('/users')
