#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from logging import INFO
from os import environ

import pytest
from flask import Flask
from peewee import IntegrityError

from weblib.login import load_user
from weblib.models import WEBLIB_MODELS, DatabaseVersionException, DatabaseVersionModel, User, flask_db
from weblib.requests import (
	get_app_db_version, get_lib_db_version, init_db_version, set_app_db_version, set_lib_db_version
)

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

	User.create(username="dgilmour", password="polop", last_name="Gilmour", first_name="David", active=True)

	flask_db.database.close()


def test01a(populate_db):
	""" load_user nominal """
	user = load_user("1")
	assert user.username == "dgilmour"


def test01b(populate_db):
	""" load_user unknown """
	user = load_user("666")
	assert user is None
