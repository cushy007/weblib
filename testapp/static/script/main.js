require.config({
	paths: {
		bootstrap:    "/static/weblib/script/external/bootstrap.bundle",
		domReady:     "/static/weblib/script/external/domReady",
		html5Qrcode:  "/static/weblib/script/external/html5-qrcode",
		lib:          "/static/weblib/script/lib",
		log:          "/static/weblib/script/log",
		dyn_table:    "/static/weblib/script/dyn_table",
		qrcodeReader: "/static/weblib/script/qrcode-reader",
	}
});


requirejs(['domReady', 'lib', 'dyn_table'], function(domReady, lib, dyn_table) {

	require(['domReady'], function(domReady) {
		domReady(function () {
			console.log("Document ready");
			lib.init();
			dyn_table.init();

			// Business logic
			// ...

		});
	});

});
