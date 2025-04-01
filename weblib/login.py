#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
from flask import redirect, url_for
from flask_login import LoginManager

from weblib.models import User
from weblib.requests import get_users

login_manager = LoginManager()
login_manager.login_view = "user_views.login"
login_manager.refresh_view = "user_views.login"


@login_manager.user_loader
def load_user(user_id):
	return User.get_or_none(id=user_id)


@login_manager.unauthorized_handler
def unauthorized():
	for r in get_users().query:
		return redirect(url_for(login_manager.login_view))
	return redirect("/user/register")
