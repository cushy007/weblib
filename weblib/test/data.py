#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
USERS = {
	'gilmour': {
		# ~ 'email': "david.gilmour@dummy.net",
		'username': "dgilmour",
		'last_name': "Gilmour",
		'first_name': "David",
		'password': "1234",
		'password_confirmation': "1234",
		'roles': ("admin", )
	},
	'knopfler': {
		'username': "mknopfler",
		'last_name': "Knopfler",
		'first_name': "Mark",
		'password': "5678",
		'password_confirmation': "5678",
		'roles': ("user", ),
	},
	'beck': {
		'username': "jbeck",
		'last_name': "Beck",
		'first_name': "Jeff",
		'password': "9012",
		'password_confirmation': "9012",
		'roles': ("admin", ),
	},
	'treasurer': {
		'username': "ir",
		'last_name': "R.",
		'first_name': "Isa",
		'password': "567",
		'password_confirmation': "567",
		'roles': ("treasurer", ),
	},
}
