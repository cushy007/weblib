#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from copy import copy
from time import sleep

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from weblib.test.data import USERS
from weblib.test.utils import SeleniumFixtures

for logger in ("urllib3", "werkzeug", "peewee", "selenium.webdriver.remote"):
	logging.getLogger(logger).setLevel(logging.WARNING)


_LOGGER = logging.getLogger(__name__)


class TestUsers(SeleniumFixtures):
	IS_FULLY_PRIVATE_SITE = True

	def test01a(self, start_app, start_driver):
		""" The application has never been used -> ask to create a root user when entering a private page """
		self.fill_form(USERS['gilmour'])

	def test02a(self, start_app, users, start_driver):
		""" Log in as admin and check the users list """
		self.login_as('gilmour')
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-page-users")
		assert self.get_table_field("users", 1, 1) == "Gilmour"
		assert self.get_table_field("users", 1, 3) == "dgilmour"
		assert self.get_table_field("users", 1, 4) == "admin"

	def test03a(self, start_app, users, start_driver):
		""" Create a user (only an admin can do that) """
		self.login_as('gilmour')
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-page-users")
		self.click_element_by_id("btn-create-users")

		jbeck = copy(USERS['beck'])
		jbeck['username'] = "dgilmour"
		self.fill_form(jbeck)
		self.assert_wtf_error("déjà")

		jbeck = copy(USERS['beck'])
		jbeck['password_confirmation'] = "inconsitent"
		self.fill_form(jbeck)
		self.assert_wtf_error("Must be identical")

		self.input_text('password', USERS['beck']['password'])
		self.input_text('password_confirmation', USERS['beck']['password_confirmation'])
		self.submit()
		self.click_element_by_id("dropdown-user")  # TODO come back to users page
		self.click_element_by_id("href-page-users")
		assert self.get_table_field("users", 1, 1) == "Beck"
		assert self.get_table_field("users", 1, 3) == "jbeck"
		assert self.driver.find_element(By.ID, "current-user").text == "David Gilmour (dgilmour)"

	def modify_roles(self, user, roles):
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-page-users")
		self.click_table_row("users", user)
		self.click_modal_button("modify_roles")
		for role in roles:
			self.select('roles', visible_text=role)
		self.submit()

	def test03b(self, start_app, users, start_driver):
		""" Modify user roles (only an admin can do that) """
		self.login_as('gilmour')
		self.modify_roles(2, ("admin", ))
		self.logout()
		self.login_as("knopfler")
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-page-users")

	def test03c(self, start_app, users, start_driver):
		""" Reset password (only an admin can do that) """
		self.login_as('gilmour')
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-page-users")
		self.click_table_row("users", 2)  # knopfler
		self.click_modal_button("reset_password")
		assert self.driver.find_element(By.TAG_NAME, "h1").text == "Réinitialisation du mot de passe"

	def test04a(self, start_app, users, start_driver):
		""" Modify a user's name """
		self.login_as('knopfler')
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-page-modify-user")
		self.input_text('username', "")
		self.submit()  # Submit should have failed
		self.input_text('username', "mknopfler")
		self.input_text('first_name', "Marc")
		self.submit()  # TODO come back to referer's page
		assert self.driver.find_element(By.ID, "current-user").text == "Marc Knopfler (mknopfler)"

	def test04b(self, start_app, users, start_driver):
		""" Modify a user's password """
		self.login_as('knopfler')
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-page-modify-password")
		self.input_text('password', "1234")
		self.input_text('password_confirmation', "5678")
		self.submit()  # TODO come back to referer's page
		self.assert_wtf_error("Must be identical")
		self.input_text('password', "newpass")
		self.input_text('password_confirmation', "newpass")
		self.submit()  # TODO come back to referer's page
		self.logout()
		login_form = {
			'username': "mknopfler",
			'password': "newpass",
		}
		self.fill_form(login_form)
		assert self.driver.find_element(By.ID, "current-user").text == "Mark Knopfler (mknopfler)"

	def test05a(self, start_app, users, start_driver):
		""" Non admin users can't acces the users list """
		self.login_as('knopfler')
		self.click_element_by_id("dropdown-user")
		with pytest.raises(NoSuchElementException):  # Neither by the dedicated button...
			self.click_element_by_id("href-page-users")
		self.get_url_of_path('/users')  # ... nor by direct URL
		self.is_forbidden()

	def test06a(self, start_app, users, start_driver):
		""" Delete the current user """
		self.login_as('gilmour')
		assert self.driver.find_element(By.ID, "current-user").text == "David Gilmour (dgilmour)"
		self.modify_roles(1, ("admin", "user"))
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-page-users")
		self.click_table_row("users", 1)
		self.click_modal_button("del", with_confirmation=True)
		self.login_as('gilmour')
		self.assert_wtf_error("utilisateur")

	def test99a(self, start_app, users, start_driver):
		""" Direct access by GET requests to private pages asks to login """
		self.get_url_of_path('/')
		for path in (
			'/login',
			'/logout',
			'/users',
			'/users/users.table',
			'/user/register',
			'/user/modify',
			'/user/modify_password',
			'/user/modify_roles',
			'/user/reset_password',
			'/user/del',
		):
			self.get_url_of_path(path)
			assert self.driver.find_element(By.TAG_NAME, "h1").text == "Page de connexion"

	sleep(.1)
