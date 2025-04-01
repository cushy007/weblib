# coding: utf-8
#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
import threading
from os import environ
from os.path import splitext
from socket import socket
from time import sleep

import pytest
from bcrypt import gensalt, hashpw
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from werkzeug.serving import make_server

from selenium import webdriver
from weblib.models import WEBLIB_MODELS
from weblib.requests import create_user
from weblib.server import create_app
from weblib.test.data import USERS
from weblib.views import gensalt, hashpw

_LOGGER = logging.getLogger(__name__)


def scroll_to_click(functor):

	def wrapper(self, *args, **kwargs):
		while "element not reacheable":
			try:
				functor(self, *args, **kwargs)
				break
			except ElementClickInterceptedException:
				self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
				sleep(.1)

	return wrapper


class ActionsMixin:

	def get_url_of_path(self, path):
		self.driver.get("http://%s:%s%s" % ("192.168.0.10", self.server_port, path))

	@property
	def title(self):
		return self.driver.title

	def __check_id_unicity(self):
		elements_with_id = self.driver.find_elements(By.CSS_SELECTOR, "[id]")
		ids = sorted([element.get_attribute("id") for element in elements_with_id])
		duplicated_ids = []
		for idx, next_id in enumerate(ids[1:]):
			if ids[idx] == next_id:
				duplicated_ids.append(next_id)
		assert not duplicated_ids

	def page_sanity_check(self):
		self.wait_for_document_ready()
		self.__check_id_unicity()
		assert self.driver.find_element(By.TAG_NAME, "footer")

	def is_forbidden(self, status=403):
		assert self.driver.find_element(By.CSS_SELECTOR, 'body[data-http-status="%s"]' % (status, ))
		self.click_element_by_id("escape")

	def is_server_error(self, status=500):
		assert self.driver.find_element(By.CSS_SELECTOR, 'body[data-http-status="%s"]' % (status, ))
		self.click_element_by_id("escape")

	def switch_to_tab(self, *tabs_tree):
		for level, tab_name in enumerate(tabs_tree, 1):
			if tab_name is not None:
				tab = self.driver.find_element(by=By.ID, value="tab-l%d-%s" % (level, tab_name))
				tab.click()
		self.page_sanity_check()

	@scroll_to_click
	def click_element_by_id(self, element_id):
		element = self.driver.find_element(By.ID, element_id)
		element.click()

	def click_modal_button(self, href, with_confirmation=False):
		self.wait_for_document_ready(is_modal=True)
		button = self.driver.find_element(By.CSS_SELECTOR, '.modal.show [href*="%s"]' % (href, ))
		button.click()
		if with_confirmation:
			self.driver.switch_to.alert.accept()

	def login_as(self, user, passwd=None, press_login_button=False):
		if press_login_button:
			self.click_element_by_id("btn-login")
		login_form = {
			'username': user if passwd else USERS[user]['username'],
			'password': passwd if passwd else USERS[user]['password'],
		}
		self.fill_form(login_form)
		sleep(.3)

	def logout(self):
		self.click_element_by_id("dropdown-user")
		self.click_element_by_id("href-logout")


