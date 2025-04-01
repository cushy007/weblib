import logging

from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

from testapp.models import ComprehensiveModel
from testapp.requests import get_color_choices, get_parent_choices
from weblib.forms import (
	BARCODE_FORMAT, BarcodeField, BaseForm, BooleanField, DatalistField, DateField, DateTimeField, DecimalField,
	DoubleSelectField, FileField, IntegerField, PriceField, SelectField, TextAreaField, TextField
)

_LOGGER = logging.getLogger(__name__)


def create_datalist_source(**kwargs):
	_LOGGER.debug("Creating datalist in DB '%s'", kwargs)


def get_datalist_sources():
	return "URL"


class ComprehensiveForm(BaseForm):
	fields = {
		#'hidden':        HiddenField      (ComprehensiveModel),
		'text':          TextField        (ComprehensiveModel),
		'text_area':     TextAreaField    (ComprehensiveModel),
		'boolean':       BooleanField     (ComprehensiveModel),
		'integer':       IntegerField     (ComprehensiveModel),
		'decimal':       DecimalField     (ComprehensiveModel),
		'price':         PriceField       (ComprehensiveModel),
		'select_field':  SelectField      (ComprehensiveModel, choices=get_color_choices),
		'double_select': DoubleSelectField((_l("Parent"), _("Child")), parent_choices=get_parent_choices),
		'datalist':      DatalistField    (ComprehensiveModel, choices=get_datalist_sources, creation_request=create_datalist_source),
		'date':          DateField        (ComprehensiveModel),
		'datetime':      DateTimeField    (ComprehensiveModel),
		'barcode':       BarcodeField     (ComprehensiveModel, code_format=BARCODE_FORMAT),
		'qrcode':        BarcodeField     (ComprehensiveModel),
		'document':      FileField        (ComprehensiveModel),
		'picture':       FileField        (ComprehensiveModel),
	}


class ComprehensiveRequiredForm(BaseForm):
	fields = {
		#'hidden':        HiddenField      (ComprehensiveModel),
		'text':          TextField        (ComprehensiveModel, required=True),
		'text_area':     TextAreaField    (ComprehensiveModel, required=True),
		'boolean':       BooleanField     (ComprehensiveModel, required=True),  # FIXME # Non sense unless for terms and conditions checkboxes
		'integer':       IntegerField     (ComprehensiveModel, required=True),
		'decimal':       DecimalField     (ComprehensiveModel, required=True),
		'price':         PriceField       (ComprehensiveModel, required=True),
		'select_field':  SelectField      (ComprehensiveModel, required=True, choices=get_color_choices),
		'double_select': DoubleSelectField((_l("Parent"), _("Child")), parent_choices=get_parent_choices),
		'datalist':      DatalistField    (ComprehensiveModel, required=True, choices=get_datalist_sources, creation_request=create_datalist_source),
		'date':          DateField        (ComprehensiveModel, required=True),
		'datetime':      DateTimeField    (ComprehensiveModel, required=True),
		'barcode':       BarcodeField     (ComprehensiveModel, required=True, code_format=BARCODE_FORMAT),  # FIXME
		'qrcode':        BarcodeField     (ComprehensiveModel, required=True),  # FIXME
		'document':      FileField        (ComprehensiveModel, required=True),
		'picture':       FileField        (ComprehensiveModel, required=True),
	}


class ComprehensiveDefaultsForm(BaseForm):
	fields = {
		#'hidden':        HiddenField      (ComprehensiveModel),
		'text':          TextField        (ComprehensiveModel, default="Default line"),
		'text_area':     TextAreaField    (ComprehensiveModel, default="Default\n\nParagraph..."),
		'boolean':       BooleanField     (ComprehensiveModel, default=True),
		'integer':       IntegerField     (ComprehensiveModel, default=7),
		'decimal':       DecimalField     (ComprehensiveModel, default=7.5, min=0, step=0.5, max=100),
		'price':         PriceField       (ComprehensiveModel, default=7.07, min=0, step=0.01),  # FIXME
		'select_field':  SelectField      (ComprehensiveModel, default=2, choices=get_color_choices),
		'double_select': DoubleSelectField((_l("Parent"), _("Child")), parent_choices=get_parent_choices),  # TODO default
		#'datalist':     DatalistField    -> Non sense
		'date':          DateField        (ComprehensiveModel, default="now"),
		'datetime':      DateTimeField    (ComprehensiveModel, default="now"),
		'barcode':       BarcodeField     (ComprehensiveModel, default="1234567", code_format=BARCODE_FORMAT),  # FIXME
		'qrcode':        BarcodeField     (ComprehensiveModel, default="https://qr.com"),
		#'document':     FileField        -> Non sense
		#'picture':      FileField        -> Non sense
	}


def percentage_validator(form, field_data):
	if 0 <= int(field_data) < 100:
		pass
	else:
		return _("A percentage can't be negative or greater than 100")


def decimal_validator(form, field_data):
	if float(field_data) > 70:
		return _("Bad value (can't be greater than 70)")


def numeric_validator(form, field_data):
	try:
		int(field_data)
	except ValueError:
		return _("A barcode is only composed of numbers")
		raise


def length_validator(form, field_data):
	if len(field_data) > 12:
		return _("An EAN-13 barcode is 12 numbers long max")


def file_validator(form, field_data):
	if "." not in field_data:
		return _("The file must have an extension")


class ComprehensiveValidatorsForm(BaseForm):
	fields = {
		'integer':       IntegerField     (ComprehensiveModel, validators=(percentage_validator, )),
		'decimal':       DecimalField     (ComprehensiveModel, validators=(decimal_validator, )),
		'barcode':       BarcodeField     (ComprehensiveModel, code_format=BARCODE_FORMAT, validators=(numeric_validator, length_validator)),  # FIXME implement errors in __str__
		'document':      FileField        (ComprehensiveModel, validators=(file_validator, ), max_size=2000),
	}
