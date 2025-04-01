//
// Copyright 2021-2025, Johann Saunier
// SPDX-License-Identifier: AGPL-3.0-or-later
//
/*
 * This is the facade for https://github.com/mebjas/html5-qrcode
 */
define(["log", "html5Qrcode"], function(log, html5Qrcode) {

	let html5QrcodeScanner = undefined;

	function start(elementId, onScannedCode, format) {

		let lastScannedCode = "";

		function onScanFailure(error) {
			console.warn(`Code scan error = ${error}`);
		}

		function onScanSuccess(decodedText, decodedResult) {
			console.log(`QR Code detected: ${decodedText}`);
			if (decodedText != lastScannedCode) {
				lastScannedCode = decodedText;
				beep();
				onScannedCode(decodedText);
			}
			else {
				console.log("Same QR Code -> debounce");
			}
		}

		function beep() {
			let audioUrl = '/static/weblib/beep.ogg';

			console.log("Will beep...");
			new Audio(audioUrl).play();
		}

		qrboxSize = (format == Html5QrcodeSupportedFormats.EAN_13) ? {width: 500, height: 250} : {width: 300, height: 300};
		html5QrcodeScanner = new Html5QrcodeScanner(
			elementId,
			{
				fps: 10,
				qrbox: qrboxSize,
				rememberLastUsedCamera: true,
				supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA],
				formatsToSupport: [format]
			},
			/* verbose= */ false
		);
		console.log("Rendering code scanner...");
		html5QrcodeScanner.render(onScanSuccess, onScanFailure);
	}

	function startQrcodeScan(elementId, onScannedCode) {
		start(elementId, onScannedCode, Html5QrcodeSupportedFormats.QR_CODE);
	}

	function startBarcodeScan(elementId, onScannedCode) {
		start(elementId, onScannedCode, Html5QrcodeSupportedFormats.EAN_13);
	}

	function stop() {
		html5QrcodeScanner.clear();
	}

	return {
		startQrcodeScan: startQrcodeScan,
		startBarcodeScan: startBarcodeScan,
		stop: stop,
	}

});
