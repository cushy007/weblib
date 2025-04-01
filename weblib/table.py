#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import json
import logging

from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

from weblib.requests import translate_row

_LOGGER = logging.getLogger(__name__)


class Table:

	def __init__(self, name, title="", row_title_builder=None, fields_builder=None):
		_LOGGER.info(f"Building {name} table")
		self.name = name
		self.title = title
		self.row_title_builder = row_title_builder or (lambda row: _("Chose an action"))
		self.default_fields_builder = fields_builder or self.default_fields_builder
		self.header = {}
		self.rows = []
		self.buttons = {}
		self.action = None

	def default_fields_builder(self, row, model_fields_to_display):
		"""
		Translates each field unless the ID one.

		:param row: the full row with the ID as first element.
		:param model_fields_to_display: the list of DB Model fields corresponding to the columns of the row.
		:return: a list of fields as they have to be displayed.

		"""
		return translate_row(row[1:], model_fields_to_display)

	def build_from_request(self, request_result, class_builder=lambda fields_dict: ()):
		self.header = tuple([{'name': field.column_name, 'i18n': field.i18n, 'values': ()} for field in request_result.model_fields_to_display])
		cols = [i['name'] for i in self.header]
		self.rows = []
		for row in request_result.query:
			self.rows.append({
				'id': row[0],
				'fields': self.default_fields_builder(row, request_result.model_fields_to_display),
				'class': class_builder(dict(zip(cols + request_result.model_fields_for_compute, row[1:]))),
				'title': self.row_title_builder(row),
			})
		self.rows = tuple(self.rows)
		return self

	@property
	def is_empty(self):
		return False  # FIXME always empty when used in the table template request

	@property
	def dict(self):
		assert not self.buttons or not self.action
		return {
			'name': self.name,
			'header': self.header,
			'rows': self.rows,
			'buttons': self.buttons,
			'action': self.action,
		}

	@property
	def json(self):
		return json.dumps(self.dict)
