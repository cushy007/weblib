//
// Copyright 2021-2025, Johann Saunier
// SPDX-License-Identifier: AGPL-3.0-or-later
//
define(["log"], function(log) {

	let mElementsBeingLoaded = new Set();

	function startElementLoading(elt) {
		document.querySelector("body").classList.remove("selenium-ready");
		mElementsBeingLoaded.add(elt);
	}

	function setElementLoaded(elt) {
		mElementsBeingLoaded.delete(elt);
		if (mElementsBeingLoaded.size == 0) {
			document.querySelector("body").classList.add("selenium-ready");
		}
	}

	function fetchGet(location, params, callback) {
		let request = location;
		if (params) {
			request = request + "?" + new URLSearchParams(params).toString();
		}
		console.log(`GET Fetch '${request}'`);
		fetch(request, {
			method: "GET"
		})
		.then((response) => response.json())
		.then(callback);
	}

	function fetchGetIfNoneMatch(location, etag, callback) {
		let etagHeaders = new Headers();
		let request = location;
		etagHeaders.append('If-None-Match', [etag]);
		console.log(`GET Fetch if none match '${etag}' '${request}'`);
		fetch(request, {
			method: "GET",
			headers: etagHeaders,
		})
		.then((response) => {
			if (response.status == 304) {
				log.info(`response.status is "${response.status}`);
				return null;
			} else {
				log.info("response is ", response);
				return response;
			}
		})
		.then(callback);
	}

	function fetchPost(location, formData, callback) {
		console.log("POST Fetch with :");
		for (let elt of formData.entries()) {
			console.log(elt);
		}
		fetch(location, {
			"method": "POST",
			"body": formData
		})
		.then((response) => response.json())
		.then(callback);
	}

	function _populateOptions(data, selectElt) {
		console.log("data =");
		console.log(data);
		selectElt.replaceChildren();
		for (pair of data) {
			let option = document.createElement("option");
			option.setAttribute("value", pair[0]);
			option.innerHTML = pair[1];
			selectElt.appendChild(option);
		}
		setElementLoaded(selectElt);
	}

	function bindSelects() {
		console.log("[bindSelects] binding interdependent selects");
		const elts = document.getElementsByClassName("double-select");
		for (let elt of elts) {
			const parentSelect = elt.querySelector("select[data-parent-select]");
			const childSelect = elt.querySelector("select[data-child-select]");
			const choicesUrl = childSelect.getAttribute("choices-url");
			if (childSelect.querySelector("option") === null) {
				startElementLoading(childSelect);
				fetchGet(choicesUrl, {
						'fetch': `${childSelect.getAttribute("name")}.choices`,
						'get_children': parentSelect.querySelector("option").getAttribute("value")
					}, (data) => {
					_populateOptions(data, childSelect);
				});
			}
			parentSelect.addEventListener("change", (evt) => {
				startElementLoading(childSelect);
				console.log("[double select] event triggered from lib !");
				setTimeout(() => {
					fetchGet(choicesUrl, {
							'fetch': `${childSelect.getAttribute("name")}.choices`,
							'get_children': evt.target.value
						}, (data) => {
						_populateOptions(data, childSelect);
					});
					console.log("[double select] event end from lib");
				}, 300);
			});
		}
	}

	function attachConfirmationBox(elt, message) {
		elt.addEventListener("click", (evt) => {
			console.log("[displayConfirmationBox] ask for confirmation");
			if (! confirm(message)) {
				evt.preventDefault();
				evt.stopImmediatePropagation();
			}
		}, false);
	}

	function bindConfirmableElements() {
		console.log("[bindConfirmableElements] binding confirmable elements to a confirmation box");
		for (let elt of document.getElementsByClassName("confirmable")) {
			console.log(`${elt} is confirmable -> attach click`);
			attachConfirmationBox(elt, "Confirm ?");
		}
	}

	function populateDataLists() {
		console.log("[populateDataLists] populating choices of input search elements");
		for (let fieldElt of document.querySelectorAll(".datalist")) {
			const inputElt = fieldElt.querySelector("[choices-url]");
			const hiddenElt = fieldElt.querySelector('[type="hidden"]');
			const choicesElt = fieldElt.querySelector(`[name=${hiddenElt.getAttribute("name")}-choices]`);
			const listElt = fieldElt.querySelector("ul");
			console.log(`${hiddenElt.getAttribute("name")} is datalist`);

			function buildDatalist(choices) {
				console.log(`[populateDataLists] choices are '${choices}'`);
				console.log(inputElt);
				inputElt.addEventListener("input", (evt) => {
					hiddenElt.value = inputElt.value;
					let str = evt.target.value.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
					console.log(`${inputElt} has changed to ${str}`);
					let filteredChoices = [];
					for (let choice of choices) {
						let normalizedStr = choice[1].normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase()
						if (normalizedStr.toLowerCase().includes(str)) {
							filteredChoices.push(choice);
						}
					}
					console.log(`Filtered choices are ${filteredChoices}`);
					listElt.replaceChildren();
					for (let choice of filteredChoices) {
						let li = document.createElement("li");
						li.classList.add("dropdown-item");
						li.innerHTML = choice[1];
						li.addEventListener("click", (evt) => {
							hiddenElt.value = choice[0];
							inputElt.value = choice[1];
							hideElement(listElt);
							inputElt.focus();
						});
						listElt.appendChild(li);
					}
					if (filteredChoices.length > 0 && filteredChoices.length < 10) {
						showElement(listElt);
					} else {
						hideElement(listElt);
					}
				});
				//~ fieldElt.addEventListener("focusout", (evt) => {
				inputElt.addEventListener("keydown", (evt) => {
					keyName = evt.key;
					if (keyName == "ArrowDown") {
						console.log("ArrowDown");
						listElt.querySelector("li:nth-child(1)").focus();
						listElt.querySelector("li").focus();
					}
				});
				inputElt.addEventListener("focus", (evt) => {
					hideElement(listElt);
				});
			}

			if (choicesElt) {
				buildDatalist(JSON.parse(choicesElt.getAttribute("value")));
			} else {
				fetchGet(inputElt.getAttribute("choices-url"), "", buildDatalist);
			}
		}
	}

	function bindXcodeFields(format) {
		for (let qrcodeReaderElt of document.querySelectorAll(`[data-${format}]`)) {
			require(['qrcodeReader'], (qrcodeReader) => {
				console.log(`[bindXcodeFields] binding ${format} element`)
				let inputElt = qrcodeReaderElt.querySelector("input");
				let btnElt = qrcodeReaderElt.querySelector("button");
				let cameraElt = qrcodeReaderElt.querySelector("[data-camera]");
				let cameraEltId = cameraElt.getAttribute("id");
				btnElt.addEventListener("click", (evt) => {
					if (! cameraElt.classList.contains("shown")) {
						showElement(cameraElt);
						console.log(`Trigger ${format} reading...`);
						readerFactory = (format == "barcode") ? qrcodeReader.startBarcodeScan : qrcodeReader.startQrcodeScan;
						readerFactory(cameraEltId, qrcodeReader.barcode, (decodedText) => {
							console.log(`${format} read: ${decodedText}`);
							inputElt.value = decodedText;
							hideElement(cameraElt);
						});
					} else {
						console.log(`Stop ${format} reading`);
						qrcodeReader.stop();
						hideElement(cameraElt);
					}
				});
			});
		}
	}

	function bindBarcodeFields() {
		bindXcodeFields("barcode");
	}

	function bindQrcodeFields() {
		bindXcodeFields("qrcode");
	}

	function showElement(elt) {
		elt.classList.remove("hidden");
		elt.classList.add("shown");
	}

	function hideElement(elt) {
		elt.classList.remove("shown");
		elt.classList.add("hidden");
	}

	function init() {
		log.init("debug");
		mElementsBeingLoaded.clear();
		bindSelects();
		bindConfirmableElements();
		populateDataLists();
		bindBarcodeFields();
		bindQrcodeFields();
		if (mElementsBeingLoaded.size == 0) {
			document.querySelector("body").classList.add("selenium-ready");
		}
		bindPasswordToggle();
	}

	function displayPopup(eltId, message, isSuccess, timeout) {
		let popupElt = document.getElementById(eltId);
		console.log("[displayPopup] displaying popup");
		popupElt.innerHTML = message;
		if (isSuccess) {
			popupElt.classList.remove("alert-danger");
			popupElt.classList.add("alert-success");
		} else {
			popupElt.classList.remove("alert-success");
			popupElt.classList.add("alert-danger");
		}
		showElement(popupElt);
		if (timeout !== undefined) {
			setTimeout(() => {
				popupElt.innerHTML = "";
				hideElement(popupElt);
			}, timeout * 1000);
		}
	}

	function hidePopup(eltId) {
		let popupElt = document.getElementById(eltId);
		console.log("[hidePopup] hiding popup");
		hideElement(popupElt);
	}

	function normalizeNFD(str) {
		return str.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
	}

	function bindPasswordToggle() {
		for (let elt of document.getElementsByClassName("password-toggle")) {
			elt.addEventListener("click", (evt) => {
				passwordField = document.getElementById(elt.id.replace("-toggle", ""));
				console.log(`toggle ${passwordField.id} visibility`);
				passwordField.type = (passwordField.type === "password") ? "text" : "password";
			});
		}
	}

	return {
		startElementLoading: startElementLoading,
		setElementLoaded: setElementLoaded,
		bindSelects: bindSelects,
		attachConfirmationBox: attachConfirmationBox,
		bindConfirmableElements: bindConfirmableElements,
		bindPasswordToggle: bindPasswordToggle,
		fetchGet: fetchGet,
		fetchGetIfNoneMatch: fetchGetIfNoneMatch,
		fetchPost: fetchPost,
		showElement: showElement,
		hideElement: hideElement,
		displayPopup: displayPopup,
		hidePopup: hidePopup,
		normalizeNFD: normalizeNFD,
		init: init,
	}

});
