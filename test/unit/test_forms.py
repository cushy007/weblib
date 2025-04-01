#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import datetime as dt
from unittest.mock import Mock

import pytest
import time_machine
from werkzeug.datastructures import MultiDict

from weblib.forms import (
	BaseForm, DateField, DecimalField, DoubleSelectField, FileField, IntegerField, PriceField, SelectField, TextAreaField,
	TextField, UnknownFieldException
)
from weblib.models import flask_db


class TestForm(BaseForm):
	pass


@pytest.fixture(scope='function')
def init_forms():
	TestForm._is_initialized = False


@pytest.fixture(scope='function')
def mock_request():
	request = Mock()
	request.form = MultiDict()
	return request


def wrap_in_form(html, label_for="text_input"):
	return f"""<div class="form-group mb-3">
	<label for="{label_for}">The label</label>
	{html}
</div>
<input type="hidden" name="id" class="form-control" value="None"></input>"""


def compact(text):
	return str(text).replace('\t', '').replace('\n', '')


def test_text_input_field_01a(init_forms, mock_request):
	"""TextField"""
	TestForm.fields = {'text_input': TextField("The label")}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<input type="text" name="text_input" class="form-control" autofocus></input>"""))


def test_text_input_field_02a(init_forms, mock_request):
	"""TextField: populated with a value by mean of the form"""
	TestForm.fields = {'text_input': TextField("The label")}
	mock_request.form.update({'text_input': "The field value"})
	form = TestForm(request_object=mock_request)
	assert form.dict == {'text_input': "The field value"}
	assert form.text_input.data == "The field value"
	assert compact(form) == compact(wrap_in_form("""<input type="text" name="text_input" class="form-control" value="The field value" autofocus></input>"""))


def test_text_input_field_02b(init_forms, mock_request):
	"""TextField: populated with a value by the field itself"""
	TestForm.fields = {'text_input': TextField("The label")}
	form = TestForm(request_object=mock_request)
	form.text_input.data = "The field value"
	assert form.dict == {'text_input': "The field value"}
	assert compact(form) == compact(wrap_in_form("""<input type="text" name="text_input" class="form-control" value="The field value" autofocus></input>"""))


def test_text_input_field_02c(init_forms, mock_request):
	"""TextField: a value is set for a name unknown to the form -> raise"""
	TestForm.fields = {'text_input': TextField("The label")}
	with pytest.raises(UnknownFieldException):
		form = TestForm(TestForm(MultiDict((('unknown_field-name', "The field value"), ))))


def test_text_input_field_03a(init_forms, mock_request):
	"""TextField: the label comes from the model"""
	ModelMock = Mock(spec=flask_db.Model)
	ModelMock.text_input = Mock(spec=['i18n'])
	ModelMock.text_input.i18n = "The label"
	TestForm.fields = {'text_input': TextField(ModelMock)}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<input type="text" name="text_input" class="form-control" autofocus></input>"""))


def test_text_input_field_04a(init_forms, mock_request):
	"""TextField: default value"""
	TestForm.fields = {'text_input': TextField("The label", default="The content")}
	form = TestForm(request_object=mock_request)
	assert form.dict == {'text_input': "The content"}
	assert compact(form) == compact(wrap_in_form("""<input type="text" name="text_input" class="form-control" value="The content" autofocus></input>"""))


def test_text_input_field_05a(init_forms, mock_request):
	"""TextField: required"""
	TestForm.fields = {'text_input': TextField("The label", required=True)}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<input type="text" name="text_input" class="form-control" required autofocus></input>"""))




@time_machine.travel(dt.datetime(2025, 2, 12))
def test_date_field_01a(init_forms, mock_request):
	"""DateField: default value is "now" """
	TestForm.fields = {'date': DateField("The label", default="now")}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<input type="date" name="date" class="form-control" value="2025-02-12" autofocus></input>""", label_for="date"))


