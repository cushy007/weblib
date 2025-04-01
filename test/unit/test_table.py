#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
from unittest.mock import Mock

from playhouse.flask_utils import FlaskDB

from weblib.requests import TableRequestResult
from weblib.table import Table


def test01a():
	""" Table request """
	table_name = "table_name"
	content_url = "/table_name/content.json"
	mock_model_fields_to_display = [Mock(spec=FlaskDB.Model, column_name=cn, i18n=i18n, lut=lut) for cn, i18n, lut in (
		('last_name'  , "Nom"           , None),
		('first_name' , "Prénom"        , None),
		('second_name', "Second prénom" , None),
		('is_alive'   , "Vivant"        , None),
	)]
	mock_query = (
		(2, "Beck", "Jeff", "", False),
		(1, "Gilmour", "David", "Marcel", True),
	)
	table = Table(table_name, content_url)
	table.build_from_request(TableRequestResult(mock_model_fields_to_display, mock_query))
	assert table.dict['name'] == table_name
	assert table.dict['header'] == (
		{'name': 'last_name'   , 'i18n': "Nom"           , 'values': ()},
		{'name': 'first_name'  , 'i18n': "Prénom"        , 'values': ()},
		{'name': 'second_name' , 'i18n': "Second prénom" , 'values': ()},
		{'name': 'is_alive'    , 'i18n': "Vivant"        , 'values': ()},
	)
	assert table.dict['rows'] == (
		{'id': 2, 'class': () , 'title': "Chose an action", 'fields': ("Beck", "Jeff", "", "No")},
		{'id': 1, 'class': () , 'title': "Chose an action", 'fields': ("Gilmour", "David", "Marcel", "Yes")},
	)

	########## Finally expected :
	# ~ assert table.dict == {
		# ~ 'name': table_name,
		# ~ 'header': (
			# ~ {'name': 'last_name'   , 'i18n': "Nom"           , 'values': ("Beck", "Gilmour")},
			# ~ {'name': 'first_name'  , 'i18n': "Prénom"        , 'values': ("David", "Jeff")},
			# ~ {'name': 'second_name' , 'i18n': "Second prénom" , 'values': (None, "Marcel")},
			# ~ {'name': 'is_alive'    , 'i18n': "Vivant"        , 'values': ({False: "Non"}, {True: "Oui"})},
		# ~ ),
		# ~ 'rows': (
		# ~ ),
		# ~ 'buttons': (
			# ~ {'href': "/gear/item/info", 'i18n': _l("Item info")},
			# ~ {'href': "/gear/item/add_inventory", 'i18n': _l("Add inventory")},
			# ~ {'href': "/gear/item/modify", 'i18n': _l("Modify item")},
			# ~ {'href': "/gear/item/delete", 'i18n': _l("Delete item"), 'confirmation_message': "Are you sure ?"},
		# ~ ),
	# ~ }


