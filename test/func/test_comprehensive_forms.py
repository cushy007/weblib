#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
from copy import copy
from datetime import datetime
from time import sleep
from zoneinfo import ZoneInfo

import pytest
import time_machine

from testapp.models import MODELS, ChildModel, ColorModel, ParentModel
from weblib.models import WEBLIB_MODELS
from weblib.test.data import USERS
from weblib.test.utils import SeleniumFixtures

for logger in ("urllib3", "werkzeug", "peewee", "selenium.webdriver.remote"):
	logging.getLogger(logger).setLevel(logging.WARNING)


_LOGGER = logging.getLogger(__name__)

FRENCH_TZ = ZoneInfo("Europe/Paris")


class TestappMacrosMixin:
	pass


class TestappFixtures(SeleniumFixtures, TestappMacrosMixin):
	IS_FULLY_PRIVATE_SITE = True

	@pytest.fixture(scope='function')
	def populate_db(self):
		colors = (
			{'name': 'Red'},
			{'name': 'Green'},
			{'name': 'Blue'},
		)
		with self.database.bind_ctx(MODELS + WEBLIB_MODELS):
			for color in colors:
				ColorModel.create(**color)

		parents = (
			{'name': 'Alice'},
			{'name': 'Bob'},
		)
		with self.database.bind_ctx(MODELS + WEBLIB_MODELS):
			for parent in parents:
				ParentModel.create(**parent)

		children = (
			{'name': 'David'},
			{'name': 'Jeff'},
			{'name': 'Mark'},
			{'name': 'Jimmy'},
		)
		with self.database.bind_ctx(MODELS + WEBLIB_MODELS):
			for child in children:
				ChildModel.create(**child)

	@pytest.fixture(scope='function')
	def form_dict(self):
		return copy({
			'text'      : "Text field",
			'text_area' : "Text area",
			'boolean'   : True,
			'integer'   : 3,
			'decimal'   : 3.5,
			'price'     : 3.07,
			'select_field': "3",
			'datalist-datalist'  :  ("Data 1", (), "Data 1"),
			'date'      : datetime(2025, 2, 27),
			'datetime'  : datetime(2025, 2, 27, 17, 33),
			'barcode'   : "1234567890",
			'qrcode'    : "https://qr.com",
			'document': "/home/seluser/resources/polop.pdf",
			'picture':  "/home/seluser/resources/polop.png",
		})

	@pytest.fixture(scope='function')
	def form_dict_default(self):
		return copy({
			'text'      : "Default line",
			'text_area' : "Default\n\nParagraph...",
			'boolean'   : "Oui",
			'integer'   : "7",
			'decimal'   : "7.5",
			'price'     : "7.07",
			'select_field': "2",
			'double_select': "1",
			'date'      : "2025-02-02",
			'datetime'  : "2025-02-02-05:33:00",
			'barcode'   : "1234567",
			'qrcode'    : "https://qr.com",
		})