@time_machine.travel(dt.datetime(2025, 2, 12))
def test_date_field_01b(init_forms, mock_request):
	"""DateField: default value is in text format "2025-02-13" """
	TestForm.fields = {'date': DateField("The label", default="2025-02-13")}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<input type="date" name="date" class="form-control" value="2025-02-13" autofocus></input>""", label_for="date"))


@time_machine.travel(dt.datetime(2025, 2, 12))
def test_date_field_01c(init_forms, mock_request):
	"""DateField: default value is datetime() format """
	TestForm.fields = {'date': DateField("The label", default=dt.date(2025, 2, 13))}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<input type="date" name="date" class="form-control" value="2025-02-13" autofocus></input>""", label_for="date"))




def test_integer_field_01a(init_forms, mock_request):
	"""IntegerField: default value"""
	TestForm.fields = {'integer': IntegerField("The label", default=3)}
	form = TestForm(request_object=mock_request)
	assert form.dict == {'integer': 3}
	assert compact(form) == compact(wrap_in_form("""<input type="number" name="integer" class="form-control" value="3" step="1" autofocus></input>""", label_for="integer"))


def test_integer_field_02a(init_forms, mock_request):
	"""IntegerField: required"""
	TestForm.fields = {'integer': IntegerField("The label", required=True)}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<input type="number" name="integer" class="form-control" step="1" required autofocus></input>""", label_for="integer"))


def test_integer_field_04a(init_forms, mock_request):
	"""IntegerField: with zero values for min and max"""
	TestForm.fields = {'integer': IntegerField("The label", min=0, max=0)}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<input type="number" name="integer" class="form-control" min="0" max="0" step="1" autofocus></input>""", label_for="integer"))


def test_integer_field_05a(init_forms, mock_request):
	"""IntegerField: the units come from the model"""
	ModelMock = Mock(spec=flask_db.Model)
	ModelMock.millimeters = Mock()
	ModelMock.millimeters.i18n = "The label"
	ModelMock.millimeters.units = "mm"
	TestForm.fields = {'millimeters': IntegerField(ModelMock)}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<div class="input-group mb-3"><input type="number" name="millimeters" class="form-control" step="1" autofocus></input><span class="input-group-text">mm</span></div>""", label_for="millimeters"))




def test_decimal_field_03a(init_forms, mock_request):
	"""DecimalField: with min, max and step"""
	TestForm.fields = {'decimal': DecimalField("The label", min=3, max=7, step=0.5)}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<input type="number" name="decimal" class="form-control" min="3" max="7" step="0.5" autofocus></input>""", label_for="decimal"))




def test_price_field_01a(init_forms, mock_request):
	"""PriceField: nominal case"""
	TestForm.fields = {'price': PriceField("The label")}
	mock_request.form.update({'price': 1.99})
	form = TestForm(request_object=mock_request)
	assert form.dict == {'price': 1.99}
	assert compact(form) == compact(wrap_in_form("""<input type="number" name="price" class="form-control" value="1.99" min="0" step="0.01" autofocus></input>""", label_for="price"))


def test_price_field_02a(init_forms, mock_request):
	"""PriceField: with default value"""
	TestForm.fields = {'price': PriceField("The label", default=1.99)}
	form = TestForm(request_object=mock_request)
	assert form.dict == {'price': 1.99}
	assert compact(form) == compact(wrap_in_form("""<input type="number" name="price" class="form-control" value="1.99" min="0" step="0.01" autofocus></input>""", label_for="price"))




def test_textarea_field_01a(init_forms, mock_request):
	"""TextAreaField: """
	TestForm.fields = {'textarea': TextAreaField("The label")}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<textarea name="textarea" class="form-control" autofocus></textarea>""", label_for="textarea"))




def test_select_field_01a(init_forms, mock_request):
	"""SelectField: no choice"""
	TestForm.fields = {'select': SelectField("The label")}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" autofocus>
	<option value=""></option>
</select>
""", label_for="select"))


def test_select_field_01b(init_forms, mock_request):
	"""SelectField: added HTML attributes"""
	TestForm.fields = {'select': SelectField("The label", data_user="user 1")}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" data-user="user 1" autofocus>
	<option value=""></option>
</select>
""", label_for="select"))


def test_select_field_02a(init_forms, mock_request):
	"""SelectField: with choices"""
	TestForm.fields = {'select': SelectField("The label", choices=((1, "text1"), (2, "text2")))}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" autofocus>
	<option value=""></option>
	<option value="1">text1</option>
	<option value="2">text2</option>
</select>
""", label_for="select"))


