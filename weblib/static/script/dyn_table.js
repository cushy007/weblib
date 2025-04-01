//
// Copyright 2021-2025, Johann Saunier
// SPDX-License-Identifier: AGPL-3.0-or-later
//
define(["bootstrap", "log", "lib"], function(bootstrap, log, lib) {

	/* mappings with 'tableElt' as key */
	let mResponses = {};
	let mFilteredIds = {};

	function _displayButtonBox(data, row) {
		let title = document.getElementById(`button-box-${data.name}-title`);
		title.innerHTML = row.title;
		let body = document.getElementById(`button-box-${data.name}-body`);
		body.replaceChildren();
		for (let button of data.buttons) {
			let elt = document.createElement("a");
			elt.setAttribute("type", "button");
			elt.classList.add("btn", "btn-primary", "btn-lg", "btn-block", "text-nowrap", "mt-3");
			elt.setAttribute("href", button.href + "?id=" + row.id);
			elt.innerHTML = button.i18n;
			body.appendChild(elt);
			if (button.confirmation_message) {
				console.log(`${button.href} is confirmable`);
				lib.attachConfirmationBox(elt, button.confirmation_message);
			}
		}
		let buttonBox = document.getElementById(`button-box-${data.name}`);
		new bootstrap.Modal(buttonBox).show();
	}

	function _populateTable(tableElt, data) {
		console.log(`[dyn-table] Populate table '${data.name}' with data:`);
		console.log(data);

		/* Do not display empty tables */
		if (data.rows.length == 0) {
			console.log(`[dyn-table] Table '${data.name}' is empty`);
			tableElt.querySelector(`#${data.name}-empty`).classList.remove("hidden");
			tableElt.querySelector(`#${data.name}-spinner`).classList.add("hidden");
		} else {

			/* Header */
			tr = tableElt.querySelector("thead tr");
			tr.replaceChildren();
			for (let field of data.header) {
				th = document.createElement("th");
				th.setAttribute('name', field.name);
				th.innerHTML = field.i18n;
				tr.appendChild(th);
			}

			/* Body */
			body = tableElt.querySelector("tbody");
			body.replaceChildren();
			len_buttons = data.buttons === undefined ? 0 : data.buttons.length;
			for (let row of data.rows) {
				if (! mFilteredIds[tableElt].includes(row.id)) {
					continue;
				}
				tr = document.createElement("tr");
				for (let c of row.class) {
					tr.classList.add(c);
				}
				for (let field of row.fields) {
					td = document.createElement("td");
					td.innerHTML = field;
					if (field.indexOf("href") < 0) {
						td.addEventListener("click", (evt) => {
							_displayButtonBox(data, row);
						});
						if (data.action !== null) {
							console.log(`Add action '${data.action.href}' when clicking on this cell`);
							td.addEventListener("click", (evt) => {
								window.location = data.action.href + "?id=" + row.id;
							});
						}
					}
					tr.appendChild(td);
				}
				body.appendChild(tr);
			}
		}
		lib.setElementLoaded(tableElt);
	}

	function fetchDynTables() {
		console.log("[dyn-table] Searching for dynamic tables...");
		const dynTables = document.querySelectorAll("table[data-content]")
		for (let tableElt of dynTables) {
			let contentUrl = tableElt.getAttribute("data-content")
			lib.startElementLoading(tableElt);
			console.log(`[dyn-table] Treating tableElt '${tableElt.getAttribute("name")}'`);
			fetchDynTable(contentUrl, tableElt);
		}
	}

	function fetchDynTable(location, tableElt) {
		console.log(`GET Fetch '${location}'`);
		fetch(location).then((response) => {
			mResponses[tableElt] = response;
			buildDynTable(tableElt);
		});
	}

	function buildDynTable(tableElt, textToFilter) {
		mResponses[tableElt].clone().json().then((data) => {
			processDynTableData(tableElt, data, textToFilter);
		});
	}

	function processDynTableData(tableElt, data, textToFilter) {
		mFilteredIds[tableElt] = [];
		for (let row of Object.values(data.rows)) {
			for (let field of row.fields) {
				console.log(`Filtering field '${field}' with filter '${textToFilter}'`);
				if (textToFilter === undefined || field.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().includes(textToFilter.toLowerCase())) {
					mFilteredIds[tableElt].push(row.id);
					break;
				}
			}
		}
		_populateTable(tableElt, data);
	}

	function bindSearchBoxes() {
		for (let searchBoxElt of document.querySelectorAll(".searchbox")) {
			const tableElt = document.querySelectorAll(`table[name="${searchBoxElt.name}"]`)[0];
			searchBoxElt.addEventListener("input", (evt) => {
				buildDynTable(tableElt, searchBoxElt.value);
			});
		}
	}

	function init() {
		fetchDynTables();
		bindSearchBoxes();
	}

	return {
		init: init,
		fetchDynTable: fetchDynTable,
	}

});
