#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from functools import wraps

from flask import abort
from flask_login import current_user

_LOGGER = logging.getLogger(__name__)


ROLE_ADMIN = "admin"
ROLE_USER = "user"
AVAILABLE_ROLES = [ROLE_ADMIN, ROLE_USER]


def user_has_role(current_user, role):
	return role in current_user.roles


def user_has_one_of_these_roles(current_user, roles):
	return set(current_user.roles) & set(roles)


def roles_required(*roles):

	def decorator(functor):

		requires_roles = list(roles)
		requires_roles.append(ROLE_ADMIN)
		functor.roles = requires_roles

		@wraps(functor)
		def wrapper(*args, **kwargs):
			_LOGGER.info("User has roles '%s' and functor accepts '%s'", current_user.roles, requires_roles)
			if any([user_has_role(current_user, role) for role in requires_roles]):
				return functor(*args, **kwargs)
			else:
				abort(403)

		return wrapper

	return decorator