def test_select_field_02b(init_forms, mock_request):
	"""SelectField: with a selected choice"""
	TestForm.fields = {'select': SelectField("The label", choices=((1, "text1"), (2, "text2")))}
	form = TestForm(MultiDict((('select', 2), )))
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" autofocus>
	<option value=""></option>
	<option value="1">text1</option>
	<option value="2" selected>text2</option>
</select>
""", label_for="select"))


def test_select_field_03a(init_forms, mock_request):
	"""SelectField: with a default value"""
	TestForm.fields = {'select': SelectField("The label", choices=((1, "text1"), (2, "text2")), default=2)}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" autofocus>
	<option value="1">text1</option>
	<option value="2" selected>text2</option>
</select>
""", label_for="select"))


def test_select_field_04a(init_forms, mock_request):
	"""SelectField: choices as a callback -> built at form's instanciation"""
	choices_cb = Mock(return_value=((1, "text1"), (2, "text2")))
	TestForm.fields = {'select': SelectField("The label", choices=choices_cb)}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" autofocus>
	<option value=""></option>
	<option value="1">text1</option>
	<option value="2">text2</option>
</select>
""", label_for="select"))


def test_select_field_10a(init_forms, mock_request):
	"""SelectField: multiple choices"""
	TestForm.fields = {'select': SelectField("The label", choices=((1, "text1"), (2, "text2"), (3, "text3")), multiple=True)}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" multiple autofocus size="3">
	<option value="1">text1</option>
	<option value="2">text2</option>
	<option value="3">text3</option>
</select>
""", label_for="select"))


def test_select_field_11a(init_forms, mock_request):
	"""SelectField: multiple choices with a default value"""
	TestForm.fields = {'select': SelectField("The label", choices=((1, "text1"), (2, "text2"), (3, "text3")), multiple=True, default=2)}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" multiple autofocus size="3">
	<option value="1">text1</option>
	<option value="2" selected>text2</option>
	<option value="3">text3</option>
</select>
""", label_for="select"))


def test_select_field_11b(init_forms, mock_request):
	"""SelectField: multiple choices with multiple default values"""
	TestForm.fields = {'select': SelectField("The label", choices=((1, "text1"), (2, "text2"), (3, "text3")), multiple=True, default=set((1, 3)))}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" multiple autofocus size="3">
	<option value="1" selected>text1</option>
	<option value="2">text2</option>
	<option value="3" selected>text3</option>
</select>
""", label_for="select"))


def test_select_field_11c(init_forms, mock_request):
	"""SelectField: multiple choices loaded by a form comming from a Flask request (MultiDict)"""
	TestForm.fields = {'select': SelectField("The label", choices=((1, "text1"), (2, "text2"), (3, "text3")), multiple=True)}
	form = TestForm(MultiDict((('select', 1), ('select', 3))))
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" multiple autofocus size="3">
	<option value="1" selected>text1</option>
	<option value="2">text2</option>
	<option value="3" selected>text3</option>
</select>
""", label_for="select"))


def test_select_field_11d(init_forms, mock_request):
	"""SelectField: more than 10 choices -> ensure that the select box does not grow too much (show 10 items max)"""
	TestForm.fields = {'select': SelectField("The label", choices=[(i, "text%d" % i) for i in range(12)], multiple=True)}
	form = TestForm(MultiDict((('select', 1), ('select', 3))))
	assert compact(form) == compact(wrap_in_form("""
<select name="select" class="form-control" multiple autofocus size="10">
	<option value="0">text0</option>
	<option value="1" selected>text1</option>
	<option value="2">text2</option>
	<option value="3" selected>text3</option>
	<option value="4">text4</option>
	<option value="5">text5</option>
	<option value="6">text6</option>
	<option value="7">text7</option>
	<option value="8">text8</option>
	<option value="9">text9</option>
	<option value="10">text10</option>
	<option value="11">text11</option>
</select>
""", label_for="select"))




def test_double_select_field_01a(init_forms, mock_request):
	"""DoubleSelectField: set choices url"""
	TestForm.fields = {'double_select': DoubleSelectField(("Parent label", "Child label"), parent_choices=((1, "text1"), (2, "text2")))}
	form = TestForm(request_object=mock_request)
	form.double_select.choices_url = "/populate/child.json"
	assert compact(form) == compact("""