class FormActionsMixin:

	def input_text(self, input_name, text, press_enter=False):
		try:
			container = self.driver.find_element(By.CSS_SELECTOR, '.modal.show')
		except NoSuchElementException:
			container = self.driver
		element = container.find_element("name", input_name)
		if element.get_attribute("type") == "number":
			for i in range(10):
				element.send_keys(Keys.DELETE)
		# ~ elif element.text or element.get_attribute("value"):
			# ~ element.clear()
		else:
			sleep(.3)
			element.clear()
		if text:
			element.send_keys(text)
		if press_enter:
			element.send_keys(Keys.ENTER)

	def input_datetime(self, input_name, value):
		try:
			container = self.driver.find_element(By.CSS_SELECTOR, '.modal.show')
		except NoSuchElementException:
			container = self.driver
		element = container.find_element("name", input_name)
		element.send_keys(value.strftime('%d%m%Y'))
		element.send_keys(Keys.TAB)
		element.send_keys(value.strftime('%H%M'))

	def input_date(self, input_name, value):
		try:
			container = self.driver.find_element(By.CSS_SELECTOR, '.modal.show')
		except NoSuchElementException:
			container = self.driver
		element = container.find_element("name", input_name)
		element.send_keys(value.strftime('%d%m%Y'))

	@scroll_to_click
	def checkbox(self, checkbox_name, state):
		checkbox = self.driver.find_element("name", checkbox_name)
		if checkbox.is_selected() != state:
			checkbox.click()

	def _select(self, select_name, value=None, visible_text=None, prefix=""):
		self.wait_for_document_ready()
		try:
			container = self.driver.find_element(By.CSS_SELECTOR, '.modal.show')
		except NoSuchElementException:
			container = self.driver
		select_element = container.find_element("name", select_name)
		select_object = Select(select_element)
		selector = getattr(select_object, "%s%s" % (prefix, ("select_by_value" if value is not None else "select_by_visible_text")))
		target = value if value is not None else visible_text
		if isinstance(target, (list, tuple)):
			for i in target:
				selector(str(i))
		else:
			selector(str(target))

	@scroll_to_click
	def select(self, select_name, value=None, visible_text=None):
		return self._select(select_name, value=value, visible_text=visible_text)

	@scroll_to_click
	def deselect(self, select_name, value=None, visible_text=None):
		return self._select(select_name, value=value, visible_text=visible_text, prefix="de")

	@scroll_to_click
	def datalist(self, name, text_to_type="", filtered_choices=(), choice_to_select=""):
		try:
			container = self.driver.find_element(By.CSS_SELECTOR, '.modal.show')
		except NoSuchElementException:
			container = self.driver
		datalist_elt = container.find_element("name", name)
		name = name.split('-')[0]
		text_zone = datalist_elt.find_element("name", f"{name}-text")
		hidden_value = datalist_elt.find_element("name", name)
		if text_to_type:
			text_zone.clear()
			text_zone.send_keys(text_to_type)
		else:
			text_zone.clear()
			text_zone.send_keys("a" + Keys.BACKSPACE)
		if filtered_choices:
			dropdown_elt = datalist_elt.find_element(By.TAG_NAME, "ul")
			choice_elt = None
			for i, choice in enumerate(filtered_choices, 1):
				elt = dropdown_elt.find_element(By.CSS_SELECTOR, f"li:nth-child({i})")
				assert elt.text == choice
				if elt.text == choice_to_select:
					choice_elt = elt
			choice_elt.click()

	def get_field_value(self, name):
		field = self.driver.find_element("name", name)
		return field.get_attribute("value")

	def get_select_choices(self, css_selector):
		select = self.driver.find_element(By.CSS_SELECTOR, css_selector)
		return [o.text for o in select.find_elements(By.TAG_NAME, "option")]

	def get_selected_choice(self, name):
		field = self.driver.find_element("name", name)
		return field.find_element(By.CSS_SELECTOR, "[selected]").text

	def fill_form(self, form_dict, select_visible_text=True, submit_btn_text=None, do_submit=True):
		for input_name, value in form_dict.items():
			if value is None:
				continue
			if type(value) is bool:
				self.checkbox(input_name, value)
			elif input_name.endswith("-datalist"):
				self.datalist(input_name, *value)
			elif self.driver.find_element("name", input_name).tag_name == "select":
				kwargs = {'visible_text' if select_visible_text else 'value': value}
				self.select(input_name, **kwargs)
			elif input_name.startswith("datetime"):
				self.input_datetime(input_name, value)
			elif input_name.startswith("date"):
				self.input_date(input_name, value)
			else:
				self.input_text(input_name, str(value))
		if do_submit:
			self.submit(submit_btn_text)

	@scroll_to_click
	def submit(self, submit_btn_text=None):
		try:
			container = self.driver.find_element(By.CSS_SELECTOR, '.modal.show')
		except NoSuchElementException:
			container = self.driver
		css_selector = '[type="submit"]'
		if submit_btn_text is not None:
			css_selector += f'[value="{submit_btn_text}"]'
		element = container.find_element(By.CSS_SELECTOR, css_selector)
		element.click()

	def assert_wtf_error(self, text=""):
		element = self.driver.find_element(By.CSS_SELECTOR, '.invalid-field')
		assert text.lower() in element.text.lower()


