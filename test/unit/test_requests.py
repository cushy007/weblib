#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from logging import INFO
from os import environ

import pytest
from flask import Flask

from weblib.models import WEBLIB_MODELS, DatabaseVersionException, DatabaseVersionModel, RoleModel, UserRole, flask_db
from weblib.requests import (
	create_user, get_app_db_version, get_lib_db_version, get_users, init_db_version, set_app_db_version,
	set_lib_db_version
)
from weblib.roles import ROLE_ADMIN, ROLE_USER

for module in ("peewee", "passlib"):
	logging.getLogger(module).setLevel(INFO)


@pytest.fixture(scope='function')
def populate_db(request):
	app = Flask(__name__)

	app.config['SECRET_KEY'] = environ.get("SECRET_KEY", 'pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw')
	app.config['DATABASE'] = {
		'host': "localhost",
		'name': "%s_test" % environ['DATABASE_NAME'],
		'engine': 'playhouse.pool.PooledPostgresqlDatabase',
		'user': environ.get('USER', ""),
	}

	flask_db.init_app(app)

	for model in WEBLIB_MODELS:
		model.drop_table(safe=True, cascade=True)
		model.create_table(safe=True)
	DatabaseVersionModel.drop_table(safe=True, cascade=True)

	with app.app_context():
		role_admin = RoleModel.create(name=ROLE_ADMIN)
		role_user = RoleModel.create(name=ROLE_USER)
		user = create_user(username="mknopfler", last_name="Knopfler", first_name="Mark", password="1234")
		UserRole.create(user=user, role=role_admin)
		UserRole.create(user=user, role=role_user)
		user = create_user(username="jbeck", last_name="Beck", first_name="Jeff", password="1234")
		UserRole.create(user=user, role=role_user)

	flask_db.database.close()


def test01a(populate_db):
	""" database version (not populated) """
	assert get_lib_db_version() == None
	assert get_app_db_version() == None


def test01b(populate_db):
	""" database version nominal case """
	init_db_version(app_version=1, lib_version=1)
	set_lib_db_version(2)
	assert get_lib_db_version() == 2


def test01c(populate_db):
	""" database can not decrease version """
	init_db_version(app_version=1, lib_version=1)
	set_lib_db_version(2)
	with pytest.raises(DatabaseVersionException):
		set_lib_db_version(1)


def test01d(populate_db):
	""" database can not set to an alredy existing version """
	init_db_version(app_version=1, lib_version=1)
	set_lib_db_version(2)
	with pytest.raises(DatabaseVersionException):
		set_lib_db_version(2)


def test01e(populate_db):
	""" lib and app database have their own versioning """
	init_db_version(app_version=1, lib_version=1)
	assert get_lib_db_version() == 1
	assert get_app_db_version() == 1
	set_lib_db_version(2)
	set_app_db_version(3)
	assert get_lib_db_version() == 2
	assert get_app_db_version() == 3


def test02a(populate_db):
	""" Get the users list """
	assert [t for t in get_users().query] == [
		[2, "Beck", "Jeff", "jbeck", "user"],
		[1, "Knopfler", "Mark", "mknopfler", "admin, user"],
	]
