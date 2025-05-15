from flask_babel import lazy_gettext as _l
from peewee import BooleanField, DateField, DateTimeField, DecimalField, ForeignKeyField, IntegerField, TextField

from weblib.database import AbstractMigrator
from weblib.models import BaseModel, FileField, PriceField, flask_db


class ColorModel(BaseModel):
	name = TextField(unique=True)
	name.i18n = _l("Color")


class ParentModel(BaseModel):
	name = TextField(unique=True)
	name.i18n = _l("Parent")


class ChildModel(BaseModel):
	name = TextField(unique=True)
	name.i18n = _l("Child")


class ComprehensiveModel(BaseModel):
	text = TextField(null=True, unique=True)
	text.i18n = _l("Text")
	text_area = TextField(null=True)
	text_area.i18n = _l("Text area")
	boolean = BooleanField(null=True)
	boolean.i18n = _l("Boolean")
	integer = IntegerField(null=True)
	integer.i18n = _l("Integer")
	decimal = DecimalField(null=True, decimal_places=1)
	decimal.i18n = _l("Decimal")
	decimal.units = "µF"
	price = PriceField(null=True)
	price.i18n = _l("Price")
	select_field = ForeignKeyField(ColorModel, null=True)
	select_field.i18n = _l("Select")
	double_select = ForeignKeyField(ChildModel, null=True)
	double_select.i18n = _l("Double select")
	datalist = TextField(null=True)
	datalist.i18n = _l("Datalist")
	date = DateField(null=True)
	date.i18n = _l("Date")
	datetime = DateTimeField(null=True)
	datetime.i18n = _l("Datetime")
	barcode = TextField(null=True)
	barcode.i18n = _l("Barcode")
	qrcode = TextField(null=True)
	qrcode.i18n = _l("Qrcode")
	document = FileField(null=True)
	document.i18n = _l("Document")
	picture = FileField(null=True)
	picture.i18n = _l("Picture")


MODELS = [
	ColorModel,
	ParentModel,
	ChildModel,
	ComprehensiveModel,
]


VERSION = 1

class Migrator(AbstractMigrator):

	def migrate_to_version_2(self):
		pass