class TableActionsMixin:

	def click_table_row(self, table_name, row_idx):
		self.wait_for_document_ready()
		tr = self.driver.find_elements(By.CSS_SELECTOR, 'table[name="%s"] tr:nth-child(%d) td' % (table_name, row_idx))[0]
		tr.click()

	def click_table_row_by_content(self, table_name, text=""):
		self.wait_for_document_ready()
		table = self.driver.find_element(By.CSS_SELECTOR, 'table[name="%s"]' % table_name)
		row_idx = 1
		while True:
			tr = table.find_elements(By.CSS_SELECTOR, 'tbody tr:nth-child(%d)' % row_idx)
			col_idx = 1
			while True:
				elt = tr[0].find_element(By.CSS_SELECTOR, 'td:nth-child(%d)' % col_idx)
				if text in elt.text:
					elt.click()
					return
				col_idx += 1
			row_idx += 1

	def click_table_add(self, table_name):
		self.wait_for_document_ready()
		element = self.driver.find_element(By.ID, f"btn-create-{table_name}")
		element.click()

	def search_table(self, table_name, text_to_search):
		self.wait_for_document_ready()
		element = self.driver.find_element(By.CSS_SELECTOR, f'.searchbox[name="{table_name}"]')
		element.send_keys(text_to_search)

	def get_table_header(self, table_name, col_nb):
		self.wait_for_document_ready()
		table = self.driver.find_element(By.CSS_SELECTOR, 'table[name="%s"]' % table_name)
		tr = table.find_element(By.CSS_SELECTOR, 'thead tr')
		return tr.find_element(By.CSS_SELECTOR, 'th:nth-child(%d)' % (col_nb)).text

	def _get_table_row(self, table_name, row):
		self.wait_for_document_ready()
		table = self.driver.find_element(By.CSS_SELECTOR, 'table[name="%s"]' % table_name)
		return table.find_elements(By.CSS_SELECTOR, 'tbody tr:nth-child(%d)' % row)[0]

	def get_table_row(self, table_name, row):
		tr = self._get_table_row(table_name, row)
		return [elt.text for elt in tr.find_elements(By.CSS_SELECTOR, 'td')]

	def _get_table_field(self, table_name, row, col, get_text=False):
		tr = self._get_table_row(table_name=table_name, row=row)
		elt = tr.find_element(By.CSS_SELECTOR, 'td:nth-child(%d)' % col)
		return elt.text if get_text else elt

	def get_table_field(self, table_name, row, col):
		return self._get_table_field(table_name, row, col, get_text=True)

	def get_table_field_raw(self, table_name, row, col):
		return self._get_table_field(table_name, row, col)

	def check_table(self, table_name, dimensions=(1, 3), header=("", "", ""), rows=(("", "", "")), has_checkboxes=False):
		self.wait_for_document_ready()
		middle_row, last_row = dimensions[0] // 2 + 1, dimensions[0]
		middle_col, last_col = dimensions[1] // 2 + 1, dimensions[1]
		cells_coordinates = (
			((1          , 1), (1          , middle_col), (1          , last_col)),
			((middle_row , 1), (middle_row , middle_col), (middle_row , last_col)),
			((last_row   , 1), (last_row   , middle_col), (last_row   , last_col)),
		)
		for col in range(3):
			header_col = cells_coordinates[0][col][1]
			if has_checkboxes:
				header_col += 1
			assert self.get_table_header(table_name, header_col) == header[col]
		for coord in [(y, x) for y in range(min(3, dimensions[0])) for x in range(min(3, dimensions[1]))]:
			row, col = cells_coordinates[coord[0]][coord[1]]
			if has_checkboxes:
				col += 1
			assert self.get_table_field(table_name,	row, col) == rows[coord[0]][coord[1]]

	def check_download_field(self, table_name, row, col, basename="polop.pdf"):
		file_field = self.get_table_field_raw(table_name, row, col)
		anchor = file_field.find_element(By.CSS_SELECTOR, "a")
		_LOGGER.critical("anchor=%s", anchor.get_attribute("href"))
		uploaded = {
			'polop.pdf': {'hash': "185b5b433e47391824dc9a6599edb8041c984b43ee31a28a5e4fd4d4e2f0b42f", 'fa': "-pdf"},
			'polop.png': {'hash': "d014466d0302c0b0ddae35a557c50f65570ab4bc4cfa9d7c4bb793d1fa576878", 'fa': ""},
			'polop.txt': {'hash': "ff3f012667b82adcebaad526b513f1ef87616baf249522e1d9858d4746a188ef", 'fa': ""},
		}[basename]
		# ~ assert f"fa-solid fa-file-{uploaded['fa']}" in anchor.get_attribute("class")
		assert f"upload/{uploaded['hash']}" in anchor.get_attribute("href")


