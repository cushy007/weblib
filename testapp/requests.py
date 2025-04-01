import logging

from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from peewee import JOIN

from testapp.models import ChildModel, ColorModel, ComprehensiveModel, ParentModel

_LOGGER = logging.getLogger(__name__)


class DatabaseException(Exception):
	pass


class InventoryException(Exception):
	pass


def create_color(**kwargs): return ColorModel.create(**kwargs)
def create_parent(**kwargs): return ParentModel.create(**kwargs)
def create_child(**kwargs): return ChildModel.create(**kwargs)
def create_comprehensive(**kwargs): return ComprehensiveModel.create(**kwargs)


def get_color_choices():
	query = (ColorModel
		.select(ColorModel.id, ColorModel.name)
		.order_by(ColorModel.name)
	)
	return tuple([(row.id, row.name) for row in query])


def get_parent_choices():
	return ParentModel.select().order_by(ParentModel.name).tuples()


def get_child_choices():
	return ((1, "David"), (2, "Jeff"))
	return ChildModel.select().where(ChildModel.id == parent_id).order_by(ChildModel.name).tuples()  # TODO


def get_comprehensive_request():
	columns = (
		ComprehensiveModel.text,
		ComprehensiveModel.text_area,
		ComprehensiveModel.boolean,
		ComprehensiveModel.integer,
		ComprehensiveModel.decimal,
		ComprehensiveModel.price,
		ColorModel.name,
		ComprehensiveModel.double_select,
		ComprehensiveModel.datalist,
		ComprehensiveModel.date,
		ComprehensiveModel.datetime,
		ComprehensiveModel.barcode,
		ComprehensiveModel.qrcode,
		ComprehensiveModel.document,
		ComprehensiveModel.picture,
	)
	request = (ComprehensiveModel
		.select(ComprehensiveModel.id, *columns)
		.join(ColorModel, JOIN.LEFT_OUTER)
		.tuples()
	)

	try:
		rows = [row for row in request]
	except Exception:
		_LOGGER.exception("Shit !" * 100)
		rows = []

	return rows, columns


