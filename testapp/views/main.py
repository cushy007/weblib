import logging
from os import environ

from flask import Blueprint, jsonify, redirect, request, send_from_directory, url_for
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from flask_login import login_required

from testapp.forms import (
	ComprehensiveDefaultsForm, ComprehensiveForm, ComprehensiveRequiredForm, ComprehensiveValidatorsForm
)
from testapp.models import ComprehensiveModel
from testapp.requests import get_child_choices, get_comprehensive_request
from weblib.roles import ROLE_ADMIN, ROLE_USER, roles_required
from weblib.views import Tab, crud_page, site

_LOGGER = logging.getLogger(__name__)


main_views = Blueprint('main_views', __name__, template_folder="templates", static_folder="static")


@main_views.before_request
@login_required
def before_request():
	pass


TABS = {
	'comprehensive_2': Tab('comprehensive_2', _l("Comprehensive 2"), children={
		'open': Tab('open', _l("Open")),
		'required': Tab('required', _l("Required")),
		'defaults': Tab('defaults', _l("Defaults")),
		'validators': Tab('validators', _l("Validators")),
	}),
}


site.set_tabs(TABS)


@main_views.route('/')
def index():
	return redirect("/comprehensive_2/")


@main_views.route('/comprehensive_2/')
def comprehensive():
	return redirect("/comprehensive_2/open")



# ~def region_choices():
	# ~country = request.args.get('get_children')
	# ~regions = get_regions(country)
	# ~_LOGGER.info(f"Regions of '{country}' are '{regions}'")
	# ~return jsonify(regions)

#@main_views.route('/comprehensive_1/comprehensive.table')
#@main_views.route('/comprehensive_1/comprehensive.table/upload/<filename>', methods=['GET'])  # TODO move this in crud_table
#def comprehensive_1(filename=None):
#	if filename is not None:
#		return send_from_directory(environ.get('UPLOAD_DIR', environ['HOME']), filename)  #, as_attachment=True)
#
#	table = Table("Comprehensive 1")
#
#	def class_builder(fields_dict):
#		return () if int(fields_dict.get('count', 0)) > 0 else ("unavailable", )
#
#	table.build_from_request(get_comprehensive_table(), class_builder=class_builder)
#	table.buttons = (
#		{'href': "/comprehensive_1/custom_action", 'i18n': _l("Custom action"), 'confirmation_message': _l("Are you sure ?")},
#	)
#	return jsonify(table.dict)


@main_views.route('/comprehensive_2/<form_type>/')
@main_views.route('/comprehensive_2/<form_type>/<table_name>.table', methods=['GET'])
@main_views.route('/comprehensive_2/<form_type>/<table_name>/<crud_step>', methods=['GET', 'POST'])
@main_views.route('/comprehensive_2/<form_type>/<table_name>/upload/<filename>', methods=['GET'])
@roles_required(ROLE_ADMIN, ROLE_USER)
def comprehensive_2(form_type, table_name=None, crud_step="read", filename=None):
	if filename is not None:
		return send_from_directory(environ.get('UPLOAD_DIR', environ['HOME']), filename)  #, as_attachment=True)

	if request.method == 'GET':
		resource_to_fetch = request.args.get('fetch')
		if resource_to_fetch:
			_LOGGER.info(f"Treating AJAX request for '{resource_to_fetch}'")
			return jsonify({'double_select.choices': get_child_choices}.get(resource_to_fetch)())

	query, columns = get_comprehensive_request()
	return crud_page(table_name, crud_step,
		url=f"/comprehensive_2/{form_type}/",
		page_title= _("Comprehensive 2"),
		active_sub_tab=form_type,
		tables={
			'comprehensive': {
				'model_factory': ComprehensiveModel,
				'query': query,
				'columns': columns,
				'order_by': ComprehensiveModel.text,
				'form_factory': {
					'open': ComprehensiveForm,
					'required': ComprehensiveRequiredForm,
					'defaults': ComprehensiveDefaultsForm,
					'validators': ComprehensiveValidatorsForm,
				}[form_type],
			},
		},
	)


#@gear_views.route('/comprehensive_3')
#@gear_views.route('/comprehensive_3/<item_id>')
#@gear_views.route('/comprehensive_3/<item_id>/<table_name>.table', methods=['GET'])
#@gear_views.route('/comprehensive_3/<item_id>/<table_name>/<crud_step>', methods=['GET', 'POST'])
#@gear_views.route('/comprehensive_3/<item_id>/<table_name>/upload/<filename>', methods=['GET'])  # TODO move this in crud_table
#def comprehensive_3(item_id=None, table_name=None, crud_step="read", filename=None):
#	item_id = item_id or request.args['id']
#	# ~group, item_type = get_group_and_type(item_id)
#
#	if filename is not None:
#		return send_from_directory(environ.get('UPLOAD_DIR', environ['HOME']), filename)  #, as_attachment=True)
#
#	return crud_page(table_name, crud_step,
#		# ~html_template="gear/item/info.html",
#		# ~item_name=Item.type.lut[get_item_type(item_id)],
#		# ~reference=get_item(item_id)['reference'],
#		# ~url=f"/gear/item/info/{item_id}",
#		# ~active_tab='gear',
#		# ~available_sub_tabs=GEAR.groups,
#		# ~active_sub_tab=GEAR[group],
#		# ~available_items=GEAR[group].items,
#		# ~active_item=GEAR[group][item_type],
#		# ~active_gear_item=GEAR[group][item_type],
#		tables={
#			'comprehensive_3_1': {
#				'title': _("Comprehensive 3.1"),
#				'model_factory': ComprehensiveModel,
#				'columns': (ComprehensiveModel.text, ComprehensiveModel.integer),
#				'where_predicate': (ComprehensiveModel.id == item_id),
#				'order_by': ItemState.date,
#				'form_factory': StateForm,
#			},
#			'comprehensive_3_2': {
#				'title': _("Comprehensive 3.2"),
#				'model_factory': Servicing,
#				'columns': (Servicing.date, Servicing.report_file),
#				'where_predicate': (Servicing.item_id == item_id),
#				'order_by': Servicing.date,
#				'form_factory': ServicingForm,
#			},
#		},
#	)