class TestForms(TestappFixtures):

	def test01a(self, start_app, start_driver):
		""" The application has never been used -> ask to create an admin user when entering a private page """
		self.fill_form(USERS['gilmour'])
		self.login_as('gilmour')

	def test02a(self, start_app, users, populate_db, start_driver):
		""" First form: leave the form empty """
		self.login_as('gilmour')
		self.switch_to_tab("comprehensive_2", "open")
		self.click_element_by_id("btn-create-comprehensive")
		self.fill_form({})
		assert self.get_table_field("comprehensive", 1, 3) == "Non"
		assert self.get_table_row("comprehensive", 1) == [
			"",
			"",
			"Non",
			"",
			"",
			"",
			"",
			"1",  # FIXME
			"",
			"",
			"",
			"",
			"",
			"",
			"",
		]

	def test02b(self, start_app, users, populate_db, start_driver):
		""" First form: populate the form """
		self.login_as('gilmour')
		self.switch_to_tab("comprehensive_2", "open")
		self.click_element_by_id("btn-create-comprehensive")
		self.select('select_field', visible_text="Green"),
		self.select('double_select-parent', visible_text="Alice"),
		form_dict = {
			'text'      : "Text field",
			'text_area' : "Text area",
			'boolean'   : True,
			'integer'   : 3,
			'decimal'   : 3.5,
			'price'     : 3.07,
			'datalist-datalist'  :  ("Data 1", (), "Data 1"),
			'date'      : datetime(2025, 2, 27),
			'datetime'  : datetime(2025, 2, 27, 17, 3),
			'barcode'   : "1234567890",
			'qrcode'    : "https://qr.com",
			'document': "/home/seluser/resources/polop.pdf",
			'picture':  "/home/seluser/resources/polop.png",
		}
		self.fill_form(form_dict)
		assert self.get_table_row("comprehensive", 1) == [
			"Text field",
			"Text area",
			"Oui",
			"3",
			"3.5",
			"3.07",
			"Green",
			"1",  # FIXME
			"Data 1",
			"27/02/2025",
			"27/02/2025 17:03",
			"1234567890",
			"https://qr.com",
			"",
			"",
		]
		self.check_download_field("comprehensive", 1, 14, "polop.pdf")
		self.check_download_field("comprehensive", 1, 15, "polop.png")

	def fill_required_form(self, form_dict):
		for key, value in form_dict.items():
			self.submit()
			self.fill_form({key: value}, do_submit=False)

	def test03a(self, start_app, users, populate_db, start_driver):
		""" Required form: check that submit doesn't work until everything is populated """
		self.login_as('gilmour')
		self.switch_to_tab("comprehensive_2", "required")
		self.click_element_by_id("btn-create-comprehensive")

		self.fill_required_form({
			#'hidden':,
			'text'      : "Text field",
			'text_area' : "Text area",
			# ~ 'boolean'   : True,  FIXME
			'integer'   : 3,
			'decimal'   : 3.5,
			'price'     : 3.07,
			'datalist-datalist'  :  ("Data 1", (), "Data 1"),
			'date'      : datetime(2025, 2, 27),
			'datetime'  : datetime(2025, 2, 27, 17, 3),
			'barcode'   : "1234567890",
			'qrcode'    : "https://qr.com",
			'document': "/home/seluser/resources/polop.pdf",
			'picture':  "/home/seluser/resources/polop.png",
		})
		self.select('select_field', visible_text="Green"),
		self.submit()

		assert self.get_table_row("comprehensive", 1) == [
			"Text field",
			"Text area",
			"Non",
			"3",
			"3.5",
			"3.07",
			"Green",
			"1",  # FIXME
			"Data 1",
			"27/02/2025",
			"27/02/2025 17:03",
			"1234567890",
			"https://qr.com",
			"",
			"",
		]
		self.check_download_field("comprehensive", 1, 14, "polop.pdf")
		self.check_download_field("comprehensive", 1, 15, "polop.png")

	@time_machine.travel(datetime(2025, 3, 14, 17, 33, tzinfo=FRENCH_TZ))
	def test04a(self, start_app, users, populate_db, start_driver, form_dict_default, form_dict):
		""" Defaults form: check that fields are pre-populated, then modify them """
		self.login_as('gilmour')
		self.switch_to_tab("comprehensive_2", "defaults")
		self.click_element_by_id("btn-create-comprehensive")
		self.submit()
		assert self.get_table_row("comprehensive", 1) == [
			"Default line",
			"Default Paragraph...",
			"Oui",
			"7",
			"7.5",
			"7.07",
			"Green",
			"1",
			"",
			"14/03/2025",
			"14/03/2025 17:33",
			"1234567",
			"https://qr.com",
			"",
			"",
		]

		# Check that the pre-populated date is not changed to "now"
		with time_machine.travel(datetime(2025, 3, 17, 3, 37, tzinfo=FRENCH_TZ)):
			self.switch_to_tab("comprehensive_2", "defaults")
			self.click_table_row("comprehensive", 1)
			self.click_modal_button("update")
			self.submit()
			assert self.get_table_row("comprehensive", 1) == [
				"Default line",
				"Default Paragraph...",
				"Oui",
				"7",
				"7.5",
				"7.07",
				"Green",
				"1",
				"",
				"14/03/2025",
				"14/03/2025 17:33",
				"1234567",
				"https://qr.com",
				"",
				"",
			]

	def test05a(self, start_app, users, populate_db, start_driver):
		""" Validators form: check that are validated """
		self.login_as('gilmour')
		self.switch_to_tab("comprehensive_2", "validators")
		self.click_element_by_id("btn-create-comprehensive")

		self.fill_form({
			'integer'   : 3,
			'decimal'   : 3.5,
			'barcode'   : "1234567890",
			'document': "/home/seluser/resources/polop.pdf",
		})
		assert self.get_table_row("comprehensive", 1) == [
			"",
			"",
			"",
			"3",
			"3.5",
			"",
			"",
			"",
			"",
			"",
			"",
			"1234567890",
			"",
			"",
			"",
		]
		self.check_download_field("comprehensive", 1, 14, "polop.pdf")

		self.click_table_row("comprehensive", 1)
		self.click_modal_button("update")
		self.fill_form({'integer': -1})
		self.assert_wtf_error("negative or greater")
		self.fill_form({'integer': 1, 'decimal': 77})
		self.assert_wtf_error("greater than 70")
		self.fill_form({'decimal': 33, 'barcode': "qwerty"})
		self.assert_wtf_error("composed of numbers")
		self.fill_form({'barcode': 123456789012345})
		self.assert_wtf_error("numbers long")
		self.fill_form({'barcode': 1234567890, 'document': "/home/seluser/resources/polop"})
		self.assert_wtf_error("must have an extension")
		self.fill_form({'document': "/home/seluser/resources/polop.png"})
		self.assert_wtf_error("Fichier trop volumineux")
		self.fill_form({'document': "/home/seluser/resources/polop.txt"})

		assert self.get_table_row("comprehensive", 1) == [
			"",
			"",
			"",
			"1",
			"33.0",
			"",
			"",
			"",
			"",
			"",
			"",
			"1234567890",
			"",
			"",
			"",
		]
		# ~ sleep(60)
		self.check_download_field("comprehensive", 1, 14, "polop.txt")


	sleep(.1)