<div class="form-group mb-3 double-select">
	<div class="col">
		<label for="double_select-parent">Parent label</label>
		<select id="double_select-parent" name="double_select-parent" class="form-control" data-parent-select autofocus>
			<option value="1">text1</option>
			<option value="2">text2</option>
		</select>
	</div>
	<div class="col">
		<label for="double_select">Child label</label>
		<select id="double_select" name="double_select" class="form-control" data-child-select choices-url="/populate/child.json"></select>
	</div>
</div>
<input type="hidden" name="id" class="form-control" value="None"></input>
""")


def test_double_select_field_01b(init_forms, mock_request):
	"""DoubleSelectField: parent choices as callback"""
	parent_choices_cb = Mock(return_value=((1, "text1"), (2, "text2")))
	TestForm.fields = {'double_select': DoubleSelectField(("Parent label", "Child label"), parent_choices=parent_choices_cb)}
	form = TestForm(request_object=mock_request)
	form.double_select.choices_url = "/populate/child.json"
	assert compact(form) == compact("""
<div class="form-group mb-3 double-select">
	<div class="col">
		<label for="double_select-parent">Parent label</label>
		<select id="double_select-parent" name="double_select-parent" class="form-control" data-parent-select autofocus>
			<option value="1">text1</option>
			<option value="2">text2</option>
		</select>
	</div>
	<div class="col">
		<label for="double_select">Child label</label>
		<select id="double_select" name="double_select" class="form-control" data-child-select choices-url="/populate/child.json"></select>
	</div>
</div>
<input type="hidden" name="id" class="form-control" value="None"></input>
""")


def test_double_select_field_02a(init_forms, mock_request):
	"""DoubleSelectField: add custom HTML attribute to child only"""
	TestForm.fields = {'double_select': DoubleSelectField(("Parent label", "Child label"), data_custom="c1")}
	form = TestForm(request_object=mock_request)
	form.double_select.choices_url = "/populate/child.json"
	assert compact(form) == compact("""
<div class="form-group mb-3 double-select">
	<div class="col">
		<label for="double_select-parent">Parent label</label>
		<select id="double_select-parent" name="double_select-parent" class="form-control" data-parent-select autofocus></select>
	</div>
	<div class="col">
		<label for="double_select">Child label</label>
		<select id="double_select" name="double_select" class="form-control" data-child-select choices-url="/populate/child.json" data-custom="c1"></select>
	</div>
</div>
<input type="hidden" name="id" class="form-control" value="None"></input>
""")


def test_double_select_field_02b(init_forms, mock_request):
	"""DoubleSelectField: add custom HTML attributes to parent and child"""
	TestForm.fields = {'double_select': DoubleSelectField(
		("Parent label", "Child label"),
		parent_attributes={'data_custom': "p1"},
		data_custom="c1",
	)}
	form = TestForm(request_object=mock_request)
	form.double_select.choices_url = "/populate/child.json"
	assert compact(form) == compact("""
<div class="form-group mb-3 double-select">
	<div class="col">
		<label for="double_select-parent">Parent label</label>
		<select id="double_select-parent" name="double_select-parent" class="form-control" data-parent-select data-custom="p1" autofocus>
		</select>
	</div>
	<div class="col">
		<label for="double_select">Child label</label>
		<select id="double_select" name="double_select" class="form-control" data-child-select choices-url="/populate/child.json" data-custom="c1"></select>
	</div>
</div>
<input type="hidden" name="id" class="form-control" value="None"></input>
""")




def test_file_field_01a(init_forms, mock_request):
	"""FileField"""
	TestForm.fields = {'file_input': FileField("The label")}
	file_storage = Mock()
	file_storage.read.return_value = b"polop"
	file_storage.filename = "report.pdf"
	mock_request.files = {'file_input': file_storage}
	form = TestForm(request_object=mock_request)
	assert compact(form) == compact(wrap_in_form("""<input type="file" name="file_input" class="form-control" value="33c0f9010ea85b9e93fa782eb6219a280a2f30caedc03add1cdf3dec6e6d18e6.pdf" autofocus></input>""", label_for="file_input"))