def pick_a_free_port():
	with socket() as s:
		s.bind(('', 0))
		return s.getsockname()[1]


class ServerThread(threading.Thread):

	def __init__(self, app, port):
		threading.Thread.__init__(self)
		self.server = make_server('0.0.0.0', port, app)
		self.ctx = app.app_context()
		self.ctx.push()

	def run(self):
		self.server.serve_forever()

	def shutdown(self):
		self.server.shutdown()


class SeleniumFixtures(ActionsMixin, FormActionsMixin, TableActionsMixin):

	@pytest.fixture(scope='function')
	def start_app(self, request):
		self.server_port = str(pick_a_free_port())
		database_name = "%s_test" % environ['DATABASE_NAME']
		# database_name = "%s_%s" % (environ['DATABASE_NAME'], server_port, )  TODO for diversification in case of parallelizing tests
		# call("sudo -u postgres dropdb %s" % database_name)
		# ~ call(shlex.split("sudo -u postgres createdb -T template0 %s" % database_name))
		self.app, self.database = create_app(cleanup=True, database_name=database_name)

		def finalize():
			self.database.close()
			# call("sudo -u postgres dropdb %s" % database_name, capture=False)  TODO for diversification in case of parallelizing tests

		request.addfinalizer(finalize)

	@property
	def driver(self):
		try:
			return self._local.current_driver
		except AttributeError:
			self._local = threading.local()
			self._local.current_driver = self._drivers[0]
			return self._local.current_driver

	def __switch_to_browser(self, idx):
		self._local.current_driver = self._drivers[idx]

	def switch_to_browser_1(self):
		self.__switch_to_browser(0)

	def switch_to_browser_2(self):
		self.__switch_to_browser(1)

	@pytest.fixture(scope='function')
	def start_driver(self, request):
		self.server = ServerThread(self.app, self.server_port)
		self.server.start()
		chrome_options = webdriver.ChromeOptions()
		for option in (
				"start-maximized",
				"auto-open-devtools-for-tabs",
			):
			chrome_options.add_argument(option)
		self._drivers = []
		for i in range(2):
			executor_port = 4444 + i
			driver = webdriver.Remote(
				command_executor=f"http://localhost:{executor_port}",
				options=chrome_options
			)
			driver.get(f"http://192.168.0.10:{self.server_port}")
			self._drivers.append(driver)

		def finalize():
			# ~ sleep(60)
			for driver in self._drivers:
				driver.quit()
				self.server.shutdown()
				self.server.join()

		request.addfinalizer(finalize)

	def wait_for_document_ready(self, is_modal=False):
		WebDriverWait(self.driver, timeout=7).until(lambda x: self.driver.find_element(By.CSS_SELECTOR,
			'.modal.show' if is_modal else '.selenium-ready, body[data-http-status]'
		))

	@pytest.fixture(scope='function')
	def users(self):
		with self.database.bind_ctx(WEBLIB_MODELS):
			for user in ('gilmour', 'knopfler'):
				user = USERS[user].copy()
				user['password'] = hashpw(user['password'].encode(), gensalt())
				create_user(**user)

	@pytest.fixture(scope='function')
	def treasurer(self):
		with self.database.bind_ctx(WEBLIB_MODELS):
			for user in ('treasurer', ):
				user = USERS[user].copy()
				user['password'] = hashpw(user['password'].encode(), gensalt())
				create_user(**user)

